# r3-P28: one annotation protocol and a priced funding ladder

Third-round panel programme, step 1 (class a.1: writing; **it funds nothing**). Written 2026-11-26 (UTC times from
`date -u` in status.json) by a step-1 agent (a model agent working for the project lead; not a person). No model call,
no network call, nothing sent or reserved. Prices come from the stored price table (`llm/openai_client.py`, parsed as
text, never imported or run) and the spend ledger (`llm/spend.jsonl`, amounts only). The key file was not opened.

**Status.** Exploratory; not a test of H1-H10. A price is an estimate, not a plan to spend. Every label the arms would
make would be model-coded and not checked by a person, except the person check's; agreement is never accuracy.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## Prespecification

`prespec.md` (SHA-256 `cd8d4ffd4a8dfd54800b5c82bd39effa3636a652dece4ae18a31d0e39cfb8c75`) was hashed at
**2026-11-26T06:46:19Z**, before any price of this entry was computed; `p28_run.py` refuses to run if it changed. Known
leak: at 06:44:35Z the writer printed a summary of the ledger's measured spend by instrument (amounts only) to choose the
anchors. Deposit 2: kind "act", no margin, no reading; account cells: r3-P28 is left out as a text entry.

## Budget state (`r3-P28-budget.csv`)

Hard stop 130 USD (`RUNAWAY_CEILING`), owner's warning 120 USD (`TOTAL_CAP`). The ledger's sum (measured costs,
allowances for answers possibly billed but lost, and reservations still held) is **126.70 USD**, so the **headroom
under the hard stop is 3.30 USD**; the warning level is already passed. Channeler discovery stays closed (its tag cap of
34.32 refuses any further call). Any cost above 2 USD is reported to the lead before it is sent. Batch prices are half
the standard prices for every model in the table; the registry records that the small model's batch queue returned
nothing for hours on 21 November, so the standard interface (twice the price) is the realistic fallback.

## The ladder (`r3-P28-funding-ladder.csv`, `fig-r3-P28-funding-ladder`)

Every unfunded arm of programme section 2.3 in the panel's spending order, then the exploratory round's not-run rows
that need model calls (HR, TL-SPEC, TL-7.3, VER-ADJ-G, NE-F, CSS-11, VER-NEXT). Each row carries the members' estimate,
what it buys, a ledger anchor (the measured seen-creator job it would re-run, priced per unit), the size basis where a
stored count applies, the ledger range (low: batch price; high: standard price x 1.25) and flags.

**What the ledger adds to the members' estimates:**

| Arm | Members' estimate | Ledger range (USD) | Basis |
|---|---|---|---|
| Punctuation-free relabel (r3-P03) | 1 to 5 | 1.41 to 3.53 | the small model's voice label and map re-run on all 1,293 seen English recordings at the measured rate |
| Masked-ask relabel (r3-P03) | 3 to 8 | at most 1.41 to 3.53 | the same re-run on all recordings (an upper bound: only recordings with asks need it) |
| Shifted-grid relabel (r4-P02) | 1 to 5 | 0.04 to 0.11 | BR-GS's 40 shifted-grid recordings, small model; the members' estimate is far above what the stored base needs (a middle-model reading or the whole roster after a GPU re-decode would cost more) |
| TL-SPEC (not run) | none | 12.2 to 30.6 | about 2,439 dated statements (27% of 9,033 coded), the large model's checkability rate, card plus second reading plus a repeat on a fifth |
| VER-ADJ-G (not run) | none | 2.37 to 5.93 | about 1,000 gate units (assumed: four instruments at about 250), the guided third reader's rate |
| Arm A, name-swap arm | 2 to 5; 2 to 4 | per constructed item 0.0011 (batch) | size not fixed (templates not written); the known-answer battery's voice rate |
| Precision reads (r3-P56, r3-P41/43/60) | under 1; 0.5 to 3 | per hit read 0.0010 (batch) | size not fixed (lists not written) |
| NE-F (not run) | none | per window 0.0019 (batch) | size not fixed (the full pass's windows are not stored) |

**Ledger anchors** (`r3-P28-ledger-anchors.csv`, measured, seen creators): the small model's voice label 0.00066 USD per
request and map 0.00083 (standard); the middle model's voice label 0.0050 per request (standard equivalent); asks find
0.00031, middle-model asks check 0.0031; the known-answer voice arms 0.0023; the large model's checkability reading
0.0046; the guided third reader 0.0047; a precision read 0.0021; the named-source pilot 0.0038 per window; sentence codes
0.00005.

**In words.** Under the 3.30 USD left below the hard stop, only arms whose whole range is small fit: the precision reads,
quotation faithfulness, the tie check, scope and recall reads at their low ends, and the shifted-grid relabel of BR-GS's
40 recordings (a few cents at the measured rate). The panel's first rung (arm A with the stripped relabel and a precision
read, about 3 to 10 USD) does not fit whole; every arm above 2 USD would be reported first. Arm A is the only test of
whether LAB-A's pattern is labelling error (D1), and it needs the scoring question decided first (the lead's step-1
decision 16). The person check (r3-P25, about 750 to 1,200 USD minimal) is the only arm that buys an accuracy word, at
hundreds of times the headroom. HR and VER-NEXT would read hold-out material: a hold-out contact, which the programme sets
aside (r3-P73).

**What each kind of arm buys** (the ladder's last column): accuracy (people only: r3-P25, r3-P18, listening checks);
counterfactual sensitivity (arm A, the name swap, the stripped, masked and shifted-grid relabels); precision or recall of
a cue list or filter (precision and recall reads); new fields (stance, scope, clusivity, modes, endorsement, event types,
qualifiers, frames, device codes, ties, TL-SPEC, TL-7.3, NE-F, CSS-11); comparability over time (anchor re-reads, drift
and transport, VER-NEXT); outcome resolution (the resolver gate, ledger resolution; the owner's act); wave and comparison
labels (section 2.2's registrations). r3-P33's informativeness table says which published rows each would move: the
relabels move the cascade's register and instrument rows; arm A moves H6's asks envelope; only r3-P25 can replace
"agreement" by "accuracy".

## One annotation protocol (for any new field, if money ever appears)

Built from the round-3 proposal and what the ledger and registry record about the first round.

1. **Freeze before reading.** Prompt, schema, model, effort, interface and the reading rule are hashed and logged before
   any production call; any revision is the one the plan allows, made on the gate sample, never on production.
2. **Rule prefilter with logged inclusion.** A hashed rule (pattern list) selects candidate units; every unit's inclusion
   probability is logged, so that recall can be bounded (as nlp-R13 did, with its caveat that two captures of one model
   overstate recall).
3. **Small model as finder** with an exact quotation from the unit and a "cannot tell" option; quotations are checked
   against the text by code.
4. **Middle model as record** on a stratified sample at least, and on every unit where money allows; a large model only
   to adjudicate disagreements, never as the record by default.
5. **Three runs on a fifth** of units for stability; a gate split drawn by rule (seeded, deposited) before any revision;
   gates and production through the same interface and settings.
6. **Ledger discipline.** Every request reserved at worst case under the hard stop; batch first for production, with a
   rule fixed in advance for when to cancel and move to standard (the registry's 30-minute rule); request bodies,
   parameters and returned identifiers logged and hashed; lost answers kept as allowances until reconciled.
7. **Two-model envelopes** printed beside every estimate as lower bounds on label uncertainty (shared errors of one vendor,
   VER-DEP, are not inside them); a reader of another vendor where the field carries a headline.
8. **Hold-out rule.** No call reads hold-out or other-group material unless the owner opens it; seen creators first.
9. **Caption on every output:** "model-coded, compared between models, not checked by a person"; "agreement, never
   accuracy"; the agnosticism sentence.
10. **Report before sending** any cost above 2 USD, with the ladder's row and what it buys.

## Departures and choices (stated)

1. **Sizes assumed where none is stored:** TL-SPEC's dated statements (27% of 9,033, from published shares) and
   VER-ADJ-G's gate units (about 1,000) are this agent's estimates; the high end's 1.25 buffer is a choice.
2. **Anchors** are the closest measured seen-creator jobs; for arms whose instrument does not exist yet (stance, scope,
   modes, CSS-11) no anchor is printed.
3. **Human-coder arms** are not priced from the ledger; members' USD are shown where given, hours otherwise.
4. **HR's estimate** comes from the registry (part a 3.5 USD) and the r2-HR tag cap (8.5 USD for all parts).

## Bases or fields not stored

The ledger holds no per-arm token counts for arms not yet designed; the members' token counts the round-3 proposal
mentions are not stored (the programme prints USD ranges only). No price is stored for a person's hour other than the
members' USD ranges.

## Contacts

None (see `contacts.md`).

## For the lead

1. Whether to keep the panel's first rung as written, given 3.30 USD of headroom: the stripped relabel alone (1.41 to
   3.53) may exceed it at standard prices; arm A cannot be priced until its templates and the scoring rule exist.
2. The shifted-grid relabel of BR-GS's 40 recordings costs cents at the measured rate (members' estimate 1 to 5 USD); it
   is the cheapest arm that removes one named dependence (grid marks in the labels, r3-P02).
3. Every arm above 2 USD in the ladder needs the lead's report-first step; none is requested here.

## Files

SHA-256 of every file: `status.json`. Public data CSVs carry a commented header; PNG at 200 dpi without text chunks;
PDF without document information.

| File | What |
|---|---|
| `prespec.md` | the pricing rule (hashed before any price) |
| `public/r3-P28-funding-ladder.csv` | every arm: members' estimate, what it buys, ledger anchor and range, flags (figure data) |
| `public/r3-P28-ledger-anchors.csv` | the measured anchors (amounts only) |
| `public/r3-P28-budget.csv` | hard stop, warning, ledger sum, headroom, closed discovery cap, reporting line |
| `public/fig-r3-P28-funding-ladder.png/.pdf` | the funding ladder on a log-cost axis |
| `code/p28_run.py` | the ladder (amounts only; the price table parsed as text) |
| `code/style.py` | the CHANGE group's style, copied unchanged |
| `code/zsolve.py`, `qscan_all2.py`, `quant.py`, `quant2.py` | the release's privacy scans, pointed at this folder |

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

Note (the lead's step-1 decision 49(h), 2026-11-26T09:22:54Z): the SHA-256 values printed here are those of the private files as written; the SHA-256 of each published file is in status.json, `published_copy.published_sha256`.
