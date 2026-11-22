"""H9. Creators who name the same family of beings share more content vocabulary than function-word style.

Estimand (hypotheses.md): unit creator-by-family cell (at least 2 recordings and 2,000 words, rarefied to equal tokens;
whole recordings in which title and opening formula agree on the family). For each representation the contrast is the
mean similarity of cells with the same family and different creators minus that of cells with different families and
different creators, divided by the SD of the different-family similarities in that representation (writer's addition in
the text). Registered estimand: the content contrast (names-masked content-word TF-IDF, cosine) minus the function-word
contrast (z-scored relative frequencies of the closed function-word list, cosine; CHOICE). Confirmed on hold-out cells
against seen cells, so that one side of every pair is unread. Reference: family labels of the hold-out cells permuted
among them (keeps the family sizes), 9,999 draws, one-sided; creator-bootstrap interval (hold-out and seen creators drawn
apart, then recordings within each drawn creator's cells, every cell re-rarefied in every draw: catalogue rule R1,
registry 2026-11-21 06:44 (4); both versions, since A10 replaces no H9 interval); leave-one-creator-out range. Refuted
by an interval at or below zero. Smallest effect 0.2 (placeholder; FREEZE2 check on seen cells). Minimum CHOICE: 8 hold-out creators with a cell (A10.2 = CAL-A9's one-sided minimum), and a
reference that can reach p = 0.005.
Recognizer-model-stratified row (registry 03:08 and 04:55 (b)): a cell holds recordings of one model, and a hold-out
cell is compared only with seen cells of its own model (a mask on the pairs); without the row nothing changes.
"""
from array import array
import bisect
from collections import Counter
from itertools import compress
import math
from operator import itemgetter

from . import common
from . import constants as K
from . import features as F
from . import stats
from . import tipping

H = "H9"
A10_REPLACES = ("minimum: none besides a reference that can reach the first Holm step (registered) -> also 8 hold-out creators "
                "with a cell, the one-sided minimum (A10.2, CAL-A9)",)


# ---------------------------------------------------------------- cells

def recording_family(title, specific):
    if not title or title["presentation"] != "P1" or title["voiced_by"] != "C":
        return None
    families = [f for f in title["source_families"] if f in specific]
    return families[0] if len(set(families)) == 1 else None


def cells(bundle, title_source="final", opening_rule=True, specific=K.SPECIFIC_FAMILIES, families=None):
    titles = (bundle.get("titles") or {}).get(title_source) or {}
    grouped = {}
    for item in bundle["recordings"]:
        feats = (item.get("features") or {}).get("h9")
        voice = item.get("voice")
        if not feats or (voice and voice["language"] != "en"):
            continue
        family = recording_family(titles.get(item.get("video_id")), specific)
        if family is None or (families and family not in families):
            continue
        if opening_rule and not feats.get("opening_family_match", {}).get(family):
            continue
        stratum = common.stratum(bundle, item)
        cell = grouped.setdefault((item["creator"], family, "" if stratum is None else stratum),
                                  {"creator": item["creator"], "family": family, "group": item["group"], "stratum": stratum,
                                   "recordings": 0, "content": {}, "function": {}, "other": 0, "parts": []})
        cell["recordings"] += 1
        cell["parts"].append(feats)                  # the recording's counts: R1's second stage resamples them
        for kind in ("content", "function"):
            for token, count in feats[kind].items():
                cell[kind][token] = cell[kind].get(token, 0) + count
        cell["other"] += feats.get("other", 0)
    out = []
    for key in sorted(grouped):
        cell = grouped[key]
        words = sum(cell["content"].values()) + sum(cell["function"].values()) + cell["other"]
        if cell["recordings"] >= K.H9_MIN_RECORDINGS_PER_CELL and words >= K.H9_MIN_CELL_WORDS:
            cell["words"] = words
            out.append(cell)
    return out


def rarefy(cell, tokens, label):
    """Draw `tokens` tokens without replacement from the cell (content, function and the rest as one bucket)."""
    items = [("c", t, n) for t, n in sorted(cell["content"].items())] + [("f", t, n) for t, n in sorted(cell["function"].items())]
    if cell["other"]:
        items.append(("o", "", cell["other"]))
    cumulative, total = [], 0
    for _, _, n in items:
        total += n
        cumulative.append(total)
    picks = stats.rng(*label, cell["creator"], cell["family"]).sample(range(total), min(tokens, total))
    content, function = {}, {}
    for pick in picks:
        kind, token, _ = items[bisect.bisect_right(cumulative, pick)]
        if kind == "c":
            content[token] = content.get(token, 0) + 1
        elif kind == "f":
            function[token] = function.get(token, 0) + 1
    return content, function


def _cosine(a, b):
    num = sum(value * b.get(key, 0.0) for key, value in a.items())
    na, nb = math.sqrt(sum(v * v for v in a.values())), math.sqrt(sum(v * v for v in b.values()))
    return num / (na * nb) if na and nb else 0.0


def representations(cell_list, label, delete=()):
    """Content TF-IDF vectors and z-scored function-word profiles of the rarefied cells."""
    return vectorize([rarefy(cell, K.H9_RAREFY_TOKENS, label) for cell in cell_list], delete)


def vectorize(drawn, delete=()):
    """Content TF-IDF vectors and z-scored function-word profiles of rarefied cells ([(content, function)])."""
    removed = set(delete)
    content = [{t: n for t, n in c.items() if t not in removed} for c, _ in drawn]
    n = len(content)
    df = {}
    for vector in content:
        for token in vector:
            df[token] = df.get(token, 0) + 1
    idf = {token: math.log((1 + n) / (1 + count)) + 1.0 for token, count in df.items()}
    tfidf = [{t: c * idf[t] for t, c in vector.items()} for vector in content]
    profiles = []
    for _, function in drawn:
        total = sum(function.values()) or 1
        profiles.append([function.get(word, 0) / total for word in F.FUNCTION_WORDS])
    zs = []
    columns = list(zip(*profiles)) if profiles else []
    centre = [sum(col) / len(col) for col in columns]
    spread = [stats.sd(col) or 0.0 for col in columns]
    for profile in profiles:
        zs.append({i: (value - centre[i]) / spread[i] for i, value in enumerate(profile) if spread[i] > 0})
    return tfidf, zs


def distinguishing_words(cell_list, top):
    """Each family's `top` most distinguishing content words (smoothed log ratio of its pooled rate to the others')."""
    families = sorted({cell["family"] for cell in cell_list})
    vocab = sorted({t for cell in cell_list for t in cell["content"]})
    out = set()
    for family in families:
        inside, outside = {}, {}
        for cell in cell_list:
            target = inside if cell["family"] == family else outside
            for t, n in cell["content"].items():
                target[t] = target.get(t, 0) + n
        ni, no, v = sum(inside.values()), sum(outside.values()), len(vocab)
        scored = sorted(vocab, key=lambda t: (-(math.log((inside.get(t, 0) + 0.5) / (ni + 0.5 * v)) - math.log((outside.get(t, 0) + 0.5) / (no + 0.5 * v))), t))
        out |= set(scored[:top])
    return sorted(out)


# ---------------------------------------------------------------- the contrast

class Pairs:
    """Similarities of every (hold-out cell, seen cell) pair in one representation, with the sums the permutation needs.
    mask (the model-stratified row only): mask[h][s] is True where hold-out cell h and seen cell s share a recognizer
    model; only those pairs count. Without a mask every pair counts and the sums are those of the unmasked code."""

    def __init__(self, vectors, held, seen, seen_families, families, mask=None):
        self.sim = [[_cosine(vectors[h], vectors[s]) for s in seen] for h in held]
        self._sums(seen_families, families, mask)

    def _sums(self, seen_families, families, mask):
        self.families, self.mask = families, mask
        if mask is None:
            count = {f: sum(1 for g in seen_families if g == f) for f in families}
            self.count = [count for _ in self.sim]
            self.s1 = [{f: sum(v for v, g in zip(row, seen_families) if g == f) for f in families} for row in self.sim]
            self.s2 = [{f: sum(v * v for v, g in zip(row, seen_families) if g == f) for f in families} for row in self.sim]
            self.t1 = [sum(row) for row in self.sim]
            self.t2 = [sum(v * v for v in row) for row in self.sim]
            self.ns = [len(seen_families) for _ in self.sim]
            return
        self.count = [{f: sum(1 for g, m in zip(seen_families, keep) if m and g == f) for f in families} for keep in mask]
        self.s1 = [{f: sum(v for v, g, m in zip(row, seen_families, keep) if m and g == f) for f in families}
                   for row, keep in zip(self.sim, mask)]
        self.s2 = [{f: sum(v * v for v, g, m in zip(row, seen_families, keep) if m and g == f) for f in families}
                   for row, keep in zip(self.sim, mask)]
        self.t1 = [sum(v for v, m in zip(row, keep) if m) for row, keep in zip(self.sim, mask)]
        self.t2 = [sum(v * v for v, m in zip(row, keep) if m) for row, keep in zip(self.sim, mask)]
        self.ns = [sum(1 for m in keep if m) for keep in mask]

    def contrast(self, labels):
        same = same_n = diff = diff_n = diff_sq = 0.0
        for h, f in enumerate(labels):
            same += self.s1[h].get(f, 0.0)
            same_n += self.count[h].get(f, 0)
            diff += self.t1[h] - self.s1[h].get(f, 0.0)
            diff_sq += self.t2[h] - self.s2[h].get(f, 0.0)
            diff_n += self.ns[h] - self.count[h].get(f, 0)
        if not same_n or diff_n < 2:
            return None
        var = (diff_sq - diff * diff / diff_n) / (diff_n - 1)
        if var <= 0:
            return None
        return (same / same_n - diff / diff_n) / math.sqrt(var)


def delta(content_pairs, function_pairs, labels):
    c, f = content_pairs.contrast(labels), function_pairs.contrast(labels)
    return None if c is None or f is None else c - f


class _Encoder:
    """Integer codes of the tokens of the cells' recordings, for the re-rarefaction of the two-stage bootstrap: content
    tokens 0 .. n_content - 1, the closed function-word list next (any other function token after it, counted in the
    function total but in no profile, as in rarefy), then one code for the rest. Each recording's tokens are expanded once
    into an array of codes."""

    def __init__(self, cell_list):
        parts = [part for cell in cell_list for part in cell["parts"]]
        content = sorted({token for part in parts for token in part["content"]})
        extra = sorted({token for part in parts for token in part["function"]} - set(F.FUNCTION_WORDS))
        self.content = {token: i for i, token in enumerate(content)}
        self.n_content = len(content)
        self.function = {word: self.n_content + i for i, word in enumerate(tuple(F.FUNCTION_WORDS) + tuple(extra))}
        self.n_listed = len(F.FUNCTION_WORDS)
        self.other = self.n_content + len(self.function)
        self._cache = {}

    def codes(self, part):
        key = id(part)
        if key not in self._cache:
            out = array("i")
            for token, n in sorted(part["content"].items()):
                out.extend([self.content[token]] * n)
            for token, n in sorted(part["function"].items()):
                out.extend([self.function[token]] * n)
            out.extend([self.other] * int(part.get("other", 0)))
            self._cache[key] = (part, out)                 # the part is kept so that its id stays its own
        return self._cache[key][1]


def _sample_indices(n, k, stream):
    """k distinct indices of range(n), drawn uniformly without replacement, as rarefaction draws them: the first k distinct
    values of a sequence of uniform draws (64 random bits each, mapped to range(n) by multiplication; for k above n / 2 the
    n - k left out are drawn instead)."""
    if k >= n:
        return range(n)
    if 2 * k > n:
        mask = bytearray(b"\x01") * n
        for i in _sample_indices(n, n - k, stream):
            mask[i] = 0
        return compress(range(n), mask)
    chosen = set()
    while len(chosen) < k:
        need = k - len(chosen)
        chosen.update([(x * n) >> 64 for x in array("Q", stream.randbytes(8 * need))])
    return chosen


def _rarefied_counts(encoder, parts, tokens, stream):
    """One cell of a bootstrap draw: the drawn recordings' tokens pooled and `tokens` of them drawn without replacement;
    returns {code: count}."""
    pool = array("i")
    for part in parts:
        pool.extend(encoder.codes(part))
    return Counter(map(pool.__getitem__, _sample_indices(len(pool), min(tokens, len(pool)), stream)))


def _draw_vectors(encoder, counters, deleted):
    """One draw's rarefied cells as vectorize represents cells, computed over the cells of the draw: content TF-IDF
    vectors ({code: value}) with their norms, and z-scored function-word profiles (dense, unit length)."""
    nc = encoder.n_content
    if deleted:
        contents = [{code: n for code, n in counter.items() if code < nc and code not in deleted} for counter in counters]
    else:
        contents = [{code: n for code, n in counter.items() if code < nc} for counter in counters]
    df = Counter()
    for vector in contents:
        df.update(vector.keys())
    n = len(contents)
    idf = {code: math.log((1 + n) / (1 + count)) + 1.0 for code, count in df.items()}
    tfidf, norms = [], []
    for vector in contents:
        weighted = {code: count * idf[code] for code, count in vector.items()}
        values = list(weighted.values())
        tfidf.append(weighted)
        norms.append(math.sqrt(math.sumprod(values, values)))
    listed = range(nc, nc + encoder.n_listed)
    extra = range(nc + encoder.n_listed, encoder.other)
    profiles = []
    for counter in counters:
        profile = [counter.get(code, 0) for code in listed]
        total = (sum(profile) + sum(counter.get(code, 0) for code in extra)) or 1
        profiles.append([value / total for value in profile])
    centre, inverse = [], []
    for column in zip(*profiles):
        mean = sum(column) / n
        var = (math.sumprod(column, column) - n * mean * mean) / (n - 1) if n > 1 else 0.0
        spread = math.sqrt(var) if var > 1e-300 else 0.0
        centre.append(mean)
        inverse.append(1.0 / spread if spread > 0 else 0.0)        # a column without spread is left out, as in vectorize
    zs = []
    for profile in profiles:
        z = [(value - c) * s for value, c, s in zip(profile, centre, inverse)]
        norm = math.sqrt(math.sumprod(z, z))
        zs.append([value / norm for value in z] if norm else [0.0] * len(z))
    return tfidf, norms, zs


def _content_similarities(held, held_norms, seen, seen_norms, size):
    """Cosines of the content vectors of hold-out and seen cells. Dense products where the vocabulary is small against the
    vectors' length, else each hold-out vector made dense once and each seen vector gathered from it."""
    mean_length = sum(len(vector) for vector in held + seen) / max(1, len(held) + len(seen))
    if size <= 8 * mean_length:
        def dense(vector):
            out = [0.0] * size
            for code, value in vector.items():
                out[code] = value
            return out
        seen_dense = [dense(vector) for vector in seen]
        return [[math.sumprod(h, s) / (hn * sn) if hn and sn else 0.0 for s, sn in zip(seen_dense, seen_norms)]
                for h, hn in ((dense(vector), norm) for vector, norm in zip(held, held_norms))]
    getters = []
    for vector in seen:
        index, values = tuple(vector), tuple(vector.values())
        getters.append((itemgetter(*index) if len(index) > 1 else (lambda dense, i=index: tuple(dense[j] for j in i)), values))
    out = []
    for vector, hn in zip(held, held_norms):
        row = [0.0] * size
        for code, value in vector.items():
            row[code] = value
        out.append([math.sumprod(values, getter(row)) / (hn * sn) if values and hn and sn else 0.0
                    for (getter, values), sn in zip(getters, seen_norms)])
    return out


def _contrast(sim, held_families, seen_families, mask):
    """Pairs.contrast on one draw's similarity matrix: same-family minus different-family mean similarity over the SD of
    the different-family similarities (same-model pairs only where mask is given)."""
    same = same_n = diff = diff_n = diff_sq = 0.0
    for h, row in enumerate(sim):
        family = held_families[h]
        keep = mask[h] if mask is not None else None
        for s, value in enumerate(row):
            if keep is not None and not keep[s]:
                continue
            if seen_families[s] == family:
                same += value
                same_n += 1
            else:
                diff += value
                diff_sq += value * value
                diff_n += 1
    if not same_n or diff_n < 2:
        return None
    var = (diff_sq - diff * diff / diff_n) / (diff_n - 1)
    return (same / same_n - diff / diff_n) / math.sqrt(var) if var > 0 else None


def _bootstrap_delta(held, seen, draws, label, level, delete=()):
    """The creator-bootstrap interval of the difference, drawn as catalogue rule R1 says (registry 2026-11-21 06:44 (4)):
    hold-out creators and seen creators drawn with replacement, apart; then, in every cell of each drawn creator, its
    recordings drawn with replacement (as many as the cell has); every drawn cell re-rarefied to H9_RAREFY_TOKENS tokens;
    TF-IDF, function-word z-scores, similarities and both contrasts computed again on the draw. CHOICE: the cell rules
    (2 recordings, 2,000 words) are not reapplied inside a draw, and the deleted words of the "100 most distinguishing
    words" row are those of the observed cells. Returns ((lo, hi), failed draws)."""
    stream = stats.rng(*label)
    encoder = _Encoder(held + seen)
    deleted = {encoder.content[token] for token in delete if token in encoder.content}
    hc, sc = sorted({c["creator"] for c in held}), sorted({c["creator"] for c in seen})
    held_by = {creator: [cell for cell in held if cell["creator"] == creator] for creator in hc}
    seen_by = {creator: [cell for cell in seen if cell["creator"] == creator] for creator in sc}
    stratified = any(cell["stratum"] is not None for cell in held + seen)
    values = []
    for _ in range(draws):
        drawn = {"held": [], "seen": []}
        for side, creators, by in (("held", hc, held_by), ("seen", sc, seen_by)):
            for _ in creators:
                for cell in by[creators[stream.randrange(len(creators))]]:
                    parts = cell["parts"]
                    drawn[side].append((cell, [parts[stream.randrange(len(parts))] for _ in parts]))
        counters = [_rarefied_counts(encoder, parts, K.H9_RAREFY_TOKENS, stream) for _, parts in drawn["held"] + drawn["seen"]]
        tfidf, norms, zs = _draw_vectors(encoder, counters, deleted)
        nh = len(drawn["held"])
        held_families = [cell["family"] for cell, _ in drawn["held"]]
        seen_families = [cell["family"] for cell, _ in drawn["seen"]]
        mask = ([[h["stratum"] == s["stratum"] for s, _ in drawn["seen"]] for h, _ in drawn["held"]] if stratified else None)
        sim = _content_similarities(tfidf[:nh], norms[:nh], tfidf[nh:], norms[nh:], encoder.n_content)
        content = _contrast(sim, held_families, seen_families, mask)
        function = _contrast([[math.sumprod(a, b) for b in zs[nh:]] for a in zs[:nh]], held_families, seen_families, mask)
        if content is not None and function is not None:
            values.append(content - function)
    return stats.percentile_interval(values, level), draws - len(values)


def distinct_labelings(labels):
    counts = {}
    for f in labels:
        counts[f] = counts.get(f, 0) + 1
    value = math.factorial(len(labels))
    for n in counts.values():
        value //= math.factorial(n)
    return value


def _comparable(cell_list):
    """(hold-out cells whose family has a seen cell of the same model, seen cells). Outside the model-stratified row
    every stratum is None, so this is "whose family has a seen cell"."""
    seen = [c for c in cell_list if c["group"] == "seen"]
    seen_keys = {(c["stratum"], c["family"]) for c in seen}
    held = [c for c in cell_list if c["group"] == "holdout" and (c["stratum"], c["family"]) in seen_keys]
    return held, seen


def eligible(bundle, title_source="final", opening_rule=True, specific=K.SPECIFIC_FAMILIES, families=None):
    cell_list = cells(bundle, title_source, opening_rule, specific, families)
    held, _ = _comparable(cell_list)
    creators = sorted({c["creator"] for c in held})
    labelings = distinct_labelings([c["family"] for c in held]) if held else 0
    reachable = labelings >= math.ceil(1 / (K.ALPHA / K.HOLM_M))
    out = common.eligibility(H, len(creators), None, {"holdout_cells": len(held), "seen_cells": sum(1 for c in cell_list if c["group"] == "seen"),
                                                      "distinct_labelings": min(labelings, 10 ** 12),
                                                      "reference_reaches_first_holm_step": reachable})
    out["determinable"] = out["determinable"] and reachable
    return out


def analyse(bundle, title_source="final", opening_rule=True, specific=K.SPECIFIC_FAMILIES, families=None, delete_top=False,
            label=("H9",), extras=True, draws=K.BOOTSTRAP_DRAWS, permutations=K.PERMUTATION_DRAWS):
    elig = eligible(bundle, title_source, opening_rule, specific, families)
    cell_list = cells(bundle, title_source, opening_rule, specific, families)
    held, seen = _comparable(cell_list)
    seen_fams = sorted({c["family"] for c in seen})
    out = {"hypothesis": H, "eligibility": elig, "holdout_cells": len(held), "seen_cells": len(seen), "version": "amended",
           "a10_replaces": list(A10_REPLACES)}
    reg_elig = dict(elig, minimum=K.REGISTERED_MIN_CREATORS[H], determinable=bool(elig.get("reference_reaches_first_holm_step")))
    if len(held) < 2 or len(seen) < 2:
        out.update({"determinable": False, "p": 1.0, "estimate": None, "creator_interval_90": (None, None),
                    "registered_version": common.version(H, "registered", False, 1.0, None, None, None, (None, None), reg_elig,
                                                         A10_REPLACES)})
        return out
    every = held + seen
    delete = distinguishing_words(every, K.H9_TOP_DISTINGUISHING) if delete_top else ()
    tfidf, zs = representations(every, label + ("rarefy",), delete)
    hi, si = list(range(len(held))), list(range(len(held), len(every)))
    seen_families = [c["family"] for c in seen]
    mask = None
    if any(c["stratum"] is not None for c in every):                    # the model-stratified row: same-model pairs only
        mask = [[h["stratum"] == s["stratum"] for s in seen] for h in held]
    content = Pairs(tfidf, hi, si, seen_families, seen_fams, mask)
    function = Pairs(zs, hi, si, seen_families, seen_fams, mask)
    labels = [c["family"] for c in held]
    observed = delta(content, function, labels)
    stream = stats.rng(*label, "perm")
    reference = []
    for _ in range(permutations):
        shuffled = labels[:]
        stream.shuffle(shuffled)
        value = delta(content, function, shuffled)
        if value is not None:
            reference.append(value)
    p = stats.permutation_p(observed, reference, "greater") if observed is not None else 1.0
    held_creators = [c["creator"] for c in held]
    seen_creators = [c["creator"] for c in seen]
    # registry 2026-11-21 06:44 (4): creators, then recordings within each creator's cells, every cell re-rarefied per draw
    (blo, bhi), failed = _bootstrap_delta(held, seen, draws, label + ("boot", "two-stage"), K.A5_LEVEL, delete)
    out.update({"determinable": elig["determinable"],
                "estimate": {"delta": observed, "content_contrast": content.contrast(labels), "function_contrast": function.contrast(labels),
                             "reference_mean": common.mean_or_none(reference)},
                "intervals": {"bootstrap_90": (blo, bhi), "bootstrap_failed_draws": failed, "bootstrap_draws": draws,
                              "bootstrap": "creators (hold-out and seen apart), then recordings within each cell, cells "
                                           "re-rarefied in every draw (R1; registry 2026-11-21 06:44 (4))"},
                "p": p, "p_method": f"label permutation, {permutations} draws", "alternative": "greater"})
    refuted = "the 90% interval of the difference lies at or below zero" if bhi is not None and bhi <= 0 else None
    out["conditions"] = {"registered": observed is not None and observed > 0, "a5": blo is not None and blo > 0, "effect_size": True,
                         "refuted": refuted}
    out["creator_interval_90"] = (blo, bhi)
    # A10 guard: before A10 H9 had no creator minimum; the reference, estimator and interval are the registered ones
    out["registered_version"] = common.version(H, "registered", reg_elig["determinable"], p, out["estimate"], out["intervals"],
                                               out["conditions"], (blo, bhi), reg_elig, A10_REPLACES, out["p_method"])
    out["tipping"] = {"dilution": tipping.dilution(observed or 0.0, blo, bhi, K.SESOI[H]),
                      "note": "random family labels shrink both contrasts; corrected interval if a share of hold-out labels were wrong"}
    if not extras:
        return out
    sec = {}
    loo = []
    for creator in sorted(set(held_creators) | set(seen_creators)):
        keep_h = [i for i, c in enumerate(held_creators) if c != creator]
        keep_s = [j for j, c in enumerate(seen_creators) if c != creator]
        if len(keep_h) < 2 or len(keep_s) < 2:
            continue
        sub_c = _subset(content, keep_h, keep_s, seen_families, seen_fams)
        sub_f = _subset(function, keep_h, keep_s, seen_families, seen_fams)
        value = delta(sub_c, sub_f, [labels[i] for i in keep_h])
        if value is not None:
            loo.append(value)
    sec["leave-one-creator-out range"] = (min(loo), max(loo)) if loo else None
    sec["mean content similarity, creators with two or more families"] = multi_family(every, tfidf)
    out["secondary"] = sec
    return out


def _subset(pairs, keep_h, keep_s, seen_families, families):
    new = Pairs.__new__(Pairs)
    new.sim = [[pairs.sim[h][s] for s in keep_s] for h in keep_h]
    mask = None if pairs.mask is None else [[pairs.mask[h][s] for s in keep_s] for h in keep_h]
    new._sums([seen_families[s] for s in keep_s], families, mask)
    return new


def multi_family(cell_list, vectors):
    """Named secondary (estimate only): for creators with two or more cells, similarity to their own other-family cells
    minus similarity to other creators' same-family cells."""
    by_creator = {}
    for i, cell in enumerate(cell_list):
        by_creator.setdefault(cell["creator"], []).append(i)
    diffs = []
    for creator in sorted(by_creator):
        own = by_creator[creator]
        if len(own) < 2:
            continue
        a = [_cosine(vectors[i], vectors[j]) for i in own for j in own if i < j and cell_list[i]["family"] != cell_list[j]["family"]]
        b = [_cosine(vectors[i], vectors[j]) for i in own for j in range(len(cell_list))
             if cell_list[j]["creator"] != creator and cell_list[j]["family"] == cell_list[i]["family"]]
        if a and b:
            diffs.append(sum(a) / len(a) - sum(b) / len(b))
    return {"creators": len(diffs), "mean": common.mean_or_none(diffs)}


def rows(sources=("final", "middle", "small")):
    out = [("primary", {}),
           ("without the title-and-opening agreement rule", {"opening_rule": False}),
           ("councils without a star name (S8) not specific", {"specific": tuple(f for f in K.SPECIFIC_FAMILIES if f != "S8")}),
           ("within one tradition: star peoples (ET)", {"families": K.ET_FAMILIES}),
           ("within one tradition: angels, masters, deities (AD)", {"families": K.AD_FAMILIES}),
           ("each family's 100 most distinguishing words deleted", {"delete_top": True})]
    for source in sources:
        if source != "final":
            out.append((f"titles: {source} model without adjudication", {"title_source": source}))
    return out
