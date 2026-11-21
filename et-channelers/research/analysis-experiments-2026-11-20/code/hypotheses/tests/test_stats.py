"""Shared statistics against brute force and known values. Synthetic numbers only."""
import itertools
import math
from pathlib import Path
import random
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from hypotheses import constants as K  # noqa: E402
from hypotheses import stats  # noqa: E402


def brute_signflip(x, alternative):
    observed, count, total = sum(x), 0, 0
    for signs in itertools.product((1, -1), repeat=len(x)):
        s = sum(a * abs(b) for a, b in zip(signs, x))
        total += 1
        if alternative == "greater":
            count += s >= observed - 1e-9
        elif alternative == "less":
            count += s <= observed + 1e-9
        else:
            count += abs(s) >= abs(observed) - 1e-9
    return count / total


class SignFlip(unittest.TestCase):
    def test_exact_matches_brute_force(self):
        r = random.Random(1)
        for n in range(1, 12):
            for _ in range(5):
                x = [r.gauss(0.3, 1.0) for _ in range(n)]
                for alternative in ("greater", "less", "two-sided"):
                    p, method = stats.signflip_p(x, alternative)
                    self.assertEqual(method, "exact")
                    self.assertAlmostEqual(p, brute_signflip(x, alternative), places=12)

    def test_ties_and_zero(self):
        self.assertEqual(stats.signflip_p([0.0, 0.0, 0.0], "two-sided")[0], 1.0)
        self.assertAlmostEqual(stats.signflip_p([1.0] * 4, "greater")[0], 1 / 16)

    def test_smallest_p_and_holm_step(self):
        self.assertAlmostEqual(stats.signflip_p([1.0] * 8, "greater")[0], 1 / 256)       # passes 0.005
        self.assertAlmostEqual(stats.signflip_p([1.0] * 8, "two-sided")[0], 2 / 256)     # does not: H2's minimum is 9
        self.assertLessEqual(stats.signflip_p([1.0] * 9, "two-sided")[0], 0.005)

    def test_monte_carlo_above_twenty(self):
        r = random.Random(2)
        x = [r.gauss(0.4, 1.0) for _ in range(22)]
        exact, _ = stats.signflip_p(x, "greater", exact_max=22)
        mc, method = stats.signflip_p(x, "greater", label=("t",), draws=20000)
        self.assertTrue(method.startswith("monte_carlo"))
        self.assertLess(abs(mc - exact), 4 * math.sqrt(exact * (1 - exact) / 20000) + 1e-4)
        again, _ = stats.signflip_p(x, "greater", label=("t",), draws=20000)
        self.assertEqual(mc, again)                                                       # seeded: deterministic


class Holm(unittest.TestCase):
    def test_fixed_count(self):
        out = stats.holm({"H1": 0.004})
        self.assertAlmostEqual(out["H1"][0], 0.04)
        self.assertTrue(out["H1"][1])
        out = stats.holm({"H1": 0.0051})
        self.assertFalse(out["H1"][1])
        self.assertEqual(out["H3"][0], 1.0)

    def test_step_down(self):
        out = stats.holm({"H1": 0.001, "H2": 0.006, "H4": 0.03})
        self.assertAlmostEqual(out["H1"][0], 0.01)
        self.assertAlmostEqual(out["H2"][0], 0.054)
        self.assertAlmostEqual(out["H4"][0], 0.24)

    def test_count_must_be_ten(self):
        with self.assertRaises(ValueError):
            stats.holm({"H1": 0.01, "X": 0.2})


class Distributions(unittest.TestCase):
    def test_t_quantiles(self):
        self.assertAlmostEqual(stats.t_ppf(0.975, 10), 2.228138851986, places=8)
        self.assertAlmostEqual(stats.t_ppf(0.95, 16), 1.745883676, places=7)
        self.assertAlmostEqual(stats.t_ppf(0.995, 1), 63.656741162, places=5)
        self.assertAlmostEqual(stats.t_ppf(0.05, 11), -1.795884819, places=7)

    def test_t_interval_and_hksj_agree_with_equal_variances(self):
        y = [0.1, -0.2, 0.3, 0.05, 0.12, -0.04]
        m, lo, hi = stats.t_interval(y, 0.90)
        pool = stats.re_hksj(y, [0.01] * len(y), (0.90,))
        self.assertAlmostEqual(pool["mu"], m)
        self.assertAlmostEqual(pool["intervals"]["0.9"][0], lo)
        self.assertAlmostEqual(pool["intervals"]["0.9"][1], hi)


class Estimators(unittest.TestCase):
    def test_somers(self):
        signed, pairs, n1, n0 = stats.somers_counts([(2, True, 1), (3, True, 1), (1, False, 1), (3, False, 1)])
        self.assertAlmostEqual(signed / pairs, 0.25)
        d, _ = stats.somers_ordinal([(2, 1, 1), (3, 1, 1), (1, 0, 1), (3, 0, 1)])
        self.assertAlmostEqual(d, 0.25)

    def test_mantel_haenszel_one_stratum(self):
        ratio, _ = stats.mh_rate_ratio([(4, 10, 1000, 2000)])
        self.assertAlmostEqual(ratio, (4 / 1000) / (10 / 2000))
        odds, _ = stats.mh_odds_ratio([(10, 20, 5, 30)])
        self.assertAlmostEqual(odds, (10 / 20) / (5 / 30))

    def test_streams_are_deterministic(self):
        self.assertEqual(stats.rng("a", 1).random(), stats.rng("a", 1).random())
        self.assertNotEqual(stats.seed_for("a"), stats.seed_for("b"))
        self.assertEqual(K.BASE_SEED, 20261120)


if __name__ == "__main__":
    unittest.main()
