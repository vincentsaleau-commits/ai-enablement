from support_rag import cli


class FakeClient:
    def __init__(self, embedding_model: str, generation_model: str) -> None:
        self.embedding_model = embedding_model
        self.generation_model = generation_model


def test_cli_runs_batch_and_prints_local_summary(monkeypatch, capsys) -> None:
    monkeypatch.setattr("sys.argv", ["support-rag", "--export", "tickets.json"])
    monkeypatch.setattr(cli, "OllamaClient", FakeClient)
    monkeypatch.setattr(
        cli,
        "run_batch",
        lambda export, knowledge, output, client: {
            "processed": 15,
            "review_status": "unverified",
            "output_path": "local-review.jsonl",
        },
    )

    assert cli.main() == 0
    assert "Processed 15 open tickets" in capsys.readouterr().out


def test_cli_reports_batch_errors_to_stderr(monkeypatch, capsys) -> None:
    monkeypatch.setattr("sys.argv", ["support-rag", "--export", "tickets.json"])
    monkeypatch.setattr(cli, "OllamaClient", FakeClient)
    monkeypatch.setattr(cli, "run_batch", lambda *args: (_ for _ in ()).throw(ValueError("bad export")))

    assert cli.main() == 1
    assert "RAG run failed: bad export" in capsys.readouterr().err


def test_cli_requires_an_export(monkeypatch) -> None:
    monkeypatch.setattr("sys.argv", ["support-rag"])

    try:
        cli.main()
    except SystemExit as error:
        assert error.code == 2
    else:
        raise AssertionError("CLI must reject a missing export")