"""Replay or extend screen.py output using the native polynomial evaluator."""

from argparse import ArgumentParser
import json
from pathlib import Path
from random import Random
from subprocess import PIPE, Popen

from networkx import from_graph6_bytes

from algebra import PRIME, factor_order, linear_factors


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("executable", type=Path)
    parser.add_argument("screen_log", type=Path)
    parser.add_argument("--state-limit", type=int, default=400_000)
    parser.add_argument("--verify-certified", action="store_true")
    args = parser.parse_args()
    if args.state_limit < 1:
        parser.error("state limit must be positive")
    with args.screen_log.open(encoding="utf-8-sig") as log:
        metadata = json.loads(next(log))
        print(json.dumps({"parent": metadata, "state_limit": args.state_limit,
                          "verify_certified": args.verify_certified}), flush=True)
        with Popen([str(args.executable.resolve())], stdin=PIPE, stdout=PIPE, text=True) as child:
            for line in log:
                previous = json.loads(line)
                if previous["status"] == "certified" and not args.verify_certified:
                    continue
                graph = from_graph6_bytes(previous["g6"].encode("ascii"))
                edges = tuple(sorted(tuple(sorted(edge)) for edge in graph.edges))
                factors = linear_factors(edges)
                order = factor_order(factors)
                random = Random(metadata["seed"])
                for trial in range(1, metadata["trials"] + 1):
                    values = [random.randrange(1, PRIME) for _ in edges]
                    request = [len(edges), args.state_limit, *values]
                    for i in order:
                        request.append(len(factors[i]))
                        for variable, sign in factors[i]:
                            request.extend((variable, sign))
                    print(*request, file=child.stdin, flush=True)
                    row = child.stdout.readline()
                    if not row:
                        raise RuntimeError("native evaluator stopped before returning a result")
                    result, peak = map(int, row.split())
                    if result != 0:
                        break
                status = "certified" if result > 0 else "state-limit" if result < 0 else "zero-evaluations"
                if previous["status"] == "certified" and (result, trial) != (previous["residue"], previous["trial"]):
                    raise RuntimeError(f"evaluators disagree for {previous['g6']}")
                print(json.dumps({"g6": previous["g6"], "n": previous["n"], "m": previous["m"],
                                  "status": status, "residue": result, "trial": trial, "peak": peak}),
                      flush=True)
            child.stdin.close()
            if child.wait() != 0:
                raise RuntimeError("native evaluator rejected the input")


if __name__ == "__main__":
    main()
