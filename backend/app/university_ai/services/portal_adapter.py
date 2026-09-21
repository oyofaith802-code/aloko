# ============================================================
# ALOKO UNIVERSITY AI
# REAL PORTAL INTEGRATION - ADAPTER ENGINE
# Phase 8.6.4.1
# ============================================================

from __future__ import annotations

from app.university_ai.services.portal_secrets import decrypt_secret
import json
import time
from dataclasses import dataclass
from typing import Any, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen


DEFAULT_TIMEOUT = 15
DEFAULT_RETRIES = 3
DEFAULT_PAGE_SIZE = 100
MAX_PAGE_SIZE = 500


class PortalAdapterError(RuntimeError):
    """Raised when a portal adapter cannot complete an operation."""


@dataclass(frozen=True)
class PortalResponse:
    status_code: int
    data: Any
    headers: dict[str, str]
    url: str


class PortalAdapter:
    """
    Generic REST/JSON adapter.

    The adapter deliberately knows nothing about a university's schema.
    Each university can expose its own endpoint paths while Aloko keeps
    one stable integration interface.
    """

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        timeout: int = DEFAULT_TIMEOUT,
        retries: int = DEFAULT_RETRIES,
        user_agent: str = "Aloko-University-Integration/1.0",
    ) -> None:
        if not base_url or not base_url.strip():
            raise ValueError("Portal API base URL is required.")

        self.base_url = base_url.strip().rstrip("/") + "/"
        self.api_key = decrypt_secret(api_key)
        self.client_id = client_id
        self.client_secret = decrypt_secret(client_secret)
        self.timeout = max(1, int(timeout))
        self.retries = max(0, int(retries))
        self.user_agent = user_agent

    # --------------------------------------------------------
    # HTTP
    # --------------------------------------------------------

    def _headers(self, extra: Mapping[str, str] | None = None) -> dict[str, str]:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": self.user_agent,
        }

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        # These headers allow portals that use client credentials to
        # identify the integration without exposing the client secret.
        if self.client_id:
            headers["X-Aloko-Client-Id"] = self.client_id

        if extra:
            headers.update(dict(extra))

        return headers

    def _url(self, path: str, params: Mapping[str, Any] | None = None) -> str:
        path = str(path or "").strip()
        if not path:
            raise ValueError("Portal endpoint path is required.")

        url = urljoin(self.base_url, path.lstrip("/"))
        if params:
            clean = {k: v for k, v in params.items() if v is not None}
            if clean:
                url += ("&" if "?" in url else "?") + urlencode(clean)
        return url

    @staticmethod
    def _retryable_status(status_code: int) -> bool:
        return status_code == 408 or status_code == 425 or status_code == 429 or status_code >= 500

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        body: Mapping[str, Any] | list[Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> PortalResponse:
        url = self._url(path, params)
        payload = None
        if body is not None:
            payload = json.dumps(body, ensure_ascii=False).encode("utf-8")

        request = Request(
            url,
            data=payload,
            headers=self._headers(headers),
            method=method.upper(),
        )

        last_error: Exception | None = None

        for attempt in range(self.retries + 1):
            try:
                with urlopen(request, timeout=self.timeout) as response:
                    raw = response.read()
                    text = raw.decode("utf-8", errors="replace")
                    data = self._decode_body(text)
                    return PortalResponse(
                        status_code=int(response.status),
                        data=data,
                        headers={k: v for k, v in response.headers.items()},
                        url=url,
                    )

            except HTTPError as exc:
                last_error = exc
                if not self._retryable_status(exc.code) or attempt >= self.retries:
                    message = self._safe_http_error(exc)
                    raise PortalAdapterError(message) from exc

            except URLError as exc:
                last_error = exc
                if attempt >= self.retries:
                    raise PortalAdapterError(
                        f"Portal network error: {exc.reason}"
                    ) from exc

            except TimeoutError as exc:
                last_error = exc
                if attempt >= self.retries:
                    raise PortalAdapterError("Portal request timed out.") from exc

            # Bounded exponential backoff: 0.5s, 1s, 2s...
            time.sleep(min(2.0, 0.5 * (2**attempt)))

        raise PortalAdapterError("Portal request failed.") from last_error

    @staticmethod
    def _decode_body(text: str) -> Any:
        if not text.strip():
            return None
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return text

    @staticmethod
    def _safe_http_error(exc: HTTPError) -> str:
        # Never include request headers or credentials in an error.
        return f"Portal returned HTTP {exc.code}."

    # --------------------------------------------------------
    # Common operations
    # --------------------------------------------------------

    def health_check(self, path: str = "") -> dict[str, Any]:
        response = self.request("GET", path or "/")
        return {
            "success": 200 <= response.status_code < 300,
            "status_code": response.status_code,
            "url": response.url,
        }

    def get(
        self,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
    ) -> PortalResponse:
        return self.request("GET", path, params=params)

    def post(
        self,
        path: str,
        *,
        body: Mapping[str, Any] | list[Any] | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> PortalResponse:
        return self.request("POST", path, params=params, body=body)

    def put(
        self,
        path: str,
        *,
        body: Mapping[str, Any] | list[Any] | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> PortalResponse:
        return self.request("PUT", path, params=params, body=body)

    # --------------------------------------------------------
    # Pagination
    # --------------------------------------------------------

    def get_collection(
        self,
        path: str,
        *,
        page_size: int = DEFAULT_PAGE_SIZE,
        max_pages: int = 100,
        page_param: str = "page",
        size_param: str = "limit",
    ) -> list[dict[str, Any]]:
        """
        Read a JSON collection from conventional page/limit endpoints.

        Supported response shapes include:
        - [ {...}, {...} ]
        - {"data": [...]}
        - {"results": [...]}
        - {"items": [...]}
        - {"records": [...]}

        Pagination stops when a page is shorter than page_size or the
        response contains no collection items.
        """
        page_size = min(MAX_PAGE_SIZE, max(1, int(page_size)))
        max_pages = max(1, int(max_pages))
        records: list[dict[str, Any]] = []

        for page in range(1, max_pages + 1):
            response = self.get(
                path,
                params={page_param: page, size_param: page_size},
            )
            items = self.extract_items(response.data)

            if not items:
                break

            for item in items:
                if isinstance(item, dict):
                    records.append(item)
                else:
                    records.append({"value": item})

            if len(items) < page_size:
                break

        return records

    @staticmethod
    def extract_items(data: Any) -> list[Any]:
        if isinstance(data, list):
            return data

        if not isinstance(data, dict):
            return []

        for key in ("data", "results", "items", "records", "students", "lecturers", "courses"):
            value = data.get(key)
            if isinstance(value, list):
                return value

        return []


# ============================================================
# NORMALIZATION
# ============================================================

FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "external_id": ("id", "uuid", "external_id", "student_id", "staff_id", "course_id"),
    "matric_number": ("matric_number", "matric", "matric_no", "registration_number", "reg_no"),
    "staff_number": ("staff_number", "staff_id", "employee_id", "employee_no"),
    "code": ("code", "course_code", "courseCode"),
    "title": ("title", "name", "course_name", "course_title"),
    "first_name": ("first_name", "firstname", "given_name", "firstName"),
    "last_name": ("last_name", "lastname", "surname", "family_name", "lastName"),
    "middle_name": ("middle_name", "middlename", "other_name", "middleName"),
    "email": ("email", "email_address", "emailAddress"),
    "phone": ("phone", "phone_number", "mobile"),
    "department_id": ("department_id", "departmentId", "dept_id"),
    "programme_id": ("programme_id", "programmeId", "program_id", "programId"),
    "session": ("session", "academic_session", "academicSession", "session_name"),
    "semester": ("semester", "academic_semester", "academicSemester"),
    "score": ("score", "marks", "mark", "value", "total_score"),
}


def first_value(record: Mapping[str, Any], aliases: tuple[str, ...]) -> Any:
    for key in aliases:
        if key in record and record[key] is not None:
            return record[key]
    return None


def normalize_record(record: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize common portal naming differences without guessing values."""
    normalized = dict(record)
    for canonical, aliases in FIELD_ALIASES.items():
        value = first_value(record, aliases)
        if value is not None:
            normalized[canonical] = value
    return normalized


def normalize_records(records: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [normalize_record(record) for record in records]


# ============================================================
# ENTITY ENDPOINT MAP
# ============================================================

DEFAULT_ENDPOINTS = {
    "students": "/students",
    "lecturers": "/lecturers",
    "faculties": "/faculties",
    "departments": "/departments",
    "programmes": "/programmes",
    "courses": "/courses",
    "results": "/results",
    "fees": "/fees",
    "clearance": "/clearance",
}


def fetch_entity_collection(
    adapter: PortalAdapter,
    entity_type: str,
    *,
    endpoint: str | None = None,
    page_size: int = DEFAULT_PAGE_SIZE,
    max_pages: int = 100,
) -> list[dict[str, Any]]:
    entity_type = (entity_type or "").strip().lower()
    path = endpoint or DEFAULT_ENDPOINTS.get(entity_type)
    if not path:
        raise ValueError(f"Unsupported portal entity type: {entity_type}")

    records = adapter.get_collection(
        path,
        page_size=page_size,
        max_pages=max_pages,
    )
    return normalize_records(records)
