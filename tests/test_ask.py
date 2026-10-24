import sys
from types import SimpleNamespace

from app import ask


class FakeChat:
    def __init__(self):
        self.messages = []

    def send_message(self, message):
        self.messages.append(message)
        return SimpleNamespace(usage_metadata=None, text=f"回答: {message}")


class FakeClient:
    def __init__(self, chat, api_key):
        self.chats = SimpleNamespace(create=self.create_chat)
        self.chat = chat
        self.api_key = api_key
        self.created_with = None

    def create_chat(self, *, model):
        self.created_with = model
        return self.chat


def test_interactive_chat_keeps_history_for_follow_up_questions(monkeypatch, capsys):
    chat = FakeChat()
    client = FakeClient(chat, "test-key")

    def create_client(*, api_key):
        assert api_key == client.api_key
        return client

    monkeypatch.setattr(ask.genai, "Client", create_client)
    monkeypatch.setattr(ask, "get_api_key", lambda: "test-key")
    questions = iter(["続きの質問", "/exit"])
    monkeypatch.setattr("builtins.input", lambda _: next(questions))

    ask.interactive_chat("最初の質問")

    assert client.created_with == ask.MODEL
    assert chat.messages == ["最初の質問", "続きの質問"]
    output = capsys.readouterr().out
    assert "回答: 最初の質問" in output
    assert "回答: 続きの質問" in output


def test_main_keeps_default_single_question_mode(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["app.ask"])
    monkeypatch.setattr(ask, "ask", lambda question: f"回答: {question}")

    ask.main()

    assert f"[質問] {ask.DEFAULT_QUESTION}" in capsys.readouterr().out


def test_main_passes_initial_question_to_interactive_mode(monkeypatch):
    received = []
    monkeypatch.setattr(sys, "argv", ["app.ask", "--interactive", "最初の質問"])
    monkeypatch.setattr(
        ask, "interactive_chat", lambda question: received.append(question)
    )

    ask.main()

    assert received == ["最初の質問"]
