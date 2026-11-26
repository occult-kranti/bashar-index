# Bibliography check, phase 2: the round-4 works behind four held novelty wordings (ruling 13; decisions 96.2 and 102)

Written 2026-11-26 at 18:18 UTC (times from `date -u`) by the paper-update agent of phase 2 (a model agent working for
the project lead; not a person). No person checked it. It checks citations, not novelty, and says nothing about the
corpus.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## What was checked, and why

- **Scope.** The lead's decision 102 held four printed novelty wordings until the round-4 works they rest on pass the
  same check as `bibliography-check.md` (this folder): N04 (Carpenter et al. 2023), N20 (Armstrong and Sotala 2012),
  N24 (Melton 1985) and N21 (the grey-literature audit of published psychic predictions). r3-P35's check of the
  attackers' and members' prior work had left these four unresolved. Each is named in the closest-work column of
  `programme.md` section 3.1 (deposit 2's novelty ledger); what each is claimed to show is taken from that column and
  from the round-4 memo that named it.
- **Questions.** As in `bibliography-check.md`: does the work exist; is it findable (a DOI, stable URL or catalogue
  record that was opened); does what was read say what the wording's closest-work entry claims. Reading depth is
  stated per work.
- **Who and when.** The paper-update agent alone, from 18:08 to 18:15 UTC on 2026-11-26.
- **Engines.** WebSearch and WebFetch; the Crossref and OpenAlex APIs; Consensus; the Internet Archive's Wayback
  Machine for two pages whose live sites refused or failed on the day (HTTP 403 and HTTP 500). Firecrawl was out of
  credits. No model call other than literature search and page fetches; no OpenAI call; no money spent; no corpus data
  read; no creator, title or corpus text in any query. Python ran only in the guarded venv.
- **Rule** (`bibliography-check.md`, "Rule for the paper"): PASS (full text or passages read) and PASS-ABSTRACT (the
  abstract or record supports the claim; full text not read) pass. A discrepancy in an author count or a year within
  one passes with a correction. A wording prints only if every work it rests on passes; the paper rewords nothing.

## Counts

| Status | Works |
|---|---|
| PASS | 3 |
| PASS-ABSTRACT (with an author correction) | 1 |
| Fail | 0 |
| **All** | **4** |

## Outcome by wording

- **Released (every round-4 work it rests on passed):** N04, N20, N21 and N24. They stay printed among the novelty wordings of
  Appendix C of the working paper in the form phase 1 printed; the round-4 works are not cited there (the closest works named in round 4
  stay in the deposited novelty ledger), so no wording changes.
- **Still held:** none of these four. N23 also names Melton 1985, which passes here, but N23 stays held because a
  work newly named in its final wording failed (`bibliography-check.md`, Jalolova 2025).
- **Correction (2026-11-26, the lead's decision 116, after the paper's independent check).** N24's round-4 work
  passes here, but N24 is held all the same: its final wording also names two works the second pass added that
  neither check covered, one of them an unnamed collection of press reports, which fails by the check's rule
  (`bibliography-check.md`, the correction under "Outcome by wording"). N04, N20 and N21 stay printed. Nothing else
  in this file changed.

## Corrections

- **Carpenter et al. 2023** has two authors: Carpenter and Pines 2023 (a book chapter). Identified by replaying the
  attacker's logged Consensus query for this claim (round 4, attack-den-meth, row 32), which returns it beside Lynöe and
  Eriksson 2023; the Crossref and OpenAlex records give two authors.
- **Melton 1985**: the journal's page prints DOI 10.1353/amsj.v26i2.2545, which Crossref does not resolve (HTTP 404 on
  2026-11-26); cite it by journal, volume, issue and pages, with the journal's stable URL.
- **Armstrong and Sotala 2012**: the proceedings have no Crossref record; the authors' own copy (MIRI) is the findable
  source, and it carries the note "The findings in this paper are based on a dataset error", which refers to its
  expert-against-non-expert comparison (AI Impacts, "Error in Armstrong and Sotala 2012", 2016, read: the column read as
  expertise recorded the method of prediction; the authors agree). The constant-horizon test that N20's closest-work
  entry names is not reported as affected.

## Every work

| Wording | Work (as named in the round-4 list) | Status | For the paper | Checked (UTC) | DOI or URL | Read | Note |
|---|---|---|---|---|---|---|---|
| N04 | Carpenter et al. 2023 (incorporation bias: "the index test forms part of the reference standard, so agreement is built in"; round 4, attack-den-meth) | PASS-ABSTRACT | passes, with the author correction (Carpenter and Pines 2023) | 2026-11-26T18:10:02Z | doi:10.1002/9781119616870.ch6 | abstract | Christopher R. Carpenter and Jesse M. Pines, "Understanding Bias in Diagnostic Research", in Evidence-Based Emergency Care: Diagnostic Testing and Clinical Decision Rules (Wiley, 2023), pp. 73-92 (Crossref; OpenAlex W4360976901, book chapter). The abstract (OpenAlex inverted index; the same text in the Consensus record) says: "Incorporation bias is likely when the index test is one determinant of the criterion standard." That is the claim. The publisher's page refused (HTTP 403), so the chapter's text was not read. |
| N20 | Armstrong and Sotala 2012 (a constant horizon across many forecasters: predictions of human-level machine intelligence tested against "always 15 to 25 years away"; round 4, attack-den-meth and attack-stat) | PASS | passes | 2026-11-26T18:13:10Z | https://intelligence.org/files/PredictingAI.pdf | passages | Stuart Armstrong and Kaj Sotala, "How We're Predicting AI—or Failing To", in Beyond AI: Artificial Dreams, ed. Jan Romportl, Pavel Ircing, Eva Zackova, Michal Polak and Radek Schuster, 52-75, Pilsen: University of West Bohemia, 2012 (citation as printed on the copy's first page; "This version contains minor changes"). Read: abstract and pp. 1-2. Abstract: "Using a database of 95 AI timeline predictions ... Predictions that AI lie 15 to 25 years in the future are the most common, from experts and non-experts alike." P. 2: "we further test two folk theorems: firstly that predictors always predict the arrival of AI just before their own deaths, and secondly that AI is always 15 to 25 years into the future. We find evidence for the second thesis but not for the first." The 2015 chapter (refs-new.bib `armstrong2015how`) was already verified. Caveat in Corrections above. |
| N24 | Melton 1985 (the spiritualization thesis, argued from cases: groups rarely experience a prophecy as failed and reinterpret it spiritually; round 4, the occult and emic memos) | PASS | passes | 2026-11-26T18:13:40Z | https://journals.ku.edu/amsj/article/view/2545 (read through http://web.archive.org/web/20250328010053/https://journals.ku.edu/amsj/article/view/2545 and the archived PDF of 2024-08-18) | passages | J. Gordon Melton, Jr., "Spiritualization and reaffirmation: what really happens when prophecy fails", American Studies 26(2), Fall 1985, 17-29 (page metadata; OpenAlex W1577128645, vol. 26, issue 2, pp. 17-29). The live journal site returned HTTP 500 on 2026-11-26, so the Internet Archive's copies were read (pp. 17-21). P. 18: the article "derives from the examination of reports of numerous examples in the life of American religious groups"; p. 20: "within religious groups, prophecy seldom fails"; p. 21: "the ultimate and more permanent reconceptualization is most frequently accomplished through a process of 'spiritualization.'" and "The event occurred as predicted, only on a spiritual level." That is the claim. |
| N21 | The grey-literature audit: "a retrospective, person-checked audit of published psychic predictions with a 'too vague' class" (the Great Australian Psychic Prediction Project, Australian Skeptics; round 4, the den-meth, den-mat and den-soc memos) | PASS | passes (grey literature) | 2026-11-26T18:14:30Z | https://www.skeptics.com.au/psychic-project-full-results-released/ (read through http://web.archive.org/web/20260120222417/https://www.skeptics.com.au/psychic-project-full-results-released/); https://articles.skeptics.nz/2021/12/15/the-great-australian-psychic-prediction-project | full text (two web pages) | Australian Skeptics, "Psychic project full results released", 9 December 2021 (the live page refused, HTTP 403; the archived copy of 2026-01-20 was read): a 12-year study covering "over 3800 predictions made between 2000 to 2020 by more than 200 Australian psychics", compiled from print, broadcast, web and social-media sources, with results given as correct, expected, too vague, unknown and wrong. NZ Skeptics, "The Great Australian Psychic Prediction Project", 15 December 2021 (read): judged "with careful deliberation by a team of people"; "Each of these predictions was given one of five statuses after researching the claim". Retrospective, person-checked and with a too-vague class: the claim holds. The in-depth report in the project's magazine was not read. |

## Files fetched

Two PDFs were fetched to read pages, each into a scratch folder of its own (not published): the MIRI copy of Armstrong
and Sotala 2012 (SHA-256 prefix `e7c4c4fc4f89f52a`) and the archived journal PDF of Melton 1985 (`c06e4450aba9f90d`).
