import sys
from argparse import ArgumentParser
from enum import Enum

from protocol import Backend, make_parser

from benchmarks import data_factory
from benchmarks.stats_logger import StatsLogger


class Scenario(str, Enum):
    msg_ok_ping_msg_pong_msg_ok = "msg_ok_ping_msg_pong_msg_ok"
    msg_ping_pong_msg = "msg_ping_pong_msg"
    ping_pong = "ping_pong"
    msg_hmsg = "msg_hmsg"


def main():
    # Define command line arguments
    parser = ArgumentParser()
    parser.add_argument(
        "--messages", "-n", type=int, default=10_000, help="Number of messages"
    )
    parser.add_argument(
        "--repeat", "-r", type=int, default=10, help="Number of repetitions"
    )
    parser.add_argument(
        "--scenario", "-s", type=str, default="ping_pong", help="Benchmark scenario"
    )
    parser.add_argument(
        "--parser", "-p", type=str, default="default", help="Parser backend"
    )
    parser.add_argument(
        "--output-dir", "-o", type=str, default=None, help="Output directory"
    )
    args = parser.parse_args()
    # Parse the backend
    try:
        backend = Backend(args.parser)
    except ValueError:
        print(f"ERROR: Invalid parser: {args.parser}", file=sys.stderr)
        print(f"Allowed parsers: {[b.value for b in Backend]}", file=sys.stderr)
        sys.exit(1)
    # Parse the scenario and generate the data
    try:
        scenario = Scenario(args.scenario)
    except ValueError:
        print(f"ERROR: Invalid scenario: {args.scenario}", file=sys.stderr)
        print(f"Allowed scenarios: {[s.value for s in Scenario]}", file=sys.stderr)
        sys.exit(1)
    if scenario == Scenario.msg_ok_ping_msg_pong_msg_ok:
        opts = {"message_size": 1024, "subject_size": 64}
        data = data_factory.msg_ping_pong_msg(args.messages, **opts)
    elif scenario == Scenario.msg_ping_pong_msg:
        opts = {"message_size": 1024, "subject_size": 64}
        data = data_factory.msg_ping_pong_msg(args.messages, **opts)
    elif scenario == Scenario.ping_pong:
        opts = {}
        data = data_factory.ping_pong(args.messages)
    elif scenario == Scenario.msg_hmsg:
        opts = {"message_size": 1024, "subject_size": 64, "header_size": 64}
        data = data_factory.msg_hmsg(args.messages, **opts)
    else:
        print(f"Scenario not implemented: {scenario}", file=sys.stderr)
        sys.exit(1)
    # Create the parser
    parser = make_parser(backend)
    parser_type = type(parser).__name__
    # Parse the data
    report = StatsLogger(
        output_dir=args.output_dir,
        scenario=scenario.value,
        parser=parser_type,
        n_messages=args.messages,
        repeat=args.repeat,
        **opts,
    )
    print("#" * 60)
    for idx in range(args.repeat):
        parser = make_parser(backend)
        with report.iteration() as iteration:
            for op in data:
                timer = iteration.observe()
                timer.reset()
                parser.parse(op)
                timer.end()
        results = iteration.result()
        print(
            f"[{backend}] {scenario} - iteration {idx+1}/{args.repeat} - {results.p50} ns/op"
        )
    results = report.results()
    print(f"[{backend}] {scenario} 🕑 {results.score} ns/op")
    # Dump the profile
    report.write_to_file()


if __name__ == "__main__":
    main()
