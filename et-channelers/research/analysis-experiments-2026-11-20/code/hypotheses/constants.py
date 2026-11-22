"""PROCEDURE: every choice the registered texts leave to the analysis code, in one place.

Sources, in order of authority: hypotheses.md (frozen 2026-11-20), registry.md (A1 to A11, the primary definitions, the
owner decisions before freeze 1), the calibration item's drafted amendments (panel round 2, CAL, approved in principle
by A9; their numbering in the draft is A8 to A14 and is cited here as "CAL-A8" and so on), and the annotation plan
(R1 to R27, sections 3.4 and 3.5). A value marked FREEZE2 must be computed from seen-creator labels and entered before
freeze 2; the code refuses a real run while it is None. A value marked CHOICE is the writer's operationalisation of a
sentence the texts leave open; it is listed in README.md for the owner to confirm before freeze 2.
"""

# ---------------------------------------------------------------- seeds and draws
BASE_SEED = 20261120                     # as H3; every stream is derived from it by sha256 of a label (stats.seed_for)
SIGNFLIP_EXACT_MAX = 20                  # A10.1 = CAL-A8: exact sign-flip up to 20 creators
SIGNFLIP_MC_DRAWS = 99999                # A10.1 = CAL-A8: Monte Carlo above 20 creators, p = (b + 1) / (m + 1)
PERMUTATION_DRAWS = 9999                 # H2's within-creator reference (secondary row), H9's family-label reference
BOOTSTRAP_DRAWS = 9999                   # creator bootstrap, as H3 (the battery gives H9 fewer: simulate.H9_BATTERY_BOOTSTRAP_DRAWS)
POWER_REPS = 2000                        # detectable-effect simulation (A10.2 = CAL-A9 point 1)

# ---------------------------------------------------------------- multiple comparisons (A6, A9, A10.1 = CAL-A8)
ALPHA = 0.05                             # family-wise level of the Holm procedure
HOLM_M = 10                              # count fixed at 10
ALL_HYPOTHESES = ("H1", "H2", "H3", "H4", "H5", "H6", "H7", "H8", "H9", "H10")
FIXED_P = {"H3": 1.0, "H8": 1.0}         # H3 closed (A6) and H8 dropped (A9): run, p = 1 (task statement; A10.1 = CAL-A8 point 3)
UNRUN = ("H7", "H10")                    # wait for the replication wave: p = 1 until run
THIS_TRACK = ("H1", "H2", "H4", "H5", "H6", "H9")
# Registry 2026-11-21 04:55 (h): no replication wave exists (downloads closed 2026-11-20), so the hold-out is the only
# confirmation sample. Every confirmatory estimate reads these groups only (common.confirmatory); a recording of any other
# group (a "wave" included) is left out, never pooled silently. If a wave is ever collected, a verdict must hold on the
# hold-out alone and on the pooled row (README; not coded). H9 pairs hold-out cells with seen cells.
CONFIRMATORY_GROUPS = ("holdout",)
# ASR-model rule (lead's decision before any label existed, applied identically to every group): H1, H2, H4, H5, H6 and
# H9 use only recordings whose resolved recognizer model is the run's English-only model ("english_only", the bundle's
# compute.text_model_role); another model, an unknown model or sources that disagree are excluded and counted per group
# in counts.json (adapter.apply_asr_rule). Timing, pause, filler and contraction measures differ by recognizer.
ASR_MODEL_REQUIRED = "english_only"
# Registry 03:08 (recognizer rule) and 04:55 (b): the seen transcripts of another recognizer model and every transcript of
# unknown model, excluded from the primary, go into one model-stratified sensitivity row per hypothesis (run.row_specs;
# adapter.model_stratified_view). Every comparison in that row stays within one model: within-recording contrasts (H1,
# H4, H6) are so by construction; H2 crosses the length band with the model; H5 compares a creator's channelled and
# own-voice recordings within one model, each model a stratum (creator by model, registry 2026-11-21 06:44 (9)); H9 builds
# cells within one model and pairs cells of the same model only.
# Recordings whose sources state different models, and hold-out recordings whose TABLE model differs, stay out of it.
ASR_STRATIFIED_ROW = "recognizer model stratified: other and unknown models included (registry 03:08)"

# ---------------------------------------------------------------- intervals (A5, A10.7 = CAL-A14)
A5_LEVEL = 0.90                          # "supported" needs the 90% interval over creators to exclude zero (H5, H6: both
                                         # the t interval on OE and the MH interval, registry 2026-11-21 06:44 (5))
REGISTERED_LEVEL = 0.95                  # H1 and H4: the 95% interval and the 95% prediction interval of the pool
# Registry 2026-11-21 04:55 (j): until the label-based coverage repeat (CAL part f) has run, the Mantel-Haenszel
# estimates of H5 and H6 carry the wider of the creator-bootstrap percentile interval and the t interval (elementwise:
# lower = the smaller lower bound, upper = the larger upper bound). The t interval of an MH estimate (CHOICE): its log
# +- t(k - 1) x the delete-one-creator jackknife standard error (stats.jackknife_t_interval). Freeze 2 may switch the
# rule to "bootstrap_percentile" or "t" once the coverage repeat has run; any other value is refused.
MH_INTERVAL_RULES = ("wider", "bootstrap_percentile", "t")
MH_INTERVAL_RULE = "wider"
# Registered "creator-bootstrap interval" (hypotheses.md H2, H5, H6) under catalogue rule R1 ("Resample creators, then
# recordings within a creator"; H3's frozen interval reads it the same way): the registered versions under the A10 guard
# draw creators, then recordings within each drawn creator (stats.bootstrap_two_stage; registry 04:55 (d)). H1 and H4
# register a random-effects pool and no bootstrap, so their registered interval is the pool's (DerSimonian-Laird, normal).

# ---------------------------------------------------------------- minimums (registry; A10.2 = CAL-A9, A10.3 = CAL-A10, A10.4 = CAL-A11)
# A10.2: "not determinable: too few eligible creators" below the smallest count at which an exact sign-flip can pass the
# first Holm step (0.005): 8 one-sided, 9 two-sided. The registry's stricter minimums stay (12 for H1, H4, H5, H6).
A10_MIN_ONE_SIDED = 8
A10_MIN_TWO_SIDED = 9
SIDEDNESS = {"H1": "less", "H2": "two-sided", "H4": "greater", "H5": "greater", "H6": "less", "H9": "greater"}
# the minimums before A10 (hypotheses.md and the registry): H2's 8 creators with 30 statements; H9 had no creator minimum
REGISTERED_MIN_CREATORS = {"H1": 12, "H2": 8, "H4": 12, "H5": 12, "H6": 12, "H9": None}
MIN_CREATORS = {name: max(REGISTERED_MIN_CREATORS[name] or 0,
                          A10_MIN_TWO_SIDED if SIDEDNESS[name] == "two-sided" else A10_MIN_ONE_SIDED)
                for name in ("H1", "H2", "H4", "H5", "H6", "H9")}          # H1 12, H2 9, H4 12, H5 12, H6 12, H9 8
REGISTERED_SIGNFLIP_DRAWS = 9999         # H5's registered reference: "sign-flip over creators (9,999)"
H6_MIN_CREATORS_WITH_ASK = 8             # A10.4 = CAL-A11: 8 or more creators with T >= 1, besides the 12 with both voices
H5_MIN_HITS_PER_GROUP = 10               # A10.4 = CAL-A11: T_A >= 10 and T_B >= 10 (margin only, never per side)
H5_RELAXED_HITS = 5                      # the protocol's relaxed row
H5_MIN_RECORDINGS_PER_SIDE = 2
H2_MIN_STATEMENTS = 30
H6_LOG_DISPLAY_MIN_T = 5                 # per-creator log ratios shown only for T >= 5 (private output)
DETECTABLE_FACTOR = 1.5                  # A10.2 = CAL-A9 point 4: "run; detectable only from X" if X > 1.5 x SESOI

# ---------------------------------------------------------------- smallest effects of interest (hypotheses.md)
SESOI = {"H1": -0.05,                    # log ratio; "slower" if the upper 95% bound of the ratio is below 0.95
         "H2": 0.10,                     # |D|
         "H4": 0.5,                      # standardised drop, between-creator SD of own-voice contraction share
         "H5": 0.4,                      # log units
         "H6": 0.5,                      # rate ratio for "does not sell"
         "H9": 0.2}                      # standardised units (placeholder of the registry; FREEZE2 check on seen cells)
H1_BAND = (0.95, 1.05)                   # "no slowing" band of the ratio
H6_EQUIVALENCE = (0.67, 1.5)             # "sells like the human"

# ---------------------------------------------------------------- voice labels (voice.py, produce.py, registry)
CLAIMED = ("V2", "V3")
EMBODIED, RELAYED, OWN = "V2", "V3", "V1"
# Registry, lead's decision of 2026-11-21 02:55 (voice revision 3, plan 3.4): gate D's specific-V3 row failed on its bound
# (0.762 [0.488] against 0.60 [0.50]) after the one revision, so relayed voice is merged into claimed voice: the claimed
# side of H1 and H6 is V2 plus V3. Relayed voice alone is a secondary estimate with the flag below and never a verdict.
# Registry 2026-11-21 04:55 (a): H4's primary stays the embodied first-person voice (V2), as hypotheses.md registers it
# ("Primary on embodied first-person spans"; gate D's embodied/own row passed, 0.921); the claimed voice V2 + V3 is a
# secondary estimate of H4 without a verdict. Every multiverse row and extra source of H4 uses V2 as well.
REGISTERED_CLAIMED = CLAIMED
H4_CLAIMED = (EMBODIED,)
CLAIMED_BY_HYPOTHESIS = {"H1": REGISTERED_CLAIMED, "H4": H4_CLAIMED, "H6": REGISTERED_CLAIMED}
BELOW_FLOOR = "below the reliability floor"
RELAYED_ONLY_NOTE = ("relayed voice alone rests on the V2/V3 split, whose specific-V3 row failed gate D on its bound "
                     "(0.762 [0.488] against 0.60 [0.50]); an estimate only, never a verdict (registry 2026-11-21 02:55)")
EMBODIED_ONLY_NOTE = ("embodied voice alone (V2) uses the same V2/V3 split; reported as an estimate only, never a verdict "
                      "(registry 2026-11-21 02:55)")
MERGED_CLAIMED_NOTE = ("H4: claimed voice V2 + V3 (relayed merged into claimed, registry 2026-11-21 02:55); a secondary "
                       "estimate without a verdict, because H4's registered primary is the embodied voice (V2; registry "
                       "2026-11-21 04:55 (a))")
PRIMARY_CLAIMANTS = ("sole_speaker", "host_or_owner")       # protocol 3.4; cannot_tell is a sensitivity set
SENSITIVITY_CLAIMANTS = ("sole_speaker", "host_or_owner", "cannot_tell")
H1_EXCLUDED_FORMATS = ("conversation", "multi_presenter")   # CHOICE: "own-voice spans exclude interviews until SP"
# Primary definitions chosen by the owner before freeze 1 (registry): broad own voice; an offer alone does not end a
# claimed voice (rule B of voice.py). The other definitions are rows.
PRIMARY_VOICE = {"model": "record", "rule": "B", "own": "broad", "claimants": PRIMARY_CLAIMANTS}
PUNCTUATION_SENTENCE = "The voice label responds to punctuation and case."
VOICE_HYPOTHESES = ("H1", "H4", "H6")

# ---------------------------------------------------------------- H1
H1_MIN_SPAN_WORDS = 300                  # each span counted on either side holds at least 300 words
H1_PAUSE_SECONDS = 0.25                  # CHOICE: inter-word gap counted as pause for the articulation split (E4)
H1_NEG_MIN_OPENING_WORDS = 100           # CHOICE: negative control, greeting of at least 100 words
H1_NEG_MIN_MAIN_WORDS = 300

# ---------------------------------------------------------------- H4
# FREEZE2 entered from the seen labels, exactly as printed by
#   the guarded analysis venv: python -I run.py constants
# (from this folder; the production tree llm/labels/seen/ through the seen-only path; 999 draws, the default), run
# 2026-11-21T14:00:03Z to 14:00:37Z UTC (date -u), exit 0; ASR-model rule english_only: 1,284 of 1,293 seen recordings
# kept (9 of unknown model out), 71 creators. Label folders, sha256 of the sorted "sha256  filename" lines:
#   voice     84026da06bf0f6a18457e2f32c0bca07d7f248c14d74823eb67b83a1492ff15c
#   asks      5da50547a1ae4ffbc64813f50daf3b2a255830babdd86eeb2a3e04643dac40a4
#   features  79bf88442ba923d3d715941d0d7c7b3125ae9b1ebc112ec4c02b3c969161e09b (features-4)
#   forecasts d103cfc787e42f2cc5173f82f4e3a3f6c33fb077f91ea5ff83f10cee9a3073e2
#   sentences 0ce26f44886a5c5919556fc31971f70ccf8ebd08ff9cbf111a6ed6700ee6f1d9
#   titles    dfa0e894da4bef6c587c69c37244794b4584430154a077ebd03001896abc9c86
# 52 seen creators with at least 40 own-voice forms (small model, the record on seen); the middle-model version printed
# beside it: 0.16182180258870596 (23 creators). An independent recomputation outside the package gave the same value.
H4_YARDSTICK = 0.14738201990446706       # FREEZE2: between-creator SD of own-voice contraction share, seen creators
H4_MIN_FORMS_PER_SIDE = 10               # CHOICE: contractible forms (contracted + full) per side and recording
H4_WINDOW_WORDS = 150                    # CHOICE: own-voice windows of the tempo negative control

# ---------------------------------------------------------------- H6
H6_ASK_CLASS = "K1"                      # pay or enrol
H6_MIN_SIDE_WORDS = 300                  # CHOICE: "with both voices": at least 300 words on each side in a recording

# ---------------------------------------------------------------- H2
# FREEZE2 entered from the seen labels, exactly as printed ([12.0, 20.0]) by
#   the guarded analysis venv: python -I run.py constants
# run 2026-11-21T14:00:03Z to 14:00:37Z UTC (date -u), seen-only path, ASR-model rule english_only (1,284 of 1,293 kept);
# label folders as for H4_YARDSTICK above (voice 84026da0..., asks 5da50547..., features 79bf8844..., forecasts
# d103cfc787e42f2cc5173f82f4e3a3f6c33fb077f91ea5ff83f10cee9a3073e2, sentences 0ce26f44..., titles dfa0e894...).
# Tertiles over 9,005 verified non-duplicate seen statements; an independent recomputation gave the same cut points.
H2_LENGTH_BANDS = (12.0, 20.0)           # FREEZE2: cut points of statement length (words) from seen statements
H2_PARTS = ("time_window", "place", "named_actor", "observable_outcome", "quantity")
H2_PRIMARY_WHERE = ("STATEMENT", "CONTEXT")                  # R10: FRAME is a sensitivity row
# Registry 2026-11-21 04:55 (second reading): a sensitivity row in which a time window taken only from the period of the
# talk counts as NO. The checkability answer marks it with "where" FRAME on time_window (forecasts_fc.txt and its schema:
# "The line 'Period of the talk' can supply the time window only ... time_window is YES with 'where' set to FRAME";
# label-files.md: fc.where; adapter.parse_statement keeps (value, where) per part). In the row a FRAME time window is NO
# whatever its value (YES or CANNOT_TELL). The primary already counts STATEMENT and CONTEXT only (R10), so for YES
# readings the row repeats the primary; it differs where a FRAME time window is CANNOT_TELL (the primary leaves such a
# statement out as missing, the row counts the part as NO).
H2_FRAME_WHERE = "FRAME"
FOUR_STEP = {"hedged": 0, "conditional": 1, "bare": 2, "boosted": 3}
# Registry, lead's decision of 2026-11-21 02:50 (meta-review M9): H2 is reduced to its checkability parts with at least 5%
# prevalence on seen statements. FREEZE2: h2_hedging.parts_from_seen on seen labels (YES in STATEMENT or CONTEXT, record
# reading, verified non-duplicate coded statements, weights 1 / p) gives the tuple, entered before freeze 2.
H2_PART_PREVALENCE_MIN = 0.05
# FREEZE2 entered from the seen labels, exactly as printed (["time_window", "named_actor", "observable_outcome"]) by
#   the guarded analysis venv: python -I run.py constants
# run 2026-11-21T14:00:03Z to 14:00:37Z UTC (date -u), seen-only path, ASR-model rule english_only (1,284 of 1,293 kept);
# label folders as for H4_YARDSTICK above (voice 84026da0..., asks 5da50547..., features 79bf8844..., forecasts
# d103cfc787e42f2cc5173f82f4e3a3f6c33fb077f91ea5ff83f10cee9a3073e2, sentences 0ce26f44..., titles dfa0e894...).
# Weighted prevalence over 9,005 verified non-duplicate seen statements with a record reading: time_window 0.1163,
# observable_outcome 0.1073, named_actor 0.0543 (retained); place 0.0429, quantity 0.0296 (below 5%). An independent
# recomputation gave the same table.
# FREEZE2: the parts of H2_PARTS whose seen prevalence is at least 5%
H2_PARTS_RETAINED = ("time_window", "named_actor", "observable_outcome")
# Registry 02:50 (M9): statements whose checkability parts and commitment code share scenario or withdrawal wording are
# flagged by a fixed rule; H2's primary row uses the unflagged statements and the row with flagged statements is
# reported beside it. The rule (wording.shared_wording) reads only the statement's wording (statement_quote, and a
# sentence field if a file carries one), never a code: a flag that read the codes would select on the outcome. Patterns
# (id, kind, regular expression on the lower-cased wording) and the prompt clauses they come from:
#   scenario   checkability (forecasts_fc.txt, observable_outcome NO): "outcomes that cannot fail (either A or B)";
#              commitment (forecasts_fd.txt): hedge "talk of probability or of one possible scenario", "one scenario
#              is"; condition CE "which of several scenarios comes about", "in one scenario ..., in the other ...",
#              "in one timeline <X>, in another <Y>", "alternative outcomes set side by side"
#   withdrawal checkability: "outcomes that the wording itself withdraws ("in some sense", "on another level")";
#              commitment: hedge "a disclaimer that the speaker is not saying it will happen" ("I'm not saying it will")
# Registry 2026-11-21 04:55 (e): the flag covers the scenario and withdrawal categories that both codebooks name; the
# plain hedge "a possibility" (the former SC5) is left out, because it is the commitment code itself and not scenario
# wording. SC1-SC4 and WD1-WD4 stay; the ids are not renumbered.
H2_SHARED_WORDING = (
    ("SC1", "scenario", r"\bscenarios?\b"),
    ("SC2", "scenario", r"\b(?:one|another|other|either|alternate|alternative|different|several|two|three|multiple|many|"
                        r"possible|potential|probable)\s+(?:possible\s+|potential\s+|probable\s+)?"
                        r"(?:timelines?|futures|outcomes|possibilities)\b"),
    ("SC3", "scenario", r"\beither\b[^.?!]{1,80}?\bor\b"),
    ("SC4", "scenario", r"\b(?:either way|one way or (?:the )?(?:other|another)|whichever (?:way|happens|comes|it goes))\b"),
    ("WD1", "withdrawal", r"\bin (?:some|a|one|certain) sense\b|\bin some ways?\b"),
    ("WD2", "withdrawal", r"\bon (?:another|a different|other|some|an? (?:higher|deeper|inner|energetic|spiritual|soul|subtle|"
                          r"other|different)|the (?:energetic|spiritual|soul|inner|higher|astral|etheric)) levels?\b"),
    ("WD3", "withdrawal", r"\b(?:energetically|metaphorically|symbolically|so to speak)\b"),
    ("WD4", "withdrawal", r"\b(?:not|never) (?:saying|predicting|promising)\b"),
)

# ---------------------------------------------------------------- H5 (protocol section 5; titles section 3)
H5_GROUPS = {"primary": ({"Q1"}, {"Q4", "Q5", "Q6"}),
             "sensitivity_A": ({"Q1", "Q2"}, {"Q4", "Q5", "Q6"}),
             "sensitivity_B": ({"Q1", "Q2"}, {"Q4", "Q5", "Q6", "Q3"}),
             "sensitivity_C": ({"Q1"}, {"Q4", "Q5", "Q6", "Q8"})}
H5_EXCLUDED_KIND_CUES = ("KM", "KI", "KP")
H5_EXCLUDED_MAIN_KINDS = ("guided_practice", "conversation")
H5_SOLO_FORMATS = ("solo",)              # "solo own-voice talks"; CHOICE: the voice map's format where it exists
# Registry 02:50 (M9): H5 reports three Q2 assignments as rows. "as registered": Q2 (general principle) on neither side
# (the primary groups); "merged with Q1": world = Q1 + Q2 (sensitivity A); "excluded": every unit whose primary or
# secondary code is Q2 leaves the sample (the Q1/Q2 boundary, where the two tiers disagree, drops out; a recording coded
# whole is rescaled without those units).
H5_Q2_ASSIGNMENTS = {"as registered": {"groups_name": "primary"},
                     "merged with Q1": {"groups_name": "sensitivity_A"},
                     "excluded": {"groups_name": "primary", "drop_codes": ("Q2",)}}
# Registry 02:50 (M9): H5 excludes units next to a self-naming cue: a unit with a self-introduction of a claimed source,
# and the unit after it. The cue is read from the voice label file: every unit's view carries the cue of its span
# (cue type and cue unit, voice.py); the cue units of type self_name (voice codebook: "The voice names or describes itself
# as a source, in forms like "I am <name>", "we are the <group>", "this is <name> of the <group>"") of the label of
# record are the self-naming units. Where a voice file carries no cue, features.py's pattern list (below) on the unit's
# words is the fallback (feature files, field "self_name"); it cannot tell a source from a person naming themselves, so
# it can only remove more units.
H5_SELF_NAMING_CUE_TYPES = ("self_name",)
H5_SELF_NAMING_UNITS_AFTER = 1
SELF_NAMING_PATTERNS = (                 # (id, regular expression on the unit's words as transcribed, case kept)
    ("SN1", r"(?i:\b(?:i am|i'm|we are|we're)\s+(?:the\s+|an?\s+)?)(?:[A-Z][\w'’-]+)"),
    ("SN2", r"(?i:\bthis is\s+)[A-Z][\w'’-]+(?:\s+[A-Z][\w'’-]+)*(?i:\s+(?:of|from)\s+the\s+)"),
    ("SN3", r"(?i:\b(?:my|our) names? (?:is|are)\s+)"),
    ("SN4", r"(?i:\b(?:i am|i'm|we are|we're) (?:known|called) (?:as\s+)?)"),
    ("SN5", r"(?i:\bwe are (?:a|the) (?:collective|council|group|federation|consciousness|family|alliance) of\b)"),
)

# ---------------------------------------------------------------- H9 (titles section 3)
SPECIFIC_FAMILIES = ("S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "A1", "A2", "A3", "A4", "A5", "G3", "G4")
ET_FAMILIES = ("S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8")
AD_FAMILIES = ("A1", "A2", "A3", "A4", "A5")
H9_MIN_RECORDINGS_PER_CELL = 2
H9_MIN_CELL_WORDS = 2000
H9_RAREFY_TOKENS = 2000
H9_TOP_DISTINGUISHING = 100

# ---------------------------------------------------------------- uninformative results (registry 2026-11-21 02:50)
# A result is uninformative when its 90% creator interval contains both zero and the smallest effect of interest in
# either direction, or its verdict is not determinable. The interval and the SESOI are on one scale: H1 log ratio (0.05),
# H2 D (0.10), H4 standardised drop (0.5), H5 MH log odds ratio (0.4), H6 log MH rate ratio (log 2: a ratio of 0.5 or 2),
# H9 standardised difference (0.2). Each analysis states its interval as creator_interval_90.
UNINFORMATIVE_SESOI = {"H1": 0.05, "H2": 0.10, "H4": 0.5, "H5": 0.4, "H6": 0.6931471805599453, "H9": 0.2}

# ---------------------------------------------------------------- wording (A8, A11, plan 3.5, registry 03:08)
MODEL_CODED = ("Labels were produced by language models from frozen prompts; no person has checked them (A8). "
               "The estimate is model-coded.")
SUPPORTED, REFUTED = "supported (model-coded)", "refuted (model-coded)"
# registry 2026-11-21 03:08: the wording of a verdict, with the verification figures passed in the config ("verification":
# {"all" or hypothesis: {"third_model": ..., "known_answer": ..., "cross_vendor": ...}}); the word "validated" is never used
VERIFICATION_PARTS = (("third_model", "verified by a third model"), ("known_answer", "on known-answer texts"),
                      ("cross_vendor", "by a reader of another vendor"))
NOT_ENTERED = "figures not entered"
DISCLOSURES = {
    "H2": "Checkability: the two-model gate failed for time window (kappa 0.55) and place (0.29; floor 0.60) after both "
          "allowed revisions; by the owner's decision the middle model codes every statement and is the record, and the "
          "largest model re-reads a sample of about 300 statements (registry, owner decisions before freeze 1).",
    "H5": "Titles: the gate failed (presentation kappa 0.45, stability 0.87; floors 0.70, 0.90); by the owner's decision "
          "the middle model is the record and the largest model decides every title on which middle and small disagree. "
          "Own-voice talks and channelled sessions are made for different occasions: the difference is voice plus occasion.",
    "H9": "Titles: the gate failed (presentation kappa 0.45, family 0.49; floors 0.70, 0.60); record as for H5. A title "
          "names the being a recording is published under, not who speaks in a span.",
}
