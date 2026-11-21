"""The battery's cost model (sim_cost, behind the ETA) and the frozen-fingerprint check of run.py simulate.
Synthetic creators only; nothing here reads a label file."""
import contextlib
import io
import json
import math
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from hypotheses import run as cli  # noqa: E402
from hypotheses import sim_cost, simulate  # noqa: E402


class CostModel(unittest.TestCase):
    def test_h9_cost_follows_the_battery_bootstrap_draws(self):
        # Registry 2026-11-21 06:44 (4) made every H9 draw re-rarefy the cells: the draws are most of H9's time, so a
        # cost that ignores their number goes stale whenever the battery's draw count changes.
        spec = ("H9", "null", 17, 0.0, 0, 25)
        with mock.patch.object(simulate, "H9_BATTERY_BOOTSTRAP_DRAWS", 0):
            without = simulate.task_cost(spec)
        with mock.patch.object(simulate, "H9_BATTERY_BOOTSTRAP_DRAWS", 99):
            with_draws = simulate.task_cost(spec)
        self.assertGreater(with_draws, 2.5 * without)

    def test_relative_costs_match_timed_repetitions(self):
        # One process, repetitions as the battery runs them (constants built first, as each worker does once), at 17
        # creators. The model may differ from this machine's speed by a common factor, not in its relative costs.
        reps = {"H1": 5, "H2": 2, "H4": 3, "H5": 3, "H6": 3, "H9": 1}
        timed = {}
        for hypothesis, count in reps.items():
            simulate.calibration_constants(hypothesis)
            started = time.perf_counter()
            simulate.task((hypothesis, "null", 17, simulate.NULL[hypothesis], 700000, count))
            timed[hypothesis] = (time.perf_counter() - started) / count
        model = {h: simulate.task_cost((h, "null", 17, simulate.NULL[h], 0, 1)) for h in reps}
        logs = {h: math.log(model[h] / timed[h]) for h in reps}
        scale = sum(logs.values()) / len(logs)
        off = {h: math.exp(abs(logs[h] - scale)) for h in reps}
        self.assertLess(max(off.values()), sim_cost.CALIBRATION_TOLERANCE,
                        "cost model off against timed repetitions (factor, model, timed s): "
                        + ", ".join(f"{h} {off[h]:.2f} {model[h]:.3f} {timed[h]:.3f}" for h in reps)
                        + "; recalibrate sim_cost.py")

    def test_table_does_not_depend_on_the_order_of_the_tasks(self):
        # The cost model orders the tasks and is outside the task fingerprint, so the rows of an experiment must reach
        # summarise in the same order whatever order the tasks ran in.
        tiny = [("H1", "null", 12, 0.0, 6)]
        seen = []

        def capture(hypothesis, scenario, n, effect, rows, target, planted):
            seen.append(json.dumps(rows, sort_keys=True))
            return {"hypothesis": hypothesis}

        for order in (lambda spec: spec[4] + 1.0, lambda spec: 1000.0 - spec[4]):
            with mock.patch.object(simulate, "plan", lambda quick=False: tiny), \
                    mock.patch.object(simulate, "large_sample_target", lambda h, e, reps=3: 0.0), \
                    mock.patch.object(simulate, "task_cost", order), \
                    mock.patch.object(simulate, "summarise", capture):
                simulate.run(1, chunk=2)
        self.assertEqual(len(seen), 2)
        self.assertEqual(seen[0], seen[1])

    def test_estimate_prints_the_plan_and_runs_nothing(self):
        out = io.StringIO()
        with mock.patch.object(simulate, "run", side_effect=AssertionError("battery started")), \
                contextlib.redirect_stdout(out):
            cli.cmd_simulate(["--estimate", "--workers", "4"])
        plan = json.loads(out.getvalue())
        tasks = simulate.tasks_for()
        self.assertEqual(plan["tasks"], len(tasks))
        self.assertAlmostEqual(plan["cpu_seconds"], sum(simulate.task_cost(spec) for spec in tasks), delta=1.0)
        self.assertAlmostEqual(plan["wall_seconds"], plan["cpu_seconds"] / 4, delta=1.0)
        self.assertEqual(plan["fingerprint"], simulate.task_fingerprint())


class FrozenFingerprint(unittest.TestCase):
    def test_simulate_refuses_another_fingerprint(self):
        with tempfile.TemporaryDirectory() as folder, \
                mock.patch.object(simulate, "run", side_effect=AssertionError("battery started")) as started, \
                mock.patch.object(simulate, "boundary_table", side_effect=AssertionError("boundary started")):
            with self.assertRaises(SystemExit) as caught:
                cli.cmd_simulate(["--expect-fingerprint", "0" * 64, "--out", folder])
            started.assert_not_called()
            self.assertEqual(list(Path(folder).iterdir()), [])            # no status, checkpoint or result written
        self.assertIn(simulate.task_fingerprint(), str(caught.exception))

    def test_the_frozen_fingerprint_passes_in_full_or_by_its_first_12_digits(self):
        fingerprint = simulate.task_fingerprint()
        self.assertEqual(simulate.require_fingerprint(fingerprint), fingerprint)
        self.assertEqual(simulate.require_fingerprint(fingerprint[:12].upper()), fingerprint)
        with self.assertRaises(SystemExit):
            simulate.require_fingerprint(fingerprint[:8])                  # too short to stand for a freeze

    def test_hashes_print_the_task_fingerprint(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            cli.main(["hashes"])
        self.assertIn(simulate.task_fingerprint(), out.getvalue())


if __name__ == "__main__":
    unittest.main()
