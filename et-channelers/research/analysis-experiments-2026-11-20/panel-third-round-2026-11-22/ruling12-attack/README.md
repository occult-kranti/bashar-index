# ruling12-attack: the second novelty-attack pass (lead's ruling 12)

> **Published copy (paper update, phase 2; the lead's decision 102; 2026-11-26).** This README and
> `bibliography-check.md` are published as redacted copies: private paths and the names of private working files
> are replaced by neutral descriptions, and nothing else is changed apart from this note. `bibliography-check.md`
> (phase 1) and `bibliography-check-phase2.md` were written later by the paper-update agents, after this README;
> `hash-record.md` keeps the attacker's hashes and adds the SHA-256 of every published file.
>
> **Correction (2026-11-26, the lead's decision 116, after the paper's independent check).** The closest works that
> round 4 named for each wording are listed in `programme.md` section 3.1, which is hashed with deposit 2; deposit 2's
> `novelty-ledger.md` holds one sentence per cluster with its verdicts and no closest-work list. Where a file of this
> folder says that the round-4 closest works are in the deposited novelty ledger (`bibliography-check.md`, "Outcome by
> wording"; `bibliography-check-phase2.md`), read `programme.md` section 3.1. Those files are otherwise unchanged by
> this note; N24's hold (decision 116) is recorded in both.

Written 2026-11-26 at 15:38 UTC (times from `date -u`) by the ruling-12 methods attacker, a model agent working for
the project lead. No person checked it. The work is exploratory: it is a novelty attack on design and method claims,
not a result, and not a test of H1 to H10.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## What this is

Ruling 12 of `lead-rulings-2026-11-26.md` grants "a second attack pass": one methods attacker re-reads the 28 novelty
claims that had a single verdict (den-soc's) and den-soc's own four (no attacker but their author), "starting with
llm-n2 and den-mat-n4". No novelty sentence prints before it. This folder holds that pass.

- **Result.** 32 claims attacked. 0 refuted, 11 narrowed, 21 survive. Final wordings are given for 28 wordings: 26
  deposited clusters, N20's count, and P32's first wording.
- **Searches.** 218 counted searches out of 265 logged, on 12 engines, run from 14:58 to 15:31 UTC. Every claim has
  at least 5 counted searches on at least 4 engines.

## Files

| File | What it holds |
|---|---|
| `attack-ledger.csv` | One row per claim and query. Columns: `claim`, `cluster`, `query_no`, `query`, `engine`, `date_utc`, `n_returned`, `counted`, `searcher`, `top_hits_examined`. The hits are written "author year \| title \| venue \| link", separated by " \|\| ". |
| `verdicts.md` | The class rule and the counting rule; the counts; one section per claim with verdict, evidence (full reference, URL or DOI, reading depth, the matching sentence) and final wording; the narrowing sources and who opened them; leads not opened; what the lead must decide. |
| `README.md` | This file. |
| `hash-record.md` | SHA-256 of the three files above, with the `date -u` time. |

In the `counted` column:
- **yes** means the search returned hits that were examined.
- **no** means the call was refused (Firecrawl web search for lack of credits; Google Books and Semantic Scholar with
  HTTP 429), returned nothing (arXiv after about 15:08 UTC), or matched another sense of a word (telecom "channel",
  "Possession Island"). These rows are kept so the search effort is complete.

In the `searcher` column:
- **lead-attacker** means the attacker ran the search directly: llm-n2, den-mat-n4 and the lead half of den-soc-n3.
- **A to D** are four search helpers. They are model agents that the attacker started under one written brief, with
  the same tools, rules and counting rule. Their groups were:
  - A: speech recognition and model-annotation claims;
  - B: linguistics and speech science of mediumship;
  - C: forecasting, prophecy and registries;
  - D: conspirituality, commerce and platforms.

The verdicts are the attacker's. Every source that narrows a claim was re-opened by the attacker, except one passage,
which is marked in `verdicts.md` section 4.

## Inputs read

- **Public, on origin/main** after `git fetch`, under
  `et-channelers/research/analysis-experiments-2026-11-20/panel-third-round-2026-11-22/`:
  - `programme.md`, sections 1.5, 2.5, 2.6 and 3 (3.1 to 3.3);
  - `lead-rulings-2026-11-26.md`;
  - `deposits/deposit-2/novelty-ledger.md`, which is the r4-P33 novelty ledger.
- **Private (the panel's working files, not published).** The pooled round-4 claims file: the novelty claims N01 to
  N31 and P32 with their search counts and verdicts. Also the novelty-claim sections and search logs of the round-4 memos of speech,
  den-meth, llm, den-mat, occult, et, emic and den-soc. These were read as design text only. The round-3 files
  were not needed beyond the claims already pooled in round 4. No corpus data was opened.

## How the pass was run

- **Rules.**
  - The deposited novelty rule was followed: no "first", "novel" or "unique"; every wording ends "Not found means only
    that."; "the method is theirs; only the target is this corpus's" where the method exists; a claim is never
    reworded upward.
  - The deposited counting rule was followed: this pass's counted searches are added to the attacker count, written
    "Y + k = Z". Member counts are unchanged.
- **Order of attack**, as deposited: done before, then trivial, then whether these data can show it, otherwise it
  survives.
- **Verdict classes** (`verdicts.md` section 1):
  - refuted: the full design was done before;
  - narrowed: a part the deposited wording claimed as new was done before;
  - survives: only parts already conceded were found.
- **Engines.**
  - Firecrawl paper search, WebSearch, Consensus, Crossref, OpenAlex, the arXiv API, Europe PMC and PubMed.
  - Semantic Scholar (mostly refused) and the Internet Archive / Open Library full-text index, which stood in for
    Google Books because Google Books refused every call.
  - Pages were opened with WebFetch and with Firecrawl's paper reader.
- **Not reached.**
  - Firecrawl web search (out of credits for the whole session) and Google Books.
  - The arXiv API after about 15:08 UTC.
  - Paywalled indexes: ATLA, PsycINFO, MLA, Scopus and Web of Science.
  - Non-English religious-studies indexes, except three Portuguese and two German queries.

  A "not found" is weakest for the humanities and monograph claims.
- **Verification fetches.** Opening a page to check a source is a read, not a search. These fetches are not ledger
  rows; what they found is quoted in `verdicts.md`.

## Run rules kept

- **Python.** Every Python process ran as `analysis-venv\Scripts\python.exe -I` (the guarded venv), one small process
  at a time per searcher.
- **Model calls.** There were no OpenAI calls and no project model calls. The only external calls were literature
  search and page fetches. The OpenAI ledger is untouched.
- **Data and names.** No corpus data was read. No creator, channel or video name appears in these files. One book
  hit by a practising channeller was replaced in the ledger by "[a channelled-source book: author and title withheld
  under the naming rule]". The helpers also withheld two titles carrying personal names and one press item naming a
  creator. One web essay cited for N15 names a medium; it is cited by its author and title only.
- **Git.** No commit, branch or push. The only git commands were `git fetch` and `git ls-tree` / `git show` on
  origin/main, which the brief's read step asked for.
- **Cost.** No OpenAI cost. Firecrawl paper-search requests used the connected Firecrawl account (its web search was
  refused for lack of credits). 19 OpenAlex queries used the shared free daily budget. Nothing approaches the 2 USD
  reporting line.

## Scratch material (not deposited)

The helpers' raw ledgers and verdict JSON, the search scripts (`litsearch.py`, `logrow.py`, `merge.py`) and the
extracted claim texts are in a session scratch folder on the machine that ran the pass (not published).
That folder can be cleared on reboot. Everything needed to audit the pass is in `attack-ledger.csv` and `verdicts.md`.

## What waits on the lead

See `verdicts.md` section 6. In short:
1. Accept or relabel the verdicts.
2. Narrow the registry's N3 addendum: "the timing of the freeze" alone is no longer new.
3. Add the audiobook literature on narrator against character voices to `related.tex`.
4. Settle N17's count discrepancy.
5. Record the preconditions from the attacks in the prespecs.
6. Run ruling 13's bibliography check on every newly named work before any novelty sentence prints.
