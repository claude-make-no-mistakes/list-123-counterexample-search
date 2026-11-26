// Replay a truncated polynomial evaluation using packed exponents.
#include <algorithm>
#include <array>
#include <cstdint>
#include <iostream>
#include <unordered_map>
#include <utility>
#include <vector>

namespace {
constexpr std::uint64_t prime = 1000000007;
using Field = std::uint64_t;
using Key = std::uint64_t;
using Factor = std::vector<std::pair<int, int>>;

std::pair<std::int64_t, std::size_t> evaluate(
    const std::vector<Factor>& factors, const std::vector<Field>& values, std::size_t limit) {
    const auto width = values.size();
    std::vector<int> uses(width, 0);
    std::vector<std::array<Field, 3>> powers;
    for (const auto value : values) {
        powers.push_back({1, value, value * value % prime});
    }
    for (const auto& factor : factors) {
        for (const auto& entry : factor) ++uses[entry.first];
    }

    std::unordered_map<Key, Field> terms{{0, 1}};
    std::size_t peak = 1;
    for (const auto& factor : factors) {
        std::vector<int> retiring;
        Key retired_bits = 0;
        for (const auto& entry : factor) {
            const int variable = entry.first;
            if (--uses[variable] == 0) {
                retiring.push_back(variable);
                retired_bits |= Key{3} << (2 * variable);
            }
        }
        std::unordered_map<Key, Field> next_terms;
        next_terms.reserve(std::min(limit, terms.size() * 2));
        for (const auto& term : terms) {
            for (const auto& entry : factor) {
                const int shift = 2 * entry.first;
                if (((term.first >> shift) & 3) == 2) continue;
                const Key exponent = term.first + (Key{1} << shift);
                Field coefficient = entry.second > 0 ? term.second : prime - term.second;
                for (const int variable : retiring) {
                    const auto power = (exponent >> (2 * variable)) & 3;
                    coefficient = coefficient * powers[variable][power] % prime;
                }
                const auto at = next_terms.try_emplace(exponent & ~retired_bits, 0).first;
                at->second += coefficient;
                if (at->second >= prime) at->second -= prime;
                if (at->second == 0) next_terms.erase(at);
            }
            if (next_terms.size() > limit) return {-1, std::max(peak, next_terms.size())};
        }
        terms.swap(next_terms);
        peak = std::max(peak, terms.size());
        if (terms.empty()) return {0, peak};
    }
    return {static_cast<std::int64_t>(terms.at(0)), peak};
}
}

int main() {
    int count;
    std::size_t limit;
    while (std::cin >> count >> limit) {
        if (count < 1 || count > 32 || limit < 1) return 1;
        std::vector<Field> values(count);
        for (auto& value : values) {
            if (!(std::cin >> value) || value >= prime) return 1;
        }
        std::vector<Factor> factors(count);
        for (auto& factor : factors) {
            int length;
            if (!(std::cin >> length) || length < 0 || length >= count) return 1;
            Key seen = 0;
            for (int j = 0; j < length; ++j) {
                int variable, sign;
                if (!(std::cin >> variable >> sign) || variable < 0 || variable >= count ||
                    (sign != 1 && sign != -1)) return 1;
                const Key bit = Key{1} << variable;
                if (seen & bit) return 1;
                seen |= bit;
                factor.emplace_back(variable, sign);
            }
        }
        const auto answer = evaluate(factors, values, limit);
        std::cout << answer.first << ' ' << answer.second << std::endl;
    }
    return std::cin.eof() ? 0 : 1;
}
