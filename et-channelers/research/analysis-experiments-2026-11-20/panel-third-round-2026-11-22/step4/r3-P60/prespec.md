# r3-P60: where audiences are sent off the platform, and suppression talk (prespecification)

Written 2026-11-26 (UTC, from `date -u`; the hash time is in `prespec-hash-record.md`) by the step-4 agent, a model agent
working for the project lead (not a person), before any count of this entry beyond r3-P42's public files was made.
Shared rules: `../common/prespec-shared.md`.

Exploratory; class a.2 (ruling 11), **tier L**: run once on the 23 non-development seen creators, with no split. Links
are read as settings: "a link is a link, not a verdict" (never allegiance, never routing). Cue counts: sense not resolved,
precision unknown. Precision reads are class c.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## 1. Inputs

- Deposit 3's L13 (binding file `addendum-2b/lists/r3-P60-destinations-suppression-a2b.csv`): destination classes by link
  domain (G1c host rule) with the writer's funnel depth (1 follow elsewhere, 2 contact capture, 3 payment, 4 one-to-one
  service or paid teaching; 0 platform self-links; undetermined for own-site and shorteners), the messaging-app broadcast
  class (DEST-MSG), and suppression talk split into platform moderation talk (SUPP-PLATFORM) and hidden-actor
  suppression talk (SUPP-HIDDEN); "censored" flagged, never counted.
- r3-P42's private counts (`p42-counts.private.pkl`, made by the shared matcher `step2/common/lexmatch.py`): the page
  links per creator by class, term and depth (links in the descriptions of the 23 creators' seen recordings), and the
  speech counts of L13's terms by form. Used as they are; the class shares are recomputed and must equal r3-P42's printed
  shares (a difference stops the run).

## 2. Rows

- **Destinations by class (programme: shares of creators by destination class).** For each class: the creators of the 23
  with one or more links of the class on their pages (count form by `Counts`; the share of the 23 printed only where the
  count is exact) and the creator-balanced share of links (r3-P42's statistic). A class whose count is under 5: "fewer
  than 5 creators". No reading (a description of settings).
- **Funnel depth (programme: shares of creators by funnel depth).** The creators whose pages carry a link at depth 3 or 4
  (payment, or one-to-one service or paid teaching), and at depth 4, in the forms `Counts` gives; the creator-balanced
  share of links at each depth (r3-P42's); r3-P42's unresolved-link rule (DEST-UNRESOLVED above 0.20 makes depth
  "undetermined (unresolved links)").
- **Suppression talk, split.** SUPP-PLATFORM and SUPP-HIDDEN each by the thin rule (addendum 2d: 3 or more expanded forms
  used by 5 or more of the 23 creators), recomputed from r3-P42's form counts and checked against r3-P42's statuses. A
  thin half prints "not computed (too few terms or creators)". The halves are never pooled (the programme splits them).
- **The paired-difference dot plot** (programme): within creator, recordings with platform-suppression talk against
  recordings without, for spoken off-platform asks, written other-platform links and explicit control vocabulary, with
  platform-engagement asks as the contrast and circular-shift permutation bands. It rests on SUPP-PLATFORM: if that half
  is thin, every row prints "not computed (too few terms or creators)".
- **Alternative video platforms against control vocabulary** (round 3's between-creator question): computed only if 5 or
  more creators link to DEST-ALTVID and 5 or more do not; otherwise "not computed (too few terms or creators)".

## 3. Plot

Creators by destination class (a point where the count is exact, the band's range where it is banded), beside the
creator-balanced share of links by funnel depth; the suppression halves' statuses as text. No per-creator point.

## 4. Consistency

The recomputed link shares equal r3-P42's printed shares (data-r3-P42-lists.csv); the suppression statuses equal
r3-P42's; CSS-10 and PT's link classes are a different instrument (PT's fixed lookup) and are not reconciled.
