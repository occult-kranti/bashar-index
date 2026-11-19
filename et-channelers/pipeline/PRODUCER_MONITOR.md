# Progress observations and early native handoff

These local helpers do not fetch source media, start a native downloader, change
provider outcomes, or count an item as archived. Deploy them in a new compatible
runtime; leave an active frame and its pinned source code unchanged.

`progress_observation_io.atomic_observation(path, value, root=job)` writes only
the explicitly owned `job/progress.json`. It preserves pending/fsync/atomic
replacement and the actual failure stage. On Windows its readers share deletion
and its writer uses `ReplaceFileW` for an existing destination. Failed pending
files remain for diagnosis. Immutable grants, results and controls keep their
normal readers.

Use one `ProgressObserver` under the controller's dispatch mutex. Call
`documents(job, active=True)` on each active child. At most three immediate
attempts handle a replaced/missing progress sample. Persist its `states` in
operator diagnostics. Unknown samples block **new admission, MEDIA_GO and
BODY_GO** through `permits_new_dispatch()`; already permitted bodies and
publication drain. Never replace unknown counters with zero. A stable sample
clears only that child's unknown state. An immutable final result alone does
not clear it: the caller must validate both that result and the child's real
owned closure, then call `accept_validated_closed_terminal`.

Child registration, `permits_first_bootstrap(video, started_videos=...)`, the
first durable GO, and updating `started_videos` belong in the **same dispatch
mutex transaction**. The first child may create its own initial sample;
started siblings with unknown observations block later bootstraps. Repeat all
live grant, provider, size and child-liveness guards at GO. Share the controller's
fatal Event with its scheduler so a fatal admission error latches before slower
diagnostic capture. Observation pausing is not a Source retry.

Run the producer monitor alongside an already owned ordinary frame from the
`et-channelers` directory (replace placeholders with the installed runtime's
exact paths and pins):

```powershell
python -B -m pipeline.native_producer_drain `
  --frame C:/private/provisioning/frame `
  --private-root C:/private `
  --scope-sha256 <successor-scope-sha256> `
  --kernel-code C:/code/pipeline/gpu_asr.py `
  --kernel-sha256 <installed-kernel-sha256> `
  --threshold 16
```

The registry supplies ordered exact video IDs and expected channel IDs. The
monitor uses `native_handoff_queue.closed_ticket` to require the current
grant/attempt, immutable child result, clean owned closure, profile cleanup,
fresh native identity, bounded known bytes and **zero selected-media requests**.
It validates each closed child's content once and checks file identities on
later polls. Changes and authoritative read/JSON errors stop the monitor;
missing not-yet-closed children remain pending. Mutable progress is never cached
by this ticket monitor. Signed private URLs are not included in its evidence.

At 16 eligible tickets (configurable 6–24), or an eligible ticket near expiry,
the monitor invokes only the frame's **already installed, settings-pinned
admission-only** `scope_drain.issue(frame, scope_sha256)`. Its verified kernel
bootstrap fixes the direct `-I scope_drain.py` import-path failure without GPU
initialization. The control still verifies live authority and owns its lock.
Existing bodies finish, the publisher drains, and the owner seals/releases the
frame. Only then may the ordinary coordinator dispatch its closed native index
under fresh provider, receipt, expiry, RAM and byte admission guards.

`native-producer-drain-intent.json` is durable before requesting the local
control. `native-producer-drain-proof.json` records its result and is reusable
without a second request. An intent without a final proof stops rather than
replaying an uncertain action. No global STOP, kill, lease mutation, receipt
append, network retry or native launch is performed by this monitor.

Focused fixture checks, including a real Windows held-reader replacement:

```powershell
python -B -m unittest pipeline.tests.test_progress_observer `
  pipeline.tests.test_native_producer_drain pipeline.tests.test_native_handoff_queue
python -B -m pipeline.native_producer_drain --help
```

## Fresh receipt check in the normal download driver

`drive_ingest.run` now creates an `ExactOwnerReceiptGate` inside its existing
collector ownership. Immediately after a worker's rate-limit wait, and before
its new metadata extraction, the worker checks the exact video/creator/tab
against stable native, qualified and independent publisher audio journals.
Parsed unchanged journals are cached. Changed journals stream one complete
JSONL line at a time while hashing, without a collection-size or line-size
ceiling. The owner's journal mutex protects brief snapshot/cache decisions;
changed-file indexing and strict validation run outside that mutex, then
revalidate their file identities. The same authoritative receipt readers accept
only selected complete rows supplied through streaming byte offsets, including
any required shared publisher anchor. A proven positive depends only on its
audio journal; an unrelated sibling append cannot invalidate it. A complete external append race gets at most
three local resamples. Malformed/unreadable snapshots hold.

A verified edition returns only that item's `already_covered` result, without
forging a native receipt or stopping siblings. Text companions do not satisfy
the gate. Legacy blank native tabs require the original selected row's exact
recording destination; conflicting tabs are rejected. Native `verified` rows
remain nonterminal and follow existing verify/delete recovery. Live source,
host capacity, provider, body and publication guards stay
in the normal driver. The gate itself performs no network calls. The ordinary
entry point and its existing bounded source/publication settings remain usable:

The independent download-only local pilot keeps its legacy local recovery path;
the Drive-edition gate is created for the normal archiving owner.

```powershell
python -B -m pipeline.drive_ingest run --root C:/private `
  --queue C:/private/jobs/queue.csv --remote 'archive:Audio' --limit 96 `
  --workers 6 --upload-transfers 3 --max-local-gb 23 --min-free-gb 12
python -B -m unittest pipeline.tests.test_receipt_admission `
  pipeline.tests.test_drive_ingest_parallel_review
```
