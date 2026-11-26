# Exact list 1–2–3 counterexample search

Every finite simple graph whose connected components each have at most nine vertices and none of whose components is a single edge is total $(1,3)$-weight choosable. Given three distinct real weights per edge and an arbitrary fixed real offset per vertex, one can pick the edge weights so that the offset plus incident sum differs across every edge. This rules out list 1–2–3 counterexamples through order nine. The general conjecture remains open. [Paper](paper.pdf) · [LaTeX source](paper.tex) · [Original conjecture](https://doi.org/10.1002/jgt.20354)

The certificates cover 273,191 connected graphs. The NetworkX atlas supplies 994 graphs through order seven. McKay’s catalogues supply 11,117 at order eight and 261,080 at order nine. Two implementations evaluated the archived coefficients. A separate search using a different prime and new exponent vectors also certified every connected case through order eight. [McKay’s graph data](https://users.cecs.anu.edu.au/~bdm/data/graphs.html)

## Replay

Use Python 3.10 or newer and a C++17 compiler. Each certificate gives the graph6 record, a degree-$|E|$ exponent vector with entries at most two, and the nonzero coefficient modulo $1\,000\,000\,007$. The verifier checks the catalogue hash and requires one valid certificate for every record in order.

```sh
python -m pip install -r requirements.txt
g++ -std=c++17 -O3 -Wall -Wextra -Wpedantic replay.cpp -o replay
python verify_certificates.py ./replay atlas-connected3-7.g6 atlas-coefficients.jsonl
python verify_certificates.py ./replay mckay-connected8.g6 order8-coefficients.jsonl
python verify_certificates.py ./replay mckay-connected9.g6 order9-coefficients.jsonl.gz
```

Run `dense_screen.py` to generate fresh coefficients. Its seed chooses which coefficient to try. Nonzero coefficients are exact certificates and zero samples leave a case unresolved.

```sh
g++ -std=c++17 -O3 -Wall -Wextra -Wpedantic coefficient.cpp -o coefficient
python dense_screen.py ./coefficient mckay-connected8.g6 --graph6 --trials 24
```

The nine-vertex replay can be split into independent processes. For `--parts 6`, run each `--part` from 0 through 5. Every part has 43,513 or 43,514 records.

The first order-ten sweep also certified all 317 connected graphs whose vertex degrees are three or four and whose edge count is 15 or 16. The input is reproducible with nauty 2.9.3. [Order-ten certificates](order10-degree34-15to16-coefficients.jsonl)

```sh
geng -cq -d3 -D4 10 15:16 > order10-degree34-15to16.g6
python verify_certificates.py ./replay order10-degree34-15to16.g6 order10-degree34-15to16-coefficients.jsonl
```

## Fixed-graph counterexample search

The search alternates between rational candidate lists and exact weighting checks. A normalized candidate contains three sorted weights per edge, with adjacent entries at least one apart. If a proper choice exists, the search adds a constraint forcing some edge to tie for those choice indices. A candidate survives only if the fixed-list solver finds no proper selection. `--smt2` saves the solver instance for a fixed-graph outer UNSAT result. Each output identifies candidate, solver UNSAT, or an unresolved budget limit.

```sh
python search.py Bw --list-size 2 --seconds 10
python search.py Bw --seconds 10
```

The triangle `Bw` is a positive control for two-list counterexamples. Its three chosen edge weights would need to be pairwise different, which is impossible if all three edges use the same two-element list. For three-element lists the triangle always has a proper choice, giving the negative control.
