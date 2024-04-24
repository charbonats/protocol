from __future__ import annotations

import json
import timeit
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean, quantiles, stdev
from typing import Any


@dataclass
class IterationResult:
    p01: int
    p05: int
    p10: int
    p25: int
    p50: int
    p75: int
    p90: int
    p95: int
    p99: int
    average: int
    maximum: int
    minimum: int
    standard_deviation: float


@dataclass
class BenchmarkResult:
    id: str
    scenario: str
    params: dict[str, Any]
    score: float
    best_result: IterationResult
    results: list[IterationResult]


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
        self._iterations: list[IterationResult] = []
        self._start = 0
        self._output_dir = output_dir
        self._kwargs = kwargs
        self._scenario = scenario
        self._parser = parser
        self._n_messages = n_messages
        self._repeat = repeat

    def iteration(self) -> Iteration:
        return self.Iteration(self)

    def results(self) -> BenchmarkResult:
        best_median = float("inf")
        best_results: IterationResult | None = None
        for result in self._iterations:
            if result.p50 < best_median:
                best_median = result.p50
                best_results = result
        if best_results is None:
            raise ValueError("no result available")
        return BenchmarkResult(
            id=f"{self._scenario}-{self._parser}-{self._n_messages}",
            scenario=self._scenario,
            params={
                "parser": self._parser,
                "n_messages": self._n_messages,
                "repeat": self._repeat,
                **self._kwargs,
            },
            score=best_results.p50,
            best_result=best_results,
            results=self._iterations,
        )

    def write_to_file(self, skip_results: bool = True) -> None:
        out = Path(self._output_dir) if self._output_dir else Path.cwd()
        # Create the output directory
        out.mkdir(exist_ok=True, parents=True)
        id = f"{self._scenario}-{self._parser}-{self._n_messages}"
        filepath = out.joinpath(f"{id}.json")
        data = asdict(self.results())
        if skip_results:
            del data["results"]
        filepath.write_text(
            json.dumps(
                data,
                indent=2,
            )
        )

    class Iteration:
        def __init__(self, stats_logger: StatsLogger) -> None:
            self._durations: list[float] = []
            self._stats_logger = stats_logger

        def __enter__(self) -> StatsLogger.Iteration:
            return self

        def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
            self._stats_logger._iterations.append(self.result())

        def result(self) -> IterationResult:
            ns_durations = [int(d * 1e9) for d in self._durations]
            distribution = quantiles(ns_durations, n=100)
            return IterationResult(
                p01=int(distribution[0]),
                p05=int(distribution[5]),
                p10=int(distribution[10]),
                p25=int(distribution[25]),
                p50=int(distribution[50]),
                p75=int(distribution[75]),
                p90=int(distribution[90]),
                p95=int(distribution[95]),
                p99=int(distribution[-1]),
                average=int(mean(ns_durations)),
                maximum=int(max(ns_durations)),
                minimum=int(min(ns_durations)),
                standard_deviation=stdev(ns_durations),
            )

        def observe(self) -> Timer:
            return self.Timer(self)

        class Timer:
            __slots__ = ["_start", "_stop", "_iteration"]

            def __init__(self, iteration: StatsLogger.Iteration) -> None:
                self._iteration = iteration
                self._start = 0
                self._stop: float | None = None

            def reset(self) -> None:
                self._start = timeit.default_timer()

            def end(self) -> None:
                self._stop = timeit.default_timer()
                self._iteration._durations.append(self._stop - self._start)
                self._start = 0
