import json
from urllib.error import URLError

import pytest

from support_rag.ollama import OllamaClient


class FakeResponse:
    def __init__(self, value: dict[str, object]) -> None:
        self.value = value

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.value).encode("utf-8")


class FakeOpener:
    def __init__(self, response: FakeResponse | Exception) -> None:
        self.response = response
        self.request = None
        self.timeout = 0

    def open(self, request, timeout: int) -> FakeResponse:
        self.request = request
        self.timeout = timeout
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


def test_embed_posts_text_to_local_endpoint_and_casts_values(monkeypatch) -> None:
    opener = FakeOpener(FakeResponse({"embeddings": [[1, 0.5]]}))
    monkeypatch.setattr("support_rag.ollama.build_opener", lambda handler: opener)
    client = OllamaClient()

    vectors = client.embed(["synthetic query"])

    assert vectors == [[1.0, 0.5]]
    assert opener.request.full_url == "http://127.0.0.1:11434/api/embed"
    assert json.loads(opener.request.data) == {
        "model": "nomic-embed-text",
        "input": ["synthetic query"],
    }


def test_generate_uses_json_schema_and_low_temperature(monkeypatch) -> None:
    opener = FakeOpener(FakeResponse({"response": '{"category":"other"}'}))
    monkeypatch.setattr("support_rag.ollama.build_opener", lambda handler: opener)
    client = OllamaClient()

    response = client.generate("synthetic prompt")

    request = json.loads(opener.request.data)
    assert response == '{"category":"other"}'
    assert opener.request.full_url == "http://127.0.0.1:11434/api/generate"
    assert request["model"] == "qwen2.5:3b"
    assert request["format"]["type"] == "object"
    assert request["options"]["temperature"] == 0.1


def test_local_connection_errors_are_actionable(monkeypatch) -> None:
    opener = FakeOpener(URLError("connection refused"))
    monkeypatch.setattr("support_rag.ollama.build_opener", lambda handler: opener)

    with pytest.raises(RuntimeError, match="start Ollama"):
        OllamaClient().embed(["synthetic query"])


def test_embed_rejects_invalid_response(monkeypatch) -> None:
    opener = FakeOpener(FakeResponse({"embeddings": "invalid"}))
    monkeypatch.setattr("support_rag.ollama.build_opener", lambda handler: opener)

    with pytest.raises(RuntimeError, match="invalid embedding response"):
        OllamaClient().embed(["synthetic query"])
