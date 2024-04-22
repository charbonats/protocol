import sys

if sys.version_info[1] >= 10:
    from .parser_310 import Parser
else:
    from .parser_300 import Parser


__all__ = ["Parser"]
