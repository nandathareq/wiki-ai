import pytest
from service import llm


def test_response_generator_plain_text(monkeypatch):
    class DummyStream:
        def __iter__(self):
            yield type("obj", (), {"content": "Hello"})
            yield type("obj", (), {"content": " world"})

    monkeypatch.setattr(llm.chat, "stream", lambda context: DummyStream())

    context = [{"role": "user", "content": "Hi"}]
    result = "".join(llm.response_generator(context))
    assert "Hello world" in result
