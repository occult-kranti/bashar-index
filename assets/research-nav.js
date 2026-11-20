/* Shared navigation: paths resolve from this asset, including GitHub Pages subpaths. */
(() => {
  'use strict';
  const script = document.currentScript;
  if (!script || document.querySelector('.rs-nav')) return;
  const root = script.dataset.root ? new URL(script.dataset.root, script.src) : new URL('../', script.src);
  const current = script.dataset.page || '';
  document.body.dataset.researchPage = current;
  const links = [
    ['hub', 'All dashboards', 'dashboards/'],
    ['predictions', 'Predictions', 'et-channelers/dashboard/predictions.html'],
    ['collection', 'Collection', 'et-channelers/dashboard/collection/'],
    ['timeline', 'Upload timeline', 'et-channelers/dashboard/collection/timeline.html'],
    ['findings', 'Transcript findings', 'et-channelers/dashboard/findings/'],
    ['youtube', 'Channel index', 'et-channelers/dashboard/'],
    ['atlas', 'Atlas', 'channeling-atlas/dist/'],
    ['bashar', 'Bashar index', ''],
    ['report', 'Research report', 'channeling-atlas/dist/analysis/report.html']
  ];
  const makeLinks = () => {
    const nav = document.createElement('nav');
    nav.className = 'rs-links'; nav.setAttribute('aria-label', 'Research dashboards');
    links.forEach(([key, label, path]) => {
      const a = document.createElement('a'); a.href = new URL(path, root).href; a.textContent = label;
      if (key === current) a.setAttribute('aria-current', 'page');
      nav.append(a);
    });
    return nav;
  };
  const header = document.createElement('header'); header.className = 'rs-nav';
  const inner = document.createElement('div'); inner.className = 'rs-nav-inner';
  const brand = document.createElement('a'); brand.className = 'rs-brand'; brand.href = new URL('dashboards/', root).href;
  const mark = document.createElement('span'); mark.className = 'rs-mark'; mark.textContent = '↗'; mark.setAttribute('aria-hidden', 'true');
  brand.append(mark, document.createTextNode('Channeling research'));
  const mobile = document.createElement('details'); mobile.className = 'rs-mobile';
  const summary = document.createElement('summary'); summary.textContent = 'Dashboards';
  mobile.append(summary, makeLinks()); inner.append(brand, makeLinks(), mobile); header.append(inner);
  document.body.prepend(header);
  const main = document.querySelector('main');
  if (main && !main.hasAttribute('tabindex')) main.setAttribute('tabindex', '-1');
  const existingSkip = main && document.querySelector('a[href="#' + (main.id || 'research-main') + '"]');
  if (existingSkip && /skip/i.test(existingSkip.textContent)) document.body.prepend(existingSkip);
  const context = {
    bashar: ['BASHAR REFERENCE INDEX', 'September 2026 research edition. Browse the original catalogue, or open the cross-channel prediction timeline.', 'Explore predictions', 'et-channelers/dashboard/predictions.html'],
    atlas: ['ATLAS · 23 OCTOBER 2026 SNAPSHOT', 'People, entities and source records from the published research edition. New collection progress is tracked separately.', 'See current collection', 'et-channelers/dashboard/collection/'],
    report: ['RESEARCH REPORT · FROZEN EVIDENCE', 'Findings below describe the 23 October 2026 sample. The current collection does not change these results.', 'Browse all dashboards', 'dashboards/']
  }[current];
  if (main && context) {
    const aside = document.createElement('aside'); aside.className = 'rs-context'; aside.setAttribute('aria-label', 'Research edition');
    const copy = document.createElement('div');
    const label = document.createElement('strong'); label.textContent = context[0];
    const description = document.createElement('p'); description.textContent = context[1];
    copy.append(label, description);
    const link = document.createElement('a'); link.href = new URL(context[3], root).href; link.textContent = context[2] + ' ↗';
    aside.append(copy, link); main.before(aside);
  }
  if (main && !document.querySelector('a[href="#' + (main.id || 'research-main') + '"]')) {
    if (!main.id) main.id = 'research-main';
    const skip = document.createElement('a'); skip.href = '#' + main.id; skip.className = 'rs-skip'; skip.textContent = 'Skip to content';
    document.body.prepend(skip);
  }
})();
