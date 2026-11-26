"""Screen graph6 records or the NetworkX graph atlas for list-choosability."""

from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path

import networkx as nx

from algebra import PRIME, screen


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--graph6-file", type=Path)
    parser.add_argument("--min-order", type=int, default=3)
    parser.add_argument("--max-order", type=int, default=7)
    parser.add_argument("--max-edges", type=int)
    parser.add_argument("--seed", type=int, default=7021)
    parser.add_argument("--trials", type=int, default=3)
    parser.add_argument("--state-limit", type=int, default=50_000)
    args = parser.parse_args()
    if args.trials < 1 or args.state_limit < 1:
        parser.error("trials and state limit must be positive")
    if args.graph6_file:
        raw = args.graph6_file.read_bytes()
        records = raw.splitlines()
        graphs = ((line.decode("ascii"), nx.from_graph6_bytes(line)) for line in records if line)
        source = {"graph6_sha256": sha256(raw).hexdigest()}
    else:
        graphs = ((nx.to_graph6_bytes(graph, header=False).strip().decode("ascii"), graph)
                  for graph in nx.graph_atlas_g())
        source = {"networkx_atlas": nx.__version__}

    print(json.dumps({"source": source, "prime": PRIME, "min_order": args.min_order,
                      "max_order": args.max_order, "max_edges": args.max_edges,
                      "seed": args.seed, "trials": args.trials, "state_limit": args.state_limit}), flush=True)
    for code, graph in graphs:
        n, m = graph.number_of_nodes(), graph.number_of_edges()
        if not (args.min_order <= n <= args.max_order and nx.is_connected(graph)):
            continue
        if args.max_edges is not None and m > args.max_edges:
            continue
        edges = tuple(sorted(tuple(sorted(edge)) for edge in graph.edges))
        print(json.dumps({"g6": code, "n": n, "m": m,
                          **screen(edges, seed=args.seed, trials=args.trials, state_limit=args.state_limit)}),
              flush=True)


if __name__ == "__main__":
    main()
