import pytest
from mcp import Client

from support_rag import server


@pytest.fixture
def anyio_backend():
    return "asyncio"


class FakeClient:
    embedding_model = "fake-embedding"
    generation_model = "fake-generation"


@pytest.mark.anyio
async def test_mcp_tool_returns_only_local_batch_metadata(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("SUPPORT_EXPORT_PATH", str(tmp_path / "tickets.json"))
    monkeypatch.setenv("SUPPORT_KNOWLEDGE_DIR", str(tmp_path))
    monkeypatch.setenv("SUPPORT_RAG_OUTPUT_PATH", str(tmp_path / "review.jsonl"))
    monkeypatch.setattr(server, "OllamaClient", lambda **kwargs: FakeClient())
    monkeypatch.setattr(
        server,
        "run_batch",
        lambda *args: {
            "processed": 2,
            "review_status": "unverified",
            "output_path": str(tmp_path / "review.jsonl"),
        },
    )

    async with Client(server.mcp) as client:
        result = await client.call_tool("run_local_rag_triage", {})

    assert not result.is_error
    assert result.structured_content["processed"] == 2
    assert result.structured_content["ticket_content_returned"] is False
    assert result.structured_content["review_status"] == "unverified"


@pytest.mark.anyio
async def test_mcp_tool_requires_a_local_export(monkeypatch) -> None:
    monkeypatch.delenv("SUPPORT_EXPORT_PATH", raising=False)

    async with Client(server.mcp) as client:
        result = await client.call_tool("run_local_rag_triage", {})

    assert result.is_error
    assert "SUPPORT_EXPORT_PATH" in str(result.content)