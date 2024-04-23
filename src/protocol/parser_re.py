# Copyright 2024 Guillaume Charbonnier
# Copyright 2016-2023 The NATS Authors
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""
NATS protocol parser.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, Dict

from .common import (
    ErrorEvent,
    Event,
    MsgEvent,
    Operation,
    parse_info,
)

MSG_RE = re.compile(
    b"\\AMSG\\s+([^\\s]+)\\s+([^\\s]+)\\s+(([^\\s]+)[^\\S\r\n]+)?(\\d+)\r\n",
    re.IGNORECASE,
)
HMSG_RE = re.compile(
    b"\\AHMSG\\s+([^\\s]+)\\s+([^\\s]+)\\s+(([^\\s]+)[^\\S\r\n]+)?([\\d]+)\\s+(\\d+)\r\n",
    re.IGNORECASE,
)
OK_RE = re.compile(
    b"\\A\\+OK\\s*\r\n",
    re.IGNORECASE,
)
ERR_RE = re.compile(
    b"\\A-ERR\\s+('.+')?\r\n",
    re.IGNORECASE,
)
PING_RE = re.compile(
    b"\\APING\\s*\r\n",
    re.IGNORECASE,
)
PONG_RE = re.compile(
    b"\\APONG\\s*\r\n",
    re.IGNORECASE,
)
INFO_RE = re.compile(
    b"\\AINFO\\s+([^\r\n]+)\r\n",
    re.IGNORECASE,
)

INFO_OP = b"INFO"
CONNECT_OP = b"CONNECT"
PUB_OP = b"PUB"
MSG_OP = b"MSG"
HMSG_OP = b"HMSG"
SUB_OP = b"SUB"
UNSUB_OP = b"UNSUB"
PING_OP = b"PING"
PONG_OP = b"PONG"
OK_OP = b"+OK"
ERR_OP = b"-ERR"
MSG_END = b"\n"
_CRLF_ = b"\r\n"

OK = OK_OP + _CRLF_
PING = PING_OP + _CRLF_
PONG = PONG_OP + _CRLF_
CRLF_SIZE = len(_CRLF_)
OK_SIZE = len(OK)
PING_SIZE = len(PING)
PONG_SIZE = len(PONG)
MSG_OP_SIZE = len(MSG_OP)
ERR_OP_SIZE = len(ERR_OP)

# States
AWAITING_CONTROL_LINE = 1
AWAITING_MSG_PAYLOAD = 2
MAX_CONTROL_LINE_SIZE = 4096

# Protocol Errors
STALE_CONNECTION = "stale connection"
AUTHORIZATION_VIOLATION = "authorization violation"
PERMISSIONS_ERR = "permissions violation"


class Parser:
    def __init__(self, *args: object, **kwargs: object) -> None:
        self.reset()

    def __repr__(self) -> str:
        return f"<nats protocol parser state={self._state}>"

    def reset(self) -> None:
        self.buf = bytearray()
        self._state = AWAITING_CONTROL_LINE
        self.needed = 0
        self.header_needed = 0
        self.msg_arg: Dict[str, Any] = {}
        self._events: list[Event] = []
        self.__parser__ = self.__parse__()

    def events_received(self) -> list[Event]:
        events = self._events
        self._events = []
        return events

    def parse(self, data: bytes) -> None:
        self.buf.extend(data)
        self.__parser__.__next__()

    def __parse__(self):
        """
        Parses the wire protocol from NATS for the client
        and dispatches the subscription callbacks.
        """
        while True:
            if not self.buf:
                yield None
                continue
            if self._state == AWAITING_CONTROL_LINE:
                msg = MSG_RE.match(self.buf)
                if msg:
                    try:
                        subject, sid, _, reply, needed_bytes = msg.groups()
                        self.msg_arg["subject"] = subject
                        self.msg_arg["sid"] = int(sid)
                        if reply:
                            self.msg_arg["reply"] = reply
                        else:
                            self.msg_arg["reply"] = b""
                        self.needed = int(needed_bytes)
                        del self.buf[: msg.end()]
                        self._state = AWAITING_MSG_PAYLOAD
                        continue
                    except Exception:
                        raise ProtocolError("nats: malformed MSG")

                msg = HMSG_RE.match(self.buf)
                if msg:
                    try:
                        subject, sid, _, reply, header_size, needed_bytes = msg.groups()
                        self.msg_arg["subject"] = subject
                        self.msg_arg["sid"] = int(sid)
                        if reply:
                            self.msg_arg["reply"] = reply
                        else:
                            self.msg_arg["reply"] = b""
                        self.needed = int(needed_bytes)
                        self.header_needed = int(header_size)
                        del self.buf[: msg.end()]
                        self._state = AWAITING_MSG_PAYLOAD
                        continue
                    except Exception:
                        raise ProtocolError("nats: malformed MSG")

                ok = OK_RE.match(self.buf)
                if ok:
                    # Do nothing and just skip.
                    del self.buf[: ok.end()]
                    self._events.append(Event(Operation.OK))
                    continue

                err = ERR_RE.match(self.buf)
                if err:
                    err_msg = err.groups()
                    emsg = err_msg[0].decode().lower()
                    self._events.append(ErrorEvent(Operation.ERR, emsg))
                    del self.buf[: err.end()]
                    continue

                ping = PING_RE.match(self.buf)
                if ping:
                    del self.buf[: ping.end()]
                    self._events.append(Event(Operation.PING))
                    continue

                pong = PONG_RE.match(self.buf)
                if pong:
                    del self.buf[: pong.end()]
                    self._events.append(Event(Operation.PONG))
                    continue

                info = INFO_RE.match(self.buf)
                if info:
                    info_line = info.groups()[0]
                    self._events.append(parse_info(info_line))
                    del self.buf[: info.end()]
                    continue

                if len(self.buf) < MAX_CONTROL_LINE_SIZE and _CRLF_ in self.buf:
                    # FIXME: By default server uses a max protocol
                    # line of 4096 bytes but it can be tuned in latest
                    # releases, in that case we won't reach here but
                    # client ping/pong interval would disconnect
                    # eventually.
                    raise ProtocolError("nats: unknown protocol")
                else:
                    # If nothing matched at this point, then it must
                    # be a split buffer and need to gather more bytes.
                    yield None
                    continue

            elif self._state == AWAITING_MSG_PAYLOAD:
                if len(self.buf) >= self.needed + CRLF_SIZE:
                    hdr = None
                    subject = self.msg_arg["subject"]
                    sid = self.msg_arg["sid"]
                    reply = self.msg_arg["reply"]

                    # Consume msg payload from buffer and set next parser state.
                    if self.header_needed > 0:
                        hbuf = bytes(self.buf[: self.header_needed])
                        payload = bytes(self.buf[self.header_needed : self.needed])
                        hdr = hbuf
                        del self.buf[: self.needed + CRLF_SIZE]
                        self.header_needed = 0
                    else:
                        payload = bytes(self.buf[: self.needed])
                        del self.buf[: self.needed + CRLF_SIZE]

                    self._state = AWAITING_CONTROL_LINE
                    self._events.append(
                        MsgEvent(
                            Operation.HMSG if self.header_needed else Operation.MSG,
                            sid,
                            subject.decode(),
                            reply.decode(),
                            payload,
                            hdr or b"",
                        )
                    )
                else:
                    # Wait until we have enough bytes in buffer.
                    yield None
                    continue


class ProtocolError(Exception):
    def __init__(self, msg: str) -> None:
        super().__init__(msg)


if TYPE_CHECKING:
    from .common import Parser as ParserProtocol

    # Verify that Parser implements ParserProtocol
    parser: ParserProtocol = Parser()
