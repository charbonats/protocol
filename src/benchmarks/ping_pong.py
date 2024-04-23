import cProfile
import pstats
from argparse import ArgumentParser

from protocol import make_parser

from benchmarks.data_factory import ping_pong


def f8_alt(x: float) -> str:
    return "%14.9f" % x


setattr(pstats, "f8", f8_alt)


def main():
    parser = ArgumentParser()
    parser.add_argument("--n", type=int, default=1_000_000)
    parser.add_argument("--parser", type=str, default=None)
    args = parser.parse_args()
    data = ping_pong(args.n)
    parser = make_parser(args.parser)
    # Parse the data
    with cProfile.Profile() as pr:
        for d in data:
            parser.parse(d)
    # Dump the profile
    pr.print_stats(sort=1)


if __name__ == "__main__":
    main()
