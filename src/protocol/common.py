"""protocol.parser module."""

from __future__ import annotations

import json
from enum import IntEnum, auto
from typing import Protocol


class ProtocolError(Exception):
    """Protocol error."""

    def __init__(self) -> None:
        super().__init__("nats: protocol error")


class ParserClosedError(Exception):
    """Parser closed error."""

    def __init__(self) -> None:
        super().__init__("nats: parser closed")


class Operation(IntEnum):
    OK = 0
    ERR = auto()
    MSG = auto()
    HMSG = auto()
    INFO = auto()
    PING = auto()
    PONG = auto()


class Event:
    """NATS Protocol event."""

    __slots__ = ["kind"]

    def __init__(self, op: Operation) -> None:
        self.kind = op

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, type(self)):
            return False
        return all(
            getattr(self, slot) == getattr(other, slot) for slot in self.__slots__
        )

    def __repr__(self) -> str:
        return f"Event(Operation.{self.kind.name})"


class Parser(Protocol):
    def close(self) -> None:
        """Close the parser."""
        raise NotImplementedError

    def parse(self, data: bytes | bytearray) -> None:
        """Parse the data."""
        raise NotImplementedError

    def events_received(self) -> list[Event]:
        """Return the list of events received."""
        raise NotImplementedError


class OkEvent(Event):
    """NATS Protocol OK event."""

    __slots__ = ["kind"]

    def __init__(self) -> None:
        super().__init__(Operation.OK)


class PingEvent(Event):
    """NATS Protocol ping event."""

    __slots__ = ["kind"]

    def __init__(self) -> None:
        super().__init__(Operation.PING)


class PongEvent(Event):
    """NATS Protocol pong event."""

    __slots__ = ["kind"]

    def __init__(self) -> None:
        super().__init__(Operation.PONG)


class ErrorEvent(Event):
    """NATS Protocol error event."""

    __slots__ = ["kind", "message"]

    def __init__(self, message: str) -> None:
        super().__init__(Operation.ERR)
        self.message = message

    def __repr__(self) -> str:
        return f"Event(Operation.{self.kind.name}, {repr(self.message)})"


class MsgEvent(Event):
    """NATS Protocol message event."""

    __slots__ = ["kind", "sid", "subject", "reply_to", "payload", "header"]

    def __init__(
        self,
        sid: int,
        subject: str,
        reply_to: str,
        payload: bytearray,
    ) -> None:
        super().__init__(Operation.MSG)
        self.sid = sid
        self.subject = subject
        self.reply_to = reply_to
        self.payload = payload
        self.header = bytearray()


class HMsgEvent(Event):
    """NATS Protocol message event."""

    __slots__ = ["kind", "sid", "subject", "reply_to", "payload", "header"]

    def __init__(
        self,
        sid: int,
        subject: str,
        reply_to: str,
        payload: bytearray,
        header: bytearray,
    ) -> None:
        self.kind = Operation.HMSG
        self.sid = sid
        self.subject = subject
        self.reply_to = reply_to
        self.payload = payload
        self.header = header


class Version:
    __slots__ = ["major", "minor", "patch", "dev"]

    def __init__(
        self,
        major: int,
        minor: int,
        patch: int,
        dev: str,
    ) -> None:
        self.major = major
        self.minor = minor
        self.patch = patch
        self.dev = dev

    def to_string(self) -> str:
        if self.dev:
            return f"{self.major}.{self.minor}.{self.patch}-{self.dev}"
        return f"{self.major}.{self.minor}.{self.patch}"

    def __repr__(self) -> str:
        return f"Version({self.major}, {self.minor}, {self.patch}, {repr(self.dev)})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Version):
            raise TypeError(f"cannot compare version with type {type(other)}")
        return (
            self.major == other.major
            and self.minor == other.minor
            and self.patch == other.patch
            and self.dev == other.dev
        )

    def __lt__(self, other: "Version") -> bool:
        if not isinstance(other, Version):  # pyright: ignore[reportUnnecessaryIsInstance]
            raise TypeError(f"cannot compare version with type {type(other)}")
        return (self.major, self.minor, self.patch, self.dev) < (
            other.major,
            other.minor,
            other.patch,
            other.dev,
        )

    def __gt__(self, other: "Version") -> bool:
        if not isinstance(other, Version):  # pyright: ignore[reportUnnecessaryIsInstance]
            raise TypeError(f"cannot compare version with type {type(other)}")
        return (self.major, self.minor, self.patch, self.dev) > (
            other.major,
            other.minor,
            other.patch,
            other.dev,
        )


class InfoEvent(Event):
    __slots__ = [
        "kind",
        "proto",
        "server_id",
        "server_name",
        "version",
        "go",
        "host",
        "port",
        "max_payload",
        "headers",
        "client_id",
        "auth_required",
        "tls_required",
        "tls_verify",
        "tls_available",
        "connect_urls",
        "ws_connect_urls",
        "ldm",
        "git_commit",
        "jetstream",
        "ip",
        "client_ip",
        "nonce",
        "cluster",
        "domain",
        "xkey",
    ]

    def __init__(
        self,
        proto: int,
        server_id: str,
        server_name: str,
        version: Version,
        go: str,
        host: str,
        port: int,
        max_payload: int | None,
        headers: bool | None,
        client_id: int | None,
        auth_required: bool | None,
        tls_required: bool | None,
        tls_verify: bool | None,
        tls_available: bool | None,
        connect_urls: list[str] | None,
        ws_connect_urls: list[str] | None,
        ldm: bool | None,
        git_commit: str | None,
        jetstream: bool | None,
        ip: str | None,
        client_ip: str | None,
        nonce: str | None,
        cluster: str | None,
        domain: str | None,
        xkey: str | None,
    ) -> None:
        self.kind = Operation.INFO
        self.proto = proto
        self.server_id = server_id
        self.server_name = server_name
        self.version = version
        self.go = go
        self.host = host
        self.port = port
        self.max_payload = max_payload
        self.headers = headers
        self.client_id = client_id
        self.auth_required = auth_required
        self.tls_required = tls_required
        self.tls_verify = tls_verify
        self.tls_available = tls_available
        self.connect_urls = connect_urls
        self.ws_connect_urls = ws_connect_urls
        self.ldm = ldm
        self.git_commit = git_commit
        self.jetstream = jetstream
        self.ip = ip
        self.client_ip = client_ip
        self.nonce = nonce
        self.cluster = cluster
        self.domain = domain
        self.xkey = xkey


def parse_info(data: bytearray | bytes) -> InfoEvent:
    try:
        raw_info = json.loads(data.decode())
    except ValueError:
        raise ProtocolError()
    return InfoEvent(
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
    if not version:
        semver.dev = "unknown"
        return semver
    v = version.split("-")
    if len(v) > 1:
        semver.dev = v[1]
    tokens = v[0].split(".")
    n = len(tokens)
    if n > 3:
        raise ValueError(f"invalid version: {version}")
    elif n > 2:
        semver.major = int(tokens[0])
        semver.minor = int(tokens[1])
        semver.patch = int(tokens[2])
    elif n > 1:
        semver.major = int(tokens[0])
        semver.minor = int(tokens[1])
    else:
        semver.major = int(tokens[0])
    return semver


PING_EVENT = PingEvent()
PONG_EVENT = PongEvent()
OK_EVENT = OkEvent()

CRLF = b"\r\n"
CRLF_SIZE = len(CRLF)
