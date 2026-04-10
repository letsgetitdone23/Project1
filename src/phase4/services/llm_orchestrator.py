from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, Optional

import requests

from .llm_types import LLMRecommendationPayload


GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


class LLMOrchestrationError(Exception):
    pass


def _read_key_from_env_file() -> Optional[str]:
    project_root = Path(__file__).resolve().parents[3]
    env_file = project_root / ".env"
    if not env_file.exists():
        return None

    try:
        for line in env_file.read_text(encoding="utf-8-sig").splitlines():
            cleaned = line.strip()
            if not cleaned or cleaned.startswith("#") or "=" not in cleaned:
                continue
            key, value = cleaned.split("=", 1)
            if key.strip() == "GROQ_API_KEY":
                return value.strip().strip('"').strip("'")
    except Exception:
        return None
    return None


def _extract_json(text: str) -> Dict:
    content = text.strip()
    if content.startswith("```"):
        lines = content.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        content = "\n".join(lines).strip()
    start = content.find("{")
    end = content.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise LLMOrchestrationError("LLM response does not contain JSON object.")
    payload_text = content[start : end + 1]
    try:
        return json.loads(payload_text)
    except json.JSONDecodeError as exc:
        marker = payload_text.find('"recommendations"')
        if marker != -1:
            left = payload_text.rfind("{", 0, marker)
            right = payload_text.rfind("}")
            if left != -1 and right != -1 and right > left:
                try:
                    return json.loads(payload_text[left : right + 1])
                except json.JSONDecodeError:
                    pass
        raise LLMOrchestrationError("Failed to parse LLM JSON output.") from exc


def call_groq_recommendation(
    *,
    messages: list[dict[str, str]],
    model: Optional[str] = None,
    timeout_seconds: int = 20,
) -> LLMRecommendationPayload:
    api_key = os.getenv("GROQ_API_KEY") or _read_key_from_env_file()
    if not api_key:
        raise LLMOrchestrationError("Missing GROQ_API_KEY in environment.")

    chosen_model = model or os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

    try:
        response = requests.post(
            GROQ_API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": chosen_model,
                "messages": messages,
                "temperature": 0.2,
                "response_format": {"type": "json_object"},
            },
            timeout=timeout_seconds,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise LLMOrchestrationError("Groq API request failed.") from exc

    body = response.json()
    try:
        content = body["choices"][0]["message"]["content"]
    except Exception as exc:  # noqa: BLE001
        raise LLMOrchestrationError("Unexpected Groq response shape.") from exc

    parsed = _extract_json(content)
    try:
        return LLMRecommendationPayload.model_validate(parsed)
    except Exception as exc:  # noqa: BLE001
        raise LLMOrchestrationError("LLM output failed schema validation.") from exc

