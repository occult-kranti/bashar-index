"""H9's token counts after registry 2026-11-21 11:08 (2) and (3), features-3: contractions whose parts are function words
count as those function words, the function-word test and the content key use the same form, and the names input holds
every token of every family variant. features-4 (registry 12:52 (3)): ain't and y'all split into function words too.
Synthetic strings only; the names below are invented."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from hypotheses import features as F  # noqa: E402


def words(text):
    return [{"t": word, "start": float(i), "end": i + 0.5} for i, word in enumerate(text.split())]


def counts(text, masked=frozenset(), formulas=frozenset(), families=None):
    return F.h9_counts(words(text), set(masked), set(formulas), families)


def parts(text):
    return [F.h9_parts(token) for token in F.tokens(text)]


class ContractionParts(unittest.TestCase):
    def test_contractions_of_function_words_split_into_them(self):
        cases = {"it's": ["it", "is"], "we're": ["we", "are"], "I'm": ["i", "am"], "you'll": ["you", "will"],
                 "they've": ["they", "have"], "she'd": ["she", "would"], "that's": ["that", "is"],
                 "there's": ["there", "is"], "don't": ["do", "not"], "doesn't": ["does", "not"],
                 "isn't": ["is", "not"], "weren't": ["were", "not"], "couldn't": ["could", "not"],
                 "can't": ["can", "not"], "won't": ["will", "not"], "I'd've": ["i", "would", "have"],
                 "shouldn't've": ["should", "not", "have"],
                 "ain't": ["is", "not"], "y'all": ["you", "all"], "y'all've": ["you", "all", "have"],      # features-4
                 "y'all'd": ["you", "all", "would"]}
        for text, expected in cases.items():
            self.assertEqual(parts(text), [expected], text)

    def test_curly_apostrophe_and_capitals_read_the_same(self):
        self.assertEqual(parts("It’s WE’RE Don’t"), [["it", "is"], ["we", "are"], ["do", "not"]])
        self.assertEqual(parts("Ain’t Y’ALL AIN'T Y'all"), [["is", "not"], ["you", "all"]] * 2)

    def test_other_apostrophe_tokens_are_one_form_without_apostrophes(self):
        cases = {"Zorbal's": "zorbals", "let's": "lets", "might've": "mightve", "o'clock": "oclock",
                 "creators'": "creators", "rock'n'roll": "rocknroll", "everything's": "everythings",
                 "shan't": "shant", "y'know": "yknow", "rain't": "raint", "ally'all": "allyall"}
        for text, expected in cases.items():
            self.assertEqual(parts(text), [[expected]], text)

    def test_a_token_without_an_apostrophe_is_itself(self):
        self.assertEqual(parts("light its were"), [["light"], ["its"], ["were"]])

    def test_every_split_part_is_a_function_word(self):
        hosts = [w for w in F.FUNCTION_WORDS if w.isalpha()]
        for host in hosts:
            for clitic in list(F.CLITICS) + ["n't", "x", ""]:
                token = host + "'" + clitic if clitic != "n't" else host + "n't"
                got = F.h9_parts(token)
                if len(got) > 1:
                    self.assertTrue(all(part in F.FUNCTION_WORDS for part in got), token)
                else:
                    self.assertEqual(got, [token.replace("'", "")], token)


class H9CountsFeatures3(unittest.TestCase):
    TEXT = "It's what we're here for. Don't you think? I'm sure you'll see the light, and they've shown it."

    def test_no_contraction_and_no_function_word_is_a_content_key(self):
        h9 = counts(self.TEXT)
        self.assertEqual(sorted(h9["content"]), ["light", "see", "shown", "sure", "think"])
        self.assertFalse(set(h9["content"]) & set(F.FUNCTION_WORDS))
        for plain in ("its", "were", "dont", "im", "youll", "theyve"):
            self.assertNotIn(plain, h9["content"])

    def test_contraction_parts_are_counted_as_function_words(self):
        function = counts(self.TEXT)["function"]
        for word, n in {"it": 2, "is": 1, "we": 1, "are": 1, "do": 1, "not": 1, "i": 1, "am": 1, "you": 2, "will": 1,
                        "they": 1, "have": 1, "what": 1, "here": 1, "for": 1, "the": 1, "and": 1}.items():
            self.assertEqual(function.get(word), n, word)
        self.assertTrue(all(word in F.FUNCTION_WORDS for word in function))

    def test_a_contraction_counts_as_its_full_form(self):
        contracted = counts("It's fine and we're done; don't stop, I'm here and you'll won't can't")
        full = counts("It is fine and we are done; do not stop, I am here and you will will not can not")
        self.assertEqual(contracted, full)

    def test_function_test_and_content_key_use_the_same_form(self):
        h9 = counts("the' its' were' The' ours'")      # stray apostrophes: the form without them is a function word
        self.assertEqual(h9["content"], {})
        self.assertEqual(h9["function"], {"the": 2, "its": 1, "were": 1, "ours": 1})

    def test_other_apostrophe_tokens_keep_one_content_key(self):
        h9 = counts("everything's changing, let's go, it ain't over")
        self.assertEqual(h9["content"], {"everythings": 1, "changing": 1, "lets": 1})
        self.assertEqual(h9["function"], {"it": 1, "is": 1, "not": 1, "over": 1})     # ain't: is + not (features-4)
        self.assertEqual(h9["other"], 1)                                 # "go": under three letters

    def test_mask_formula_and_length_rules_read_the_same_form(self):
        h9 = counts("Zorbal's zorbals zorbal light ox", masked={"zorbal"})
        self.assertEqual(h9["content"], {"zorbals": 1, "light": 1})    # "zorbal's" is masked by its host
        self.assertEqual(h9["other"], 3)                                 # zorbal's, zorbal, ox (under 3 letters)
        h9 = counts("Zorbal's light", masked={"zorbals"})
        self.assertEqual((h9["content"], h9["other"]), ({"light": 1}, 1))
        h9 = counts("we're the ones who came", formulas={("we're", "the", "ones", "who")})
        self.assertEqual(h9["content"], {"came": 1})
        self.assertEqual(h9["other"], 1)                                 # "ones" inside the formula
        self.assertEqual(h9["function"], {"we": 1, "are": 1, "the": 1, "who": 1})   # function words before the formula

    def test_the_opening_rule_is_unchanged(self):
        h9 = counts("I'm here. We are the Zorbal council of light", families={"S1": ["Zorbal Council"], "S2": ["Quex"]})
        self.assertEqual(h9["opening_family_match"], {"S1": True, "S2": False})

    def test_feature_version(self):
        self.assertEqual(F.FEATURE_VERSION, "features-4")


class AintAndYall(unittest.TestCase):
    """features-4 (registry 12:52 (3)): ain't and y'all are contractions of function words and count as them."""

    def test_they_count_as_their_full_forms_and_never_as_content(self):
        contracted = counts("Y'all ain't ready, and we ain't done; y’all’ve seen it")
        full = counts("You all is not ready, and we is not done; you all have seen it")
        self.assertEqual(contracted, full)
        self.assertEqual(sorted(contracted["content"]), ["done", "ready", "seen"])
        for plain in ("aint", "yall", "yallve"):
            self.assertNotIn(plain, contracted["content"])

    def test_the_host_mask_and_formula_rules_do_not_reach_a_split(self):
        h9 = counts("ain't y'all light today shine", masked={"ai", "y", "aint", "yall"},
                    formulas={("ain't", "y'all", "light", "today")})
        self.assertEqual(h9["content"], {"shine": 1})
        self.assertEqual(h9["function"], {"is": 1, "not": 1, "you": 1, "all": 1})   # function words before the formula
        self.assertEqual(h9["other"], 2)                                 # light, today: inside the formula

    def test_written_without_an_apostrophe_they_stay_one_form(self):
        h9 = counts("aint yall")                     # not contractions as written: the rule reads apostrophes only
        self.assertEqual(h9["content"], {"aint": 1, "yall": 1})


class ClosedListOfH4(unittest.TestCase):
    """Every contraction of prep.contractible_pairs (H4's closed list) that `tokens` keeps as one token with an apostrophe
    and whose full forms are all function words is split by h9_parts into function words, and the split is one of prep's
    readings. ('cause is not such a token: `tokens` drops a leading apostrophe.) prep is reached through features._prep,
    as features.py's command reaches it; the test is skipped where the private archive is absent. No transcript is
    opened: contractible_pairs is a closed list in code."""

    def test_every_function_word_contraction_of_the_closed_list_splits(self):
        try:
            prep = F._prep()
        except ImportError:
            self.skipTest("prep.py (private archive) is not on this machine")
        readings = {}
        for short, full in prep.contractible_pairs():
            if "'" in short and F.tokens(short) == [short] and all(word in F.FUNCTION_WORDS for word in full.split()):
                readings.setdefault(short, set()).add(full.replace(" ", ""))
        self.assertIn("ain't", readings)
        self.assertIn("y'all", readings)
        for short, fulls in readings.items():
            got = F.h9_parts(short)
            self.assertGreater(len(got), 1, short)
            self.assertTrue(all(part in F.FUNCTION_WORDS for part in got), short)
            self.assertIn("".join(got), fulls, short)                    # can't: "can" + "not" is prep's "cannot"
            self.assertEqual(counts(short)["content"], {}, short)


class NamesInput(unittest.TestCase):
    def test_union_of_list_forms_and_every_variant_token(self):
        families = {"S1": ["The Zorbal Council", "zorbals"], "G3": ["star-wanderers", "Quex’s Ring"], "X1": []}
        forms = F.h9_mask_forms(["veltharan", "zorbal"], families)
        self.assertEqual(forms, sorted({"veltharan", "zorbal", "the", "council", "zorbals", "star", "wanderers",
                                        "quexs", "ring"}))

    def test_every_variant_token_leaves_the_content(self):
        families = {"S1": ["The Zorbal Council"], "G3": ["star-wanderers", "Quex’s Ring"]}
        masked = set(F.h9_mask_forms([], families))
        h9 = counts("the zorbal council spoke of star wanderers and quex's ring today", masked=masked)
        self.assertEqual(h9["content"], {"spoke": 1, "today": 1})
        self.assertEqual(h9["function"].get("the"), 1)                   # a function-word token stays a function word


if __name__ == "__main__":
    unittest.main()
