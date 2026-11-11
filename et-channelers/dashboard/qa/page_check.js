
const $ = (s, r = document) => r.querySelector(s);
const el = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; };
const fmt = d3.format(',');
const compact = (n) => new Intl.NumberFormat('en', {notation: 'compact', maximumFractionDigits: 1}).format(n);
const num = (x) => (x === '' || x == null || isNaN(Number(x)) ? null : Number(x));
const safeUrl = (u) => (/^https:\/\/(www\.|m\.)?youtube\.com\//.test(u || '') ? u : null);
const STATUS = {'ok': 'Latest uploads read', 'metadata-only': 'Channel details from notes', 'no_youtube': 'No channel recorded yet', 'not_found': 'Not found'};
const statusColor = (s) => (s === 'ok' ? dash.colors[0] : s === 'metadata-only' ? dash.colors[1] : s === 'not_found' ? dash.colors[2] : 'var(--cds-chart-muted)');

dash.calc('coverage', {
  inputs: ['channels', 'videos'],
  title: 'Coverage counts',
  description: 'Counts of channel entries by index status, and of video rows and channeling sessions.',
  fn: (channels, videos) => {
    const by = (s) => channels.filter((c) => c.index_status === s).length;
    return [
      {key: 'channels', n: channels.length},
      {key: 'ok', n: by('ok')},
      {key: 'metadata-only', n: by('metadata-only')},
      {key: 'no_youtube', n: by('no_youtube')},
      {key: 'not_found', n: by('not_found')},
      {key: 'videos', n: videos.length},
      {key: 'channeling', n: videos.filter((v) => v.channeling === 'yes').length}
    ];
  }
});

function makeTip(wrap) {
  const t = el('div', 'ci-tip');
  t.hidden = true;
  wrap.appendChild(t);
  let timer = 0;
  const hide = () => { t.hidden = true; clearTimeout(timer); };
  const show = (ev, lines) => {
    t.replaceChildren(...lines.map((l, i) => el('div', i ? 'ci-tip-line' : 'ci-tip-head', l)));
    t.hidden = false;
    const p = d3.pointer(ev, wrap);
    const w = t.offsetWidth, h = t.offsetHeight, W = wrap.clientWidth;
    t.style.left = Math.max(0, Math.min(W - w, p[0] + 12)) + 'px';
    t.style.top = Math.max(0, p[1] - h - 8) + 'px';
    clearTimeout(timer);
    if (ev.pointerType && ev.pointerType !== 'mouse') timer = setTimeout(hide, 4000);
  };
  return {show, hide};
}

const failLine = () => { const w = el('div', 'ci-fail'); w.append(el('i'), el('span', null, 'Failed to load')); return w; };
const showFail = (box) => { box.classList.remove('dash-skeleton'); box.replaceChildren(failLine()); };

function drawCoverage(rows) {
  document.querySelectorAll('.ci [data-source="coverage"][data-where]').forEach((e) => {
    const k = e.getAttribute('data-where').slice(4);
    const r = rows.find((x) => x.key === k);
    e.textContent = r ? fmt(Number(r.n)) : '—';
  });
  const bar = $('#seg-bar');
  bar.classList.remove('dash-skeleton');
  bar.replaceChildren();
  ['ok', 'metadata-only', 'no_youtube', 'not_found'].forEach((s) => {
    const r = rows.find((x) => x.key === s);
    const seg = el('div', 'ci-seg');
    seg.style.flexGrow = String(r ? Number(r.n) : 0);
    seg.style.background = statusColor(s);
    bar.append(seg);
  });
  document.querySelectorAll('.ci-sw[data-k]').forEach((sw) => { sw.style.background = statusColor(sw.dataset.k); });
}

function drawAudience(allRows) {
  const box = $('#audience-chart');
  box.classList.remove('dash-skeleton');
  box.replaceChildren();
  const rows = allRows.map((r) => ({r, subs: num(r.subscribers)})).filter((d) => d.subs).sort((a, b) => b.subs - a.subs);
  if (!rows.length) return;
  const W = Math.max(260, box.clientWidth), rowH = 22, top = 6, axisH = 26;
  const H = top + rows.length * rowH + axisH;
  const leg = el('div', 'ci-legend-inline');
  ['ok', 'metadata-only'].forEach((s) => {
    const k = el('span', 'ci-key');
    const sw = el('span', 'ci-sw');
    sw.style.background = statusColor(s);
    k.append(sw, document.createTextNode(STATUS[s]));
    leg.append(k);
  });
  box.append(leg);
  const svg = d3.select(box).append('svg').attr('width', '100%').attr('viewBox', `0 0 ${W} ${H}`)
    .attr('role', 'img').attr('aria-label', 'Dot plot of YouTube subscribers per channel on a log scale; the table below lists the same channels');
  const labelOf = (d) => d.r.person_name + (d.r.role && d.r.role !== 'channeler' ? ` (${d.r.role})` : '');
  const probe = svg.append('text').style('font-size', '12px').attr('visibility', 'hidden');
  const widthOf = (s) => { probe.text(s); return probe.node().getComputedTextLength(); };
  const maxLab = Math.min(Math.round(W * 0.44), d3.max(rows, (d) => widthOf(labelOf(d))) + 4);
  const fit = (s) => {
    if (widthOf(s) <= maxLab) return s;
    let a = s;
    while (a.length > 1 && widthOf(a + '…') > maxLab) a = a.slice(0, -1);
    return a + '…';
  };
  rows.forEach((d) => { d.label = fit(labelOf(d)); });
  const endW = d3.max(rows, (d) => widthOf(compact(d.subs))) + 10;
  probe.remove();
  const x0 = maxLab + 12, x1 = W - endW - 4;
  const dom = [d3.min(rows, (d) => d.subs) / 1.6, d3.max(rows, (d) => d.subs)];
  const x = d3.scaleLog().domain(dom).range([x0, x1]);
  const decades = Math.log10(dom[1] / dom[0]);
  const step = (x1 - x0) / decades >= 52 ? 1 : 2;
  const ticks = d3.range(Math.ceil(Math.log10(dom[0])), Math.floor(Math.log10(dom[1])) + 1).filter((e) => e % step === 0).map((e) => Math.pow(10, e));
  svg.append('g').selectAll('line').data(ticks).join('line')
    .attr('x1', (t) => x(t)).attr('x2', (t) => x(t)).attr('y1', top).attr('y2', H - axisH)
    .style('stroke', 'var(--cds-chart-grid)').attr('stroke-width', 1);
  svg.append('g').selectAll('text').data(ticks).join('text')
    .attr('x', (t) => x(t)).attr('y', H - 8).attr('text-anchor', 'middle')
    .style('font-size', '11px').style('fill', 'var(--color-fg-muted)').text((t) => compact(t));
  const tip = makeTip(box);
  const row = svg.append('g').selectAll('g').data(rows).join('g')
    .attr('transform', (d, i) => `translate(0,${top + i * rowH + rowH / 2})`);
  row.append('line').attr('x1', x0).attr('x2', (d) => x(d.subs)).style('stroke', 'var(--cds-chart-grid)').attr('stroke-width', 1);
  row.append('circle').attr('cx', (d) => x(d.subs)).attr('r', 4.5)
    .style('fill', (d) => statusColor(d.r.index_status)).style('stroke', 'var(--color-panel)').attr('stroke-width', 1.5);
  row.append('text').attr('x', maxLab).attr('text-anchor', 'end').attr('dy', '0.32em')
    .style('font-size', '12px').style('fill', 'var(--color-fg)').text((d) => d.label);
  row.append('text').attr('x', (d) => x(d.subs) + 8).attr('dy', '0.32em')
    .style('font-size', '11px').style('fill', 'var(--color-fg-muted)').text((d) => compact(d.subs));
  row.append('rect').attr('x', 0).attr('y', -rowH / 2).attr('width', W).attr('height', rowH).style('fill', 'transparent')
    .on('pointerover pointermove pointerdown', (ev, d) => {
      const lines = [d.r.person_name, 'Subscribers: ' + fmt(d.subs)];
      const vc = num(d.r.video_count);
      if (vc != null) lines.push('Videos on channel: ' + fmt(vc));
      lines.push('Role: ' + d.r.role, STATUS[d.r.index_status] || d.r.index_status);
      tip.show(ev, lines);
    })
    .on('pointerleave', (ev) => { if (ev.pointerType === 'mouse') tip.hide(); });
}

function drawEntities(rows, nameById) {
  const box = $('#entity-bars');
  box.classList.remove('dash-skeleton');
  box.replaceChildren();
  const data = rows.map((r) => ({r, n: Number(r.channeling_videos), v: Number(r.videos)}))
    .sort((a, b) => b.n - a.n || a.r.entity_name.localeCompare(b.r.entity_name));
  const max = d3.max(data, (d) => d.n) || 1;
  const tip = makeTip(box);
  data.forEach((d) => {
    const row = el('div', 'ci-bar-row');
    const lab = el('div', 'ci-bar-label', d.r.entity_name);
    lab.setAttribute('data-source', 'entities');
    lab.setAttribute('data-field', 'entity_name');
    lab.setAttribute('data-where', 'entity_id=' + d.r.entity_id);
    const track = el('div', 'ci-bar-track');
    const fill = el('div', 'ci-bar-fill');
    fill.style.width = (100 * d.n / max) + '%';
    fill.style.background = dash.colors[0];
    track.append(fill);
    const val = el('div', 'ci-bar-val', fmt(d.n));
    val.setAttribute('data-source', 'entities');
    val.setAttribute('data-field', 'channeling_videos');
    val.setAttribute('data-where', 'entity_id=' + d.r.entity_id);
    row.append(lab, track, val);
    const who = String(d.r.people || '').split(';').map((s) => s.trim()).filter(Boolean).map((id) => nameById.get(id) || id).join(', ');
    row.addEventListener('pointerover', (ev) => tip.show(ev, [d.r.entity_name, 'Channeling videos naming it: ' + fmt(d.n), 'All videos naming it: ' + fmt(d.v), 'Voiced by: ' + who]));
    row.addEventListener('pointermove', (ev) => tip.show(ev, [d.r.entity_name, 'Channeling videos naming it: ' + fmt(d.n), 'All videos naming it: ' + fmt(d.v), 'Voiced by: ' + who]));
    row.addEventListener('pointerleave', (ev) => { if (ev.pointerType === 'mouse') tip.hide(); });
    box.append(row);
  });
}

function sortRows(rows, st, numeric) {
  const k = st.key, isNum = numeric.has(k), sk = st.sortKey || k;
  const val = (r) => (isNum || st.sortKey ? num(r[sk]) : String(r[k] || '').toLowerCase());
  return rows.slice().sort((a, b) => {
    const A = val(a), B = val(b);
    const aE = A === null || A === '', bE = B === null || B === '';
    if (aE && bE) return 0;
    if (aE) return 1;
    if (bE) return -1;
    return (A < B ? -1 : A > B ? 1 : 0) * st.dir;
  });
}

function wireSort(table, st, numeric, redraw, sortKeys) {
  table.querySelectorAll('.ci-sort').forEach((btn) => {
    btn.addEventListener('click', () => {
      const k = btn.dataset.k;
      if (st.key === k) st.dir *= -1; else { st.key = k; st.dir = numeric.has(k) || (sortKeys && sortKeys[k]) ? -1 : 1; }
      st.sortKey = sortKeys && sortKeys[k] ? sortKeys[k] : null;
      redraw();
    });
  });
}

function markSort(table, st) {
  table.querySelectorAll('th').forEach((th) => {
    const k = th.querySelector('.ci-sort').dataset.k;
    if (k === st.key) th.setAttribute('aria-sort', st.dir > 0 ? 'ascending' : 'descending'); else th.removeAttribute('aria-sort');
  });
}

function linkCell(td, text, href) {
  const u = safeUrl(href);
  if (u) {
    const a = el('a', null, text);
    a.href = u; a.target = '_blank'; a.rel = 'noopener noreferrer';
    td.append(a);
  } else td.textContent = text;
}

function fillSelect(sel, first, values, labelOf) {
  const keep = sel.value;
  sel.replaceChildren(new Option(first, ''), ...values.map((v) => new Option(labelOf ? labelOf(v) : v, v)));
  sel.value = values.includes(keep) ? keep : '';
}

const chSt = {key: 'subscribers', dir: -1, sortKey: null};
const vdSt = {key: 'person_name', dir: 1, sortKey: null};
const plSt = {key: 'playlist_id', dir: 1, sortKey: null};
const chNum = new Set(['subscribers', 'video_count', 'channeling_videos_in_sample']);
const vdKeys = {views_as_displayed: 'views'};
const vdNum = new Set([]);
const plNum = new Set(['video_count_if_known']);
const chTable = $('#ch-table'), vdTable = $('#vd-table'), plTable = $('#pl-table');

function renderChannels() {
  const d = dash.data('channels');
  if (d.status !== 'ok') return;
  const q = $('#ch-q').value.trim().toLowerCase(), st = $('#ch-status').value, role = $('#ch-role').value;
  let rows = d.data.filter((r) => (!st || r.index_status === st) && (!role || r.role === role)
    && (!q || [r.person_name, r.channel_title, r.handle, r.entities_seen].join(' ').toLowerCase().includes(q)));
  rows = sortRows(rows, chSt, chNum);
  const body = chTable.tBodies[0];
  body.replaceChildren(...rows.map((r) => {
    const tr = el('tr');
    tr.dataset.key = r.person_id;
    const name = el('td'); linkCell(name, r.person_name, r.channel_url);
    const role = el('td', 'ci-hide-narrow', r.role);
    const status = el('td'); const pill = el('span', 'ci-pill', r.index_status); pill.style.setProperty('--dot', statusColor(r.index_status)); status.append(pill);
    const subs = el('td', 'ci-num', num(r.subscribers) == null ? '' : fmt(num(r.subscribers)));
    const vc = el('td', 'ci-num ci-hide-narrow', num(r.video_count) == null ? '' : fmt(num(r.video_count)));
    const cv = el('td', 'ci-num ci-hide-narrow', r.channeling_videos_in_sample);
    const ent = el('td', 'ci-hide-narrow', r.entities_seen);
    tr.append(name, role, status, subs, vc, cv, ent);
    return tr;
  }));
  markSort(chTable, chSt);
  $('#ch-count').textContent = 'Showing ' + fmt(rows.length) + ' of ' + fmt(d.data.length) + ' entries';
}

function renderVideos() {
  const d = dash.data('videos');
  if (d.status !== 'ok') return;
  const q = $('#vd-q').value.trim().toLowerCase(), who = $('#vd-who').value, chan = $('#vd-chan').checked;
  let rows = d.data.filter((r) => (!who || r.person_name === who) && (!chan || r.channeling === 'yes')
    && (!q || [r.title, r.person_name, r.entity_named_in_title].join(' ').toLowerCase().includes(q)));
  rows = sortRows(rows, vdSt, vdNum);
  const body = vdTable.tBodies[0];
  body.replaceChildren(...rows.map((r) => {
    const tr = el('tr');
    tr.dataset.key = r.row_id;
    const person = el('td', null, r.person_name);
    const title = el('td'); linkCell(title, r.title, r.url);
    const ent = el('td', 'ci-hide-narrow', r.entity_named_in_title);
    const chn = el('td', 'ci-hide-narrow', r.channeling);
    const views = el('td', 'ci-num', r.views_as_displayed);
    const pub = el('td', 'ci-hide-narrow', r.published_relative);
    const len = el('td', 'ci-num ci-hide-narrow', r.length);
    tr.append(person, title, ent, chn, views, pub, len);
    return tr;
  }));
  markSort(vdTable, vdSt);
  $('#vd-count').textContent = 'Showing ' + fmt(rows.length) + ' of ' + fmt(d.data.length) + ' videos';
}

function renderPlaylists() {
  const d = dash.data('playlists');
  if (d.status !== 'ok') return;
  const rows = sortRows(d.data, plSt, plNum);
  const body = plTable.tBodies[0];
  body.replaceChildren(...rows.map((r) => {
    const tr = el('tr');
    tr.dataset.key = r.row_id;
    const id = el('td'); linkCell(id, r.playlist_id, r.url);
    const title = el('td', null, r.title_if_known);
    const owner = el('td', 'ci-hide-narrow', r.owner_person_or_section);
    const cnt = el('td', 'ci-num', r.video_count_if_known);
    tr.append(id, title, owner, cnt);
    return tr;
  }));
  markSort(plTable, plSt);
}

wireSort(chTable, chSt, chNum, renderChannels, null);
wireSort(vdTable, vdSt, vdNum, renderVideos, vdKeys);
wireSort(plTable, plSt, plNum, renderPlaylists, null);
['#ch-q'].forEach((s) => $(s).addEventListener('input', renderChannels));
['#ch-status', '#ch-role'].forEach((s) => $(s).addEventListener('change', renderChannels));
$('#vd-q').addEventListener('input', renderVideos);
$('#vd-who').addEventListener('change', renderVideos);
$('#vd-chan').addEventListener('change', renderVideos);

const go = (e) => { e.scrollIntoView({behavior: 'smooth', block: 'start'}); dash.setLink(e.id); };
document.querySelectorAll('.ci-chip').forEach((b) => b.addEventListener('click', () => { const t = document.getElementById(b.dataset.to); if (t) go(t); }));

let opened = false;
dash.onData(() => {
  const ch = dash.data('channels'), vd = dash.data('videos'), en = dash.data('entities'), pl = dash.data('playlists'), cov = dash.data('coverage');
  if (cov.status === 'ok') drawCoverage(cov.data); else if (cov.status !== 'loading') showFail($('#seg-bar'));
  if (ch.status === 'ok') {
    if ($('#ch-status').options.length === 0) {
      fillSelect($('#ch-status'), 'All index statuses', Object.keys(STATUS), (v) => STATUS[v]);
      fillSelect($('#ch-role'), 'All roles', [...new Set(ch.data.map((r) => r.role))].sort());
    }
    drawAudience(ch.data);
    renderChannels();
    const nameById = new Map(ch.data.map((r) => [r.person_id, r.person_name]));
    if (en.status === 'ok') drawEntities(en.data, nameById); else if (en.status !== 'loading') showFail($('#entity-bars'));
  } else if (ch.status !== 'loading') { showFail($('#audience-chart')); showFail($('#entity-bars')); }
  if (vd.status === 'ok') {
    if ($('#vd-who').options.length === 0) fillSelect($('#vd-who'), 'All channelers', [...new Set(vd.data.map((r) => r.person_name))].sort((a, b) => a.localeCompare(b)));
    renderVideos();
  }
  if (pl.status === 'ok') renderPlaylists();
  if (!opened && ch.status === 'ok' && vd.status === 'ok') {
    opened = true;
    const named = document.getElementById(location.hash.slice(1));
    if (named) go(named);
  }
});
