"""Tests for dashboard_local.py (invented fragment, no network)."""
import json
import unittest

from pipeline import dashboard_local


FRAGMENT = (
    '<meta name="dash-one-writer">\n<style>.x{color:var(--color-fg)}</style>\n'
    '<div class="page"><b data-draw="g-people" data-source="totals" data-field="people" data-row="0">—</b></div>\n'
    "<script>dash.calc('totals', { inputs: ['targets'], fn: (t) => [{ people: t.length }] });</script>\n"
)


class BuildTests(unittest.TestCase):
    def test_wraps_fragment_in_a_page_with_a_host(self):
        html = dashboard_local.build(FRAGMENT, "../../plan/")
        self.assertTrue(html.startswith("<!doctype html>"))
        self.assertNotIn('dash-one-writer', html)
        self.assertIn("window.dash = {", html)
        self.assertIn('data-draw="g-people"', html)
        self.assertIn("dash.calc('totals'", html)
        self.assertIn(json.dumps("../../plan/"), html)
        self.assertIn('"bashar_channels": "bashar_host_channels"', html)
        for name in ("coverage", "sources", "targets", "contacts", "transcript_audio"):
            self.assertIn(json.dumps(name), html)
        self.assertEqual(html.count("<script"), 3)  # d3, the host, the fragment's own script
        self.assertIn('@media (prefers-color-scheme: dark)', html)
        self.assertIn(':root[data-theme="dark"]', html)
        self.assertTrue(html.rstrip().endswith("</html>"))

    def test_base_is_json_escaped(self):
        html = dashboard_local.build(FRAGMENT, "./da\"ta/")
        self.assertIn(json.dumps("./da\"ta/"), html)


if __name__ == "__main__":
    unittest.main()
