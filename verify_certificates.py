"""Validate catalogue coverage and replay the archived coefficients."""

from argparse import ArgumentParser
from collections import Counter
from hashlib import sha256
import gzip
import json
from pathlib import Path
from subprocess import PIPE, Popen

from networkx import from_graph6_bytes, is_connected

from algebra import PRIME
from dense_screen import evaluate


def records(path):
    raw = path.read_bytes()
    codes = [line.decode("ascii") for line in raw.splitlines() if line]
    if len(codes) != len(set(codes)):
        raise ValueError("duplicate graph6 records in the supplied catalogue")
    return codes, sha256(raw).hexdigest()


def verify(executable, source, certificates, *, parts=1, part=0):
    codes, digest = records(source)
    open_log = gzip.open if certificates.suffix == ".gz" else open
    counts = Counter()
    with open_log(certificates, "rt", encoding="utf-8-sig") as log:
        metadata = json.loads(next(log))
        if metadata["prime"] != PRIME or metadata["parent"]["graph6_sha256"] != digest:
            raise ValueError("certificate metadata does not match the catalogue or coefficient field")
        with Popen([str(executable.resolve())], stdin=PIPE, stdout=PIPE, text=True) as child:
            for index, (code, line) in enumerate(zip(codes, log, strict=True)):
                if index % parts != part:
                    continue
                item = json.loads(line)
                if item["g6"] != code or item["status"] != "certified":
                    raise ValueError(f"missing certificate for {code}")
                graph = from_graph6_bytes(code.encode("ascii"))
                n = graph.number_of_nodes()
                if n < 3 or n != item["n"] or not is_connected(graph):
                    raise ValueError(f"unexpected graph in the catalogue at {code}")
                edges = tuple(sorted(tuple(sorted(edge)) for edge in graph.edges))
                powers = item["exponents"]
                m = len(edges)
                if item["m"] != m or len(powers) != m or sum(powers) != m or any(p not in (0, 1, 2) for p in powers):
                    raise ValueError(f"invalid exponent vector for {code}")
                residue = evaluate(child, n, edges, powers)
                if not 0 < residue < PRIME or residue != item["coefficient_mod_prime"]:
                    raise ValueError(f"coefficient replay failed for {code}")
                counts[n] += 1
            child.stdin.close()
            if child.wait() != 0:
                raise RuntimeError("coefficient checker rejected the input")
    return dict(sorted(counts.items()))


if __name__ == "__main__":
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("executable", type=Path)
    parser.add_argument("catalogue", type=Path)
    parser.add_argument("certificates", type=Path)
    parser.add_argument("--parts", type=int, default=1)
    parser.add_argument("--part", type=int, default=0)
    args = parser.parse_args()
    if not 0 <= args.part < args.parts:
        parser.error("the part must be a zero-based index smaller than the number of parts")
    counts = verify(args.executable, args.catalogue, args.certificates, parts=args.parts, part=args.part)
    print(json.dumps({"verified_graphs_by_order": counts, "parts": args.parts, "part": args.part}))
