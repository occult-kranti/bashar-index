(() => {
  'use strict';
  const text = (id, value) => { const el = document.getElementById(id); if (el) el.textContent = value; };
  const number = value => typeof value === 'number' && Number.isFinite(value) ? value.toLocaleString('en-US') : '—';
  fetch('../et-channelers/plan/ingestion_status.json', {cache: 'no-cache'})
    .then(response => { if (!response.ok) throw new Error('Snapshot unavailable'); return response.json(); })
    .then(data => {
      const names = {cooldown: 'Waiting for Drive', paused: 'Collection paused', ready: 'Ready to collect', running: 'Collection in progress', unknown: 'Status not confirmed'};
      text('run-state', names[data.operation?.state] || 'Status not confirmed');
      const stamp = new Date(data.generated_at);
      text('run-date', Number.isNaN(stamp.valueOf()) ? 'Snapshot date unavailable.' : 'Published snapshot · ' + stamp.toLocaleString('en-US', {dateStyle:'medium',timeStyle:'short',timeZone:'UTC'}) + ' UTC');
      text('pair-count', number(data.counts?.verified_pairs));
      text('channel-count', number(data.counts?.channels));
      text('remaining-count', number(data.counts?.final_round_indexed));
    }).catch(() => text('run-date', 'Status snapshot unavailable. Open the collection dashboard for its dated source tables.'));
})();
