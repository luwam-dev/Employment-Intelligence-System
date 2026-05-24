import json

from ollama import chat

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


def empty_result():
    return {
        "company": "",
        "role": "",
        "location": "",
        "evidence": "",
        "confidence": 0.0,
    }


def clamp_confidence(value):
    try:
        confidence = float(value or 0)
    except (TypeError, ValueError):
        return 0.0

    if confidence < 0:
        return 0.0

    if confidence > 1:
        return 1.0

    return confidence


def parse_llm_response(raw_response):
    try:
        data = json.loads(raw_response)
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


def extract_with_llm(name, text):
    name = str(name or "").strip()
    text = str(text or "").strip()

    if not name or not text:
        return empty_result()

    prompt = PROMPT_TEMPLATE.format(
        name=name,
        text=text[:SETTINGS.max_text_for_llm],
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

    except Exception as error:
        print(f"   Ollama request failed: {error}")
        return empty_result()

    raw_response = str(response.message.content or "").strip()

    if not raw_response:
        return empty_result()

    return parse_llm_response(raw_response)