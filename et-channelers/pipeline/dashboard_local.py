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
      const labels = {cooldown:'Waiting for Drive', paused:'Collection paused', ready:'Ready at saved checkpoint', running:'Running at saved checkpoint', unknown:'Status not yet recorded'};
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
      if (state === 'paused' && data.operation.cooldown_provider === 'youtube' && data.operation.retry_after) explanations.paused += ' The recorded source retry window ends ' + date(data.operation.retry_after) + '; this does not resume collection automatically.';
      const supportedNative = Number.isFinite(data.counts.supported_native_verified_videos) ? data.counts.supported_native_verified_videos : 0;
      put('cc-current-state', labels[state]);
      const nativeReady = data.native_lane?.state === 'ready';
      let explanation = nativeReady ? 'The last owned native run is terminal and its allocation is released. The native lane is ready for a separately admitted batch; no worker is confirmed running.' : explanations[state];
      const snapshotAge = (Date.now() - new Date(data.generated_at).getTime()) / 60000;
      if (state === 'running') explanation = 'The owned native process was confirmed running when this snapshot was saved. ' + (data.native_lane?.asr_handoff_enabled === false ? 'This batch does not hand audio to ASR. ' : '') + 'This page does not poll the worker.';
      if (data.native_lane?.kind === 'native_v4_source_hold') explanation = 'Native YouTube acquisition is held ' + (data.native_lane.reason === 'repeated_bound_403' ? 'after repeated HTTP 403 responses. ' : 'by its current source controls. ') + 'Saved recordings remain available. Further acquisition needs a reviewed source recovery; transcription is tracked separately.';
      if (data.native_lane?.kind === 'native_v5_source_hold') explanation = data.native_lane.reason === 'worker_startup' ? 'The native batch is paused after a local worker startup failure. This is an administrative pause; no new completed audio is credited. Saved recordings remain available while the startup fix is prepared.' : 'The native batch is held by its current source controls. Saved recordings remain available; no automatic retry is scheduled.';
      if (data.native_lane?.kind === 'native_v5_bulk' && data.native_lane.reason === 'worker_diagnostics_missing') explanation = 'A download worker ended without saving its final diagnostics. The batch is paused for a reviewed continuation. Completed audio and metadata remain verified on Drive; this diagnostic failure does not establish a new source rate limit.';
      if (snapshotAge >= 10) explanation += ' This checkpoint is ' + Math.floor(snapshotAge) + ' minutes old; present worker state needs a fresh snapshot.';
      if (supportedNative > 0) explanation += ' ' + number(supportedNative) + ' native-format recordings from the browser-assisted route have paired metadata verified on Drive.';
      put('cc-current-explanation', explanation);
      const legacy = data.legacy_operation;
      put('cc-legacy-summary', legacy ? 'Legacy collector: ' + (labels[legacy.state] || 'state unconfirmed').toLowerCase() + (legacy.retry_after ? '; its recorded retry window ends ' + date(legacy.retry_after) : '') + '. Its preserved controls are separate from the native batch lane.' : '');
      put('cc-current-date', date(data.generated_at)); put('cc-verified', number(data.counts.audio_archived_videos ?? data.counts.verified_pairs));
      put('cc-awaiting', number(data.counts.awaiting_upload)); put('cc-channels', number(data.counts.channels));
      put('cc-indexed', number(data.counts.indexed_total)); put('cc-workers', number(data.operation.workers));
      if (Number.isFinite(data.counts.caption_verified_videos)) {
        const captionAvailable = data.counts.caption_text_available_videos;
        let captionSummary = Number.isFinite(captionAvailable) ? number(captionAvailable) + ' audio items have English caption text verified on Drive. ' : '';
        captionSummary += number(data.counts.caption_verified_videos) + ' caption inventories are complete (' + number(data.counts.caption_verified_tracks) + ' verified tracks overall). ';
        if (Number.isFinite(data.counts.caption_inventory_review_videos)) captionSummary += number(data.counts.caption_inventory_review_videos) + ' items with saved captions still need inventory review. ';
        captionSummary += number(data.counts.caption_pending_videos) + ' await caption completion; ' + number(data.counts.caption_none_english) + ' have no English track in the saved source inventory.';
        if (data.operation.caption_state === 'cooldown') captionSummary += ' Caption requests are waiting for YouTube' + (data.operation.caption_retry_after ? ' until ' + date(data.operation.caption_retry_after) : '') + '. Audio collection can continue independently.';
        else if (data.operation.caption_state === 'paused') captionSummary += ' Caption backfill is paused.';
        put('cc-captions-summary', captionSummary);
      }
      put('cc-final-policy', data.operation.full_archive_requested ? 'Full archive follows the newest-50 tier.' : 'Final-round downloads are not enabled in this snapshot.');
      if (Number.isFinite(data.counts.asr_verified_videos)) {
        const asrStates = {running:'GPU transcription was reported running.', complete:'The latest GPU batch reported completion.', stopped_error:'The GPU batch stopped for review.', paused:'GPU transcription is paused.', stopping:'A stop has been requested for GPU transcription.'};
        const reported = asrStates[data.operation.asr_last_reported_state];
        const textSummary = Number.isFinite(data.counts.text_available_videos)
          ? number(data.counts.text_available_videos) + ' audio items have saved text; ' + number(data.counts.text_missing_videos) + ' have no saved text. ' + number(data.counts.text_inventory_complete_videos) + ' meet text-inventory completion checks. '
          : number(data.counts.text_artifact_videos) + ' audio items meet text-inventory completion checks; ' + number(data.counts.text_pending_videos) + ' remain under review. Separate text availability was not recorded in this snapshot. ';
        put('cc-asr-summary', number(data.counts.asr_verified_videos) + ' videos have generated ASR bundles verified on Drive. ' + textSummary + 'Generated ASR accuracy is unreviewed. Saved text does not establish coverage of every spoken word. ' + number(data.counts.verified_pairs) + ' native audio pairs; ' + number(data.counts.browser_recorded_videos ?? 0) + ' re-encoded browser recordings.' + (reported ? ' ' + reported + ' Reported ' + date(data.operation.asr_reported_at) + '.' : ''));
      }
      if (Number.isFinite(data.counts.publisher_text_target_videos) && Number.isFinite(data.counts.publisher_audio_variant_target_videos)) {
        let publisherSummary = number(data.counts.publisher_text_target_videos) + ' latest-20 videos have publisher-written companions; ';
        if (Number.isFinite(data.counts.publisher_transcript_target_videos)) publisherSummary += number(data.counts.publisher_transcript_target_videos) + ' have publisher transcripts; ';
        publisherSummary += number(data.counts.publisher_audio_variant_target_videos) + ' have publisher podcast audio variants. ';
        if (data.counts.publisher_audio_qualified_variant_target_videos > 0) publisherSummary += number(data.counts.publisher_audio_qualified_variant_target_videos) + ' source associations remain qualified. ';
        if (Number.isFinite(data.counts.publisher_variant_asr_target_videos)) publisherSummary += number(data.counts.publisher_variant_asr_target_videos) + ' podcast editions have ASR verified on Drive. ';
        if (Number.isFinite(data.counts.publisher_mirror_asr_target_videos)) publisherSummary += number(data.counts.publisher_mirror_asr_target_videos) + ' mirror editions have ASR or original/English translation bundles verified on Drive. ';
        if (data.counts.publisher_standalone_timed_text_target_videos > 0) publisherSummary += number(data.counts.publisher_standalone_timed_text_target_videos) + ' entries have separate publisher timed text; its audio edition and manual/automatic origin are unverified. ';
        put('cc-publisher-summary', publisherSummary + 'Publisher transcripts can be untimed and editions can differ from YouTube; native-audio progress is shown above.');
      }
      if (data.browser_support?.state === 'verified_local') {
        put('cc-browser-summary', 'Project Chromium: ' + data.browser_support.name + ' ' + data.browser_support.version + ' installed. Local filtering and downloader coexistence passed ' + date(data.browser_support.tested_at) + '. Full-file source transfer has separate acceptance checks.');
      }
      if (Number.isFinite(data.counts.publisher_mirror_audio_target_videos) && Number.isFinite(data.counts.publisher_mirror_caption_target_videos)) {
        put('cc-mirror-audio', number(data.counts.publisher_mirror_audio_target_videos));
        put('cc-mirror-captions', number(data.counts.publisher_mirror_caption_target_videos));
        const mirrors = document.getElementById('cc-mirrors'); if (mirrors) mirrors.hidden = false;
        if (Number.isFinite(data.counts.source_audio_available_target_videos)) {
          put('cc-source-coverage', number(data.counts.source_audio_available_target_videos) + ' latest-20 entries have verified audio from at least one source; ' + number(data.counts.source_audio_with_text_target_videos) + ' have a verified audio edition with saved text. Counts deduplicate entries across native and publisher sources; publisher edits may differ.');
        }
      }
      const used = data.storage.managed_bytes ?? data.storage.local_bytes;
      const cap = data.storage.managed_ceiling_bytes ?? data.storage.ceiling_bytes;
      put('cc-local-storage', (used / 1e9).toFixed(2) + ' / ' + number(cap / 1e9) + ' GB' + (Number.isFinite(data.storage.managed_bytes) ? ' including tools and models' : ''));
      const status = document.getElementById('cc-current-state'); if (status) status.dataset.state = state;
      const fill = document.getElementById('cc-storage-meter');
      if (fill) { fill.max = cap; fill.value = used; }
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
  async function collectionEta() {
    const hours = (values) => Array.isArray(values) && values.length === 2 && values.every(v => Number.isFinite(v) && v >= 0) ? values.map(v => v.toFixed(1)).join('–') : 'Unknown';
    try {
      const response = await fetch(BASE + 'collection_eta.json', {cache:'no-cache'});
      if (!response.ok) throw new Error('estimate unavailable');
      const data = await response.json();
      if (data.schema_version !== 2 || data.scope !== 'collection_eta' || !data.current) throw new Error('unexpected estimate');
      const current = data.current, next = current.next_recovery_batch, first = current.untouched_first_pass, service = current.measured_service;
      const nextMinutes = next.planning_active_hours?.map(v => v * 60);
      put('cc-eta-next-value', next.items === 0 ? 'Selected plan terminal' : Array.isArray(nextMinutes) && nextMinutes.every(Number.isFinite) ? nextMinutes.map(v => Math.round(v)).join('–') + ' active min' : 'Unknown');
      let recoveryScope = number(next.items) + ' items remain in the ' + number(next.selected_items ?? next.items) + '-item recovery plan. ';
      if (next.completed_decisions > 0) recoveryScope += number(next.completed_decisions) + ' decisions completed: ' + number(next.completed_verified_pairs) + ' verified, ' + number(next.completed_held_items) + ' held. ';
      recoveryScope += next.state === 'running' ? 'Owned batch confirmed running at the saved checkpoint.' : ['terminal_with_holds', 'complete'].includes(next.state) ? 'The selected recovery plan is terminal; held items need separate review.' : 'Remaining frames need separate admission; no worker is confirmed running by this ETA checkpoint.';
      put('cc-eta-next-scope', recoveryScope);
      put('cc-eta-first-value', hours(first.planning_active_hours) + ' active h');
      let firstScope = number(first.items) + ' decisions remain from the ' + number(first.selected_items ?? first.items) + '-item frozen selection / ' + number(first.frames) + ' frames. ';
      firstScope += first.state === 'running_admitted_cohort' ? number(first.current_cohort_items) + '-item cohort running at the checkpoint; ' + number(first.later_prepared_items) + ' later items remain prepared and disabled. ' : first.state === 'held_native_source' ? 'Native acquisition is held after source refusals. This service-time scenario is not a scheduled finish; ' + number(first.later_prepared_items) + ' later candidates remain prepared. ' : 'Campaign is prepared; running is not confirmed by this checkpoint. ';
      put('cc-eta-first-scope', firstScope + 'This estimates a first pass, including holds and failures.');
      put('cc-eta-calendar', 'At 50% availability, the untouched first pass would take ' + hours(first.calendar_hours_at_half_availability) + ' calendar hours, plus admission delays.');
      put('cc-eta-evidence', number(service.first_pass_decisions) + ' decisions in ' + (service.elapsed_seconds / 60).toFixed(1) + ' minutes; ' + number(service.verified_native_pairs) + ' verified pairs (' + Math.round(service.immediate_success_fraction * 100) + '% immediate success). Includes startup, source requests, upload and backpressure. The range assumes 1–2× that service time; item mix may differ.');
      const c = current.coverage;
      put('cc-eta-coverage', number(c.source_audio_available_target_videos) + ' / ' + number(current.newest20_items) + ' latest-20 entries have verified audio from any source; ' + number(c.source_audio_with_text_target_videos) + ' have an audio edition with saved text. ' + number(c.verified_pairs) + ' native pairs and ' + number(c.asr_verified_videos) + ' native ASR bundles.');
      put('cc-eta-date', date(current.generated_at));
      put('cc-eta-basis-date', date(service.ended_at));
      const generated = new Date(current.status_snapshot_at).getTime();
      const age = Number.isFinite(generated) ? Math.max(0, (Date.now() - generated) / 3600000) : null;
      put('cc-eta-freshness', age === null ? 'Coverage checkpoint date unavailable.' : 'Coverage checkpoint ' + date(current.status_snapshot_at) + (age >= 1 ? ' · ' + Math.floor(age) + ' hours old; refresh before using it as current queue state.' : '.'));
    } catch (_) {
      put('cc-eta-next-value', 'Unavailable'); put('cc-eta-first-value', 'Unavailable');
      put('cc-eta-next-scope', 'No current recovery estimate is available.');
      put('cc-eta-first-scope', 'No current first-pass estimate is available.');
      put('cc-eta-coverage', 'Estimate coverage is unavailable; collection counts are shown separately above.');
      put('cc-eta-date', 'unavailable'); put('cc-eta-basis-date', 'unavailable');
      put('cc-eta-evidence', 'The saved ETA could not be loaded. No finish date is inferred from historical transfer assumptions.');
      put('cc-eta-freshness', 'Estimate checkpoint unavailable.');
    }
  }
  async function collectionCoverage() {
    const body = document.getElementById('cc-coverage-body');
    if (!body) return;
    const search = document.getElementById('cc-coverage-search'), filter = document.getElementById('cc-coverage-filter');
    const headers = [...document.querySelectorAll('[data-coverage-key]')];
    try {
      const response = await fetch(BASE + 'channel_download_coverage.json', {cache:'no-cache'});
      if (!response.ok) throw new Error('coverage unavailable');
      const data = await response.json();
      if (data.schema_version !== 1 || data.scope !== 'newest20_receipt_coverage' || !Array.isArray(data.channels)) throw new Error('unexpected coverage');
      const numeric = ['target','youtube_audio','publisher_only_audio','audio_total','with_saved_text','remaining_audio'];
      if (!data.channels.every(row => typeof row.channel === 'string' && numeric.every(key => Number.isInteger(row[key]) && row[key] >= 0) && row.target <= 20 && row.youtube_audio + row.publisher_only_audio === row.audio_total && row.audio_total + row.remaining_audio === row.target && row.with_saved_text <= row.audio_total)) throw new Error('invalid channel counts');
      const stages = ['saved','downloading','processing','awaiting_upload','queued','other_pending'];
      const activity = data.activity;
      const byChannel = new Map((Array.isArray(activity?.channels) ? activity.channels : []).map(row => [row.channel_dir, row]));
      const activityValid = activity?.schema_version === 1 && byChannel.size === data.channels.length && data.channels.every(row => {
        const current = byChannel.get(row.channel_dir);
        return current && stages.every(field => Number.isInteger(current[field]) && current[field] >= 0) && current.saved === row.audio_total && current.target === row.target && stages.reduce((total, field) => total + current[field], 0) === row.target;
      });
      const channels = data.channels.map(row => {
        const current = activityValid ? byChannel.get(row.channel_dir) : null;
        return {...row, active: current ? current.downloading + current.processing + current.awaiting_upload : -1, queued: current ? current.queued : -1, activity: current};
      });
      let key = 'channel', ascending = true;
      const addCell = (tr, value, name = false) => { const cell = document.createElement('td'); cell.textContent = String(value); if (name) cell.className = 'cc-left cc-coverage-name'; tr.append(cell); return cell; };
      function render() {
        const query = search.value.trim().toLocaleLowerCase();
        const rows = channels.filter(row => row.channel.toLocaleLowerCase().includes(query) && (filter.value === 'active' ? row.active > 0 : filter.value === 'audio' ? row.remaining_audio > 0 : filter.value === 'text' ? row.audio_total > row.with_saved_text : true));
        rows.sort((a,b) => (typeof a[key] === 'string' ? a[key].localeCompare(b[key]) : a[key] - b[key]) * (ascending ? 1 : -1));
        body.replaceChildren();
        for (const row of rows) {
          const tr = document.createElement('tr');
          addCell(tr, row.channel, true); addCell(tr, row.audio_total + ' / ' + row.target);
          const activeCell = addCell(tr, row.active < 0 ? '\u2014' : row.active);
          if (row.activity) activeCell.setAttribute('aria-label', row.active + ' in progress: ' + row.activity.downloading + ' downloading, ' + row.activity.processing + ' preparing or validating, ' + row.activity.awaiting_upload + ' awaiting upload');
          addCell(tr, row.queued < 0 ? '\u2014' : row.queued);
          for (const field of ['youtube_audio','publisher_only_audio','with_saved_text','remaining_audio']) addCell(tr, row[field]);
          body.append(tr);
        }
        if (!rows.length) { const tr = document.createElement('tr'), td = document.createElement('td'); td.colSpan = 8; td.className = 'cc-left'; td.textContent = 'No channels match these filters.'; tr.append(td); body.append(tr); }
        for (const header of headers) header.setAttribute('aria-sort', header.dataset.coverageKey === key ? (ascending ? 'ascending' : 'descending') : 'none');
        put('cc-coverage-shown', rows.length + ' of ' + data.channels.length + ' channels shown.');
      }
      search.addEventListener('input', render); filter.addEventListener('change', render);
      for (const header of headers) header.querySelector('button').addEventListener('click', () => { const next = header.dataset.coverageKey; ascending = key === next ? !ascending : next === 'channel'; key = next; render(); });
      const totals = data.summary;
      put('cc-coverage-summary', number(totals.audio_available) + ' / ' + number(totals.latest20_target) + ' entries have saved audio: ' + number(totals.youtube_native_audio) + ' YouTube originals and ' + number(totals.publisher_only_audio) + ' additional publisher editions. ' + number(totals.audio_with_saved_text) + ' have an audio edition with saved captions or a transcript.');
      const activityTotals = activityValid ? stages.reduce((result, field) => ({...result, [field]: channels.reduce((total, row) => total + row.activity[field], 0)}), {}) : null;
      put('cc-coverage-activity', activityTotals ? 'At this checkpoint: ' + number(activityTotals.downloading) + ' transferring audio, ' + number(activityTotals.processing) + ' preparing or validating, and ' + number(activityTotals.awaiting_upload) + ' awaiting upload. ' + number(activityTotals.queued) + ' are queued in the running batch. In progress includes these three working stages; remaining entries need separate scheduling or recovery.' : 'Worker activity was not verified for this checkpoint; archived counts remain available.');
      const activityDownload = document.getElementById('cc-activity-download');
      if (activityDownload && activityValid) {
        const csvCell = value => { let text = String(value); if ([61,43,45,64].includes(text.trimStart().charCodeAt(0)) || [9,10,13].includes(text.charCodeAt(0))) text = "'" + text; return '"' + text.replaceAll('"', '""') + '"'; };
        const records = [['Creator','Target','Saved audio','Downloading','Preparing or validating','Awaiting upload','Queued','Other pending'], ...channels.map(row => [row.channel,row.target,...stages.map(field => row.activity[field])])];
        const newline = String.fromCharCode(13,10);
        const url = URL.createObjectURL(new Blob([String.fromCharCode(0xfeff) + records.map(row => row.map(csvCell).join(',')).join(newline) + newline], {type:'text/csv;charset=utf-8'}));
        activityDownload.href = url; activityDownload.hidden = false;
        window.addEventListener('pagehide', () => URL.revokeObjectURL(url), {once:true});
      }
      put('cc-coverage-date', date(data.generated_at));
      render();
    } catch (_) {
      body.replaceChildren(); const tr = document.createElement('tr'), td = document.createElement('td'); td.colSpan = 8; td.className = 'cc-left'; td.textContent = 'The channel coverage checkpoint could not be loaded.'; tr.append(td); body.append(tr);
      put('cc-coverage-summary', 'Channel coverage is unavailable. Use the dated collection snapshot above.');
      put('cc-coverage-date', 'unavailable'); put('cc-coverage-shown', ''); search.disabled = true; filter.disabled = true;
    }
  }
  const loadCollection = () => { collectionStatus(); collectionEta(); collectionCoverage(); };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', loadCollection, {once:true}); else loadCollection();
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
