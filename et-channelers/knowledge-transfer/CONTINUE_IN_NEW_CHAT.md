# Continue in a new chat

Brought to 27 November 2026, 19:13 UTC (from `date -u`), from the files on `main` up to
[PR #137](https://github.com/occult-kranti/bashar-index/pull/137). Copy the prompt below into a new chat that has
repository access. It names only public files. The private run state is in the owner's private archive, outside Git.
The prompt of 20 and 21 November is superseded; it stays in this file's git history.
Do not paste the earlier prompt.
[Handoff](../HANDOFF.md#current-state-27-november-2026) · [Research status](../research/analysis-experiments-2026-11-20/README.md) ·
[Findings dashboard](https://occult-kranti.github.io/bashar-index/et-channelers/dashboard/findings/)

```text
Continue the ET Channelers project as research lead. Repository: https://github.com/occult-kranti/bashar-index. Work reaches main only by pull request from a fresh branch in its own worktree. Compare every checkout with its remote first, and preserve other worktrees and live jobs.

Where the work stands on 27 November 2026. The cohort is the newest 20 public completed uploads on each creator's Videos tab, frozen at 1,976 recordings on 101 channels. 1,946 are archived. The 30 others are final failures: do not retry them. 1,697 audio files are transcribed. The registered first round ran on 21 November and gave no determinable verdict. Everything after it is exploratory; not a test of H1-H10. Every label is model-coded and not checked by a person. Every comparison between labels, models, instruments or agents is agreement, never accuracy. Every result carries this sentence: "No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these recordings and how the creators present it."

Published on main:
- the exploratory release (PR #110);
- the third-round panel's programme, its steps 0 to 5 and its audio entries (PRs #107 to #123);
- the new-files round, a descriptive persistence check on new recordings of the seen creators (PR #124);
- the fourth panel's programme (PR #127), with deposit 5a (PR #129), deposit 5 (PR #133) and addendum 1, its step 0 (PR #135), all before any count;
- the working paper's Appendices C.6 to C.8 (PRs #123, #126 and #132);
- the dashboards, up to addendum 1 (PR #136), and the channel index's list of ET civilizations (PR #137).
New recordings outside the frozen corpus are descriptive material only. 102 new uploads are archived. The latest-50+ download has finished. Its transcription was stopped by the owner and stays stopped.

Under way: the fourth panel's step 1 (label-free list counts on the 48 development creators) and the GPU re-decode. Next, in order:
1. step 1's publication;
2. step 2, the by-voice rows that pass the decision 129.6 guard;
3. r3-P30 version 2's calibration battery;
4. the end of the GPU re-decode;
5. step 3, then step 4 (the acoustic readings, one heavy job at a time);
6. the dashboards after each publication, and the paper's next appendix;
7. f4-Q19's forecast windows, which mature in January 2027.

Read first, in this order:
1. README.md, section "Where things stand (27 November 2026)".
2. et-channelers/HANDOFF.md, section "Current state, 27 November 2026".
3. et-channelers/research/analysis-experiments-2026-11-20/README.md, "Status, 27 November 2026".
4. The same folder's registry.md: the last rows of "Decisions taken by the lead under the owner's delegation", and "Deviations from the frozen registry".
5. The same folder's panel-fourth-round-2026-11-27/: programme.md (sections 0 and 4), lead-decisions.md (decisions 125 to 155), deposits/deposit-5a/, deposits/deposit-5/ (registration.md, section 3.3, the order of runs) and deposits/deposit-5/addendum-1/.
6. et-channelers/dashboard/findings/README.md, and the findings dashboard's run-status table.
7. et-channelers/paper/measurement-protocol-2026-11-21/README.md, its latest sections.

Rules that bind:
- Every registration is hashed and merged before any count. Each entry's prespecification is hashed before its outputs are read. No registered rule is loosened after its result.
- Class-a and a.2 entries make no model call. The owner's hard stop for model calls is 130 USD.
- Run Python in the guarded analysis environment with isolated Python (-I). Use one worker per heavy job and at most two heavy jobs at a time; the GPU re-decode counts as one while it runs.
- Public files hold no transcript text, creator code, video id, title or quotation, and no cell of fewer than 5 creators. Research documents name no creator, channeller or being. Two printed counts of nested creator groups never differ by 1 to 4.
- Take every time from date -u.
- Tier 2 listening stays closed, and the paper is not submitted, until an ethics or exemption determination exists.
- Do not restart jobs or scheduled tasks that the owner stopped, and do not stop processes you did not start.

The private run state is in the owner's private archive, outside Git: run ledgers, spend records, transcripts, the private copies of deposits and term lists, and the lead's handoff notes. Ask the owner for access, read the lead's handoff notes there first, and compare them with main before acting. Nothing from the private archive enters the public repository.
```

## First checks

Run these commands from the repository checkout to see where `main` and the local worktrees stand. They change no
working file; `git fetch` only updates the remote-tracking refs.

```powershell
git fetch origin
git status --short --branch
git log --oneline -12 origin/main
git worktree list
```

[Knowledge-transfer index](README.md) · [Analysis handoff of 20 November (history)](analysis-handoff-2026-11-20.md) ·
[All dashboards](https://occult-kranti.github.io/bashar-index/dashboards/) · [Collection close](evidence/2026-11-20-close/)
