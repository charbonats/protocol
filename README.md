# Protocol

> A NATS protocol parser written in Python

## Motivation

1. This project was created to parse the NATS protocol in order to understand how it works and to be able to create a NATS client from scratch.

2. This project was created to compare the performance of a Regular Expressions parser with a look ahead bytes parser.

## Install

```bash
git clone https://github.com/charbonats/protocol.git
cd protocol
rye run bootstrap
```

## Test

Tests can be run using `pytest`, but it's recommended to use the `rye` command to collect coverage:

```bash
rye run test
```

## Benchmark

Benchmarks can be run individually using `python -m benchmarks` command, but it's recommended to use the `rye` command to run all benchmarks sequentially and collect results into a single directory:

```bash
rye run bench
```
