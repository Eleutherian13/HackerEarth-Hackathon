from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from typing import Any

from app.core.config import settings


class LLMClientError(Exception):
    """Exception raised when LLM integration is unavailable or fails."""


class LLMClient:
    @classmethod
    def _openai_api_key(cls) -> str:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise LLMClientError("OPENAI_API_KEY is not configured")
        return api_key

    @classmethod
    def _openai_base_url(cls) -> str:
        base_url = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
        return base_url.rstrip("/")

    @classmethod
    def _build_headers(cls) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {cls._openai_api_key()}",
        }

    @classmethod
    def _clean_response(cls, raw_text: str) -> str:
        cleaned = re.sub(r"```(?:json)?", "", raw_text, flags=re.IGNORECASE).strip()
        first = cleaned.find("{")
        last = cleaned.rfind("}")
        if first >= 0 and last >= 0 and last > first:
            cleaned = cleaned[first:last + 1]
        return cleaned

    @classmethod
    def call_model(cls, prompt: str) -> str:
        payload = {
            "model": settings.EXTRACTION_MODEL,
            "temperature": settings.EXTRACTION_TEMPERATURE,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a structured extraction assistant. Return valid JSON only.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        }
        data = json.dumps(payload).encode("utf-8")
        request_url = f"{cls._openai_base_url()}/chat/completions"
        request = urllib.request.Request(request_url, data=data, headers=cls._build_headers(), method="POST")

        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                body = response.read().decode("utf-8")
                parsed = json.loads(body)
                message = parsed["choices"][0]["message"]["content"]
                return cls._clean_response(message)
        except urllib.error.HTTPError as error:
            message = error.read().decode("utf-8") if error.fp else str(error)
            raise LLMClientError(f"LLM request failed: {message}")
        except urllib.error.URLError as error:
            raise LLMClientError(f"LLM request failed: {error.reason}")
        except (KeyError, json.JSONDecodeError) as error:
            raise LLMClientError(f"LLM response parsing failed: {str(error)}")


class FallbackLLMClient(LLMClient):
    @classmethod
    def call_model(cls, prompt: str) -> str:
        raise LLMClientError("No external LLM client available")
