import json
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, Request, build_opener



NOTE_SCHEMA = {
    "type": "object",
    "properties": {
        "internal_note": {"type": "string"},
        "citations": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["internal_note", "citations"],
}


OLLAMA_BASE_URL = "http://127.0.0.1:11434"


class OllamaClient:
    def __init__(
        self,
        embedding_model: str = "nomic-embed-text",
        generation_model: str = "qwen2.5:3b",
    ) -> None:
        self.embedding_model = embedding_model
        self.generation_model = generation_model

    def embed(self, texts: list[str]) -> list[list[float]]:
        response = self._post("/api/embed", {"model": self.embedding_model, "input": texts})
        embeddings = response.get("embeddings")
        if not isinstance(embeddings, list) or any(not isinstance(item, list) for item in embeddings):
            raise RuntimeError("Ollama returned an invalid embedding response")
        return [[float(value) for value in item] for item in embeddings]

    def generate(self, prompt: str) -> str:
        response = self._post(
            "/api/generate",
            {
                "model": self.generation_model,
                "prompt": prompt,
                "stream": False,
                "format": NOTE_SCHEMA,
                "options": {"temperature": 0.1},
            },
        )
        result = response.get("response")
        if not isinstance(result, str):
            raise RuntimeError("Ollama returned an invalid generation response")
        return result

    @staticmethod
    def _post(path: str, payload: dict[str, object]) -> dict[str, object]:
        request = Request(
            f"{OLLAMA_BASE_URL}{path}",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with build_opener(ProxyHandler({})).open(request, timeout=300) as response:
                result = json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            raise RuntimeError(f"Ollama request failed with HTTP {error.code}") from error
        except URLError as error:
            raise RuntimeError(
                "Cannot reach local Ollama at 127.0.0.1:11434; start Ollama and retry"
            ) from error
        if not isinstance(result, dict):
            raise RuntimeError("Ollama returned an invalid response")
        return result