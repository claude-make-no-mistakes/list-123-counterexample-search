// Check a single degree-m coefficient through multivariate finite differences.
#include <array>
#include <cstdint>
#include <iostream>
#include <utility>
#include <vector>

namespace {
constexpr std::int64_t prime = 1000000007;
using Edge = std::pair<int, int>;

std::int64_t differences(const std::vector<Edge>& edges, const std::vector<int>& powers,
                         std::vector<int>& totals, std::size_t offset, std::int64_t weight) {
    if (offset == edges.size()) {
        for (const auto& [u, v] : edges) {
            const auto delta = totals[u] - totals[v];
            if (delta == 0) return 0;
            weight = weight * delta % prime;
        }
        return weight;
    }
    const auto count = powers[offset];
    const auto [u, v] = edges[offset];
    const std::array<std::array<int, 3>, 3> weights{{{1, 0, 0}, {-1, 1, 0}, {1, -2, 1}}};
    std::int64_t sum = 0;
    for (int k = 0; k <= count; ++k) {
        if (k > 0) {
            ++totals[u];
            ++totals[v];
        }
        sum += differences(edges, powers, totals, offset + 1, weight * weights[count][k] % prime);
    }
    totals[u] -= count;
    totals[v] -= count;
    return sum % prime;
}
}

int main() {
    int vertices, size;
    while (std::cin >> vertices >> size) {
        if (vertices < 2 || vertices > 32 || size < 1 || size > 64) return 1;
        std::vector<Edge> edges(size);
        std::vector<int> powers(size);
        int total_degree = 0;
        int doubles = 0;
        for (int i = 0; i < size; ++i) {
            auto& [u, v] = edges[i];
            if (!(std::cin >> u >> v >> powers[i]) || u < 0 || v <= u || v >= vertices ||
                powers[i] < 0 || powers[i] > 2) return 1;
            total_degree += powers[i];
            if (powers[i] == 2) ++doubles;
        }
        if (total_degree != size) return 1;
        std::vector<int> totals(vertices, 0);
        auto coefficient = differences(edges, powers, totals, 0, 1);
        if (coefficient < 0) coefficient += prime;
        for (int i = 0; i < doubles; ++i) coefficient = coefficient * ((prime + 1) / 2) % prime;
        std::cout << coefficient << std::endl;
    }
    return std::cin.eof() ? 0 : 1;
}
