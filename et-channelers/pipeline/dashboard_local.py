#!/usr/bin/env python3
"""Build a stand-alone copy of the collection dashboard that reads the tables from plan/*.csv.

The dashboard on claude.ai is a "Data" artifact: its page (dashboard/collection/page.fragment.html, saved from the
artifact's files/index.html document) is a fragment that expects a host object `dash` with the datasets. This script
wraps the fragment in a page of its own with a small `dash` of the same shape, reading each dataset from a CSV file
next to the repository's plan/ folder, so the dashboard works without claude.ai: on GitHub Pages, from any static
server (python3 -m http.server in the repository root), or in a private folder with the private tables beside it.

    python3 pipeline/dashboard_local.py --fragment dashboard/collection/page.fragment.html \
        --out dashboard/collection/index.html --base ../../plan/

The private contacts table is not in the repository; the public copy shows a dash for it. A private copy can pass
--base <folder>/ that holds contacts.csv as well.
"""
from __future__ import annotations

import argparse
import pathlib
import re

DATASETS = [
    "bashar_channels", "bashar_host_channels", "bashar_podcasts", "bashar_recordings", "bashar_sessions",
    "channel_inventory", "contacts", "coverage", "keywords_newest10", "keywords_newest20", "keywords_newest50",
    "methods", "prediction_counts", "prediction_samples", "prediction_timeline_counts", "sources", "targets",
    "theme_blackouts", "theme_blackouts_newest10", "transcript_audio",
]

# A dataset whose file carries another name than the dataset: the artifact's "bashar_channels" is plan/bashar_host_channels.csv.
FILES = {"bashar_channels": "bashar_host_channels"}

HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Collection dashboard</title>
<meta name="description" content="What the ET-channelers archive holds, read from the repository's tables: a local copy of the claude.ai dashboard.">
<style>
:root { color-scheme: light dark;
  --font-anthropic-sans: system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  --font-anthropic-serif: Georgia, "Times New Roman", serif;
  --color-bg: #f7f6f2; --color-panel: #ffffff; --color-fg: #1b1b1a; --color-fg-muted: #5f5e5a;
  --color-border-line: #d9d7d0; --color-ok: #2f7d4f; --color-warn: #a86a00; --color-bad: #b23a3a;
  --cds-border: 1px solid #d9d7d0; --cds-chart-muted: #b9b7b0; --cds-chart-status-critical: #b23a3a;
  --cds-dur-slow: 320ms; --cds-ease-out: cubic-bezier(.2,.7,.3,1);
  --cds-font-size-body: 15px; --cds-font-size-caption: 13px; --cds-font-size-heading: 20px; --cds-font-size-title: 30px;
  --cds-font-weight-medium: 600; --cds-gap-xs: 4px; --cds-gap-sm: 8px; --cds-gap-md: 12px; --cds-gap-lg: 20px; --cds-gap-xl: 32px;
  --cds-pad-md: 12px; --cds-pad-lg: 20px; --cds-radius: 10px; --cds-shadow-popover: 0 6px 24px rgba(0,0,0,.12);
  --cds-surface-popover: #ffffff; --cds-text-secondary: #5f5e5a; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
  --color-bg: #15161a; --color-panel: #1e2026; --color-fg: #ececea; --color-fg-muted: #a7a7a2;
  --color-border-line: #33363d; --color-ok: #6dc38f; --color-warn: #e0a84a; --color-bad: #e07070;
  --cds-border: 1px solid #33363d; --cds-chart-muted: #5c5f67; --cds-shadow-popover: 0 6px 24px rgba(0,0,0,.5);
  --cds-surface-popover: #1e2026; --cds-text-secondary: #a7a7a2; } }
:root[data-theme="dark"] {
  --color-bg: #15161a; --color-panel: #1e2026; --color-fg: #ececea; --color-fg-muted: #a7a7a2;
  --color-border-line: #33363d; --color-ok: #6dc38f; --color-warn: #e0a84a; --color-bad: #e07070;
  --cds-border: 1px solid #33363d; --cds-chart-muted: #5c5f67; --cds-shadow-popover: 0 6px 24px rgba(0,0,0,.5);
  --cds-surface-popover: #1e2026; --cds-text-secondary: #a7a7a2; }
html, body { margin: 0; background: var(--color-bg); color: var(--color-fg); font-family: var(--font-anthropic-sans); }
body { padding: 24px 16px 48px; max-width: 1240px; margin: 0 auto; }
.local-note { font-size: var(--cds-font-size-caption); color: var(--color-fg-muted); border: var(--cds-border); border-radius: var(--cds-radius); padding: 8px 12px; margin: 0 0 16px; }
.local-note b { color: var(--color-fg); }
table { border-collapse: collapse; } th, td { padding: 4px 8px; text-align: left; vertical-align: top; }
</style>
<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.9.0/d3.min.js"></script>
</head>
<body>
<p class="local-note"><b>Local copy.</b> This page reads the tables from <code>plan/*.csv</code> of the repository (base <code>__BASE__</code>); the live dashboard on claude.ai is the same page over the same tables. Private tables (the contacts) are not in the repository, so their sections show a dash here. Fetching from a file:// address is blocked by most browsers: open it from a static server or GitHub Pages.</p>
<script>
(function () {
  const BASE = __BASE_JSON__;
  const NAMES = __NAMES_JSON__;
  const FILES = __FILES_JSON__;
  const store = {}; const calcs = []; const draws = new Map(); const listeners = []; let params = {};
  const colors = ['#2f6db5', '#c6692a', '#3b8c5a', '#8459a8', '#b03a5b', '#2a8f99', '#8a7a2f'];
  function parseCSV(text) {
    const rows = []; let row = []; let field = ''; let q = false; let i = 0; const n = text.length;
    while (i < n) { const c = text[i];
      if (q) { if (c === '"') { if (text[i + 1] === '"') { field += '"'; i += 2; continue; } q = false; i++; continue; } field += c; i++; continue; }
      if (c === '"') { q = true; i++; continue; }
      if (c === ',') { row.push(field); field = ''; i++; continue; }
      if (c === '\\r') { i++; continue; }
      if (c === '\\n') { row.push(field); rows.push(row); row = []; field = ''; i++; continue; }
      field += c; i++; }
    if (field.length || row.length) { row.push(field); rows.push(row); }
    if (!rows.length) return [];
    const head = rows[0]; const out = [];
    for (let r = 1; r < rows.length; r++) { if (rows[r].length === 1 && rows[r][0] === '') continue; const o = {}; head.forEach((h, k) => { o[h] = rows[r][k] ?? ''; }); out.push(o); }
    return out;
  }
  const fmt = (v) => { if (v === null || v === undefined || v === '') return '—'; const x = +v; return Number.isFinite(x) && String(v).trim() !== '' ? x.toLocaleString('en-US') : String(v); };
  let pending = false;
  function compute() {
    for (let pass = 0; pass < 6; pass++) {
      for (const c of calcs) {
        const ins = c.spec.inputs.map((nm) => store[nm]);
        if (ins.every((t) => t && t.status === 'ok')) {
          try { store[c.name] = { status: 'ok', data: c.spec.fn(...ins.map((t) => t.data)) }; }
          catch (e) { store[c.name] = { status: 'error', error: String(e) }; console.error('calc ' + c.name, e); }
        } else if (!store[c.name] || store[c.name].status !== 'ok') {
          store[c.name] = { status: ins.some((t) => t && t.status === 'error') ? 'error' : (ins.some((t) => !t || t.status === 'loading') ? 'loading' : 'missing') };
        }
      }
    }
  }
  function render() {
    pending = false; compute();
    for (const [name, fn] of draws) {
      document.querySelectorAll('[data-draw="' + CSS.escape(name) + '"]').forEach((el) => { try { fn(el); } catch (e) { console.error('draw ' + name, e); } });
    }
    document.querySelectorAll('[data-draw][data-source]').forEach((el) => {
      if (draws.has(el.dataset.draw)) return;
      const t = store[el.dataset.source]; const rows = t && t.status === 'ok' && Array.isArray(t.data) ? t.data : null;
      const row = rows ? rows[+(el.dataset.row || 0)] : null;
      el.textContent = row ? fmt(row[el.dataset.field]) : '—';
    });
    listeners.forEach((cb) => { try { cb(); } catch (e) { console.error(e); } });
  }
  function schedule() { if (pending) return; pending = true; requestAnimationFrame(render); }
  async function load(name) {
    store[name] = { status: 'loading' };
    try { const r = await fetch(BASE + (FILES[name] || name) + '.csv', { cache: 'no-cache' }); if (!r.ok) throw new Error(r.status); store[name] = { status: 'ok', data: parseCSV(await r.text()) }; }
    catch (e) { store[name] = { status: 'missing', error: String(e) }; }
  }
  window.dash = {
    colors,
    calc(name, spec) { calcs.push({ name, spec }); schedule(); },
    draw(name, fn) { draws.set(name, fn); schedule(); },
    data(name) { return store[name] || { status: 'loading' }; },
    params() { return Object.assign({}, params); },
    setParams(p) { for (const k of Object.keys(p || {})) { if (p[k] === null || p[k] === undefined || p[k] === '') delete params[k]; else params[k] = p[k]; } schedule(); },
    onData(cb) { listeners.push(cb); schedule(); },
    setLink(h) { if (h) location.hash = String(h).replace(/^#/, ''); },
  };
  NAMES.forEach((nm) => { store[nm] = { status: 'loading' }; });
  Promise.all(NAMES.map(load)).then(schedule);
})();
</script>
"""

FOOT = "\n</body>\n</html>\n"


def build(fragment: str, base: str) -> str:
    import json
    head = HEAD.replace("__BASE__", base).replace("__BASE_JSON__", json.dumps(base)).replace("__NAMES_JSON__", json.dumps(DATASETS)).replace("__FILES_JSON__", json.dumps(FILES))
    frag = re.sub(r'<meta name="dash-one-writer">\s*', "", fragment, count=1)
    return head + frag + FOOT


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--fragment", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--base", default="../../plan/")
    a = ap.parse_args()
    fragment = pathlib.Path(a.fragment).read_text(encoding="utf-8")
    html = build(fragment, a.base)
    pathlib.Path(a.out).write_text(html, encoding="utf-8")
    print(f"wrote {a.out} ({len(html.encode('utf-8'))} bytes, base {a.base}, {len(DATASETS)} datasets)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
