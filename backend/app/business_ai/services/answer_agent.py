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


def _normalize_answer(result: dict) -> dict:
    if not isinstance(result.get("answer"), str) or not result["answer"].strip():
        raise ValueError("AI returned no business answer.")

    if not isinstance(result.get("key_findings"), list):
        result["key_findings"] = []

    if not isinstance(result.get("caveats"), list):
        result["caveats"] = []

    return result


def generate_business_answer(question: str, sql: str, summary: dict) -> dict:
    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")

    system_prompt = """
You are Aloko Business Answer AI, an expert business data analyst.

Explain the results of a database analysis clearly.
Use the user's question, SQL query, and supplied query results.
Never invent numbers or claim the results prove something they do not.
Summarize meaningful patterns and explain their business implications.

Return JSON only:
{
  "answer": "Clear business explanation",
  "key_findings": ["Important finding"],
  "caveats": []
}
Do not include Markdown fences or text outside the JSON.
"""

    user_content = json.dumps(
        {"question": question.strip(), "sql": sql, "results": summary},
        default=str,
    )

    content = generate_response(
        system_prompt=system_prompt,
        user_message=user_content,
        temperature=0.1,
        max_tokens=2000,
    )

    return _normalize_answer(_extract_json(content))


def generate_general_business_answer(
    question: str,
    dataset_context=None,
    limitation: str = "",
) -> dict:
    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")

    system_prompt = """
You are Aloko Business AI, a knowledgeable business adviser and analyst.

Answer business questions across industries, company sizes, and business
models. Topics can include sales, marketing, customer retention, pricing,
operations, finance, productivity, strategy, customer service, and growth.

Do not require an SQL query to give general business advice.
Give practical, specific, prioritized actions rather than vague slogans.
Adapt recommendations to any business details the user provides.
Ask for clarification only when it is genuinely necessary; otherwise state
reasonable assumptions and give a useful answer.

If the question asks for findings from business data, use only actual
query results supplied to you. Dataset schemas alone are not data findings.
Never invent company facts, dataset results, metrics, or numbers.
If the data has not been analyzed, say so briefly and still provide useful
general guidance. Explain what additional data would help where relevant.

Return JSON only:
{
  "answer": "Helpful, complete answer",
  "key_findings": ["Actionable recommendation or supported observation"],
  "caveats": ["Important limitation, if any"]
}
Do not include Markdown fences or text outside the JSON.
"""

    user_content = json.dumps(
        {
            "question": question.strip(),
            "available_dataset_schemas": dataset_context or [],
            "data_analysis_limitation": limitation or None,
        },
        default=str,
    )

    content = generate_response(
        system_prompt=system_prompt,
        user_message=user_content,
        temperature=0.2,
        max_tokens=2500,
    )

    return _normalize_answer(_extract_json(content))
