"""The lead's decisions of 2026-11-21 09:19 ("Hypothesis code, decisions after the third verification"), items (1) to (4):
H6's conditional Monte Carlo reference, the OE-scale tolerance of the A10.7 null check, the null check keeping recordings
without an ask file, and no file of the package opening the hold-out or other-group label tree. Constructed numbers,
synthetic records and the package's own sources only: no test opens the production label tree."""
import itertools
import math
from pathlib import Path
import re
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from hypotheses import a10_checks, common  # noqa: E402
from hypotheses import constants as K  # noqa: E402
from hypotheses import h5_world_claims, h6_asks, simulate, stats  # noqa: E402
from hypotheses import voice_sets as vs  # noqa: E402

HERE = Path(__file__).resolve().parents[1]


def recording(a, b, s, words=1000):
    """A recording row of h6_asks.creator_tables with claimed share s of its words in the two voices."""
    return {"a": a, "b": b, "wc": words * s, "wo": words * (1 - s), "unchecked": 0, "neither": 0}


def exact_lower_tail(creators):
    """P(mean OE <= observed) under the per-recording null, by enumeration of every recording's a_i (small cases)."""
    observed = sum(h6_asks.oe_value(rows) for rows in creators)
    cells = [(row["a"] + row["b"], row["wc"] / (row["wc"] + row["wo"])) for rows in creators for row in rows]
    tail = 0.0
    for draw in itertools.product(*[range(t + 1) for t, _ in cells]):
        prob, k = 1.0, 0
        redrawn = []
        for rows in creators:
            new = []
            for row in rows:
                t, s = cells[k]
                a = draw[k]
                prob *= math.comb(t, a) * s ** a * (1 - s) ** (t - a)
                new.append(dict(row, a=a, b=t - a))
                k += 1
            redrawn.append(new)
        if sum(h6_asks.oe_value(rows) for rows in redrawn) <= observed + 1e-12:
            tail += prob
    return tail


# ---------------------------------------------------------------- (1) H6's conditional Monte Carlo reference

class H6ConditionalReference(unittest.TestCase):
    """09:19 (1): the amended version's p is the mean OE against its conditional Monte Carlo reference under the
    per-recording null (a_i ~ Binomial(T_i, s_i) given T_i), p = (b + 1) / (m + 1); the registered version unchanged."""

    creators = [[recording(0, 1, 0.3)], [recording(1, 1, 0.4), recording(0, 1, 0.2)], [recording(0, 2, 0.5)],
                [recording(1, 2, 0.25)], [recording(0, 1, 0.35), recording(0, 0, 0.6)]]

    def test_the_integer_statistic_orders_draws_as_the_mean_oe(self):
        cells = h6_asks.reference_cells(self.creators)
        self.assertEqual([total for total, _, _ in cells], [1, 3, 2, 3, 1])         # the a = b = 0 recording adds nothing
        lcm, value = h6_asks._integer_statistic(cells)
        self.assertEqual(lcm, 6)
        centre = sum(sum(t_i * s_i for t_i, s_i in rows) / total for total, _, rows in cells)
        self.assertAlmostEqual(value / lcm - centre, sum(h6_asks.oe_values(self.creators)), places=12)

    def test_p_is_the_exact_conditional_tail_up_to_monte_carlo_error(self):
        tail = exact_lower_tail(self.creators)
        draws = 20000
        # the ask-level reference of 09:19 (since 11:08 (1) shown beside the amended p); rows without cluster sizes
        # count every ask as a cluster of one, so the cluster-level reference is the same law here
        p, method = h6_asks.conditional_p(self.creators, ("t-0919", "tail"), draws, by="ask")
        self.assertEqual(method, "conditional_monte_carlo_asks_20000")
        se = math.sqrt(tail * (1 - tail) / draws)
        self.assertLess(abs(p - tail), 4 * se + 1.0 / draws)

    def test_seeded_and_counted_as_b_plus_one_over_m_plus_one(self):
        first = h6_asks.conditional_p(self.creators, ("t-0919", "seed"), 999)
        self.assertEqual(first, h6_asks.conditional_p(self.creators, ("t-0919", "seed"), 999))
        self.assertAlmostEqual(first[0] * 1000, round(first[0] * 1000), places=9)
        # the smallest possible outcome (every ask in own voice) is at the bottom of the reference
        low = [[dict(row, a=0, b=row["a"] + row["b"]) for row in rows] for rows in self.creators]
        p_low, _ = h6_asks.conditional_p(low, ("t-0919", "low"), 999)
        self.assertLess(p_low, 0.2)
        self.assertEqual(h6_asks.conditional_p([], ("t",), 99), (1.0, "none"))

    def test_a_recording_without_asks_changes_nothing(self):
        more = [rows + [recording(0, 0, 0.9)] for rows in self.creators]
        self.assertEqual(h6_asks.conditional_p(self.creators, ("t-0919", "same"), 999),
                         h6_asks.conditional_p(more, ("t-0919", "same"), 999))

    def test_analyse_uses_it_and_keeps_the_registered_version(self):
        """Amended by 11:08 (1): the amended p is the larger of the cluster-level conditional p and the sign-flip p of OE;
        the ask-level conditional p of 09:19 is computed beside it."""
        b = simulate.cohort(stats.seed_for("t-0919-analyse"), 12, {"exact": True, "rr": 0.3}, parts=("voice", "asks"))
        result = h6_asks.analyse(b, label=("t-0919",), extras=False, draws=99)
        self.assertEqual(result["p_method"], f"max(conditional_monte_carlo_clusters_{h6_asks.REFERENCE_DRAWS}, signflip_oe_exact)")
        self.assertGreaterEqual(h6_asks.REFERENCE_DRAWS, 9999)
        tables = h6_asks.creator_tables(common.confirmatory(b), vs.definition())
        hit = [c for c in sorted(tables) if h6_asks._sum(tables[c])["a"] + h6_asks._sum(tables[c])["b"] >= 1]
        self.assertEqual(result["p"], h6_asks.amended_p([tables[c] for c in hit], ("t-0919",))[0])
        self.assertEqual(result["p_parts"]["ask_level_conditional_0919"],
                         h6_asks.conditional_p([tables[c] for c in hit], ("t-0919", "conditional"), by="ask")[0])
        registered = result["registered_version"]
        values = [h6_asks.half_count(h6_asks._sum(tables[c])) for c in sorted(tables)]
        self.assertEqual(registered["p"], stats.signflip_p(values, "less", label=("t-0919", "registered"))[0])
        self.assertTrue(any("conditional Monte Carlo" in item for item in result["a10_replaces"]))

    def test_the_level_on_constructed_numbers(self):
        """17 creators with 1 to 3 asks at claimed shares 0.2 to 0.5 (exact enumeration, simulate.h6_reference_levels):
        the conditional reference holds 0.005 and 0.05 where the sign-flip of OE did not."""
        names = ("17 creators, T = 1, s = 0.3", "17 creators, T = 2, s = 0.3", "17 creators, T = 1, s = 0.2",
                 "17 creators, T = 3, s = 0.5", "17 creators, T = 1, s cycled 0.2 to 0.5", "12 creators, T = 1, s = 0.3")
        rows = {row["case"]: row for row in simulate.h6_reference_levels([c for c in simulate.h6_level_cases() if c[0] in names])}
        self.assertEqual(set(rows), set(names))
        for row in rows.values():
            for alpha in ("0.005", "0.05"):
                self.assertLessEqual(row["conditional_mc_" + alpha], float(alpha) + 1e-12, row["case"])
                self.assertLessEqual(row["exact_conditional_" + alpha], float(alpha) + 1e-12, row["case"])
        flip = rows["17 creators, T = 1, s = 0.3"]
        self.assertAlmostEqual(flip["signflip_0.005"], 0.0193, places=4)            # the verifiers' 1.93%
        self.assertGreater(flip["signflip_0.05"], 0.07)
        self.assertGreater(rows["17 creators, T = 2, s = 0.3"]["signflip_0.005"], 0.009)
        self.assertAlmostEqual(rows["12 creators, T = 1, s = 0.3"]["signflip_0.005"], 0.7 ** 12, places=12)

    def test_the_level_formula_matches_the_code(self):
        self.assertEqual(simulate.largest_count_rejected(0.005, 9999), 49)
        self.assertEqual(simulate.largest_count_rejected(K.ALPHA / K.HOLM_M, 9999), 49)
        self.assertEqual(simulate.largest_count_rejected(0.05, 9999), 499)
        self.assertEqual(simulate.largest_count_rejected(0.005, 99), -1)
        # the enumerated Monte Carlo rate against the code's own p on one constructed case, by simulation of the data
        # (8 creators of one ask at a share of 0.5: about 0.03 at 0.05 with 199 draws)
        case = [[(1, 0.5)] for _ in range(8)]
        level = simulate.h6_conditional_level(case, alphas=(0.05,), draws=199)["monte_carlo"][0.05]
        self.assertGreater(level, 0.02)
        stream, hits, sets = stats.rng("t-0919-level"), 0, 1500
        for k in range(sets):
            creators = []
            for _ in case:
                a = int(stream.random() < 0.5)
                creators.append([recording(a, 1 - a, 0.5)])
            hits += h6_asks.conditional_p(creators, ("t-0919-level", k), 199)[0] <= 0.05
        self.assertLess(abs(hits / sets - level), 4 * math.sqrt(level * (1 - level) / sets) + 0.005)


class SparseLowShareScenario(unittest.TestCase):
    """09:19 (1): the battery's null scenario with claimed shares below one half and 1 to 3 asks per creator."""

    def test_the_plan_and_the_generator(self):
        for n in (12, 17):
            self.assertIn(("H6", "null_sparse_low_share", n, 1.0, 30), simulate.plan(quick=True))
            self.assertIn(("H6", "null_sparse_low_share", n, 1.0, 2000), simulate.plan())
        cfg = simulate.experiment_cfg("H6", 1.0, "null_sparse_low_share")
        self.assertEqual(cfg["claimed_fraction"], simulate.H6_SPARSE_CLAIMED_FRACTION)
        self.assertEqual(cfg["asks_per_creator"], (1, 3))
        b = simulate.cohort(stats.seed_for("t-0919-sparse"), 17, cfg, parts=simulate.PARTS["H6"])
        tables = h6_asks.creator_tables(common.confirmatory(b), vs.primary_definition("H6"))
        self.assertGreaterEqual(len(tables), 15)
        shares = [row["wc"] / (row["wc"] + row["wo"]) for rows in tables.values() for row in rows]
        self.assertLess(max(shares), 0.5)
        self.assertGreater(min(shares), 0.15)
        totals = [sum(row["a"] + row["b"] for row in rows) for rows in tables.values()]
        self.assertLessEqual(max(totals), 3)
        self.assertGreaterEqual(sum(1 for t in totals if t >= 1), 12)
        per_creator = {}
        for item in b["recordings"]:                # every recording has an asks record; only those with both voices hold asks
            per_creator[item["creator"]] = per_creator.get(item["creator"], 0) + len(item["asks"]["asks"])
        self.assertEqual(len(per_creator), 17)
        self.assertTrue(all(1 <= count <= 3 for count in per_creator.values()))
        # the other scenarios draw as before: a null cohort does not carry the scenario's settings
        self.assertNotIn("asks_per_creator", simulate.experiment_cfg("H6", 1.0, "null"))
        self.assertNotIn("claimed_fraction", simulate.experiment_cfg("H6", 1.0, "null_heterogeneous"))

    def test_the_rows_carry_the_reference_it_replaced(self):
        """Since 11:08 (1) the rows carry the sign-flip of OE as one half of the amended p, under the name p_signflip_oe."""
        rows = simulate.task(("H6", "null_sparse_low_share", 12, 1.0, 0, 2))["rows"]
        self.assertTrue(all("p_signflip_oe" in row and "p_pooled_oe_before_0644" in row for row in rows))
        b = simulate.cohort(stats.seed_for("t-0919-draws"), 12, simulate.experiment_cfg("H6", 1.0, "null"), parts=simulate.PARTS["H6"])
        result = simulate._run_one("H6", b, 1, light=True)
        self.assertEqual(result["p_method"],
                         f"max(conditional_monte_carlo_clusters_{simulate.H6_BATTERY_REFERENCE_DRAWS}, signflip_oe_exact)")
        table = simulate.summarise("H6", "null_sparse_low_share", 12, 1.0, rows, None, 0.0)
        self.assertIn("reject_0.005_signflip_oe", table)


# ---------------------------------------------------------------- (2) the OE-scale tolerance of A10.7

class OEScaleTolerance(unittest.TestCase):
    """09:19 (2): the OE versions are flagged against a tenth of the smallest effect expressed on the OE scale."""

    def test_h6_formula(self):
        self.assertAlmostEqual(a10_checks.h6_oe_smallest_effect([[(2, 0.5)]]), 1 / 3 - 0.5)
        q = 0.5 * 0.3 / (0.5 * 0.3 + 0.7)
        self.assertAlmostEqual(a10_checks.h6_oe_smallest_effect([[(1, 0.3), (3, 0.5)], [(0, 0.9)]]), (1 * (q - 0.3) + 3 * (1 / 3 - 0.5)) / 4)
        self.assertIsNone(a10_checks.h6_oe_smallest_effect([[(0, 0.4)]]))

    def test_h5_formula_is_the_expected_oe(self):
        row = {"WA": 10, "PA": 10, "WB": 10, "PB": 10}
        self.assertAlmostEqual(a10_checks.h5_oe_smallest_effect([row]), 0.5 * (a10_checks._expit(0.2) - a10_checks._expit(-0.2)), places=9)
        # E[OE | T_A, T_B] at the two side shares the formula solves for, by exact enumeration
        row = {"WA": 9, "PA": 3, "WB": 2, "PB": 6}
        ta, tb = 12, 8
        p_a, p_b = a10_checks._side_shares(11, ta, tb, 0.4)
        self.assertAlmostEqual(math.log(p_a / (1 - p_a)) - math.log(p_b / (1 - p_b)), 0.4, places=9)
        self.assertAlmostEqual(ta * p_a + tb * p_b, 11, places=9)
        expected = sum(math.comb(ta, wa) * p_a ** wa * (1 - p_a) ** (ta - wa) * math.comb(tb, wb) * p_b ** wb * (1 - p_b) ** (tb - wb)
                       * h5_world_claims.oe({"WA": wa, "PA": ta - wa, "WB": wb, "PB": tb - wb})
                       for wa in range(ta + 1) for wb in range(tb + 1))
        self.assertAlmostEqual(expected, tb / (ta + tb) * (p_a - p_b), places=12)
        self.assertIsNone(a10_checks.h5_oe_smallest_effect([row]))                # 8 hits on side B: below the margin
        self.assertEqual(a10_checks.h5_oe_smallest_effect([{"WA": 12, "PA": 0, "WB": 10, "PB": 0}]), 0.0)

    def test_the_flags_read_the_oe_scale(self):
        self.assertEqual(a10_checks._flag(0.02, -0.17), "recentring needed")        # 0.1 on the share scale said "centred"
        self.assertEqual(a10_checks._flag(0.01, -0.17), "centred")
        self.assertIsNone(a10_checks._flag(0.01, None))
        b = simulate.cohort(stats.seed_for("t-0919-tol"), 0, {"exact": True, "theta": 0.8}, n_seen=12,
                            parts=("voice", "asks", "titles", "content"))
        out = a10_checks.null_means(b, {}, draws=19)
        h6, h5 = out["H6"], out["H5"]
        self.assertAlmostEqual(h6["OE_smallest_effect"], h6["amended_OE_mean_at_plant"], places=12)
        self.assertAlmostEqual(h6["OE_tolerance"], 0.1 * abs(h6["OE_smallest_effect"]))
        self.assertLess(h6["OE_smallest_effect"], -0.05)
        self.assertEqual(h6["registered_tolerance"], 0.1 * math.log(2))
        self.assertGreater(h5["OE_smallest_effect"], 0.01)
        self.assertLess(h5["OE_smallest_effect"], 0.1)
        self.assertEqual(h5["amended_flag"], a10_checks._flag(h5["amended_OE_null_mean"], h5["OE_smallest_effect"]))
        self.assertIn("09:19 (2)", out["tolerance"])


# ---------------------------------------------------------------- (3) the null check keeps recordings without an ask file

class H6NullKeepsRecordingsWithoutAskFile(unittest.TestCase):
    def test_as_the_analysis(self):
        b = simulate.cohort(stats.seed_for("t-0919-noask"), 0, {"exact": True}, n_seen=12, parts=("voice", "asks"))
        seen = a10_checks.seen_only(b)
        creators = sorted(h6_asks.creator_tables(seen, vs.definition()))      # creators with both voices
        for item in seen["recordings"]:            # one creator loses every ask file, another its first
            if item["creator"] == creators[0] or (item["creator"] == creators[1] and item["audio"].endswith("-00")):
                item["asks"] = None
        tables = h6_asks.creator_tables(seen, vs.definition())
        out = a10_checks.h6_null(seen)
        self.assertEqual(out["creators"], len(tables))                               # the creator without asks counts
        self.assertEqual(out["recordings"], sum(len(rows) for rows in tables.values()))
        self.assertGreater(out["recordings_without_ask_file"], 0)
        self.assertEqual(out["amended_OE_null_mean"], 0.0)
        # the registered half-count expectation over every creator with both voices, word totals with a = b = 0 rows
        totals = {c: h6_asks._sum(rows) for c, rows in tables.items()}
        t0 = totals[creators[0]]
        self.assertEqual(t0["a"] + t0["b"], 0)
        # the analysis's registered version counts the same creators (the same records read as hold-out ones)
        held = dict(seen, recordings=[dict(item, group="holdout") for item in seen["recordings"]])
        result = h6_asks.analyse(held, extras=False, draws=19, reference_draws=99)
        self.assertEqual(result["registered_version"]["eligibility"]["creators"], out["creators"])
        self.assertIn(creators[0], result["registered_creator_values"])
        self.assertAlmostEqual(result["registered_creator_values"][creators[0]], h6_asks.half_count(t0))


# ---------------------------------------------------------------- (4) nothing in the package opens the hold-out tree

_TREE = r"(?:\bLLM\b|PRODUCTION_LABELS)"
# what enumerates a folder: a Path's .glob, .rglob, .iterdir or .walk (Python 3.12), and os.walk, os.listdir, os.scandir,
# glob.glob and glob.iglob (verifier and H6 engineer, 2026-11-21)
_METHODS = r"\.(?:r?glob|iterdir|walk)\("
_CALLS = r"\b(?:os\.(?:walk|listdir|scandir)|glob\.i?glob)\("
# a group name as a whole string or as a path part inside one ('holdout', 'holdout/voice', '/holdout/x.json',
# f'{...}/other/'); verifier, 2026-11-21 after 11:08: the closing quote alone let "TREE / 'holdout/voice'" pass
_GROUP = r"(?:[\"'}][\\/]*|[\\/]+)(?:holdout|other)[\"'\\/]"
SCAN = {"joins the production label tree with holdout or other":
        re.compile(r"(?:\bLLM\b|PRODUCTION_LABELS|\bllm\b)[^\n#]*?" + _GROUP),
        "names a hold-out or other-group label file": re.compile(r"labels[\\/]+(?:holdout|other)\b[^\n]*?\.json"),
        # the tree on one line with the call, or as the call's argument over several lines
        "enumerates the production tree": re.compile(_TREE + r"[^\n]*" + _METHODS + "|" + _CALLS + r"[^\n]*" + _TREE
                                                     + "|" + _CALLS + r"[^)]*?" + _TREE)}
LABELS_ROOT = re.compile(_TREE + r"\s*/\s*[\"'](?:labels|holdout|other)[\"'\\/]")
# outside the adapter: the tree joined with a name, whose value (a group) the scan cannot see (verifier, after 11:08)
JOIN_NAME = re.compile(_TREE + r"\s*/\s*[A-Za-z_]|" + _TREE + r"\.joinpath\(\s*[A-Za-z_]")
PRIVATE = re.compile("et-channelers" + "-private")        # written in two parts so that this file does not match
# outside the adapter: a string that names the production label tree, and a name bound to the tree (an assignment from
# LLM or PRODUCTION_LABELS, or an import of them under another name) that is then enumerated or joined with a group
LABELS_STRING = re.compile(r"[\"'][\w.:~\\/-]*\bllm[\\/]+labels\b")      # a path literal, not prose
ALIASES = (re.compile(r"^[ \t]*(\w+)[ \t]*=[^\n#=]*" + _TREE, re.M),
           re.compile(r"\bimport\b[^\n]*\b(?:LLM|PRODUCTION_LABELS)[ \t]+as[ \t]+(\w+)"))


def _aliases(text):
    return sorted({name for pattern in ALIASES for name in pattern.findall(text)} - {"LLM", "PRODUCTION_LABELS"})


def scan_problems(name, text):
    """The static scan of one source (09:19 (4)): what it does that the package must not."""
    out = [f"{name} {what}" for what, pattern in SCAN.items() if pattern.search(text)]
    if name != "adapter.py" and LABELS_ROOT.search(text):     # the adapter defines PRODUCTION_LABELS and gates every opening
        out.append(f"{name} builds a path into the production label tree")
    if name != "adapter.py" and JOIN_NAME.search(text):
        out.append(f"{name} joins the production label tree with a name")
    if PRIVATE.search(text) and name not in ("adapter.py", "features.py"):
        out.append(f"{name} builds a path into the private folder")
    if name != "adapter.py":
        if LABELS_STRING.search(text):
            out.append(f"{name} names the production label tree in a string")
        for alias in _aliases(text):
            word = r"\b" + re.escape(alias) + r"\b"
            if re.search(word + r"[^\n]*" + _METHODS + "|" + _CALLS + r"[^)]*?" + word + "|" + word
                         + r"\s*/\s*[\"'](?:labels|holdout|other)[\"'\\/]", text):
                out.append(f"{name} enumerates or joins the production tree through the name {alias}")
    return out


class NothingOpensTheHoldOutOrOtherTree(unittest.TestCase):
    """09:19 (4): the verifier's test file that globbed llm/labels left the package, and no .py file left in it names
    a path under the production tree's labels/holdout or labels/other (the adapter refuses such paths before freeze 2;
    tests build their own temporary trees). A static scan of the sources: nothing is opened."""

    def test_no_verifier_file_left(self):
        self.assertFalse((HERE / "verify").exists())
        self.assertEqual([p.name for p in HERE.rglob("test_verify*.py")], [])

    def test_no_source_names_the_production_holdout_or_other_tree(self):
        for path in sorted(p for p in HERE.rglob("*.py") if "__pycache__" not in p.parts):
            self.assertEqual(scan_problems(path.name, path.read_text(encoding="utf-8")), [])

    def test_the_scan_catches_what_opens_the_production_tree(self):
        """Verifier, 2026-11-21: the first scan matched .glob( and .rglob( only, so an iterdir, os.walk, os.listdir,
        os.scandir or glob.glob of the production tree passed it. The names are written in parts so that this file does
        not match."""
        name = "PRODUCTION_" + "LABELS"
        caught = {"iterdir": f"for group in adapter.{name}.iterdir():\n",
                  "rglob": f"files = list(adapter.{name}.rglob('*.json'))\n",
                  "os.walk": f"for root, _, names in os.walk(adapter.{name}):\n",
                  "os.listdir": f"names = os.listdir(adapter.{name} / group)\n",
                  "os.scandir": f"entries = os.scandir(str(adapter.{name}))\n",
                  "glob.glob": f"names = glob.glob(str(adapter.{name}) + '/*/*.json')\n",
                  "joined": f"folder = adapter.{name} / 'holdout' / 'voice'\n",
                  "the moved verifier file": "LLM = Path.home() / '" + "et-channelers" + "-private' / 'llm'\n"
                                             "folder = L" + "LM / 'labels' / group\n"}
        # H6 engineer, 2026-11-21 (after 11:08): a Path's .walk, a call over several lines, a name bound to the tree,
        # an import under another name, and a string naming the tree
        caught.update({"Path.walk": f"for root, dirs, files in adapter.{name}.walk():\n",
                       "os.walk over two lines": f"for root, _, names in os.walk(\n        adapter.{name}):\n",
                       "glob.glob over two lines": f"names = glob.glob(os.path.join(\n    str(adapter.{name}), '*'))\n",
                       "alias iterdir": f"root = adapter.{name}\nfor group in root.iterdir():\n",
                       "alias os.scandir": f"root = adapter.{name} / group\nentries = os.scandir(root)\n",
                       "alias joined": f"base = adapter.L" + "LM\nfolder = base / 'labels'\n",
                       "import alias": f"from hypotheses.adapter import {name} as tree\nfiles = list(tree.rglob('*.json'))\n",
                       "string": "folder = Path.home() / 'x' / 'l" + "lm/labels' / group\n"})
        # verifier, 2026-11-21 after 11:08: a group name as a path part inside a string, and the tree joined with a name
        caught.update({"group inside a string": f"folder = adapter.{name} / 'hold" + "out/voice'\n",
                       "other inside a string": f"folder = adapter.{name} / \"oth" + "er/asks\"\n",
                       "concatenated string": f"data = Path(str(adapter.{name}) + '/hold" + "out/asks/x.json').read_text()\n",
                       "f-string": f"folder = Path(f'{{adapter.{name}}}/hold" + "out/voice')\n",
                       "alias then a string": f"root = adapter.{name}\nfolder = root / 'hold" + "out/voice'\n",
                       "joined with a name": "group = 'hold" + f"out'\npath = adapter.{name} / group / 'asks' / audio\n",
                       "joinpath with a name": f"path = adapter.{name}.joinpath(group, 'asks')\n"})
        for what, text in caught.items():
            self.assertNotEqual(scan_problems("example.py", text), [], what)
        self.assertEqual(scan_problems("example.py", "for path in sorted(HERE.rglob('*.py')):\n"), [])
        # an alias that is only compared or printed, and enumeration of another folder, pass
        self.assertEqual(scan_problems("example.py", f"root = adapter.{name}\nprint(root == other)\n"
                                                     "for entry in os.scandir(folder):\n"), [])
        # a literal file name under the tree (the freeze-2 record, produce's key list) passes
        self.assertEqual(scan_problems("example.py", "record = adapter.L" + "LM / 'freeze2.json'\n"), [])


if __name__ == "__main__":
    unittest.main()
