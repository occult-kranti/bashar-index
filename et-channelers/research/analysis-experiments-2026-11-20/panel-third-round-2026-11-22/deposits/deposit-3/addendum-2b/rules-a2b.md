# Addendum 2b: amended matching rules (binding on every step-2 list)

Written 2026-11-26 from 10:38 UTC (from `date -u`) by the step-2 cross-reviewer, a model agent working for the project
lead (not a person). These rules carry the lead's decision 54 (2026-11-26). They amend rules G1 and G5 of
`r3-P41/README.md` and leave every other rule (G2 to G4, G6 to G10) unchanged. The hashed README is not edited. Where
this file and the README differ, this file binds.

**Written from the literature only, blind to the corpus; no count has been made.**

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## G1 Normalisation (amended)

The README's G1 still applies (lower-case; straight apostrophes; hyphens to spaces; punctuation removed except
apostrophes inside words, digits and $ % £ €). Three steps are added, applied in this order **before** G1:

- **G1b (the country, not the pronoun; decision 54 item 1, A2-084).** On the cased text, every token written `US`,
  `U.S.` or `U.S` is removed before lower-casing. The country is never counted as the first-person plural "us". L09's
  exclusion forms "the us" and "u s" stay.
- **G1a (spoken years; decision 54 item 1, A2-088).** Spoken years are written as digits:
  - Forms such as "twenty twelve", "two thousand and twelve" and "nineteen fifty-four" are converted by the function
    `normalise_years` of the ledger's rule coder (deposit 2, SHA-256 `4fe41740...5aef71`). The coder is not changed;
    the function is called, not copied.
  - Spoken years of the 1800s ("eighteen forty-four") are written as 18xx by the same rule, with "eighteen" in place
    of "nineteen".
  - Spaced and word numerals of the dimension scale ("5 d", "five d") are listed as forms of T127 in addendum 2b.
- **G1c (link hosts; decision 54 item 1, with A2-093).** A domain form matches a link whose host equals the form or
  ends with "." followed by the form. A form with a path (for example "whatsapp.com/channel") matches the host and the
  start of the path. A form is never matched as a substring: "t.co" does not match a host that merely contains those
  letters. Links are read from page text only, and no link is followed or resolved.

## G5 Gates (amended)

- **G5 (decision 54 item 8).** No gate word may be a counted form of any other list. The words "uap", "uaps" and
  "aaro" were counted forms of L01 and L07, so they are removed from G-DISC-INST. They stay counted terms.
- **Same-list gate words (open).** Sixteen gate words are counted forms of the gate's own list:
  - in G-SHIP: mothership(s) and mother ship(s);
  - in G-2012: mayan or maya calendar and long count;
  - in G-DISC-INST: governments, pentagon, nasa, declassified, declassify and declassification.

  Read literally, decision 54 item 8 covers them too. They are not changed here, and the lead decides.
- **G5b (decision 54 item 1, A2-085).** Before any gate is evaluated:
  1. Every list is matched.
  2. Every token that lies inside a counted match of another list is masked.
  3. A masked token is not gate evidence.

  So "consciousness" inside an L06 phrase cannot move an L07 "disclosure" hit, and "government" inside an L05 phrase
  cannot either.
- **Gate sets changed** (`register-gates-a2b.csv`):
  - G-DISC-INST loses uap, uaps and aaro.
  - G-DISC-CONSC loses "within", a function word (A2-087).
  - G-DRACO-L01 and G-DRACO-L05 are new, with a window of 15 tokens. They gate the bare forms "draco" and "dracos"
    (T262; "draco malfoy" excluded). None of their words is a counted form of any list; the build checks this.

## Set-aside (decision 51 L1 and decision 54 items 2 and 3)

Every term marked "yes" or "possible" for trope adjacency is set aside from every count of:
- r3-P43 and r3-P44;
- r3-P48 and r3-P49;
- r3-P50 and r4-P18;
- r4-P27;
- r4-P28;
- r4-P29, whose base is formed after the set-aside.

Each list file of addendum 2b marks these terms in column `L1_set_aside`.

A class emptied by the set-aside prints "not computed until r3-P54 (waits for the owner's ethics act)". The emptied
classes are CR-A, r4-P27's decisive pair and et's A-window estimand for r3-P48. No residual is built after the fact.

r3-P38's counts follow the frozen rule coder unchanged. A sensitivity row beside them drops every statement whose
prevention-family match lies on a span matched by a register term marked "yes" or "possible".
