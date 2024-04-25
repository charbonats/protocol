from protocol import Backend, make_parser


class Connection:
    def __init__(self, parser_backend: Backend | None = None) -> None:
        self.parser = make_parser(parser_backend)
