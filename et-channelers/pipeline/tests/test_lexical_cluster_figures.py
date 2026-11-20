import itertools
import unittest

from pipeline import corpus_group_lexical as lexical, lexical_cluster_figures as figures


def fixture():
    groups = [dict(id=name, kind=kind, selected_recordings=3, observed_recordings=0 if name=="d" else 3,
                   top_terms=[] if name=="d" else [{"term":"fixture","weight":1}])
              for name,kind in [("a","creator"),("b","creator"),("c","creator"),("d","creator"),("e","claimed_entity")]]
    scores = {("a","b"):.8, ("a","c"):.99, ("b","c"):.6}
    pairs = []
    for a,b in itertools.combinations([g["id"] for g in groups], 2):
        overlap = (a,b) == ("a","c")
        pairs.append(dict(left=a,right=b,cosine=scores.get((a,b)), shared_text_units=int(overlap),
                          shared_reviewed_family_or_singleton_units=int(overlap),overlap_is_not_independent=overlap))
    return {"method":lexical.METHOD, "groups":groups, "cosine_overlap":pairs}


class LexicalFigureTests(unittest.TestCase):
    def test_shared_editions_and_unassessed_creators_do_not_join_clusters(self):
        pairs, curves = figures.summarize(fixture(), [.9,.5,.75,.75])
        self.assertEqual(len(pairs), 6)
        self.assertTrue(all(p["kind"]=="creator" for p in pairs))
        marked = {(p["left"],p["right"]):p["comparison"] for p in pairs}
        self.assertEqual(marked["a","c"], "shared source")
        self.assertEqual(marked["a","d"], "no lexical evidence")
        creators = [r for r in curves if r["kind"]=="creator"]
        self.assertEqual([r["threshold"] for r in creators], [.5,.75,.9])
        self.assertEqual([r["largest_component"] for r in creators], [3,2,1])
        self.assertEqual([r["edges"] for r in creators], [2,1,0])
        self.assertEqual([r["isolated_groups"] for r in creators], [0,1,3])
        self.assertTrue(all(r["eligible_groups"]==3 and r["unassessed_groups"]==1 and r["compared_pairs"]==2 for r in creators))

    def test_checks_full_matrix_and_reports_zero_evidence_as_missing(self):
        source = fixture()
        source["cosine_overlap"].pop(0)
        with self.assertRaisesRegex(ValueError, "incomplete"):
            figures.summarize(source,[.5])
        source = {"method":lexical.METHOD, "groups":[dict(id="empty",kind="creator",selected_recordings=2,
                  observed_recordings=0,top_terms=[])],"cosine_overlap":[]}
        _, series = figures.summarize(source,[.5])
        self.assertIsNone(series[0]["largest_component_share"])
        with self.assertRaisesRegex(ValueError, "thresholds"):
            figures.summarize(source,[float("nan")])
        source = fixture()
        source["cosine_overlap"][0]["overlap_is_not_independent"] = True
        with self.assertRaisesRegex(ValueError, "Shared source"):
            figures.summarize(source,[.5])


if __name__=="__main__":
    unittest.main()
