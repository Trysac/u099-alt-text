"""Tests for the LLM port doubles."""

from __future__ import annotations

import pytest

from alt_text import AltTextError
from alt_text.llm import FakeLLM, Message, RecordedLLM, RecordingExhaustedError


def test_recorded_llm_replays_in_order_and_records_calls():
    llm = RecordedLLM(["one", "two"])
    assert llm.calls == []
    messages = [Message(role="user", content="hi")]
    assert llm.complete(messages, max_tokens=5) == "one"
    messages.append(Message(role="user", content="later"))
    reply = llm.complete_with_image(messages, image=b"abc", mime_type="image/png", max_tokens=7)
    assert reply == "two"
    assert len(llm.calls) == 2
    first, second = llm.calls
    assert first.messages == ({"role": "user", "content": "hi"},)
    assert first.image_size is None
    assert first.mime_type is None
    assert first.max_tokens == 5
    assert len(second.messages) == 2
    assert second.image_size == 3
    assert second.mime_type == "image/png"
    assert second.max_tokens == 7


def test_recorded_llm_runs_out_of_replies():
    llm = RecordedLLM(["only"])
    llm.complete([], max_tokens=1)
    with pytest.raises(RecordingExhaustedError) as excinfo:
        llm.complete([], max_tokens=1)
    assert isinstance(excinfo.value, AltTextError)
    assert excinfo.value.code == "invalid_reply"
    assert len(llm.calls) == 1


def test_fake_llm_delegates_to_the_function():
    seen = []

    def answer(messages):
        seen.append(len(messages))
        return "fake"

    llm = FakeLLM(answer)
    message = Message(role="system", content="s")
    assert llm.complete([message], max_tokens=1) == "fake"
    reply = llm.complete_with_image(
        [message, message], image=b"x", mime_type="image/gif", max_tokens=1
    )
    assert reply == "fake"
    assert seen == [1, 2]
