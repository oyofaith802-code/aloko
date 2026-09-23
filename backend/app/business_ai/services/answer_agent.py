import json
import os
import re

import requests
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_URL = (
    "https://generativelanguage.googleapis.com/"
    "v1beta/models/{model}:generateContent"
)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.8-flash",
)


def _extract_json(text: str) -> dict:
    text = text.strip()

    text = re.sub(
        r"^```(?:json)?\\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"\\s*```$",
        "",
        text,
        flags=re.IGNORECASE,
    )

    match = re.search(
        r"\\{.*\\}",
        text,
        flags=re.DOTALL,
    )

    if not match:
        raise ValueError(
            "AI did not return valid JSON."
        )

    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"AI returned invalid JSON: {str(exc)}"
        ) from exc


def generate_business_answer(
    question: str,
    sql: str,
    summary: dict,
) -> dict:

    if not question or not question.strip():
        raise ValueError(
            "Question cannot be empty."
        )

    if not GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured for Business AI."
        )

    system_prompt = """
You are Aloko Business Answer AI.

Your job is to explain database analysis results
to a business user in clear natural language.

The SQL query has already been generated and executed.

You MUST use ONLY the information contained in:

1. The user's question
2. The SQL query
3. The query results

Never invent numbers.
Never invent facts.
Never claim information that is not supported by
the query results.

Do not recalculate results incorrectly.

If the result is a ranking, identify the most important
ranking results.

If the result contains multiple rows, summarize the
important patterns rather than dumping every row.

If the result contains one value, explain what that value
means in the context of the question.

Keep the answer concise but useful.

The answer should sound like a professional business
analyst speaking to a business owner.

============================================================
OUTPUT
============================================================

Return JSON ONLY:

{
  "answer": "Clear business explanation",
  "key_findings": [
    "Important finding 1",
    "Important finding 2"
  ],
  "caveats": [
    "Important limitation if one exists"
  ]
}

If there are no meaningful caveats, return:

"caveats": []

Never return Markdown.
Never return SQL as the answer.
Never return code fences.
Never return text outside the JSON object.
"""

    user_content = json.dumps(
        {
            "question": question.strip(),
            "sql": sql,
            "results": summary,
        },
        default=str,
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": (
                            system_prompt
                            + "\n\nBUSINESS ANALYSIS INPUT:\n"
                            + user_content
                        )
                    }
                ]
            }
        ]
    }

    response = requests.post(
        GEMINI_API_URL.format(
            model=GEMINI_MODEL
        ),
        headers={
            "x-goog-api-key": GEMINI_API_KEY,
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=120,
    )

    response.raise_for_status()

    data = response.json()

    content = (
        data
        .get("candidates", [{}])[0]
        .get("content", {})
        .get("parts", [{}])[0]
        .get("text", "")
    )

    result = _extract_json(content)

    answer = result.get("answer")

    if not answer:
        raise ValueError(
            "AI returned no business answer."
        )

    if not isinstance(
        result.get("key_findings"),
        list,
    ):
        result["key_findings"] = []

    if not isinstance(
        result.get("caveats"),
        list,
    ):
        result["caveats"] = []

    return result
