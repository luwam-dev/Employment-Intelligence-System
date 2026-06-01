import json
import re
from typing import Any

from ollama import ResponseError, chat

from src.config import SETTINGS


PROMPT_TEMPLATE = """
Extract current employment details from the public profile text.

Return JSON only.
Do not include markdown.
Do not include explanation.

Use exactly these keys:
company
role
location
evidence
confidence

Rules:
- Use only the provided text.
- Do not guess.
- If a field is unclear, return an empty string.
- confidence must be a number from 0 to 1.
- evidence must be a short quote or short summary from the text.
- If no clear employment evidence exists, return empty strings and confidence 0.

Person name: {name}

Profile text:
{text}
""".strip()


def empty_result() -> dict[str, str | float]:
    return {
        "company": "",
        "role": "",
        "location": "",
        "evidence": "",
        "confidence": 0.0,
    }


def clamp_confidence(value: Any) -> float:
    try:
        confidence = float(value or 0)
    except (TypeError, ValueError):
        return 0.0

    if confidence < 0:
        return 0.0

    if confidence > 1:
        return 1.0

    return confidence


def extract_json_text(raw_response: str) -> str:
    raw_response = raw_response.strip()

    if raw_response.startswith("{") and raw_response.endswith("}"):
        return raw_response

    match = re.search(r"\{.*\}", raw_response, flags=re.DOTALL)
    if match:
        return match.group(0)

    return ""


def parse_llm_response(raw_response: str) -> dict[str, str | float]:
    json_text = extract_json_text(raw_response)

    if not json_text:
        print("   Ollama returned no JSON")
        return empty_result()

    try:
        data = json.loads(json_text)
    except json.JSONDecodeError:
        print("   Ollama returned invalid JSON")
        return empty_result()

    return {
        "company": str(data.get("company", "") or "").strip(),
        "role": str(data.get("role", "") or "").strip(),
        "location": str(data.get("location", "") or "").strip(),
        "evidence": str(data.get("evidence", "") or "").strip(),
        "confidence": clamp_confidence(data.get("confidence", 0)),
    }


def extract_with_llm(name: object, text: object) -> dict[str, str | float]:
    name = str(name or "").strip()
    text = str(text or "").strip()

    if not name or not text:
        return empty_result()

    prompt = PROMPT_TEMPLATE.format(
        name=name,
        text=text[: SETTINGS.max_text_for_llm],
    )

    try:
        response = chat(
            model=SETTINGS.ollama_model,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            format="json",
        )

    except ResponseError as error:
        print(f"   Ollama response error: {error}")
        return empty_result()

    except ConnectionError as error:
        print(f"   Could not connect to Ollama: {error}")
        return empty_result()

    content = getattr(response.message, "content", "")
    raw_response = str(content or "").strip()

    if not raw_response:
        return empty_result()

    return parse_llm_response(raw_response)