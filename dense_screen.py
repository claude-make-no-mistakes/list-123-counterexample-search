"""Certify unresolved graphs by checking individual polynomial coefficients."""

from argparse import ArgumentParser
from contextlib import nullcontext
import gzip
from hashlib import sha256
import json
from pathlib import Path
from random import Random
from subprocess import PIPE, Popen
import sys

from networkx import from_graph6_bytes

from algebra import linear_factors, PRIME


def exponent_samples(factors, seed, trials):
    rng = Random(seed)
    m = len(factors)
    for attempt in range(trials):
        if attempt % 3 != 2:
            caps = [2] * (m // 2) + [1] * (m % 2) + [0] * (m // 2)
            rng.shuffle(caps)
            yield tuple(caps)
            continue
        order = list(range(m))
        rng.shuffle(order)
        order.sort(key=lambda i: len(factors[i]))
        ranks = [rng.random() for _ in factors]
        caps = [0] * m
        for i in order:
            available = [j for j, _ in factors[i] if caps[j] < 2]
            if not available:
                break
            j = max(available, key=lambda v: (caps[v], ranks[v]))
            caps[j] += 1
        else:
            yield tuple(caps)


def evaluate(child, n, edges, exponents):
    data = [n, len(edges)]
    for (u, v), exponent in zip(edges, exponents, strict=True):
        data.extend((u, v, exponent))
    print(*data, file=child.stdin, flush=True)
    row = child.stdout.readline()
    if not row:
        raise RuntimeError("coefficient checker stopped before returning a result")
    return int(row)


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("executable", type=Path)
    parser.add_argument("screen_log", type=Path)
    parser.add_argument("--graph6", action="store_true", help="read graph6 records instead of a JSONL log")
    parser.add_argument("--trials", type=int, default=60)
    parser.add_argument("--seed", type=int, default=9412)
    parser.add_argument("--gzip-output", type=Path)
    args = parser.parse_args()
    if args.trials < 1:
        parser.error("trials must be positive")
    output_stream = (gzip.open(args.gzip_output, "wt", encoding="utf-8", newline="\n")
                     if args.gzip_output else nullcontext(sys.stdout))
    with args.screen_log.open(encoding="utf-8-sig") as log, output_stream as output:
        if args.graph6:
            metadata = {"graph6_sha256": sha256(args.screen_log.read_bytes()).hexdigest()}
            rows = ({"g6": row.strip(), "status": "unresolved"} for row in log if row.strip())
        else:
            metadata = json.loads(next(log))
            rows = map(json.loads, log)
        print(json.dumps({"parent": metadata, "seed": args.seed, "trials": args.trials,
                          "prime": PRIME}), file=output, flush=True)
        with Popen([str(args.executable.resolve())], stdin=PIPE, stdout=PIPE, text=True) as child:
            for previous in rows:
                if previous["status"] == "certified":
                    continue
                code = previous["g6"]
                graph = from_graph6_bytes(code.encode("ascii"))
                n, m = graph.number_of_nodes(), graph.number_of_edges()
                edges = tuple(sorted(tuple(sorted(edge)) for edge in graph.edges))
                factors = linear_factors(edges)
                tried = set()
                certificate = {}
                for exponents in exponent_samples(factors, args.seed, args.trials):
                    if exponents in tried:
                        continue
                    tried.add(exponents)
                    result = evaluate(child, n, edges, exponents)
                    if result:
                        certificate = {"coefficient_mod_prime": result, "exponents": exponents}
                        break
                print(json.dumps({"g6": code, "n": n, "m": m, "samples": len(tried),
                                  "status": "certified" if certificate else "unresolved", **certificate}),
                      file=output, flush=not args.gzip_output)
            child.stdin.close()
            if child.wait() != 0:
                raise RuntimeError("coefficient checker rejected the input")


if __name__ == "__main__":
    main()
