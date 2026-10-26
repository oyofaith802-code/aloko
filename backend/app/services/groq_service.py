import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from groq import Groq

_BACKEND_DIR = Path(__file__).resolve().parents[2]
load_dotenv(_BACKEND_DIR / ".env")


def generate_response(
    system_prompt: str,
    user_message: str,
    model: Optional[str] = None,
    temperature: float = 0.2,
    max_tokens: int = 1024,
) -> str:
    """Generate a text response through Groq without exposing credentials."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is missing from backend/.env")

    selected_model = model or os.getenv(
        "GROQ_MODEL",
        "llama-3.3-70b-versatile",
    )

    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model=selected_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )

    if not response.choices:
        raise RuntimeError("Groq returned no response choices.")

    content = response.choices[0].message.content
    if not content or not content.strip():
        raise RuntimeError("Groq returned an empty response.")

    return content.strip()
