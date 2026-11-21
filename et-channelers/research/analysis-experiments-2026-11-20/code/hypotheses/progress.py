"""Progress with an estimated time of completion, and a deterministic parallel map.

Progress prints at most every `every` seconds to stderr: done/total, elapsed, ETA and the clock time of completion. The
ETA is elapsed / done * remaining, weighted by each task's declared cost when the tasks are of unequal size. With a
status path, every printed line is also written there as JSON (share done, elapsed, ETA, expected finish), so that the ETA
of a detached run can be read at any time.

parallel_map runs independent tasks in worker processes (spawn), one task per call, and returns the results in task
order. Every task carries its own seed label, so the results do not depend on the number of workers or on the order in
which tasks finish. The pool is capped by os.cpu_count(), which the analysis venv's resource guard caps at
ET_MAX_WORKERS (4 by default). on_result(task, result) is called in the parent as each result arrives (the simulation
battery appends it to its checkpoint there, so a run that dies resumes without losing finished tasks). prior_tasks and
prior_cost are the tasks a resumed run found finished: they count in the share done, not in the rate behind the ETA.
"""
import os
import datetime as dt
import json
import multiprocessing as mp
from pathlib import Path
import sys
import time


def _clock(seconds):
    seconds = int(max(0, seconds))
    return f"{seconds // 3600}:{seconds % 3600 // 60:02d}:{seconds % 60:02d}"


def default_workers(cap=None):
    """os.cpu_count() (4 under the analysis venv's resource guard), lowered to cap when given."""
    count = os.cpu_count() or 1
    return max(1, min(count, cap) if cap else count)


class Progress:
    def __init__(self, total_cost, label, every=5.0, stream=None, status_path=None, tasks=None, prior_tasks=0, prior_cost=0.0):
        self.total, self.label, self.every = float(total_cost), label, every
        self.status_path, self.tasks = (Path(status_path) if status_path else None), tasks
        self.prior_tasks, self.prior_cost = prior_tasks, float(prior_cost)
        self.done = 0.0
        self.count = 0
        self.start = time.monotonic()
        self.last = 0.0
        self.stream = stream or sys.stderr
        self.history = []

    def eta_seconds(self):
        elapsed = time.monotonic() - self.start
        if self.total <= 0:
            return 0.0
        if self.done <= 0:
            return None
        return elapsed / self.done * (self.total - self.done)

    def share(self):
        whole = self.prior_cost + self.total
        return (self.prior_cost + self.done) / whole if whole > 0 else 1.0

    def update(self, cost=1.0, force=False, count=True):
        self.done += cost
        self.count += 1 if count else 0
        now = time.monotonic()
        if force or now - self.last >= self.every or self.done >= self.total:
            self.last = now
            eta = self.eta_seconds()
            finish = (dt.datetime.now() + dt.timedelta(seconds=eta)).strftime("%H:%M:%S") if eta is not None else "?"
            resumed = f" ({self.prior_tasks} found finished)" if self.prior_tasks else ""
            line = (f"[{self.label}] {self.prior_tasks + self.count} of {self.tasks} tasks{resumed}, {100 * self.share():5.1f}% of work, "
                    f"elapsed {_clock(now - self.start)}, ETA {_clock(eta) if eta is not None else '?'} (about {finish} local)")
            self.history.append({"elapsed": round(now - self.start, 1), "share": round(self.share(), 4),
                                 "eta_seconds": None if eta is None else round(eta, 1)})
            print(line, file=self.stream, flush=True)
            if self.status_path:
                status = {"label": self.label, "tasks_done": self.prior_tasks + self.count, "tasks_total": self.tasks,
                          "tasks_found_finished_at_start": self.prior_tasks, "share_done": round(self.share(), 4),
                          "elapsed_seconds": round(now - self.start, 1), "eta_seconds": None if eta is None else round(eta, 1),
                          "expected_finish_local": None if eta is None else (dt.datetime.now() + dt.timedelta(seconds=eta)).isoformat(timespec="seconds"),
                          "finished": self.done >= self.total, "pid": os.getpid(),
                          "updated_local": dt.datetime.now().isoformat(timespec="seconds")}
                self.status_path.write_text(json.dumps(status, indent=1), encoding="utf-8")

    def summary(self):
        return {"tasks": self.count, "tasks_found_finished": self.prior_tasks, "elapsed_seconds": round(time.monotonic() - self.start, 1),
                "eta_history": self.history}


def parallel_map(function, tasks, workers, label, cost=None, status_path=None, on_result=None, prior_tasks=0, prior_cost=0.0,
                 total_tasks=None):
    """function(task) -> result, for picklable tasks; cost(task) -> relative size for the ETA. Returns (results, summary)."""
    cost = cost or (lambda task: 1.0)
    progress = Progress(sum(cost(task) for task in tasks), label, status_path=status_path,
                        tasks=total_tasks if total_tasks is not None else len(tasks), prior_tasks=prior_tasks, prior_cost=prior_cost)
    progress.update(0.0, force=True, count=False)                    # a status line at the start (also of a resumed run)
    results = [None] * len(tasks)
    if workers <= 1 or len(tasks) <= 1:
        for index, task in enumerate(tasks):
            results[index] = function(task)
            if on_result:
                on_result(task, results[index])
            progress.update(cost(task))
        return results, progress.summary()
    context = mp.get_context("spawn")
    with context.Pool(processes=min(workers, len(tasks), os.cpu_count() or 1)) as pool:   # capped by the CPU count (4 in the guarded venv)
        for index, result in pool.imap_unordered(_indexed, [(function, index, task) for index, task in enumerate(tasks)]):
            results[index] = result
            if on_result:
                on_result(tasks[index], result)
            progress.update(cost(tasks[index]))
    return results, progress.summary()


def _indexed(packed):
    function, index, task = packed
    return index, function(task)
