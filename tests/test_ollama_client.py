from __future__ import annotations

import json
import unittest
import urllib.error
from unittest.mock import MagicMock, patch

from animatube.ai.ollama_client import OllamaClient, OllamaError


def response(payload: dict) -> MagicMock:
    mock = MagicMock()
    mock.__enter__.return_value = mock
    mock.read.return_value = json.dumps(payload).encode("utf-8")
    return mock


class OllamaClientTests(unittest.TestCase):
    """Keep host/model environment settings from the developer machine out of mocks."""

    @patch.dict("os.environ", {}, clear=True)
    def test_default_host_is_loopback_and_model_is_not_hardcoded(self):
        client = OllamaClient()
        self.assertEqual(client.host, "http://127.0.0.1:11434")
        self.assertIsNone(client.model)

    def test_rejects_invalid_host_and_timeout(self):
        with self.assertRaises(ValueError):
            OllamaClient(host="localhost:11434")
        with self.assertRaises(ValueError):
            OllamaClient(timeout_seconds=0)

    @patch.dict("os.environ", {}, clear=True)
    @patch("urllib.request.urlopen")
    def test_lists_installed_models(self, mock_urlopen):
        mock_urlopen.return_value = response({
            "models": [{"name": "qwen2.5:7b"}, {"model": "llama3.2:latest"}]
        })
        client = OllamaClient()
        self.assertEqual(client.list_models(), ["llama3.2:latest", "qwen2.5:7b"])

    @patch.dict("os.environ", {}, clear=True)
    @patch("urllib.request.urlopen")
    def test_health_check_reports_unavailable_without_raising(self, mock_urlopen):
        mock_urlopen.side_effect = urllib.error.URLError("connection refused")
        result = OllamaClient().health_check()
        self.assertFalse(result["available"])
        self.assertEqual(result["models"], [])
        self.assertIn("Cannot reach Ollama", result["error"])

    @patch.dict("os.environ", {}, clear=True)
    @patch("urllib.request.urlopen")
    def test_resolves_the_only_installed_model_automatically(self, mock_urlopen):
        mock_urlopen.return_value = response({"models": [{"name": "qwen2.5:7b"}]})
        self.assertEqual(OllamaClient().resolve_model(), "qwen2.5:7b")

    @patch.dict("os.environ", {}, clear=True)
    @patch("urllib.request.urlopen")
    def test_requires_explicit_selection_when_multiple_models_are_installed(self, mock_urlopen):
        mock_urlopen.return_value = response({
            "models": [{"name": "qwen2.5:7b"}, {"name": "llama3.2:latest"}]
        })
        with self.assertRaisesRegex(OllamaError, "select a model explicitly"):
            OllamaClient().resolve_model()

    @patch.dict("os.environ", {}, clear=True)
    @patch("urllib.request.urlopen")
    def test_rejects_a_model_that_is_not_installed(self, mock_urlopen):
        mock_urlopen.return_value = response({"models": [{"name": "qwen2.5:7b"}]})
        with self.assertRaisesRegex(OllamaError, "not installed"):
            OllamaClient(model="llama3").resolve_model()

    @patch.dict("os.environ", {}, clear=True)
    @patch("urllib.request.urlopen")
    def test_generates_a_structured_json_object(self, mock_urlopen):
        mock_urlopen.side_effect = [
            response({"models": [{"name": "qwen2.5:7b"}]}),
            response({"message": {"content": '{"title": "Magic Train", "scenes": []}'}}),
        ]
        result = OllamaClient().generate_json(
            "Create a short preschool episode outline.",
            system="You are the Little Dreamers story planner.",
        )
        self.assertEqual(result["title"], "Magic Train")
        self.assertEqual(result["scenes"], [])

        request = mock_urlopen.call_args_list[1].args[0]
        payload = json.loads(request.data.decode("utf-8"))
        self.assertEqual(payload["model"], "qwen2.5:7b")
        self.assertEqual(payload["format"], "json")
        self.assertFalse(payload["stream"])
        self.assertEqual(payload["messages"][0]["role"], "system")

    @patch.dict("os.environ", {}, clear=True)
    @patch("urllib.request.urlopen")
    def test_rejects_invalid_model_json(self, mock_urlopen):
        mock_urlopen.side_effect = [
            response({"models": [{"name": "qwen2.5:7b"}]}),
            response({"message": {"content": "not-json"}}),
        ]
        with self.assertRaisesRegex(OllamaError, "invalid JSON content"):
            OllamaClient().generate_json("Create an outline.")

    @patch.dict("os.environ", {}, clear=True)
    @patch("urllib.request.urlopen")
    def test_rejects_empty_prompt_and_invalid_temperature(self, _mock_urlopen):
        client = OllamaClient()
        with self.assertRaises(ValueError):
            client.generate_json("  ")
        with self.assertRaises(ValueError):
            client.generate_json("Create an outline.", temperature=2.1)


if __name__ == "__main__":
    unittest.main()
