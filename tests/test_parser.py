import itertools
import json

import pytest
from protocol import Backend, make_parser
from protocol.common import (
    OK_EVENT,
    PING_EVENT,
    PONG_EVENT,
    ErrorEvent,
    Event,
    HMsgEvent,
    InfoEvent,
    MsgEvent,
    ProtocolError,
    Version,
)
from protocol.parser_re import ParserRE as ParserRe


def fuzz_case(string: str, suffix: str | None = None) -> list[str]:
    return list(
        set(
            map(
                lambda parts: "".join(parts) + suffix if suffix else "".join(parts),
                itertools.product(*zip(string.upper(), string.lower())),
            )
        )
    )


def make_server_info(
    server_id: str = "test",
    server_name: str = "test",
    version: str = "0.0.0-test",
    go: str = "go0.0.0-test",
    host: str = "memory",
    port: int = 0,
    headers: bool = True,
    max_payload: int = 1024 * 1024,
    proto: int = 1,
    auth_required: bool | None = None,
    tls_required: bool | None = None,
    tls_verify: bool | None = None,
    tls_available: bool | None = None,
    connect_urls: list[str] | None = None,
    ws_connect_urls: list[str] | None = None,
    ldm: bool | None = None,
    git_commit: str | None = None,
    jetstream: bool | None = None,
    ip: str | None = None,
    client_ip: str | None = None,
    nonce: str | None = None,
    cluster: str | None = None,
    domain: str | None = None,
    xkey: str | None = None,
) -> str:
    info_dict: dict[str, object] = {
        "server_id": server_id,
        "server_name": server_name,
        "version": version,
        "go": go,
        "host": host,
        "port": port,
        "headers": headers,
        "max_payload": max_payload,
        "proto": proto,
    }
    if auth_required is not None:
        info_dict["auth_required"] = auth_required
    if tls_required is not None:
        info_dict["tls_required"] = tls_required
    if tls_verify is not None:
        info_dict["tls_verify"] = tls_verify
    if tls_available is not None:
        info_dict["tls_available"] = tls_available
    if connect_urls is not None:
        info_dict["connect_urls"] = connect_urls
    if ws_connect_urls is not None:
        info_dict["ws_connect_urls"] = ws_connect_urls
    if ldm is not None:
        info_dict["ldm"] = ldm
    if git_commit is not None:
        info_dict["git_commit"] = git_commit
    if jetstream is not None:
        info_dict["jetstream"] = jetstream
    if ip is not None:
        info_dict["ip"] = ip
    if client_ip is not None:
        info_dict["client_ip"] = client_ip
    if nonce is not None:
        info_dict["nonce"] = nonce
    if cluster is not None:
        info_dict["cluster"] = cluster
    if domain is not None:
        info_dict["domain"] = domain
    if xkey is not None:
        info_dict["xkey"] = xkey
    json_info = json.dumps(info_dict, separators=(",", ":"), sort_keys=True)
    return f"INFO {json_info}\r\n"


@pytest.mark.parametrize(
    "backend",
    [Backend.PARSER_300, Backend.PARSER_310, Backend.PARSER_RE],
)
class TestParserBasic:
    @pytest.fixture(autouse=True)
    def setup(self, backend: Backend) -> None:
        self.parser = make_parser(backend)

    def parse_text(self, data: str) -> list[Event]:
        self.parser.parse(data.encode("ascii"))
        if isinstance(self.parser, ParserRe):
            return self.parser.events_received()
        else:
            return self.parser.events_received()

    @pytest.mark.parametrize("data", fuzz_case("ping", "\r\n"))
    def test_parse_ping(self, data: str):
        events = self.parse_text(data)
        assert events == [
            PING_EVENT,
        ]

    @pytest.mark.parametrize("data", fuzz_case("pong", "\r\n"))
    def test_parse_pong(self, data: str):
        events = self.parse_text(data)
        assert events == [
            PONG_EVENT,
        ]

    @pytest.mark.parametrize("data", fuzz_case("+ok", "\r\n"))
    def test_parse_ok(self, data: str):
        events = self.parse_text(data)
        assert events == [
            OK_EVENT,
        ]

    @pytest.mark.parametrize(
        "data", fuzz_case("-err", " this is the error message\r\n")
    )
    def test_parse_err(self, data: str):
        if isinstance(self.parser, ParserRe):
            pytest.skip("ParserRe does not parse errors yet")
        events = self.parse_text(data)
        assert events == [
            ErrorEvent(message="this is the error message"),
        ]

    def test_parse_msg_with_empty_payload(self):
        events = self.parse_text("msg the.subject 1234 0\r\n\r\n")
        assert events == [
            MsgEvent(
                sid=1234,
                subject="the.subject",
                reply_to="",
                payload=bytearray(),
            ),
        ]

    def test_parse_msg_with_reply_and_empty_payload(self):
        events = self.parse_text("msg the.subject 1234 the.reply.subject 0\r\n\r\n")
        assert events == [
            MsgEvent(
                sid=1234,
                subject="the.subject",
                reply_to="the.reply.subject",
                payload=bytearray(),
            ),
        ]

    @pytest.mark.parametrize(
        "data", fuzz_case("msg", " the.subject 1234 12\r\nhello world!\r\n")
    )
    def test_parse_msg(self, data: str):
        events = self.parse_text(data)
        assert events == [
            MsgEvent(
                sid=1234,
                subject="the.subject",
                reply_to="",
                payload=bytearray(b"hello world!"),
            ),
        ]

    @pytest.mark.parametrize(
        "data",
        fuzz_case("msg", " the.subject 1234 the.reply.subject 12\r\nhello world!\r\n"),
    )
    def test_parse_msg_with_reply(self, data: str):
        events = self.parse_text(data)
        assert events == [
            MsgEvent(
                sid=1234,
                subject="the.subject",
                reply_to="the.reply.subject",
                payload=bytearray(b"hello world!"),
            ),
        ]

    def test_parse_hmsg_with_empty_header_and_empty_payload(self):
        if isinstance(self.parser, ParserRe):
            pytest.skip("ParserRe does not parse headers yet")
        events = self.parse_text("hmsg the.subject 1234 4 4\r\n\r\n\r\n\r\n")
        assert events == [
            HMsgEvent(
                sid=1234,
                subject="the.subject",
                reply_to="",
                payload=bytearray(),
                header=bytearray(),
            ),
        ]

    def test_parse_hmsg_with_header_and_empty_payload(self):
        if isinstance(self.parser, ParserRe):
            pytest.skip("ParserRe does not parse headers yet")
        events = self.parse_text(
            "hmsg the.subject 1234 22 22\r\nNATS/1.0\r\nFoo: Bar\r\n\r\n\r\n"
        )
        assert events == [
            HMsgEvent(
                sid=1234,
                subject="the.subject",
                reply_to="",
                payload=bytearray(),
                header=bytearray(b"NATS/1.0\r\nFoo: Bar"),
            ),
        ]

    @pytest.mark.parametrize(
        "data",
        ["hmsg the.subject 1234 18 30\r\nNATS/1.0\r\nA: B\r\n\r\nhello world!\r\n"],
    )
    def test_parse_hmsg(self, data: str):
        if isinstance(self.parser, ParserRe):
            pytest.skip("ParserRe does not parse headers yet")
        events = self.parse_text(data)
        assert events == [
            HMsgEvent(
                sid=1234,
                subject="the.subject",
                reply_to="",
                payload=bytearray(b"hello world!"),
                header=bytearray(b"NATS/1.0\r\nA: B"),
            ),
        ]

    @pytest.mark.parametrize(
        "data",
        [
            "hmsg the.subject 1234 the.reply.subject 18 30\r\nNATS/1.0\r\nA: B\r\n\r\nhello world!\r\n"
        ],
    )
    def test_parse_hmsg_with_reply(self, data: str):
        if isinstance(self.parser, ParserRe):
            pytest.skip("ParserRe does not parse headers yet")
        events = self.parse_text(data)
        assert events == [
            HMsgEvent(
                sid=1234,
                subject="the.subject",
                reply_to="the.reply.subject",
                payload=bytearray(b"hello world!"),
                header=bytearray(b"NATS/1.0\r\nA: B"),
            ),
        ]

    def test_parse_info(self):
        events = self.parse_text(make_server_info())
        assert events == [
            InfoEvent(
                proto=1,
                server_id="test",
                server_name="test",
                version=Version(major=0, minor=0, patch=0, dev="test"),
                go="go0.0.0-test",
                host="memory",
                port=0,
                max_payload=1048576,
                headers=True,
                client_id=None,
                auth_required=None,
                tls_required=None,
                tls_verify=None,
                tls_available=None,
                connect_urls=None,
                ws_connect_urls=None,
                ldm=None,
                git_commit=None,
                jetstream=None,
                ip=None,
                client_ip=None,
                nonce=None,
                cluster=None,
                domain=None,
                xkey=None,
            ),
        ]

    @pytest.mark.parametrize("data", ["ping\r\npong\r\n"])
    def test_parse_ping_pong(self, data: str):
        events = self.parse_text(data)
        assert events == [
            PING_EVENT,
            PONG_EVENT,
        ]

    @pytest.mark.parametrize("data", ["ping\r\n+ok\r\n"])
    def test_parse_ping_ok(self, data: str):
        events = self.parse_text(data)
        assert events == [PING_EVENT, OK_EVENT]

    @pytest.mark.parametrize(
        "data", ["-err the error message\r\n-err the other error message\r\n"]
    )
    def test_parse_err_err(self, data: str):
        if isinstance(self.parser, ParserRe):
            pytest.skip("ParserRe does not parse errors yet")
        events = self.parse_text(data)
        assert events == [
            ErrorEvent(message="the error message"),
            ErrorEvent(message="the other error message"),
        ]

    @pytest.mark.parametrize(
        "chunks",
        [
            [
                b"msg the.subject 1234 12\r\n",
                b"hello world!\r\n",
            ],
            [
                b"msg the.subject 1234 12\r\nhello",
                b" world!\r\n",
            ],
            [
                b"msg the.subject 1234 12\r\nhello",
                b" world!",
                b"\r\n",
            ],
            [
                b"msg the.subject",
                b" 1234 12\r\nhello world!\r\n",
            ],
            [
                b"msg the.subject",
                b" 1234 12\r\nhello world",
                b"!\r\n",
            ],
        ],
        ids=[
            "args_then_payload",
            "args_then_payload_in_chunks",
            "args_then_payload_in_chunks_then_cr",
            "chunked_args_then_payload",
            "chunked_args_then_chunked_payload",
        ],
    )
    def test_parse_msg_in_several_chunks(self, chunks: list[bytes]):
        for chunk in chunks:
            self.parser.parse(chunk)
        events = self.parser.events_received()
        assert events == [
            MsgEvent(
                sid=1234,
                subject="the.subject",
                reply_to="",
                payload=bytearray(b"hello world!"),
            ),
        ]

    @pytest.mark.parametrize(
        "chunks",
        [
            [
                b"msg the.subject 1234 the.reply.subject 12\r\n",
                b"hello world!\r\n",
            ],
            [
                b"msg the.subject 1234 the.reply.subject 12\r\nhello",
                b" world!\r\n",
            ],
            [
                b"msg the.subject 1234 the.reply.subject 12\r\nhello",
                b" world!",
                b"\r\n",
            ],
            [
                b"msg the.subject",
                b" 1234 the.reply.subject 12\r\nhello world!\r\n",
            ],
            [
                b"msg the.subject 1234 the.reply.",
                b"subject 12\r\nhello world",
                b"!\r\n",
            ],
        ],
        ids=[
            "args_then_payload",
            "args_then_payload_in_chunks",
            "args_then_payload_in_chunks_then_cr",
            "chunked_args_then_payload",
            "chunked_args_then_chunked_payload",
        ],
    )
    def test_parse_msg_with_reply_in_several_chunks(self, chunks: list[bytes]):
        for chunk in chunks:
            self.parser.parse(chunk)
        events = self.parser.events_received()
        assert events == [
            MsgEvent(
                sid=1234,
                subject="the.subject",
                reply_to="the.reply.subject",
                payload=bytearray(b"hello world!"),
            ),
        ]

    def test_parse_invalid(self):
        if isinstance(self.parser, ParserRe):
            pytest.skip("ParserRe does not parse errors yet")
        with pytest.raises(ProtocolError) as exc:
            self.parse_text("invalid\r\n")
        assert exc.match("unexpected byte:")
