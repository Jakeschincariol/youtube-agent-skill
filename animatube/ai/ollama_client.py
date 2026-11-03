from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any


class OllamaError(RuntimeError):
    """Raised when the local Ollama service cannot complete a request."""


class OllamaClient:
    """Small standard-library client for local Ollama model discovery and JSON chat.

    The default host is loopback-only. A model can be selected explicitly through
    the constructor or OLLAMA_MODEL. If neither is set, a single installed model
    is selected automatically; multiple installed models require an explicit
    choice so production output is reproducible.
    """

    def __init__(
        self,
        host: str | None = None,
        model: str | None = None,
        timeout_seconds: float = 60.0,
    ) -> None:
        resolved_host = (host or os.getenv("OLLAMA_HOST") or "http://127.0.0.1:11434").rstrip("/")
        if not resolved_host.startswith(("http://", "https://")):
            raise ValueError("Ollama host must start with http:// or https://")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be greater than zero")

        self.host = resolved_host
        self.model = model or os.getenv("OLLAMA_MODEL") or None
        self.timeout_seconds = timeout_seconds

    def _request_json(self, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            f"{self.host}{path}",
            data=data,
            headers={"Content-Type": "application/json"} if data is not None else {},
            method="GET" if data is None else "POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            try:
                detail = exc.read().decode("utf-8", errors="replace")
            except Exception:
                detail = str(exc)
            raise OllamaError(f"Ollama returned HTTP {exc.code}: {detail[:500]}") from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise OllamaError(f"Cannot reach Ollama at {self.host}: {exc}") from exc

        try:
            result = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise OllamaError("Ollama returned an invalid JSON response") from exc
        if not isinstance(result, dict):
            raise OllamaError("Ollama returned an unexpected response shape")
        if result.get("error"):
            raise OllamaError(str(result["error"]))
        return result

    def health_check(self) -> dict[str, Any]:
        """Return service reachability and the installed model names."""
        try:
            payload = self._request_json("/api/tags")
            models = self._model_names(payload)
            return {
                "available": True,
                "host": self.host,
                "models": models,
                "error": None,
            }
        except OllamaError as exc:
            return {
                "available": False,
                "host": self.host,
                "models": [],
                "error": str(exc),
            }

    def list_models(self) -> list[str]:
        """Return installed model names from Ollama's /api/tags endpoint."""
        return self._model_names(self._request_json("/api/tags"))

    @staticmethod
    def _model_names(payload: dict[str, Any]) -> list[str]:
        entries = payload.get("models", [])
        if not isinstance(entries, list):
            raise OllamaError("Ollama /api/tags response has an invalid models field")

        names: list[str] = []
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            name = entry.get("name") or entry.get("model")
            if isinstance(name, str) and name.strip() and name not in names:
                names.append(name)
        return sorted(names)

    def resolve_model(self, model: str | None = None) -> str:
        """Resolve and verify the selected model against locally installed models."""
        installed = self.list_models()
        requested = model or self.model

        if requested:
            match = next(
                (
                    name
                    for name in installed
                    if name == requested or (":" not in requested and name.startswith(f"{requested}:"))
                ),
                None,
            )
            if match is None:
                raise OllamaError(
                    f"Model '{requested}' is not installed. Installed models: "
                    f"{', '.join(installed) if installed else 'none'}"
                )
            return match

        if not installed:
            raise OllamaError("No Ollama models are installed. Pull a model before generating content.")
        if len(installed) > 1:
            raise OllamaError(
                "More than one Ollama model is installed. Set OLLAMA_MODEL or select a model explicitly: "
                + ", ".join(installed)
            )
        return installed[0]

    def generate_json(
        self,
        prompt: str,
        *,
        system: str | None = None,
        model: str | None = None,
        temperature: float = 0.4,
    ) -> dict[str, Any]:
        """Generate a JSON object through /api/chat using Ollama's JSON mode."""
        if not prompt.strip():
            raise ValueError("prompt must not be empty")
        if not 0.0 <= temperature <= 2.0:
            raise ValueError("temperature must be between 0.0 and 2.0")

        selected_model = self.resolve_model(model)
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = self._request_json(
            "/api/chat",
            {
                "model": selected_model,
                "messages": messages,
                "stream": False,
                "format": "json",
                "options": {"temperature": temperature},
            },
        )
        message = response.get("message")
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(content, str):
            raise OllamaError("Ollama chat response did not contain message.content")

        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as exc:
            raise OllamaError("Ollama model returned invalid JSON content") from exc
        if not isinstance(parsed, dict):
            raise OllamaError("Ollama model must return a JSON object")
        return parsed
