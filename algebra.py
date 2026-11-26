"""Exact modular checks of the bounded coefficients of the weighting polynomial."""

from collections import Counter
from random import Random


PRIME = 1_000_000_007


def linear_factors(edges: tuple[tuple[int, int], ...]) -> tuple[tuple[tuple[int, int], ...], ...]:
    """Return the signs of the edge variables in each endpoint-sum difference."""
    incident = {}
    for index, (u, v) in enumerate(edges):
        incident.setdefault(u, set()).add(index)
        incident.setdefault(v, set()).add(index)
    return tuple(
        tuple((j, 1 if j in incident[u] else -1) for j in sorted(incident[u] ^ incident[v]))
        for u, v in edges
    )


def factor_order(factors: tuple[tuple[tuple[int, int], ...], ...]) -> list[int]:
    remaining = set(range(len(factors)))
    uses = Counter(j for factor in factors for j, _ in factor)
    active = set()
    order = []
    while remaining:
        def score(i: int) -> tuple[int, int, int]:
            variables = {j for j, _ in factors[i]}
            after = len(active | variables) - sum(uses[j] == 1 for j in variables)
            return after, len(variables), i

        i = min(remaining, key=score)
        order.append(i)
        remaining.remove(i)
        for j, _ in factors[i]:
            uses[j] -= 1
            if uses[j]:
                active.add(j)
            else:
                active.discard(j)
    return order


def residue(factors: tuple[tuple[tuple[int, int], ...], ...], order: list[int],
            values: tuple[int, ...], *, cap: int, state_limit: int) -> tuple[int | None, int]:
    """Evaluate the part with all exponents at most cap in a prime field."""
    if not 0 <= cap <= 3:
        raise ValueError("the packed exponent representation supports caps from 0 to 3")
    uses = Counter(j for factor in factors for j, _ in factor)
    multipliers = [tuple(pow(x, e, PRIME) for e in range(cap + 1)) for x in values]
    states = {0: 1}
    peak = 1
    for i in order:
        factor = factors[i]
        retiring = []
        for j, _ in factor:
            uses[j] -= 1
            if uses[j] == 0:
                retiring.append(j)
        mask = sum(3 << (2 * j) for j in retiring)
        next_states = {}
        for key, coefficient in states.items():
            for j, sign in factor:
                shift = 2 * j
                if ((key >> shift) & 3) == cap:
                    continue
                updated = key + (1 << shift)
                term = sign * coefficient
                for r in retiring:
                    term = term * multipliers[r][(updated >> (2 * r)) & 3] % PRIME
                target = updated & ~mask
                value = (next_states.get(target, 0) + term) % PRIME
                if value:
                    next_states[target] = value
                else:
                    next_states.pop(target, None)
            if len(next_states) > state_limit:
                return None, max(peak, len(next_states))
        states = next_states
        peak = max(peak, len(states))
        if not states:
            break
    return states.get(0, 0), peak


def screen(edges: tuple[tuple[int, int], ...], *, seed: int, trials: int,
           state_limit: int, list_size: int = 3) -> dict:
    factors = linear_factors(edges)
    order = factor_order(factors)
    random = Random(seed)
    peak = 0
    for trial in range(1, trials + 1):
        values = tuple(random.randrange(1, PRIME) for _ in edges)
        value, used = residue(factors, order, values, cap=list_size - 1, state_limit=state_limit)
        peak = max(peak, used)
        if value:
            return {"status": "certified", "residue": value, "trial": trial, "peak": peak}
        if value is None:
            return {"status": "state-limit", "trial": trial, "peak": peak}
    return {"status": "zero-evaluations", "trial": trials, "peak": peak}
