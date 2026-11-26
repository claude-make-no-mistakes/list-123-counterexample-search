"""Seek lists for which every weighting causes an adjacent tie."""

import argparse
from itertools import product
import json
from math import lcm
from time import monotonic

import z3

from algebra import linear_factors


def valid_weightings(factors, lists):
    """Build the fixed-list SAT instance by forbidding exact local ties."""
    size = len(lists[0])
    select = [[z3.Bool(f"b_{edge}_{k}") for k in range(size)] for edge in range(len(lists))]
    solver = z3.Solver() if any(len(factor) > 8 for factor in factors) else z3.SolverFor("QF_FD")
    for row in select:
        solver.add(z3.PbEq([(entry, 1) for entry in row], 1))
    for factor in factors:
        if len(factor) > 8:
            # For high degrees avoid enumerating all local choices.
            solver.add(z3.Sum(*(z3.If(select[j][k], sign * value, 0)
                                for j, sign in factor for k, value in enumerate(lists[j]))) != 0)
            continue
        for indices in product(range(size), repeat=len(factor)):
            if sum(sign * lists[j][k] for (j, sign), k in zip(factor, indices)) == 0:
                solver.add(z3.Or(*(z3.Not(select[j][k]) for (j, _), k in zip(factor, indices))))
    return solver, select


def verify_choices(edges, lists, indices):
    """Check a coloring using endpoint sums, independently of the encoding."""
    weights = [row[k] for row, k in zip(lists, indices, strict=True)]
    totals = {v: 0 for edge in edges for v in edge}
    for (u, v), w in zip(edges, weights, strict=True):
        totals[u] += w
        totals[v] += w
    return all(totals[u] != totals[v] for u, v in edges)


def find_lists(edges, *, size, rounds, batch, seconds, proof_file=None):
    factors = linear_factors(edges)
    x = [[z3.Real(f"x_{j}_{k}") for k in range(size)] for j in range(len(edges))]
    outer = z3.SolverFor("QF_LRA")
    for row in x:
        outer.add(*(b - a >= 1 for a, b in zip(row, row[1:])))
    deadline = monotonic() + seconds
    all_clauses = 0

    def timed_check(solver):
        remaining = deadline - monotonic()
        if remaining <= 0:
            return z3.unknown
        solver.set(timeout=max(1, int(1000 * remaining)))
        return solver.check()

    for iteration in range(1, rounds + 1):
        result = timed_check(outer)
        if result == z3.unsat:
            if proof_file:
                proof_file.write_text(outer.to_smt2(), encoding="ascii")
            return {"status": "no-lists-solver-unsat", "round": iteration, "cuts": all_clauses}
        if result != z3.sat:
            break
        model = outer.model()
        rationals = [model.evaluate(value, model_completion=True) for row in x for value in row]
        scale = lcm(*(value.denominator_as_long() for value in rationals))
        integers = [value.numerator_as_long() * (scale // value.denominator_as_long()) for value in rationals]
        lists = [integers[offset:offset + size] for offset in range(0, len(integers), size)]
        if any(a >= b for row in lists for a, b in zip(row, row[1:])):
            raise RuntimeError("the outer model does not contain strictly ordered lists")

        solver, select = valid_weightings(factors, lists)
        for batch_index in range(batch):
            result = timed_check(solver)
            if result == z3.unsat:
                if batch_index == 0:
                    return {"status": "candidate", "round": iteration, "cuts": all_clauses, "lists": lists}
                break
            if result != z3.sat:
                break
            weighting = solver.model()
            indices = [next(k for k, entry in enumerate(row) if z3.is_true(weighting.evaluate(entry)))
                       for row in select]
            if not verify_choices(edges, lists, indices):
                raise RuntimeError("the inner model failed independent endpoint-sum verification")
            outer.add(z3.Or(*(sum(sign * x[j][indices[j]] for j, sign in factor) == 0
                              for factor in factors)))
            solver.add(z3.Or(*(z3.Not(row[k]) for row, k in zip(select, indices))))
            all_clauses += 1
        if monotonic() >= deadline:
            break
    return {"status": "unresolved", "round": iteration, "cuts": all_clauses}


def main():
    from pathlib import Path

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("graph", help="graph6 string")
    parser.add_argument("--list-size", type=int, choices=(2, 3), default=3)
    parser.add_argument("--rounds", type=int, default=2_000)
    parser.add_argument("--batch", type=int, default=24)
    parser.add_argument("--seconds", type=float, default=45)
    parser.add_argument("--smt2", type=Path)
    args = parser.parse_args()
    if min(args.rounds, args.batch, args.seconds) <= 0:
        parser.error("search limits must be positive")
    from networkx import from_graph6_bytes

    graph = from_graph6_bytes(args.graph.encode("ascii"))
    edges = tuple(sorted(tuple(sorted(edge)) for edge in graph.edges))
    if not edges:
        parser.error("provide a graph with an edge")
    if any(graph.degree[u] == graph.degree[v] == 1 for u, v in edges):
        parser.error("the conjecture requires no single-edge component")
    result = find_lists(edges, size=args.list_size, rounds=args.rounds, batch=args.batch,
                        seconds=args.seconds, proof_file=args.smt2)
    print(json.dumps({"graph6": args.graph, "edges": edges, "list_size": args.list_size, **result}))


if __name__ == "__main__":
    main()
