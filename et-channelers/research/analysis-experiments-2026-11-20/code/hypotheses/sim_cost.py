"""The simulation battery's cost model: expected seconds of each task in one worker, for the ETA, the planned wall time
(run.py simulate --estimate) and the order in which tasks are handed out (largest first). Nothing else uses it.

This module is not in simulate.TASK_MODULES. Recalibrating it therefore changes no task fingerprint: a battery's
checkpoint stays valid and a frozen fingerprint stays frozen. simulate.run assembles the table in a fixed order (by
experiment, then first repetition), so the table does not depend on the order this model gives the tasks either.

The figures are seconds per repetition, measured in the guarded venv in a 4-worker spawn pool (as the battery runs),
with each worker's FREEZE2 constants built beforehand, on 2026-11-21 07:19 to 07:22 UTC, task fingerprint da93bb3e7b7a
(simulate.task_fingerprint()), synthetic creators only, with no other heavy local job running. They are averaged over the
battery's scenarios with the plan's weights. H9 is split into a base (its cohort of 40 seen and the hold-out creators,
the permutation p) and a part per creator-bootstrap draw (two-stage, every cell re-rarefied in every draw, registry
2026-11-21 06:44 (4)), from a single-process run on fingerprint 29e3bc523c5e at 07:13 to 07:17 UTC (analyse alone: 0.29
and 0.34 s with no draw, 6.34 and 7.64 s with 99 draws, at 12 and 17 creators). The base and the per-draw part are
scaled so that at 99 draws they give the pool's figures; the cost then follows simulate.H9_BATTERY_BOOTSTRAP_DRAWS.

tests/test_sim_cost.py times repetitions of every hypothesis and fails when the model's relative costs are off by more
than CALIBRATION_TOLERANCE, as they were after H9's bootstrap became two-stage (the earlier table, simulate.COST, gave
H9 15 units against H1's 1, with a measured 22 to 37). Recalibrate by rerunning the pool measurement and replacing the
figures.

History of the earlier relative table simulate.COST (units of H1, scaled by creators / 12; removed 2026-11-21 07:26
UTC): measured 2026-11-20 23:55 local on the revised code (at 17 creators: H1 0.33 s, H2 1.17, H4 0.88, H5 0.99, H6
0.83, H9 5.0); again 2026-11-21 05:43 UTC after the decisions of 04:55 with another battery running (H1 0.32 s, H2 1.6,
H4 0.8, H5 1.06, H6 0.91; H9 not remeasured); and about 07:15 UTC after the decisions of 06:44 with no battery running
(12 / 17 creators: H1 0.21 / 0.32, H2 0.57 / 0.86, H4 0.27 / 0.44, H5 0.37 / 0.55, H6 0.3 / 0.4, H9 7.8 / 9.2), which
set it to H1 1, H2 2.7, H4 1.4, H5 1.7, H6 1.3, H9 29. Its scaling by creators / 12 put H9's 17-creator rows 20% high and
its 12-creator rows 20% low (H9 is 1.18 times dearer at 17 than at 12, not 1.42), and its targets far off (H9's target
870 units, about 180 s, against a measured 25 s; the others about half their measured time).
"""

MEASURED = "2026-11-21 07:19-07:22 UTC, 4-worker spawn pool, guarded venv, task fingerprint da93bb3e7b7a"
CALIBRATION_TOLERANCE = 1.6          # largest accepted ratio between the model's and a timed repetition's cost (vs H1)

# seconds per repetition at 12 and at 17 hold-out creators
REP_SECONDS = {"H1": (0.307, 0.447), "H2": (0.688, 0.966), "H4": (0.263, 0.381), "H5": (0.365, 0.595),
               "H6": (0.345, 0.487)}
# H9 (40 seen creators): base seconds and seconds per bootstrap draw, at 12 and at 17 hold-out creators
H9_BASE_SECONDS = (2.67, 2.50)
H9_SECONDS_PER_DRAW = (0.0611, 0.0737)
# one large-sample target task (3 designs of 240 creators; H9 60 hold-out and 60 seen, 10 draws and 10 permutations)
TARGET_SECONDS = {"H1": 28.2, "H2": 59.6, "H4": 27.6, "H5": 34.2, "H6": 41.8, "H9": 24.8}


def _at(pair, n):
    """Linear in the hold-out count through the figures at 12 and 17 creators, never below a tenth of the first."""
    low, high = pair
    return max(0.1 * low, low + (high - low) * (n - 12) / 5.0)


def rep_seconds(hypothesis, n, h9_draws):
    """Expected seconds of one repetition of hypothesis at n hold-out creators (H9 with h9_draws bootstrap draws)."""
    if hypothesis == "H9":
        return _at(H9_BASE_SECONDS, n) + h9_draws * _at(H9_SECONDS_PER_DRAW, n)
    return _at(REP_SECONDS[hypothesis], n)


def task_seconds(spec, h9_draws):
    """Expected seconds of one battery task (hypothesis, scenario, n, effect, first repetition, repetitions)."""
    hypothesis, scenario, n, effect, first, reps = spec
    if scenario == "target":
        return TARGET_SECONDS[hypothesis]
    return reps * rep_seconds(hypothesis, n, h9_draws)


def estimate(tasks, workers, h9_draws):
    """Planned CPU seconds and wall seconds of a list of tasks on `workers` workers. The wall time is the CPU time
    divided by the workers, and never less than the largest task (largest-first scheduling leaves at most one such
    task as the tail). Run 3 of the battery (2026-11-20/21) kept its 4 workers 99.9% busy."""
    seconds = [task_seconds(spec, h9_draws) for spec in tasks]
    cpu = sum(seconds)
    by_hypothesis = {}
    for spec, value in zip(tasks, seconds):
        by_hypothesis[spec[0]] = by_hypothesis.get(spec[0], 0.0) + value
    wall = max(cpu / max(1, workers), max(seconds) if seconds else 0.0)
    return {"tasks": len(tasks), "cpu_seconds": round(cpu, 1), "workers": workers, "wall_seconds": round(wall, 1),
            "cpu_seconds_by_hypothesis": {key: round(value, 1) for key, value in sorted(by_hypothesis.items())},
            "h9_bootstrap_draws": h9_draws, "measured": MEASURED}
