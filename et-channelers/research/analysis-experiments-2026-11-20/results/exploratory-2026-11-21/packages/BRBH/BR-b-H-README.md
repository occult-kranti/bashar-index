# BR-b-H: word error rate on hold-out and other-group recordings (not run)

Exploratory (registry A2); not a test of H1-H10. **Status: not run** (lead's decision D33, 2026-11-22; the plan's BR-b
row: "reported as not run, with the reason"): fewer than 5 creators in each group have a reference that could be made
by people; the recognizer was not run. This covers every hold-out and other-group part of BR-b, its machine-agreement
rows included. BR-b's seen rows stay as built.

BR-b-H eligibility (package BRBH; brbh_eligibility.py, added after the exploratory reporting plan; code written after freeze 2, a deviation from the plan's 'code frozen in the freeze-2 record'). Made after a hold-out contact on 2026-11-22: the upper-bound rule was set after an inline read of the hold-out's and the other group's receipt classes that had no seen run first; that rule can only widen the bound, and the earlier bound gives the same status. Reference classes were read by code from receipt fields only (platform caption track kind; caption kind, maker, origin, label and track-key fields of publisher captions; addendum 2 item 10), with BR-b's classifier unchanged; no reference text, text bundle or audio was opened and no recognizer ran. Verification: on seen creators the same code reproduced BR-b's classes reference by reference, and BR-b's classifier passes its 29 tests on synthetic receipts (test_build_plan.py); not checked by a person. A count of 1 to 4 creators reads 'fewer than 5 creators'; 'under 5 creators (0 to 4)' is a bound that includes 0.

**What BR-b-H is.** Plan section 8 lists BR-b-H as the word error rate on hold-out and other-group recordings with
third-party text; plan section 6.7 makes it the hold-out and other-group part of BR-b. Its human-reference part, the
run's recognizer against reference texts made or edited by people, moved here from BR-b after freeze 2, unchanged in its
rules (addendum 1, item 2). On seen creators that part was not run, because no seen reference is known to be made by
people (BR-b).

**What was done.** Receipt classing 2026-11-22T02:16:21Z; eligibility 2026-11-22T02:19:21Z; this table 2026-11-22T02:43:42Z, rebuilt from the group-level eligibility record with no new read of any receipt. Each
reference of the hold-out's and the other group's recordings was classed by BR-b's own classifier from its receipt fields
only, as addendum 2 item 10 requires: a platform caption track counts as made by people when its kind is "published"; a
publisher or standalone caption when its receipt declares a human maker with no automatic sign and no sign that the maker
is undeclared (in a feed, "published" names no maker); untimed publisher transcripts never count. The same code ran on
the seen creators first and reproduced BR-b's seen classes reference by reference.

**Result.** In the hold-out, references declared made or edited by people cover fewer than 5 creators; in the other
group, none. The status was decided by an upper bound that also counts, as if made by people, every caption whose
receipt leaves its maker to its bundle or text view: in each group that bound is also under 5 creators (a bound of 0 to
4), so no reading of those bundles could bring either part to 5 creators. Both parts are therefore **not run**: no text
bundle, reference text or audio was opened, and the recognizer was not run. So no word error rate against texts made by
people exists for the seen creators, the hold-out or the other group. The upper-bound rule was set after a hold-out
contact on 2026-11-22 (see the label above).

**BR-b's machine-agreement rows on the hold-out and the other group: not run (lead's decision D33).** BR-b's
machine-to-machine rows (platform automatic captions, publisher texts of undeclared origin, the project's earlier
speech-to-text by the same recognizer and by the larger model) are agreement of two machines, not an error rate; BR-b
reported them for seen creators. The lead decided that BR-b-H's status covers every hold-out and other-group part of
BR-b, these rows included. BR-b's machine-agreement rows on these groups were not run because the lead's decision D33 placed them in BR-b-H; the recognizer was not run for any part. These rows need no reference made by people, so the reason above for the human-reference part is not theirs. So no hold-out or other-group value of these rows exists.

**Files.** `BR-b-H-eligibility.csv`: one row per group, with the public form of its creator count only (0, "fewer than 5
creators", or a count of 5 or more); the bound appears in words only.

**Change of 2026-11-22T05:07:43Z (release pass, lead's decision D33).** The status word "not released" (decision D5)
became "not run", with the reason above, and the paragraph that left the scope of the machine-agreement rows open for the
lead now states the lead's decision. No count, row or bound changed; the earlier wording is kept by the package.

**Change of 2026-11-22T05:57:15Z (release fix pass).** One sentence was added to the paragraph on the machine-agreement rows, and to the table's comment row and note cells, to give those rows' own reason: they were not run because the lead's decision D33 placed them in BR-b-H, and the recognizer was not run for any part. The status words of D33, every count, row and bound are unchanged.
