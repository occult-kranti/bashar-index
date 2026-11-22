"""Which units of a recording count as claimed voice and which as own voice, under one definition (H1, H4, H6).

A definition is a dict:
  model      "record" (the label of record: middle on hold-out, small on seen), "small" or "middle"
  rule       "A" (labels as the model gives them) or "B" (an offer alone does not end a claimed voice; voice.rule_b)
  own        "broad" (own_broad of voice.py: V1, and uncued solo speech outside any claimed voice in recordings whose
             claimant is the sole speaker or the host) or "strict" (V1 only)
  claimants  the map claimants admitted
  claimed    the labels on the claimed side: ("V2", "V3") for the claimed voice, ("V2",) embodied, ("V3",) relayed
The primary definition (registry, owner's choice before freeze 1) is model "record", rule "B", own "broad".
Under rule B a unit that rule B moved into a claimed voice is never own voice, whatever own_broad says.

Claimed voice of the registered quantities (constants.CLAIMED_BY_HYPOTHESIS): V2 plus V3 for H1 and H6 (registry, lead's
decision of 2026-11-21 02:55: gate D's specific-V3 row failed on its bound after the one revision, so relayed voice is
merged into claimed voice), and the embodied voice V2 for H4, as hypotheses.md registers it (registry 2026-11-21 04:55
(a)). Every multiverse row and extra source of a hypothesis uses its claimed side. Secondary estimates only: embodied
alone (H1), relayed alone (H1, H4; flag "below the reliability floor", never a verdict) and the merged V2 + V3 (H4).
"""
from . import constants as K


def definition(**changes):
    """A voice definition; the claimed side is REGISTERED_CLAIMED (V2 + V3) unless a change sets another."""
    base = dict(K.PRIMARY_VOICE, claimed=K.REGISTERED_CLAIMED)
    base.update(changes)
    return base


def primary_definition(hypothesis, **changes):
    """The definition of a hypothesis's registered quantity: the primary definition with its claimed side
    (constants.CLAIMED_BY_HYPOTHESIS: H1 and H6 V2 + V3, H4 V2), and the given changes."""
    return definition(**dict({"claimed": K.CLAIMED_BY_HYPOTHESIS[hypothesis]}, **changes))


def registered(how=None):
    """`how` with the claimed side set to the merged claimed voice V2 + V3 (H1 and H6; H4's secondary estimate)."""
    return dict(how or definition(), claimed=K.REGISTERED_CLAIMED)


def merged_claimed(how):
    """H4's secondary estimate: the merged claimed voice V2 + V3 (K.MERGED_CLAIMED_NOTE), never a verdict."""
    return dict(how, claimed=K.REGISTERED_CLAIMED)


def embodied_only(how):
    """Secondary estimate: embodied voice (V2) alone. Estimate only (K.EMBODIED_ONLY_NOTE)."""
    return dict(how, claimed=(K.EMBODIED,))


def relayed_only(how):
    """Secondary estimate: relayed voice (V3) alone, below the reliability floor (K.RELAYED_ONLY_NOTE)."""
    return dict(how, claimed=(K.RELAYED,))


def below_floor(summary):
    """A relayed-only secondary estimate as reported: the flag, the note, and no verdict."""
    return dict(summary, flag=K.BELOW_FLOOR, note=K.RELAYED_ONLY_NOTE, verdict=None)


def sides(record, how):
    """Per unit: "claimed", "own" or None; and the label under the rule. None for the whole recording if it is outside the
    definition (claimant not admitted, not English, or the chosen model did not label every unit)."""
    if record["language"] != "en" or record["claimant"] not in how["claimants"]:
        return None
    model = how["model"]
    if model == "record":
        model = record["label_of_record"]
    elif model == "other":                              # the second model: the one that is not the record
        model = "small" if record["label_of_record"] == "middle" else "middle"
    out, labels = [], []
    for unit in record["units"]:
        view = unit["labels"].get(model)
        if view is None:
            return None
        label = view["B"] if how["rule"] == "B" else view["A"]
        labels.append(label)
        if label in how["claimed"]:
            out.append("claimed")
        elif label in K.CLAIMED:
            out.append(None)                            # a claimed label outside the chosen side (e.g. relayed for H4)
        elif how["own"] == "strict":
            out.append("own" if label == K.OWN else None)
        else:
            out.append("own" if view["own_broad"] and label not in K.CLAIMED else None)
    return out, labels


def spans(record, side_list):
    """Maximal runs of consecutive units on one side: (side, first index, last index, words)."""
    out, units, n, i = [], record["units"], len(side_list), 0
    while i < n:
        side = side_list[i]
        if side is None:
            i += 1
            continue
        j = i
        while j + 1 < n and side_list[j + 1] == side:
            j += 1
        out.append((side, i, j, sum(units[k]["n_words"] for k in range(i, j + 1))))
        i = j + 1
    return out


def words_by_side(record, side_list):
    out = {"claimed": 0, "own": 0}
    for unit, side in zip(record["units"], side_list):
        if side:
            out[side] += unit["n_words"]
    return out


def confusion(record, left, right):
    """Word-weighted table of two side lists (claimed, own, neither)."""
    table = {}
    for unit, a, b in zip(record["units"], left, right):
        key = (a or "neither", b or "neither")
        table[key] = table.get(key, 0) + unit["n_words"]
    return table


def self_naming_units(record, after=K.H5_SELF_NAMING_UNITS_AFTER):
    """H5 (registry 02:50, M9): the ids of the units that hold a self-naming cue of the label of record (the cue unit of
    every span whose cue type is in H5_SELF_NAMING_CUE_TYPES) and of the `after` units that follow each. None where no
    unit view of the file carries a cue (then the caller falls back to the feature files' pattern flags)."""
    model = record["label_of_record"]
    cues, any_cue = set(), False
    for unit in record["units"]:
        view = unit["labels"].get(model) or unit["labels"].get("small" if model == "middle" else "middle")
        cue = (view or {}).get("cue")
        if cue is None:
            continue
        any_cue = True
        if cue[0] in K.H5_SELF_NAMING_CUE_TYPES and cue[1]:
            cues.add(cue[1])
    if not any_cue:
        return None
    return sorted({unit_id + step for unit_id in cues for step in range(after + 1)})


def standard_rows(extra_claimed=None):
    """The multiverse rows of the plan (section 3.5) that one voice label file supports, besides the primary:
    the second model, rule A against rule B, strict against broad own voice, labels as the model gives them, and the
    claimant sensitivity set. Every row uses the hypothesis's claimed side (V2 + V3 by default; H4 passes V2)."""
    claimed = extra_claimed or K.REGISTERED_CLAIMED
    return [
        ("primary", definition(claimed=claimed)),
        ("second model (small against middle)", definition(model="other", claimed=claimed)),
        ("rule A (offer ends a claimed voice)", definition(rule="A", claimed=claimed)),
        ("strict own voice", definition(own="strict", claimed=claimed)),
        ("labels as the model gives them (rule A, strict)", definition(rule="A", own="strict", claimed=claimed)),
        ("claimant cannot_tell admitted", definition(claimants=K.SENSITIVITY_CLAIMANTS, claimed=claimed)),
    ]
