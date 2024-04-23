import json
from secrets import token_hex


def ok() -> bytes:
    return b"+OK\r\n"


def msg(
    sid: int = 1,
    subject_size: int = 16,
    reply_subject_size: int = 0,
    message_size: int = 0,
) -> bytes:
    subject = token_hex(subject_size)
    reply = token_hex(reply_subject_size)
    message = token_hex(message_size)
    return f"MSG {subject} {sid} {reply} {len(message)}\r\n{message}\r\n".encode()


def hmsg(
    sid: int = 1,
    subject_size: int = 16,
    reply_subject_size: int = 0,
    message_size: int = 0,
    header_size: int = 0,
) -> bytes:
    subject = token_hex(subject_size)
    reply = token_hex(reply_subject_size)
    message = token_hex(message_size)
    header = "NATS/1.0\r\n" + token_hex(header_size)
    return f"HMSG {subject} {sid}{(' ' + reply + ' ') if reply else ' '}{len(header) + 4} {len(message) + len(header) + 4}\r\n{header}\r\n\r\n{message}\r\n".encode()


def ping() -> bytes:
    return b"PING\r\n"


def pong() -> bytes:
    return b"PONG\r\n"


def info(
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


def ping_pong(n: int) -> list[bytes]:
    return [ping(), pong()] * n


def msg_ping_pong_msg(
    n: int,
    sid: int = 1,
    subject_size: int = 16,
    reply_subject_size: int = 0,
    message_size: int = 0,
) -> list[bytes]:
    return [
        msg(sid, subject_size, reply_subject_size, message_size),
        ping(),
        pong(),
        msg(sid, subject_size, reply_subject_size, message_size),
    ] * n


def ping_pong_hmsg(
    n: int,
    sid: int = 1,
    subject_size: int = 16,
    reply_subject_size: int = 0,
    message_size: int = 0,
    header_size: int = 0,
) -> list[bytes]:
    return [
        ping(),
        pong(),
        hmsg(sid, subject_size, reply_subject_size, message_size, header_size),
    ] * n


def msg_hmsg(
    n: int,
    sid: int = 1,
    subject_size: int = 16,
    reply_subject_size: int = 0,
    message_size: int = 0,
    header_size: int = 0,
) -> list[bytes]:
    return [
        msg(sid, subject_size, reply_subject_size, message_size),
        hmsg(sid, subject_size, reply_subject_size, message_size, header_size),
    ] * n
