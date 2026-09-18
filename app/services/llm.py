import requests
from typing import Dict, Any, List

from app.config import settings


def build_prompt(
    user_message: str,
    analysis: Dict[str, Any],
    evidence: List[Dict[str, Any]],
) -> str:
    """
    Build a grounded prompt for an OpenAI-compatible LLM.

    The model is instructed to use only the supplied analysis
    and scientific evidence.
    """

    evidence_text = "\n\n".join(
        [
            (
                f"Source: {item.get('source')}\n"
                f"Title: {item.get('title')}\n"
                f"Topic: {item.get('topic')}\n"
                f"Evidence: {item.get('text')}"
            )
            for item in evidence
        ]
    )

    return f"""
You are an environmental science assistant.

User message:
{user_message}

Deterministic environmental analysis:
{analysis}

Retrieved scientific evidence:
{evidence_text}

Write a concise, scientifically cautious explanation for the user.

Rules:
1. Use only the supplied evidence and analysis.
2. Do not invent statistics.
3. Do not invent citations.
4. Clearly distinguish observations from model-based inference.
5. Do not claim a field diagnosis.
6. Explain important relationships between environmental variables.
7. Keep the answer understandable to a student or environmental practitioner.
""".strip()


def generate_llm_response(
    user_message: str,
    analysis: Dict[str, Any],
    evidence: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Call an OpenAI-compatible chat completion endpoint.

    Returns demo mode information when no API key is configured.
    """

    if settings.DEMO_MODE:
        return {
            "success": False,
            "text": "",
            "reason": "Demo mode is enabled."
        }

    if not settings.LLM_API_KEY:
        return {
            "success": False,
            "text": "",
            "reason": "No LLM API key configured."
        }

    prompt = build_prompt(
        user_message=user_message,
        analysis=analysis,
        evidence=evidence,
    )

    url = f"{settings.LLM_BASE_URL.rstrip('/')}/chat/completions"

    headers = {
        "Authorization": f"Bearer {settings.LLM_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": settings.LLM_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a careful environmental science "
                    "assistant grounded in provided evidence."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "temperature": 0.2,
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=60,
        )

        response.raise_for_status()

        result = response.json()

        text = (
            result.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
        )

        if not text:
            return {
                "success": False,
                "text": "",
                "reason": "LLM returned an empty response."
            }

        return {
            "success": True,
            "text": text,
            "reason": "LLM response generated successfully."
        }

    except requests.RequestException as exc:
        return {
            "success": False,
            "text": "",
            "reason": f"LLM request failed: {exc}"
        }