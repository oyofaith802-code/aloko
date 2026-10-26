import json
import re

from app.services.groq_service import generate_response


def _extract_json(text: str) -> dict:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text, flags=re.IGNORECASE)

    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        raise ValueError("AI did not return valid JSON.")

    try:
        result = json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        raise ValueError(f"AI returned invalid JSON: {exc}") from exc

    if not isinstance(result, dict):
        raise ValueError("AI JSON response must be an object.")

    return result


def generate_business_answer(question: str, sql: str, summary: dict) -> dict:
    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")

    system_prompt = """
You are Aloko Business Answer AI.
Explain database analysis results clearly to a business user.
Use ONLY the user's question, SQL query, and supplied query results.
Never invent numbers or facts. Summarize important patterns concisely.
Return JSON ONLY with:
{
  "answer": "Clear business explanation",
  "key_findings": ["Important finding"],
  "caveats": []
}
Do not return Markdown, SQL as the answer, or text outside JSON.
"""

    user_content = json.dumps(
        {
            "question": question.strip(),
            "sql": sql,
            "results": summary,
        },
        default=str,
    )

    content = generate_response(
        system_prompt=system_prompt,
        user_message=user_content,
        temperature=0.1,
        max_tokens=2000,
    )

    result = _extract_json(content)

    if not result.get("answer"):
        raise ValueError("AI returned no business answer.")

    if not isinstance(result.get("key_findings"), list):
        result["key_findings"] = []

    if not isinstance(result.get("caveats"), list):
        result["caveats"] = []

    return result
