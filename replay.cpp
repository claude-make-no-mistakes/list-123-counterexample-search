// Recompute each coefficient with endpoint sums finalized during enumeration.
#include <cstdint>
#include <iostream>
#include <utility>
#include <vector>

namespace {
using Edge = std::pair<int, int>;
constexpr std::int64_t prime = 1000000007;

struct Variable {
    int u;
    int v;
    int exponent;
};

std::int64_t sum_of_terms(const std::vector<Variable>& variables,
                          const std::vector<std::vector<Edge>>& ready, std::vector<int>& totals,
                          std::size_t step, std::int64_t term) {
    for (const auto& [u, v] : ready[step]) {
        const int difference = totals[u] - totals[v];
        if (difference == 0) return 0;
        term = term * difference % prime;
    }
    if (step == variables.size()) return term;
    const auto [u, v, exponent] = variables[step];
    // This includes the factorial denominator locally when the exponent is 2.
    constexpr std::int64_t half = (prime + 1) / 2;
    const std::int64_t weights[3] = {exponent == 1 ? -1 : half, exponent == 1 ? 1 : -1, half};
    std::int64_t sum = 0;
    for (int value = 0; value <= exponent; ++value) {
        totals[u] += value;
        totals[v] += value;
        sum += sum_of_terms(variables, ready, totals, step + 1, term * weights[value] % prime);
        totals[u] -= value;
        totals[v] -= value;
    }
    return sum % prime;
}
}

int main() {
    int n, m;
    while (std::cin >> n >> m) {
        if (n < 2 || n > 32 || m < 1 || m > 64) return 1;
        std::vector<Edge> edges;
        std::vector<Variable> variables;
        std::vector<std::size_t> finalized(n, 0);
        int total_degree = 0;
        for (int i = 0; i < m; ++i) {
            int u, v, exponent;
            if (!(std::cin >> u >> v >> exponent) || u < 0 || v <= u || v >= n ||
                exponent < 0 || exponent > 2) return 1;
            edges.emplace_back(u, v);
            total_degree += exponent;
            if (exponent > 0) {
                variables.push_back({u, v, exponent});
                finalized[u] = finalized[v] = variables.size();
            }
        }
        if (total_degree != m) return 1;
        std::vector<std::vector<Edge>> ready(variables.size() + 1);
        for (const auto& [u, v] : edges) {
            ready[finalized[u] > finalized[v] ? finalized[u] : finalized[v]].emplace_back(u, v);
        }
        std::vector<int> totals(n, 0);
        const auto value = sum_of_terms(variables, ready, totals, 0, 1);
        std::cout << (value + prime) % prime << std::endl;
    }
    return std::cin.eof() ? 0 : 1;
}
