import asyncio
import logging
import os
from typing import Any, Dict, Optional

import httpx

from app.services.llm_explainability_service import (
    PROMPT_ENGINEERING_TECHNIQUE,
    SYSTEM_PROMPT,
    build_user_prompt,
    generate_deterministic_explanation,
)

logger = logging.getLogger(__name__)

GEMINI_MODEL = "gemini-3.6-flash"
GEMINI_TIMEOUT_SECONDS = 20

_configured_state: Optional[bool] = None
_last_available: Optional[bool] = None


def get_ai_status() -> Dict[str, Any]:
    global _configured_state, _last_available

    configured = bool(os.getenv("GEMINI_API_KEY", "").strip())
    if configured != _configured_state:
        _configured_state = configured
        _last_available = None

    available = bool(configured and _last_available is True)
    if not configured:
        status = "offline"
        reason = "gemini_not_configured"
    elif _last_available is False:
        status = "fallback"
        reason = "gemini_request_failed"
    elif _last_available is True:
        status = "online"
        reason = None
    else:
        status = "configured"
        reason = "availability_checked_on_explanation_request"

    return {
        "provider": "gemini" if configured and _last_available is not False else "offline",
        "mode": status,
        "available": available,
        "configured": configured,
        "availability_checked": _last_available is not None,
        "fallback_enabled": True,
        "reason": reason,
    }


def _record_availability(available: bool) -> None:
    global _configured_state, _last_available
    _configured_state = True
    _last_available = available


async def _request_gemini(api_key: str, prompt: str) -> str:
    endpoint = (
        "https://generativelanguage.googleapis.com/v1beta/"
        f"models/{GEMINI_MODEL}:generateContent"
    )
    payload = {
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "topP": 0.95,
            "maxOutputTokens": 1024,
        },
    }

    async with httpx.AsyncClient(timeout=GEMINI_TIMEOUT_SECONDS) as client:
        response = await client.post(
            endpoint,
            headers={"x-goog-api-key": api_key},
            json=payload,
        )
    response.raise_for_status()
    candidates = response.json().get("candidates", [])
    if not candidates:
        raise ValueError("Gemini returned no candidate explanation")
    parts = candidates[0].get("content", {}).get("parts", [])
    text = "".join(part.get("text", "") for part in parts)
    if not text.strip():
        raise ValueError("Gemini returned an empty explanation")
    return text


def _offline_result(prompt_data: Dict[str, Any]) -> Dict[str, Any]:
    result = generate_deterministic_explanation(prompt_data)
    result.update(
        {
            "provider": "offline",
            "mode": "offline",
            "fallback_used": True,
        }
    )
    return result


def _extract_sections(text: str) -> Dict[str, str]:
    sections = {"exec": "", "math": "", "runner_up": "", "sdg8": ""}
    for part in text.split("## "):
        heading = part[:80].lower()
        if "executive" in heading:
            sections["exec"] = part.split("\n", 1)[-1].strip()
        elif "mathematical" in heading:
            sections["math"] = part.split("\n", 1)[-1].strip()
        elif "runner-up" in heading:
            sections["runner_up"] = part.split("\n", 1)[-1].strip()
        elif "sdg" in heading:
            sections["sdg8"] = part.split("\n", 1)[-1].strip()
    return sections


async def generate_agent_explanation(prompt_data: Dict[str, Any]) -> Dict[str, Any]:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return _offline_result(prompt_data)

    try:
        text = await asyncio.wait_for(
            _request_gemini(api_key, build_user_prompt(prompt_data)),
            timeout=GEMINI_TIMEOUT_SECONDS,
        )

        sections = _extract_sections(text)
        _record_availability(True)
        return {
            "provider_used": f"Google Gemini ({GEMINI_MODEL})",
            "provider": "gemini",
            "mode": "online",
            "fallback_used": False,
            "explanation_markdown": text,
            "executive_summary": sections["exec"] or text[:250],
            "math_breakdown": sections["math"] or "See the full explanation for score details.",
            "runner_up_comparison": sections["runner_up"] or "See the full explanation for candidate comparison.",
            "sdg8_audit": sections["sdg8"] or "See the full explanation for fairness factors.",
            "is_fallback": False,
        }
    except Exception as exc:
        _record_availability(False)
        logger.warning(
            "Gemini explanation failed; using offline fallback (%s).",
            type(exc).__name__,
        )
        return _offline_result(prompt_data)


async def explain_allocation(
    task: Dict[str, Any],
    selected_worker: Dict[str, Any],
    runner_up: Optional[Dict[str, Any]],
    policy: str = "WAFR",
    lambda_val: float = 0.08,
) -> Dict[str, Any]:
    from app.services.llm_explainability_service import build_prompt_payload

    prompt_data = build_prompt_payload(
        task, selected_worker, runner_up, policy, lambda_val
    )
    result = await generate_agent_explanation(prompt_data)
    result["prompt_inspector"] = {
        "system_prompt": SYSTEM_PROMPT.strip(),
        "user_prompt": build_user_prompt(prompt_data),
        "prompt_engineering_technique": PROMPT_ENGINEERING_TECHNIQUE,
        "temperature": 0.2,
        "top_p": 0.95,
        "input_context_json": prompt_data,
    }
    return result
