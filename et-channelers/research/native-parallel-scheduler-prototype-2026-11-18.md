# Source/publication scheduler prototype, November 18

`pipeline/native_bulk/parallel_scheduler.py` isolates a concrete scheduling change for a future `NativeBatch` adapter: keep the manager available to drain source completions and refill eligible source slots while **one separate publisher** is working. It has no Source, Drive, media or process-launch implementation and is not imported by the running executor. No existing executor, runtime setting, policy, source grant or ASR state changes.

## What the evidence establishes

The saved 140-decision profile measured a source-process-plus-cleanup concurrency **upper bound of 0.973 out of two**, about 1,130 seconds with neither owned source process/cleanup interval active, and about 962 seconds where that idle time overlapped completed files awaiting receipts. Five intentional 30-second adaptive pauses also occurred, and actual publication-start/copy boundaries were not recorded. These observations do **not** identify Drive bandwidth as the bottleneck or establish a production speedup.

The current `NativeBatch.run()` manager drains completed sources, refills eligible slots and then calls `publish()` synchronously. Source workers that finish during that call cannot be drained/refilled until publication returns. The prototype removes that specific blocking path. A controlled Event fixture proves that a fourth source job starts while the first publisher is still deliberately blocked, using only two source threads. This is a control-flow result, not a throughput benchmark.

## Execution and outcome contract

One finite, immutable ordered list of unique `WorkItem` keys enters a one-shot scheduler. There are at most **two source futures and one publisher future**. The default limit is four outstanding jobs, configurable up to six. Outstanding means active source futures + ready unpublished outputs + the current publisher. A result becoming ready does not free that slot. The limit is a count envelope; the caller's byte-admission callback remains authoritative.

`before_submit(item, active_items)` sees every submitted source future, including a future whose real child reservation is not visible yet. The adapter must charge such virtual commitments under the same dispatch lock as real reservations. A false decision defers locally without invoking a source callback. Existing owned work/publication may release space and cause a later admission check. If no in-flight work or ready publication can release anything, the scheduler returns the ordered unsubmitted tail as **pending** instead of spinning indefinitely.

The manager consumes publication failures and source completions before admitting more work. Source callbacks receive fresh guards before submission and again in the worker; a fatal flag is checked again after the worker guard, preventing a sibling from entering source execution after a fatal event occurred during that guard. Failure reason and flag are published together, independently of a manager's byte-admission lock.

The source adapter returns `Acquisition`: **ready**, **held** or **retained**, with its original opaque result preserved. Ready means local output is available for the publisher; it never means remotely verified. A ready result requires a payload. A local format hold can remain nonfatal. Unknown callback exceptions, explicit source/global fatal outcomes and invalid callback contracts hold new admissions and new publication starts.

The publisher adapter returns `Publication(verified=True, proof=...)` only after the existing canonical paired receipt verifier succeeds. A truthy status string or `local_complete` is insufficient. Only one publisher may run. Fresh Drive guards precede its callback. A publication failure retains its original acquisition payload and stops new source and publication work; it is not automatically retried. Publication already in flight may finish truthfully after a source hold.

On a fatal event, `stop_owned(reason, active_items)` is called once so the real owner can signal its existing owned-worker stop mechanism. The manager continues collecting in-flight outcomes and retains all completed unpublished output. Unsubmitted items remain pending. The callback must be bounded and must not force-kill unowned work, rewrite provider history or invent zero access. Failure of the stop callback is explicit in the report.

The drain deadline does not pretend that arbitrary Python threads can be canceled. A callback that fails to return becomes **inflight**, and the report is **unclosed**. The outer owned-process supervisor must retain its reservations and reconcile actual closure. Background callbacks may still finish later; a report snapshot cannot replace their receipts or audits. Cancelable futures that never entered a callback remain pending. No source invocation or upload is automatically replayed.

Report `complete` means this scheduler has processed its finite work list; individual held or retained outcomes remain explicit. It does not mean all audio was acquired. `submitted` counts scheduler submissions, not proven source attempts or requests. All work items reconcile to exactly one reported outcome: verified, held, retained, pending or inflight.

## Concrete future NativeBatch adapter

Keep the current outer collector ownership, immutable frame settings, source policies, owned-process containment, cleanup and receipt-skip/recovery preflight. Construct the scheduler only from that frame's admitted untouched items after preflight. Do not edit a running package to install this prototype.

The callback mapping for an isolated future subclass is:

```python
def acquire(work):
    result = batch.execute_child(work.value)  # Existing owned Job/HTTP/cleanup path.
    fatal = batch.source_stop.is_set()
    if result.get('status') == 'local_complete':
        return Acquisition('ready', result, fatal=fatal)
    return Acquisition('held', result, fatal=fatal)

def publish(work, acquisition, trace):
    done = batch.publish(work.value, acquisition.value)
    # The mature helper already enforces this; retain the explicit adapter check.
    if not storage.receipt_complete(done, work.value, batch.s['remote']):
        return Publication(False, reason='canonical_receipt_incomplete')
    return Publication(True, proof=done)
```

This mapping does not replace `execute_child()`'s strict quality/closure logic or `publish()`'s exact audio/metadata size, MD5, ID, immutable metadata lineage and proof-before-cleanup rules. Source callback exceptions remain unknown/fatal in the scheduler, not fabricated held worker results. Valid final diagnostics remain authoritative even without progress.

Before every submit, the adapter must use `batch.lock`, fresh exact-item `batch.guard(source=True, video_id=...)`, current HTTP/fatal observation ingestion, active source lease/pins and the actual Drive cooldown. Compute full active commitments plus virtual slots for `active_items` not yet represented in `batch.live_reservations`, the candidate, publisher headroom and inactive files. Check both spool and global managed/physical limits. Reuse `capacity_partition()` invalidation/reconciliation; do not count completed files as free before receipt/owned cleanup. The separate admission-budget prototype provides a stronger reservation component for a later integration; it does not remove these checks.

Use the existing lane's actual controls. The old parked collector's `STOP_DRIVE_INGEST` is intentionally preserved and is not a new generic stop condition. `drive_guard` checks the current publication lease/expiry and shared Drive cooldown; the existing Rclone helper repeats its own guarded calls. `stop_requested` observes the current owner's sticky Source/administrative stop. `stop_owned` signals the existing batch stop/dispatch mechanism, allowing `execute_child()` to return only through its owned cleanup/audit path. A scheduler return alone proves no process closure.

An adaptive pause or admission deadline must remain explicit policy. Before entering or resuming an otherwise idle scheduler, the owning controller can wait boundedly for a known pause with fresh guards and the existing grant deadline. Only report **pending**, never held/retained/verified items, may be scheduled afterward after checking no actual attempt was spent. Do not blindly rerun a scheduler after fatal/unclosed results, or convert a local initial capacity false into a source quarantine or a completed frame. Unknown/static capacity without work able to free space needs a truthful local hold. No initial 60-second child GO window is repurposed for capacity waits.

The publisher callback runs on its dedicated thread. Audit shared catalog/state/Rclone access and keep one outer collector owner; do not reacquire a process-wide collector lock from that thread. Use the existing short dispatch-lock sections for partition invalidation and reconciliation. **Do not hold the dispatch lock over copy/stat network work**, or the manager would again be unable to refill source work. The byte budget must reserve publication's auxiliary workspace and enforce all writes, not rely only on the outstanding count.

This first scheduler experiment deliberately retains two source callbacks for comparison. The separate four-child metadata-first design needs a subsequent scoped integration: increasing this component's source bound or using extra bootstrap children is not authorized here.

## Timing hooks and validation

Internal timings record source callback start/finish, submission/refill, ready observation, publication start/finish and manager idle intervals. Publication-start duration measures source-completion-to-publication-start wait. Source callback duration includes its guard, bootstrap, transfer, quality and cleanup; it is not isolated network time. Sequence numbers order events even when the Windows monotonic clock returns equal timestamps.

`PublisherTrace.mark()` offers copy, stat, receipt and cleanup boundaries. Instrument the **actual** `Rclone.copy_pair/copy_batch`, `stat/stat_batch`, canonical proof and owned cleanup boundaries in a caller-owned wrapper. Wrapping the whole `NativeBatch.publish()` call with `copy_start/copy_finish` would falsely label hashing, scans, metadata preservation and queueing as copy time. Phase marks are observations, not archive proofs. The event observer must be bounded and preserve private logs; observer failures hold dispatch and retain output. No URLs, tokens or raw exception messages are generated by scheduler diagnostics.

Controlled source-free fixtures demonstrate source refill while publication is blocked, outstanding limits of four/six, a single publisher, fresh guards and virtual reservations, correct failure retention, one stop call, truthful unclosed deadlines, no initial-capacity spin, explicit held decisions and real timing hooks. Independent review reproduced a fatal-during-worker-guard race; the post-guard fatal check and its regression fix that path. No production speedup or live acceptance follows from these tests. The next admitted experiment should compare the same two-source scope with publication-start/copy/scan timings, validated pairs, ready-byte peaks, intentional pauses and actual resource use.
