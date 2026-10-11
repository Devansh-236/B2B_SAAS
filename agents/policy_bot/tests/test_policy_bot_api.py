"""
Automated tests that run offline: fake embeddings and a scripted LLM stand in for
HuggingFace and Gemini, and the vector store lives in a temporary directory.
"""

import pytest
from fastapi.testclient import TestClient
from langchain_core.documents import Document
from langchain_core.embeddings import DeterministicFakeEmbedding
from langchain_core.language_models.fake_chat_models import FakeListChatModel

import api_server
import policy_agent
from policy_agent import PolicyBot

POLICY_DOCS = [
    Document(
        page_content="Employees may work remotely up to three days per week with manager approval.",
        metadata={"source": "/srv/kb/remote.txt", "filename": "remote.txt", "file_size": 80},
    ),
    Document(
        page_content="Full-time employees receive 20 vacation days per year.",
        metadata={"source": "/srv/kb/<img src=x onerror=alert(1)>.txt", "filename": "leave.txt", "file_size": 60},
    ),
]


class RecordingLLM(FakeListChatModel):
    """Fake chat model that remembers the prompts it received."""
    prompts: list = []

    def _call(self, messages, *args, **kwargs):
        self.prompts.append(messages[-1].content)
        return super()._call(messages, *args, **kwargs)


def make_bot(tmp_path, answers=("Up to three days per week [remote.txt].",)):
    llm = RecordingLLM(responses=list(answers), prompts=[])
    bot = PolicyBot(
        embeddings=DeterministicFakeEmbedding(size=32),
        llm=llm,
        vector_db_path=str(tmp_path / "vector_db"),
    )
    return bot, llm


@pytest.fixture
def client(tmp_path, monkeypatch):
    bot, llm = make_bot(tmp_path)
    bot.add_documents(POLICY_DOCS)
    monkeypatch.setattr(api_server, "get_policy_bot", lambda: bot)
    monkeypatch.setattr(api_server, "API_KEY", "")
    return TestClient(api_server.app), bot, llm


def test_empty_store_then_add_documents_builds_chain(tmp_path):
    bot, _ = make_bot(tmp_path)
    assert bot.vectorstore is None and bot.chain is None
    assert bot.ask_question("anything")["status"] == "error"

    assert bot.add_documents(POLICY_DOCS) == 2
    assert bot.chain is not None
    assert bot.get_knowledge_base_stats()["total_documents"] == 2


def test_re_adding_same_documents_does_not_duplicate(tmp_path):
    bot, _ = make_bot(tmp_path)
    bot.add_documents(POLICY_DOCS)
    bot.add_documents(POLICY_DOCS)
    assert bot.get_knowledge_base_stats()["total_documents"] == 2

    bot.replace_documents(POLICY_DOCS[:1])
    assert bot.get_knowledge_base_stats()["total_documents"] == 1


def test_existing_store_is_loaded_on_startup(tmp_path):
    bot, _ = make_bot(tmp_path)
    bot.add_documents(POLICY_DOCS)

    reloaded, _ = make_bot(tmp_path)
    assert reloaded.chain is not None
    assert reloaded.get_knowledge_base_stats()["total_documents"] == 2


def test_ask_returns_answer_and_only_safe_source_metadata(client):
    http, _, llm = client
    response = http.post("/ask", json={"question": "Can I work from home?", "user_id": "u1"})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["answer"].startswith("Up to three days")
    assert body["num_sources"] == 2
    for source in body["sources"]:
        assert set(source["metadata"]) == {"filename"}

    prompt = llm.prompts[-1]
    assert "<question>\nCan I work from home?\n</question>" in prompt
    assert "[remote.txt]" in prompt
    assert "Document(" not in prompt and "/srv/kb" not in prompt


def test_braces_in_company_name_do_not_break_prompt(tmp_path, monkeypatch):
    monkeypatch.setattr(policy_agent, "COMPANY_NAME", "Acme {Labs}")
    bot, llm = make_bot(tmp_path)
    bot.add_documents(POLICY_DOCS)
    assert bot.ask_question("vacation?")["status"] == "success"
    assert "Acme {Labs}" in llm.prompts[-1]


def test_llm_failure_returns_error_without_leaking_details(tmp_path):
    bot, llm = make_bot(tmp_path)
    bot.add_documents(POLICY_DOCS)

    def boom(*args, **kwargs):
        raise RuntimeError("secret internal detail")

    object.__setattr__(bot, "chain", type("Broken", (), {"invoke": staticmethod(boom)})())
    result = bot.ask_question("vacation?")
    assert result["status"] == "error"
    assert "secret internal detail" not in str(result)


def test_question_length_is_limited(client):
    http, _, _ = client
    response = http.post("/ask", json={"question": "x" * 5000})
    assert response.status_code == 422


def test_unknown_route_returns_json_404(client):
    http, _, _ = client
    response = http.get("/does-not-exist")
    assert response.status_code == 404
    assert response.json() == {"detail": "Not Found"}


def test_health_does_not_call_llm(client):
    http, _, llm = client
    response = http.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert llm.prompts == []


def test_api_key_is_enforced_when_configured(client, monkeypatch):
    http, _, _ = client
    monkeypatch.setattr(api_server, "API_KEY", "s3cret")

    assert http.post("/ask", json={"question": "vacation?"}).status_code == 401
    assert http.get("/stats", headers={"X-API-Key": "wrong"}).status_code == 401
    ok = http.get("/stats", headers={"X-API-Key": "s3cret"})
    assert ok.status_code == 200
    assert ok.json() == {"total_documents": 2, "status": "active"}


def test_cors_rejects_unknown_origins(client):
    http, _, _ = client
    response = http.options(
        "/ask",
        headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "POST"},
    )
    assert response.headers.get("access-control-allow-origin") is None
