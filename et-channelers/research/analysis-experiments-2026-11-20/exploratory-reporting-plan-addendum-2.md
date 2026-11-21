# Exploratory reporting plan, addendum 2

Written by the lead under the owner's delegation, 2026-11-21 13:05 UTC, from the facts the word-error-rate engineer recorded
(`wer-anchor-20261121/addendum-facts.md`, private run folder, about 08:26 UTC) and the verifications of that item. It
belongs to `exploratory-reporting-plan.md` (SHA-256 `061bab3303a03951a57e2f05f58ca3ee86bbdba29db637117831715b6acf3c7c`) and follows addendum 1 (SHA-256
`0a574770ad8a281e56185bb6a528c84111deb45fb46f20475fbd9f7f0f10d0f7`). Like addendum 1, it records outputs as built, added or not run, corrects
factual errors and records departures from section 3 decided after a result; it removes no output and changes no estimand.

## 1. Correction to addendum 1: when the normaliser became version 2

Addendum 1 (timing paragraph and item 10) gives 03:43 UTC. The normaliser became wa-norm-v2 between 03:31:13 and
03:31:26 UTC, after the confusion check of 03:30; the edit at 03:43:42 changed only the trimming rule (`trimmed_span`) and
no part of the normaliser. Version 1 was written at 03:06:05 and gave the first tables at 03:21:30.

## 2. Version 1 was rebuilt exactly and run

Replaying the 03:06:05 write and the later edits in order gives today's normaliser byte for byte, so version 1 is known
exactly (wa-norm-v1, SHA-256 `fa543673e9982337b5a4b8d7a8223b330c05c2a4120b2f0e5fb12d7b738a6492`; wa-norm-v2, SHA-256
`208c78f069de65742775103cbfcaa55f6a1e97e3d07a57d733dd41ee58912655`; both hashed about 06:50 UTC, after the first word error
rates, so plan section 6.7 was not met). Version 1 was run beside version 2 on the same pairs. Its status is "run". Its
public rows give recordings, creators and the share without error but no rates, because beside the version-2 row of the
same variant each version-1 row differs in fewer than 5 creators (rule of item 9 below).

## 3. Public form of the other-text inventory

The 214 recordings with other text are counted in public by three text classes that match the BR-b rows (the project's
earlier speech-to-text; captions; untimed publisher transcripts of undeclared origin), in two groups (seen; not seen).
No single text kind and no group total is printed; the undeclared class reads "fewer than 5 creators" in both groups; the
seen creator count of the first class is not printed. This replaces the earlier four-group layout.

## 4. The precision check of the positional filter

Its public form is the count of removals and the statement "fewer than 5 creators with a recurring removal"; neither a
recurring share nor a precision band is printed, because a band read together with that status bounds a cell of fewer
than 5 creators (lead's decision after the second privacy verification). The detection rate is "not estimable" in public.

## 5. Choices in BR-GS as built

The filter's positional rule is applied on each decode's own grid (a segment is late when (start - 15) mod 30 > 27 on the
shifted grid, start mod 30 > 27 on the run grid); segment rates are per hour of speech of each decode; the definitions of
thanks-phrase and isolated segments, the filter (version 2) and the pause and word measures are those of the GRID item;
SD units are the SD across seen creators of creator means on transcripts of record with 200 words or more. These were
fixed by the engineer while building, after the plan, and are labelled "added after the exploratory reporting plan".

## 6. Intervals

Every interval has its own seeded generator (2,000 resamples), so an added cell leaves the others unchanged. Against the
05:15 tables, no point value changed; interval ends moved by a median of 0.0004 and at most 0.012. None of the 05:15
numbers had been published.

## 7. Merged rows

The row of isolated segments of 1 to 3 words removed by the filter, and the two thanks-phrase sub-rows (in a window's last
3 s; removed by the filter), rest on fewer than 5 creators or give such a cell by difference; under section 3 they are
merged into the rows of all isolated segments and all thanks-phrase segments.

## 8. The required label of version 2

Version 2 is labelled "chosen after the result" in every output and in the paper. The normaliser's own docstring words it
more softly; the docstring is not changed, because its hash is recorded.

## 9. Two rules applied to every public cell of BR-b and BR-GS

- Dominance: a statistic is printed only where 5 or more creators carry a non-zero value; a statistic that is 0 for every
  creator is printed as 0.
- Pairs: of two printed rows whose difference rests on 1 to 4 creators, one is not printed.
Both were decided after results were seen, for privacy only; they hide values and choose none.

## 10. For BR-b-H after freeze 2

A caption counts as made by people when its receipt declares it ("published" for platform tracks and publisher captions),
except a feed caption whose maker the receipt leaves unspecified, which counts as undeclared. References are extracted
(`extract_refs.py`) and classed before any word error rate is computed on them.
