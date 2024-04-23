from __future__ import annotations

import json
import timeit
from pathlib import Path
from statistics import mean, quantiles


class StatsLogger:
    def __init__(
        self,
        output_dir: str | None,
        scenario: str,
        parser: str,
        n_messages: int,
        repeat: int,
        **kwargs: object,
    ) -> None:
        self.durations: list[float] = []
        self._start = 0
        self._output_dir = output_dir
        self._kwargs = kwargs
        self._scenario = scenario
        self._parser = parser
        self._n_messages = n_messages
        self._repeat = repeat

    class Timer:
        def __init__(self, report: StatsLogger) -> None:
            self.report = report
            self._start = 0

        def __enter__(self) -> None:
            self._start = timeit.default_timer()

        def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
            self.report.durations.append(timeit.default_timer() - self._start)
            self._start = 0

    def observe(self) -> StatsLogger.Timer:
        return StatsLogger.Timer(self)

    def write_to_file(self) -> None:
        out = Path(self._output_dir) if self._output_dir else Path.cwd()
        # Create the output directory
        out.mkdir(exist_ok=True, parents=True)
        id = f"{self._scenario}-{self._parser}-{self._n_messages}"
        filepath = out.joinpath(f"{id}.json")
        ns_durations = [d * 1e9 for d in self.durations]
        distribution = quantiles(ns_durations, n=100)
        filepath.write_text(
            json.dumps(
                {
                    "id": f"{self._scenario}-{self._parser}-{self._n_messages}",
                    "scenario": self._scenario,
                    "parser": self._parser,
                    "n_messages": self._n_messages,
                    "repeat": self._repeat,
                    "params": self._kwargs,
                    "results": {
                        "mean": mean(ns_durations),
                        "max": max(ns_durations),
                        "min": min(ns_durations),
                        "p01": distribution[0],
                        "p05": distribution[5],
                        "p10": distribution[10],
                        "p25": distribution[25],
                        "p50": distribution[50],
                        "p75": distribution[75],
                        "p90": distribution[90],
                        "p95": distribution[95],
                        "p99": distribution[-1],
                    },
                },
                indent=2,
            )
        )
