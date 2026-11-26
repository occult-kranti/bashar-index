(() => {
  'use strict';
  // The strip reads the published collection record (et-channelers/pipeline/collection_state.py), not a live process.
  const text = (id, value) => { const el = document.getElementById(id); if (el) el.textContent = value; };
  const whole = value => Number.isInteger(value) && value >= 0;
  const number = value => whole(value) ? value.toLocaleString('en-US') : '—';
  const utc = (value, options) => { const stamp = new Date(value); return Number.isNaN(stamp.valueOf()) ? 'date unavailable' : stamp.toLocaleString('en-GB', {timeZone: 'UTC', ...options}); };
  const day = value => utc(value, {day: 'numeric', month: 'short', year: 'numeric'});
  const clock = value => utc(value, {hour: '2-digit', minute: '2-digit', hourCycle: 'h23'}) + ' UTC';
  fetch('../et-channelers/plan/collection_state.json', {cache: 'no-cache'})
    .then(response => { if (!response.ok) throw new Error('Record unavailable'); return response.json(); })
    .then(data => {
      const selection = data.selection || {}, downloads = data.downloads || {}, run = data.transcription || {};
      if (data.schema_version !== 1 || data.scope !== 'latest20_collection_state' || downloads.state !== 'closed'
          || ![selection.recordings, selection.creators, downloads.archived_with_verified_audio, downloads.final_failures].every(whole)
          || downloads.archived_with_verified_audio + downloads.final_failures !== selection.recordings) throw new Error('Unexpected record');
      const finished = run.state === 'finished' && whole(run.audio_files_transcribed) && whole(run.audio_files);
      text('run-state', finished ? 'Latest-20 downloads closed · transcription finished' : 'Latest-20 downloads closed');
      text('run-date', number(selection.creators) + ' channels · closed by the owner ' + day(downloads.closed_at_utc)
        + (finished ? ' · transcription finished ' + day(run.finished_at_utc) + ', ' + clock(run.finished_at_utc) : '') + '.');
      text('archived-count', number(downloads.archived_with_verified_audio));
      text('archived-label', 'of ' + number(selection.recordings) + ' selected recordings archived with verified audio');
      text('failure-count', number(downloads.final_failures));
      text('failure-label', 'final download failures, not retried');
      text('transcribed-count', finished ? number(run.audio_files_transcribed) : '—');
      text('transcribed-label', finished ? 'of ' + number(run.audio_files) + ' audio files transcribed'
        + (Number.isFinite(run.hours_transcribed) ? ', ' + run.hours_transcribed.toFixed(1) + ' hours' : '') : 'audio files transcribed');
    }).catch(() => text('run-date', 'Collection record unavailable. Open the collection dashboard for its dated tables.'));
})();
