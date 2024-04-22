"""protocol.parser module."""

from __future__ import annotations

import json
from collections import deque
from dataclasses import dataclass
from enum import IntEnum, auto


class ProtocolError(Exception):
    """Protocol error."""

    def __init__(self, invalid_byte: int, bad_value: bytes) -> None:
        self.bad_value = bad_value
        self.invalid_byte = invalid_byte
        super().__init__(f"unexpected byte: {bytes([invalid_byte])}")


class State(IntEnum):
    OP_START = 0
    OP_PLUS = auto()
    OP_PLUS_O = auto()
    OP_PLUS_OK = auto()
    OP_MINUS = auto()
    OP_MINUS_E = auto()
    OP_MINUS_ER = auto()
    OP_MINUS_ERR = auto()
    OP_MINUS_ERR_SPC = auto()
    MINUS_ERR_ARG = auto()
    OP_M = auto()
    OP_MS = auto()
    OP_MSG = auto()
    OP_MSG_SPC = auto()
    MSG_ARG = auto()
    MSG_PAYLOAD = auto()
    MSG_END = auto()
    OP_H = auto()
    OP_HM = auto()
    OP_HMS = auto()
    OP_HMSG = auto()
    OP_HMSG_SPC = auto()
    HMSG_ARG = auto()
    HMSG_END = auto()
    HMSG_PAYLOAD = auto()
    OP_P = auto()
    OP_PI = auto()
    OP_PIN = auto()
    OP_PING = auto()
    OP_PO = auto()
    OP_PON = auto()
    OP_PONG = auto()
    OP_I = auto()
    OP_IN = auto()
    OP_INF = auto()
    OP_INFO = auto()
    OP_INFO_SPC = auto()
    INFO_ARG = auto()
    OP_END = auto()


class Character(IntEnum):
    # +/-
    plus = ord("+")
    minus = ord("-")
    # ok
    o = ord("o")
    O = ord("O")
    k = ord("k")
    K = ord("K")
    # err
    e = ord("e")
    E = ord("E")
    r = ord("r")
    R = ord("R")
    # pub
    p = ord("p")
    P = ord("P")
    u = ord("u")
    U = ord("U")
    b = ord("b")
    B = ord("B")
    # sub
    s = ord("s")
    S = ord("S")
    # hpub
    h = ord("h")
    H = ord("H")
    # msg
    m = ord("m")
    M = ord("M")
    g = ord("g")
    G = ord("G")
    # ping
    i = ord("i")
    I = ord("I")
    n = ord("n")
    N = ord("N")
    # info
    f = ord("f")
    F = ord("F")
    # special characters
    space = ord(" ")
    newline = ord("\n")
    carriage_return = ord("\r")
    left_json_bracket = ord("{")


class Operation(IntEnum):
    OK = 0
    ERR = auto()
    MSG = auto()
    HMSG = auto()
    INFO = auto()
    PING = auto()
    PONG = auto()


@dataclass
class Event:
    """NATS Protocol event."""

    operation: Operation


@dataclass
class ErrorEvent(Event):
    """NATS Protocol error event."""

    message: str


@dataclass
class MsgEvent(Event):
    """NATS Protocol message event."""

    sid: int
    subject: str
    reply_to: str
    payload: bytes
    header: bytes


@dataclass
class Version:
    major: int
    minor: int
    patch: int
    dev: str

    def as_string(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}-{self.dev}"

    def __eq__(self, other: "Version") -> bool:
        if not isinstance(other, Version):
            return False
        return (
            self.major == other.major
            and self.minor == other.minor
            and self.patch == other.patch
            and self.dev == other.dev
        )

    def __gt__(self, other: "Version") -> bool:
        if not isinstance(other, Version):
            raise TypeError("unorderable types: Version() > {}".format(type(other)))
        if self.major > other.major:
            return True
        if self.major == other.major:
            if self.minor > other.minor:
                return True
            if self.minor == other.minor:
                if self.patch > other.patch:
                    return True
                if self.patch == other.patch:
                    return self.dev > other.dev
        return False


@dataclass
class InfoEvent(Event):
    proto: int
    server_id: str
    server_name: str
    version: Version
    go: str
    host: str
    port: int
    max_payload: int | None
    headers: bool | None
    client_id: int | None
    auth_required: bool | None
    tls_required: bool | None
    tls_verify: bool | None
    tls_available: bool | None
    connect_urls: list[str] | None
    ws_connect_urls: list[str] | None
    ldm: bool | None
    git_commit: str | None
    jetstream: bool | None
    ip: str | None
    client_ip: str | None
    nonce: str | None
    cluster: str | None
    domain: str | None
    xkey: str | None


CRLF = bytes([Character.carriage_return, Character.newline])
CRLF_SIZE = len(CRLF)


def parse_info(data: bytes) -> InfoEvent:
    raw_info = json.loads(data.decode())
    return InfoEvent(
        operation=Operation.INFO,
        server_id=raw_info["server_id"],
        server_name=raw_info["server_name"],
        version=parse_version(raw_info["version"]),
        go=raw_info["go"],
        host=raw_info["host"],
        port=raw_info["port"],
        headers=raw_info["headers"],
        proto=raw_info["proto"],
        max_payload=raw_info.get("max_payload"),
        client_id=raw_info.get("client_id"),
        auth_required=raw_info.get("auth_required"),
        tls_required=raw_info.get("tls_required"),
        tls_verify=raw_info.get("tls_verify"),
        tls_available=raw_info.get("tls_available"),
        connect_urls=raw_info.get("connect_urls"),
        ws_connect_urls=raw_info.get("ws_connect_urls"),
        ldm=raw_info.get("ldm"),
        git_commit=raw_info.get("git_commit"),
        jetstream=raw_info.get("jetstream"),
        ip=raw_info.get("ip"),
        client_ip=raw_info.get("client_ip"),
        nonce=raw_info.get("nonce"),
        cluster=raw_info.get("cluster"),
        domain=raw_info.get("domain"),
        xkey=raw_info.get("xkey"),
    )


def parse_version(version: str) -> Version:
    semver = Version(0, 0, 0, "")
    v = version.split("-")
    if len(v) > 1:
        semver.dev = v[1]
    tokens = v[0].split(".")
    n = len(tokens)
    if n > 1:
        semver.major = int(tokens[0])
    if n > 2:
        semver.minor = int(tokens[1])
    if n > 3:
        semver.patch = int(tokens[2])
    return semver


def make_history(max_length: int) -> deque[State]:
    if max_length < -1:
        raise ValueError(
            "history must be -1, 0 or a positive integer. "
            "-1 means unlimited history. "
            "0 means no history. "
            "A positive integer means the maximum number of states to keep in history excluding the current state."
        )
    if __debug__:
        maxlen = max_length + 1 if max_length >= 0 else None
    else:
        if max_length:
            raise ValueError("history is only available in debug mode")
        maxlen = 1
    return deque([State.OP_START], maxlen=maxlen)
