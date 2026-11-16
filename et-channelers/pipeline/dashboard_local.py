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
<title>Collection · Channeling research archive</title>
<meta name="description" content="Follow the newest YouTube collection, its verified audio and metadata, and the historical research archive.">
<link rel="stylesheet" href="../../../assets/research-nav.css">
<script defer src="../../../assets/research-nav.js" data-page="collection"></script>
<style>
:root { color-scheme: light dark;
  --font-anthropic-sans: system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  --font-anthropic-serif: Georgia, "Times New Roman", serif;
  --color-bg: #f5f2eb; --color-panel: #fffdf8; --color-fg: #17211e; --color-fg-muted: #5d665f;
  --color-border-line: #d6d9ce; --color-ok: #1f554b; --color-warn: #805a1e; --color-bad: #a03d35;
  --cds-border: 1px solid #d9d7d0; --cds-chart-muted: #b9b7b0; --cds-chart-status-critical: #b23a3a;
  --cds-dur-slow: 320ms; --cds-ease-out: cubic-bezier(.2,.7,.3,1);
  --cds-font-size-body: 16px; --cds-font-size-caption: 13px; --cds-font-size-heading: 25px; --cds-font-size-title: 36px;
  --cds-font-weight-medium: 600; --cds-gap-xs: 4px; --cds-gap-sm: 8px; --cds-gap-md: 12px; --cds-gap-lg: 20px; --cds-gap-xl: 32px;
  --cds-pad-md: 14px; --cds-pad-lg: 24px; --cds-radius: 5px; --cds-shadow-popover: 0 6px 24px rgba(0,0,0,.12);
  --cds-surface-popover: #fffdf8; --cds-text-secondary: #5d665f; }
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
body { padding: 0 32px 64px; max-width: 1440px; margin: 0 auto; line-height: 1.55; }
* { box-sizing: border-box; }
a { color: var(--color-ok); text-underline-offset: 3px; }
:focus-visible { outline: 3px solid var(--color-ok); outline-offset: 4px; }
.cc-skip { position: absolute; top: -100px; left: 24px; z-index: 100; background: var(--color-panel); padding: 12px 18px; }
.cc-skip:focus { top: 8px; }
@media(max-width: 700px) { body { padding-inline: 16px; } }
table { border-collapse: collapse; } th, td { padding: 4px 8px; text-align: left; vertical-align: top; }
</style>
<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.9.0/d3.min.js"></script>
</head>
<body>
<a class="cc-skip" href="#collection-current">Skip to collection status</a>
<script>
(function () {
  const BASE = __BASE_JSON__;
  const NAMES = __NAMES_JSON__;
  const FILES = __FILES_JSON__;
  const store = {}; const calcs = []; const draws = new Map(); const listeners = []; let params = {};
  const colors = ['#1f554b', '#a16a30', '#597665', '#747793', '#a0564a', '#4d7c89', '#8a8051'];
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
    document.querySelectorAll('.cc-table tbody[data-draw]').forEach((body) => {
      if (body.children.length) return;
      const table = body.closest('table'); const state = store[table.dataset.source];
      if (!state || state.status === 'loading') return;
      const row = document.createElement('tr'); const cell = document.createElement('td');
      cell.colSpan = Math.max(1, table.querySelectorAll('thead tr:last-child th').length);
      cell.className = 'cc-empty'; cell.style.textAlign = 'left'; cell.style.whiteSpace = 'normal';
      cell.textContent = table.dataset.source === 'contacts' ? 'Contact details are not published in this view. Public source links are listed in Sources & links.' : state.status === 'ok' ? 'No rows match these filters. Try another search or clear the filters.' : 'This table is unavailable in the current snapshot.';
      row.append(cell); body.append(row);
    });
    listeners.forEach((cb) => { try { cb(); } catch (e) { console.error(e); } });
  }
  function schedule() { if (pending) return; pending = true; requestAnimationFrame(render); }
  async function load(name) {
    if (name === 'contacts' && BASE === '../../plan/') { store[name] = {status:'missing'}; return; }
    store[name] = { status: 'loading' };
    try { const r = await fetch(BASE + (FILES[name] || name) + '.csv', { cache: 'no-cache' }); if (!r.ok) throw new Error(r.status); store[name] = { status: 'ok', data: parseCSV(await r.text()) }; }
    catch (e) { store[name] = { status: 'missing', error: String(e) }; }
  }
  window.dash = {
    colors,
    calc(name, spec) { calcs.push({ name, spec }); schedule(); },
    draw(name, fn) { if (typeof fn === 'function') draws.set(name, fn); schedule(); },
    data(name) { return store[name] || { status: 'loading' }; },
    params() { return Object.assign({}, params); },
    setParams(p) { for (const k of Object.keys(p || {})) { if (p[k] === null || p[k] === undefined || p[k] === '') delete params[k]; else params[k] = p[k]; } schedule(); },
    onData(cb) { listeners.push(cb); schedule(); },
    setLink(h) { if (h) history.pushState(null, '', '#' + String(h).replace(/^#/, '')); },
  };
  NAMES.forEach((nm) => { store[nm] = { status: 'loading' }; });
  Promise.all(NAMES.map(load)).then(schedule);
  function put(id, value) { const el = document.getElementById(id); if (el) el.textContent = value; }
  function number(value) { return Number.isFinite(+value) ? (+value).toLocaleString('en-US') : '—'; }
  function date(value) { const d = new Date(value); return Number.isNaN(d.getTime()) ? 'Date unavailable' : new Intl.DateTimeFormat('en-US', {dateStyle:'medium', timeStyle:'short'}).format(d); }
  async function collectionStatus() {
    try {
      const response = await fetch(BASE + 'ingestion_status.json', {cache:'no-cache'});
      if (!response.ok) throw new Error('status unavailable');
      const data = await response.json();
      if (data.schema_version !== 1 || data.scope !== 'local_youtube_collection') throw new Error('unexpected status');
      const labels = {cooldown:'Waiting for Drive', paused:'Collection paused', ready:'Ready to resume', running:'Collecting audio', unknown:'Status not yet recorded'};
      const explanations = {cooldown:'Drive has temporarily limited requests. Downloaded files are retained for the next upload attempt.', paused:'Collection is paused. Completed audio and metadata remain available for a safe resume.', ready:'The last Drive retry window has passed. This snapshot does not confirm that a worker is running.', running:'Audio and metadata are being saved together. Local copies are released after Drive verification.', unknown:'Queue totals are available; a current worker state has not been recorded.'};
      const state = labels[data.operation.state] ? data.operation.state : 'unknown';
      if (data.operation.cooldown_provider === 'youtube') {
        labels.cooldown = 'Waiting for YouTube';
        explanations.cooldown = 'New YouTube downloads are paused after a source refusal. Completed audio and metadata can still be saved to Drive.';
      } else if (data.operation.cooldown_provider === 'both') {
        labels.cooldown = 'Waiting for YouTube and Drive';
        explanations.cooldown = 'Source downloads and Drive uploads are paused until their recorded retry windows pass. Local files are retained.';
      }
      if (state === 'cooldown' && data.operation.retry_after) explanations.cooldown += ' Next attempt after ' + date(data.operation.retry_after) + '.';
      put('cc-current-state', labels[state]); put('cc-current-explanation', explanations[state]);
      put('cc-current-date', date(data.generated_at)); put('cc-verified', number(data.counts.verified_pairs));
      put('cc-awaiting', number(data.counts.awaiting_upload)); put('cc-channels', number(data.counts.channels));
      put('cc-indexed', number(data.counts.indexed_total)); put('cc-workers', number(data.operation.workers));
      if (Number.isFinite(data.counts.caption_verified_videos)) {
        let captionSummary = number(data.counts.caption_verified_videos) + ' videos have English caption text verified on Drive (' + number(data.counts.caption_verified_tracks) + ' tracks). ' + number(data.counts.caption_pending_videos) + ' await caption completion; ' + number(data.counts.caption_none_english) + ' have no English track in the saved source inventory.';
        if (data.operation.caption_state === 'cooldown') captionSummary += ' Caption requests are waiting for YouTube' + (data.operation.caption_retry_after ? ' until ' + date(data.operation.caption_retry_after) : '') + '. Audio collection can continue independently.';
        else if (data.operation.caption_state === 'paused') captionSummary += ' Caption backfill is paused.';
        put('cc-captions-summary', captionSummary);
      }
      put('cc-final-policy', data.operation.full_archive_requested ? 'Full archive follows the newest-50 tier.' : 'Final-round downloads are not enabled in this snapshot.');
      put('cc-local-storage', (data.storage.local_bytes / 1e9).toFixed(2) + ' / ' + number(data.storage.ceiling_bytes / 1e9) + ' GB');
      const status = document.getElementById('cc-current-state'); if (status) status.dataset.state = state;
      const fill = document.getElementById('cc-storage-meter');
      if (fill) { fill.max = data.storage.ceiling_bytes; fill.value = data.storage.local_bytes; }
      const holder = document.getElementById('cc-stages');
      if (holder) { holder.replaceChildren(); for (const [i, stage] of data.stages.entries()) {
        const item = document.createElement('li'); item.className = 'cc-stage'; item.dataset.state = stage.state;
        const ordinal = document.createElement('span'); ordinal.className = 'cc-stage-order'; ordinal.textContent = String(i + 1).padStart(2, '0');
        const title = document.createElement('h3'); title.textContent = stage.label;
        const total = document.createElement('p'); total.className = 'cc-stage-total'; total.textContent = number(stage.total) + ' items';
        const caption = document.createElement('p'); caption.className = 'cc-stage-caption'; caption.textContent = stage.key === 'final_index' ? 'Indexed · final round stays on hold' : number(stage.verified) + ' verified pairs' + (stage.state === 'waiting' ? (stage.key === 'final_archive' ? ' · follows newest 50' : ' · follows newest 20') : '');
        if (stage.unavailable) caption.textContent += ' \u00b7 ' + number(stage.unavailable) + ' unavailable';
        item.append(ordinal, title, total, caption);
        if (stage.key !== 'final_index') { const progress = document.createElement('progress'); progress.max = Math.max(1, stage.total); progress.value = stage.verified; progress.setAttribute('aria-label', stage.label + ' verified pairs'); item.append(progress); }
        holder.append(item);
      } }
    } catch (_) { put('cc-current-state', 'Status unavailable'); put('cc-current-explanation', 'The latest collection snapshot could not be loaded. The historical archive tables remain available below.'); }
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', collectionStatus, {once:true}); else collectionStatus();
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
