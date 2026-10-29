"""Swappable LLM providers over plain REST (OpenRouter / Groq / Gemini).

Lightweight ports of the Level-4 `providers.py` concept: one interface, three
brains. No SDKs — just `httpx`, which is already a project dependency. A
provider without a key is simply unavailable; agents degrade gracefully.
"""
from __future__ import annotations

import os
from typing import Any

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

DEFAULT_TIMEOUT = 20.0


class TransientProviderError(RuntimeError):
    """Provider-side blip worth retrying: 408/429/5xx or transport death."""

PROVIDERS = {
    "groq": {
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "key_var": "GROQ_API_KEY",
        "model_var": "GROQ_MODEL",
        "default_model": "openai/gpt-oss-120b",
    },
    "openrouter": {
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "key_var": "OPENROUTER_API_KEY",
        "model_var": "OPENROUTER_MODEL",
        "default_model": "nvidia/nemotron-3.5-lightning:free",
    },
    "gemini": {
        "url": "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        "key_var": "GEMINI_API_KEY",
        "model_var": "GEMINI_MODEL",
        "default_model": "gemini-3.8-flash",
    },
}

RESERVED_ALT = {  # second OpenRouter model behind the same key (L4 failover)
    "openrouter-alt": {
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "key_var": "OPENROUTER_API_KEY",
        "model_var": "OPENROUTER_MODEL_2",
        "default_model": "meta-llama/llama-3.3-70b-instruct:free",
    }
}


def _config(name: str):
    cfg = PROVIDERS.get(name) or RESERVED_ALT.get(name)
    if not cfg:
        return None
    key = os.environ.get(cfg["key_var"], "").strip()
    model = os.environ.get(cfg["model_var"], "").strip() or cfg["default_model"]
    return cfg, key, model


def provider_status() -> list[dict[str, str]]:
    out = []
    for name in list(PROVIDERS):
        cfg = _config(name)
        if not cfg:
            continue
        _, key, model = cfg
        out.append({"provider": name, "model": model, "available": bool(key)})
    return out


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.5, max=4),
    retry=retry_if_exception_type(TransientProviderError),
    reraise=True,
)

def _post_with_backoff(url: str, payload: dict, headers: dict, timeout: float) -> httpx.Response:
    """POST with tenacity: exponential backoff on rate-limits and 5xx, fast-fail on 4xx."""
    resp = httpx.post(url, json=payload, headers=headers, timeout=timeout)
    if resp.status_code in (408, 429) or resp.status_code >= 500:
        raise TransientProviderError(f"HTTP {resp.status_code}")
    return resp


def call_provider(name: str, prompt: str, timeout: float = DEFAULT_TIMEOUT) -> dict[str, Any]:
    """Send one chat prompt. Returns {ok, text|error, provider, model}."""
    import json as _json

    cfg = _config(name)
    if not cfg:
        return {"ok": False, "error": f"Unknown provider {name!r}", "provider": name, "model": ""}
    spec, key, model = cfg
    if not key:
        return {"ok": False, "error": f"No API key configured ({spec['key_var']})", "provider": name, "model": model}
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    try:
        if name.startswith("gemini"):
            url = spec["url"].format(model=model)
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            headers.pop("Authorization")
            headers["x-goog-api-key"] = key
        else:
            url = spec["url"]
            payload = {"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.3}
        resp = _post_with_backoff(url, payload, headers, timeout)
    except TransientProviderError as exc:
        return {"ok": False, "error": f"{name} rate-limited/unavailable after retries ({exc})",
                "provider": name, "model": model}
    except (httpx.HTTPError, OSError) as exc:
        return {"ok": False, "error": f"{name} request failed: {exc.__class__.__name__}", "provider": name, "model": model}
    if resp.status_code // 100 != 2:
        return {"ok": False, "error": f"{name} returned HTTP {resp.status_code}", "provider": name, "model": model}
    try:
        body = resp.json()
        if name.startswith("gemini"):
            text = body["candidates"][0]["content"]["parts"][0]["text"]
        else:
            text = body["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError, ValueError):
        return {"ok": False, "error": f"{name} returned an unreadable response body", "provider": name, "model": model}
    return {"ok": True, "text": text, "provider": name, "model": model}
