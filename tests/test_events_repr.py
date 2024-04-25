from __future__ import annotations

from protocol.common import ErrorEvent, OkEvent, PingEvent, PongEvent


def test_ping_event_repr() -> None:
    event = PingEvent()
    assert repr(event) == "Event(Operation.PING)"


def test_pong_event_repr() -> None:
    event = PongEvent()
    assert repr(event) == "Event(Operation.PONG)"


def test_ok_event_repr() -> None:
    event = OkEvent()
    assert repr(event) == "Event(Operation.OK)"


def test_err_event_repr() -> None:
    err = ErrorEvent("the error message")
    assert repr(err) == "Event(Operation.ERR, 'the error message')"


def test_err_event_repr_empty() -> None:
    err = ErrorEvent("")
    assert repr(err) == "Event(Operation.ERR, '')"
