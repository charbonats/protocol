"""
NATS protocol parser.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Iterator

from .common import (
    CRLF,
    CRLF_SIZE,
    ErrorEvent,
    Event,
    MsgEvent,
    Operation,
    ProtocolError,
    State3102,
    parse_info,
)

STOP_HEADER = bytearray(b"\r\n\r\n")
PING_OP = bytearray(b"PING")
PONG_OP = bytearray(b"PONG")
PING_OR_PONG_LEN = len(PING_OP)
PING_OR_PONG_OP_LEN = PING_OR_PONG_LEN + CRLF_SIZE


class Parser3102:
    """NATS Protocol parser."""

    __slots__ = ["_closed", "_state", "_data_received", "_events_received", "__loop__"]

    def __init__(self) -> None:
        # Initialize the parser state.
        self._closed = False
        self._data_received = bytearray()
        self._events_received: list[Event] = []
        # Initialize the parser iterator
        self.__loop__ = self.__parse__()

    def events_received(self) -> list[Event]:
        """Pop and return the events generated by the parser."""
        events = self._events_received
        self._events_received = []
        return events

    def parse(self, data: bytes | bytearray) -> None:
        self._data_received.extend(data)
        self.__loop__.__next__()

    def __parse__(self) -> Iterator[None]:
        """Parse some bytes."""

        expected_header_size = 0
        expected_total_size = 0
        partial_msg: MsgEvent | None = None
        state = State3102.AWAITING_CONTROL_LINE

        while not self._closed:
            # If there is no data to parse, yield None.
            if not self._data_received:
                yield None
                continue
            # Take the first byte
            next_byte = self._data_received[0]

            match state:
                case State3102.AWAITING_CONTROL_LINE:
                    match next_byte:
                        # case "m" | "M"
                        case 77 | 109:
                            try:
                                end = self._data_received.index(CRLF)
                            except ValueError:
                                yield None
                                continue

                            data = self._data_received[4:end]
                            args = data.decode().split(" ")
                            nbargs = len(args)
                            match nbargs:
                                case 4:
                                    subject, raw_sid, reply_to, raw_total_size = args
                                case 3:
                                    reply_to = ""
                                    subject, raw_sid, raw_total_size = args
                                case _:
                                    raise ProtocolError(next_byte, self._data_received)
                            try:
                                sid = int(raw_sid)
                                expected_total_size = int(raw_total_size)
                            except Exception as e:
                                raise ProtocolError(
                                    next_byte, self._data_received
                                ) from e
                            partial_msg = MsgEvent(
                                Operation.MSG,
                                sid=sid,
                                subject=subject,
                                reply_to=reply_to,
                                payload=bytearray(),
                                header=bytearray(),
                            )
                            state = State3102.AWAITING_MSG_PAYLOAD
                            self._data_received: bytearray = self._data_received[
                                end + 2 :
                            ]
                            continue
                        # case "H" | "h"
                        case 72 | 104:
                            # Fast path for HMSG
                            try:
                                end = self._data_received.index(CRLF)
                            except ValueError:
                                yield None
                                continue
                            args = self._data_received[5:end].decode().split(" ")
                            match len(args):
                                case 5:
                                    (
                                        subject,
                                        raw_sid,
                                        reply_to,
                                        raw_header_size,
                                        raw_total_size,
                                    ) = args
                                case 4:
                                    reply_to = ""
                                    (
                                        subject,
                                        raw_sid,
                                        raw_header_size,
                                        raw_total_size,
                                    ) = args
                                case _:
                                    raise ProtocolError(next_byte, self._data_received)
                            try:
                                expected_header_size = int(raw_header_size)
                                expected_total_size = int(raw_total_size)
                                sid = int(raw_sid)
                            except Exception as e:
                                raise ProtocolError(
                                    next_byte, self._data_received
                                ) from e
                            partial_msg = MsgEvent(
                                Operation.HMSG,
                                sid=sid,
                                subject=subject,
                                reply_to=reply_to,
                                payload=bytearray(),
                                header=bytearray(),
                            )
                            state = State3102.AWAITING_HMSG_PAYLOAD
                            self._data_received = self._data_received[end + 2 :]
                            continue
                        # case "P" | "p"
                        case 80 | 112:
                            # Fast path for PING or PONG
                            if len(self._data_received) >= PING_OR_PONG_OP_LEN:
                                data = self._data_received[:PING_OR_PONG_LEN].upper()
                                if data == PING_OP:
                                    self._events_received.append(Event(Operation.PING))
                                elif data == PONG_OP:
                                    self._events_received.append(Event(Operation.PONG))
                                else:
                                    raise ProtocolError(next_byte, self._data_received)
                                self._data_received = self._data_received[
                                    PING_OR_PONG_OP_LEN:
                                ]
                                continue
                            # Split buffer
                            else:
                                yield None
                                continue
                        # case "I" | "i
                        case 73 | 105:
                            if CRLF in self._data_received:
                                end = self._data_received.index(CRLF)
                                data = self._data_received[5:end]
                                self._data_received = self._data_received[
                                    end + CRLF_SIZE + 1 :
                                ]
                                state = State3102.AWAITING_CONTROL_LINE
                                try:
                                    self._events_received.append(parse_info(data))
                                except Exception as e:
                                    raise ProtocolError(next_byte, data) from e
                                continue
                            else:
                                yield None
                                continue
                        # case "+"
                        case 43:
                            if CRLF in self._data_received:
                                end = self._data_received.index(CRLF)
                                data = self._data_received[1:end]
                                self._data_received = self._data_received[
                                    end + CRLF_SIZE + 1 :
                                ]
                                state = State3102.AWAITING_CONTROL_LINE
                                self._events_received.append(Event(Operation.OK))
                                continue
                            else:
                                yield None
                                continue
                        # case "-"
                        case 45:
                            if CRLF in self._data_received:
                                end = self._data_received.index(CRLF)
                                msg = self._data_received[5:end].decode()
                                self._events_received.append(
                                    ErrorEvent(Operation.ERR, msg)
                                )
                                self._data_received = self._data_received[
                                    end + CRLF_SIZE :
                                ]
                                state = State3102.AWAITING_CONTROL_LINE
                                continue
                            else:
                                yield None
                                continue
                        # Anything else is an error
                        case _:
                            raise ProtocolError(next_byte, self._data_received)
                case State3102.AWAITING_HMSG_PAYLOAD:
                    assert partial_msg is not None, "pending_msg is None"
                    if len(self._data_received) >= expected_total_size + CRLF_SIZE:
                        msg = partial_msg
                        partial_msg = None
                        header = self._data_received[:expected_header_size]
                        if header[-4:] != STOP_HEADER:
                            raise ProtocolError(next_byte, header)
                        msg.header = header[:-4]
                        payload = self._data_received[
                            expected_header_size:expected_total_size
                        ]
                        msg.payload = payload
                        self._data_received = self._data_received[
                            expected_total_size + CRLF_SIZE + 1 :
                        ]
                        self._events_received.append(msg)
                        state = State3102.AWAITING_CONTROL_LINE
                        continue
                    else:
                        yield None
                        continue
                case State3102.AWAITING_MSG_PAYLOAD:
                    assert partial_msg is not None, "pending_msg is None"
                    if len(self._data_received) >= expected_total_size + CRLF_SIZE:
                        msg = partial_msg
                        partial_msg = None
                        msg.payload = self._data_received[:expected_total_size]
                        self._data_received = self._data_received[
                            expected_total_size + CRLF_SIZE + 1 :
                        ]
                        self._events_received.append(msg)
                        state = State3102.AWAITING_CONTROL_LINE
                        continue
                    else:
                        yield None
                        continue


if TYPE_CHECKING:
    from .common import Parser as ParserProtocol

    # Verify that Parser implements ParserProtocol
    parser: ParserProtocol = Parser3102()
