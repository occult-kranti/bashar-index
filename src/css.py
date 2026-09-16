CSS = r"""
:root{
  color-scheme:light;
  --bg:#F1F3F0; --surface:#FAFBF9; --surface-2:#E7ECE8; --ink:#141822; --ink-2:#2F3644; --muted:#5B6371;
  --line:#D5DAD6; --line-2:#BFC7C2; --accent:#0E8F7A; --accent-ink:#0A6C5C; --accent-soft:rgba(14,143,122,.12);
  --tint-2:rgba(74,110,160,.16); --series:#0E8F7A; --series-muted:#C4CCC8; --amber:#B8791F; --amber-soft:rgba(184,121,31,.14);
  --shadow:0 18px 40px rgba(20,24,34,.16); --focus:#0E8F7A;
  --font-display:'Bricolage Grotesque','Helvetica Neue',Arial,sans-serif;
  --font-body:'Newsreader',Georgia,'Times New Roman',serif;
  --font-mono:'IBM Plex Mono',ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
}
@media (prefers-color-scheme:dark){
  :root:not([data-theme="light"]){
    color-scheme:dark;
    --bg:#0C1019; --surface:#141A27; --surface-2:#1C2434; --ink:#E8ECF2; --ink-2:#CBD3DE; --muted:#98A2B3;
    --line:#253044; --line-2:#36435C; --accent:#33C9AD; --accent-ink:#5ADBC2; --accent-soft:rgba(51,201,173,.15);
    --tint-2:rgba(120,150,205,.2); --series:#1BA58C; --series-muted:#3A4558; --amber:#D9A24A; --amber-soft:rgba(217,162,74,.18);
    --shadow:0 18px 40px rgba(0,0,0,.5); --focus:#5ADBC2;
  }
}
:root[data-theme="dark"]{
  color-scheme:dark;
  --bg:#0C1019; --surface:#141A27; --surface-2:#1C2434; --ink:#E8ECF2; --ink-2:#CBD3DE; --muted:#98A2B3;
  --line:#253044; --line-2:#36435C; --accent:#33C9AD; --accent-ink:#5ADBC2; --accent-soft:rgba(51,201,173,.15);
  --tint-2:rgba(120,150,205,.2); --series:#1BA58C; --series-muted:#3A4558; --amber:#D9A24A; --amber-soft:rgba(217,162,74,.18);
  --shadow:0 18px 40px rgba(0,0,0,.5); --focus:#5ADBC2;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
@media (prefers-reduced-motion:reduce){html{scroll-behavior:auto} *{animation:none!important;transition:none!important}}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--font-body);font-size:17px;line-height:1.55;-webkit-font-smoothing:antialiased}
a{color:var(--accent-ink);text-decoration-thickness:1px;text-underline-offset:2px}
a:hover{text-decoration-thickness:2px}
:focus-visible{outline:2px solid var(--focus);outline-offset:2px;border-radius:4px}
img,svg{max-width:100%}
h1,h2,h3,h4{font-family:var(--font-display);line-height:1.08;margin:0;text-wrap:balance;letter-spacing:-.01em}
h1{font-size:clamp(2.4rem,7vw,4.6rem);font-weight:800;letter-spacing:-.03em}
h2{font-size:clamp(1.7rem,3.6vw,2.4rem);font-weight:700}
h3{font-size:1.2rem;font-weight:650}
h4{font-size:1.02rem;font-weight:650}
p{margin:0 0 1em}
.prose{max-width:68ch}
.prose p,.prose li{font-size:1.02rem}
.prose ul,.prose ol{padding-left:1.2em}
.prose li{margin-bottom:.35em}
.eyebrow,.mono{font-family:var(--font-mono);font-size:.72rem;letter-spacing:.12em;text-transform:uppercase;color:var(--muted)}
.mono-num{font-family:var(--font-mono);font-variant-numeric:tabular-nums}
.small{font-size:.9rem;color:var(--muted)}
.wrap{max-width:1120px;margin:0 auto;padding-inline:clamp(16px,4vw,36px)}
.sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}
/* masthead */
.mast{position:sticky;top:0;z-index:40;background:color-mix(in srgb,var(--bg) 88%,transparent);backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px);border-bottom:1px solid var(--line)}
.mast .row{display:flex;align-items:center;gap:12px;padding-block:10px;flex-wrap:nowrap}
@media (max-width:520px){.brand{font-size:1rem;gap:6px}.brand .sig{width:18px;height:18px}.search input{padding:7px 10px;font-size:.88rem}}
.brand{font-family:var(--font-display);font-weight:800;font-size:1.15rem;letter-spacing:-.02em;color:var(--ink);text-decoration:none;display:flex;align-items:center;gap:10px;white-space:nowrap}
.brand .sig{width:22px;height:22px;display:inline-block}
.search{margin-left:auto;display:flex;align-items:center;gap:8px;flex:1 1 220px;max-width:420px;min-width:0}
.search input{flex:1;min-width:0;font:500 .95rem var(--font-display);padding:8px 12px;border:1px solid var(--line-2);border-radius:999px;background:var(--surface);color:var(--ink)}
.search input::placeholder{color:var(--muted)}
.theme-btn{border:1px solid var(--line-2);background:var(--surface);color:var(--ink);border-radius:999px;width:36px;height:36px;display:grid;place-items:center;cursor:pointer;flex:none}
.chips{display:flex;gap:6px;overflow-x:auto;padding-block:0 10px;scrollbar-width:none;-ms-overflow-style:none}
.chips::-webkit-scrollbar{display:none}
.chip{flex:none;font:600 .82rem var(--font-display);padding:6px 12px;border-radius:999px;border:1px solid var(--line-2);color:var(--ink-2);text-decoration:none;background:transparent;cursor:pointer;white-space:nowrap}
.chip:hover{border-color:var(--accent)}
.chip.on,.chip[aria-current="true"]{background:var(--ink);color:var(--bg);border-color:var(--ink)}
/* sections */
section.sec{padding-block:56px 40px;border-top:1px solid var(--line);scroll-margin-top:110px}
@media (max-width:600px){section.sec{scroll-margin-top:118px}}
section.sec:first-of-type{border-top:0}
.sec-head{margin-bottom:26px}
.sec-head h2{margin-top:6px}
.ruler{height:12px;margin-top:14px;background:
  repeating-linear-gradient(90deg,var(--line-2) 0 1px,transparent 1px 7px) 0 6px/100% 6px no-repeat,
  repeating-linear-gradient(90deg,var(--line-2) 0 1px,transparent 1px 70px) 0 0/100% 12px no-repeat;opacity:.9}
.lede{font-size:clamp(1.1rem,2.2vw,1.35rem);line-height:1.45;max-width:60ch;color:var(--ink-2)}
/* hero */
.hero{padding-block:44px 24px}
.hero h1{max-width:14ch}
.hero .lede{margin-top:18px}
.notice{border:1px solid var(--line-2);border-left:4px solid var(--amber);background:var(--surface);padding:12px 16px;border-radius:8px;font-size:.95rem;max-width:72ch;margin-top:22px}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:1px;background:var(--line);border:1px solid var(--line);border-radius:10px;overflow:hidden;margin-top:28px}
.stat{background:var(--surface);padding:14px 16px}
.stat b{display:block;font:700 1.9rem var(--font-display);letter-spacing:-.02em;line-height:1}
.stat span{display:block;margin-top:6px;font-size:.82rem;color:var(--muted)}
.grid{display:grid;gap:16px}
.grid.c2{grid-template-columns:repeat(auto-fit,minmax(280px,1fr))}
.grid.c3{grid-template-columns:repeat(auto-fit,minmax(240px,1fr))}
.grid.c3f{grid-template-columns:repeat(auto-fit,minmax(300px,1fr))}
.card{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:18px 18px 16px}
.card h3,.card h4{margin-bottom:8px}
.card p{font-size:.98rem;margin-bottom:.5em}
.card .mono{display:block;margin-bottom:8px}
.finding{border-left:4px solid var(--accent);border-radius:6px 12px 12px 6px}
.finding b.num{font:700 1.6rem var(--font-display);display:block;letter-spacing:-.02em;margin-bottom:6px}
.jump{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px;margin-top:22px}
.jump a{display:block;padding:12px 14px;border:1px solid var(--line);border-radius:10px;text-decoration:none;color:var(--ink);background:var(--surface);font:600 .95rem var(--font-display)}
.jump a small{display:block;font:400 .82rem var(--font-body);color:var(--muted);margin-top:3px}
.jump a:hover{border-color:var(--accent)}
/* charts (HTML bars) */
.chart{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:18px 18px 12px;margin-top:18px}
.chart header{margin-bottom:12px}
.chart header h3{margin-bottom:4px}
.chart .cap{font-size:.86rem;color:var(--muted);margin:0}
.bars{display:grid;grid-template-columns:minmax(120px,1.1fr) minmax(0,2fr) 44px;gap:8px 12px;align-items:center;font-size:.9rem}
.bars .lab{font:500 .86rem var(--font-display);color:var(--ink-2);text-align:right;line-height:1.15;overflow-wrap:anywhere}
.bars .track{position:relative;height:12px;background:var(--surface-2);border-radius:4px}
.bars .bar{position:absolute;inset:0 auto 0 0;background:var(--series);border-radius:4px;min-width:2px}
.bars .bar.muted{background:var(--series-muted)}
.bars .val{font-family:var(--font-mono);font-size:.8rem;color:var(--muted);text-align:right;font-variant-numeric:tabular-nums}
.bars .row-hit{display:contents;cursor:default}
.bars .row-hit:hover .bar{filter:brightness(1.12)}
.multi{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:14px}
.multi .mini{border:1px solid var(--line);border-radius:10px;padding:12px}
.multi .mini h4{margin-bottom:2px}
.multi .mini .n{font-family:var(--font-mono);font-size:.74rem;color:var(--muted);margin-bottom:10px;display:block}
.multi .bars{grid-template-columns:minmax(90px,1fr) minmax(0,1.4fr) 38px;gap:6px 8px}
.multi .bars .lab{font-size:.78rem}
.multi .bars .track{height:9px}
details.tbl{margin-top:10px}
details.tbl summary{cursor:pointer;font:600 .8rem var(--font-display);color:var(--accent-ink);list-style:none;display:inline-block;padding:4px 0}
details.tbl summary::-webkit-details-marker{display:none}
details.tbl summary::before{content:"▸ ";}
details.tbl[open] summary::before{content:"▾ ";}
table{border-collapse:collapse;width:100%;font-size:.88rem}
th,td{text-align:left;padding:6px 8px;border-bottom:1px solid var(--line);vertical-align:top}
th{font:600 .74rem var(--font-mono);letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}
td.num,th.num{text-align:right;font-family:var(--font-mono);font-variant-numeric:tabular-nums}
.tscroll{overflow-x:auto}
/* map small multiples */
.maps{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px}
.map{border:1px solid var(--line);border-radius:10px;padding:10px;background:var(--surface)}
.map svg{width:100%;height:auto;display:block}
.map .pt{fill:var(--series-muted)}
.map .pt.hi{fill:var(--series);stroke:var(--surface);stroke-width:2}
.map .pt.hi:hover{stroke:var(--ink)}
.map h4{font-size:.92rem;margin-top:8px}
.map .n{font-family:var(--font-mono);font-size:.72rem;color:var(--muted)}
.map .tags{font-size:.8rem;color:var(--ink-2);margin-top:4px}
/* dot strip */
.strip{position:relative;height:150px;margin:10px 4px 0}
.strip .axis{position:absolute;left:0;right:0;top:96px;height:1px;background:var(--line-2)}
.strip .tick{position:absolute;top:96px;width:1px;height:8px;background:var(--line-2)}
.strip .tick span{position:absolute;top:12px;left:0;transform:translateX(-50%);font:.7rem var(--font-mono);color:var(--muted)}
.strip .dot{position:absolute;top:96px;transform:translate(-50%,-50%);border-radius:50%;background:var(--series);border:2px solid var(--surface);cursor:default}
.strip .dot:hover{outline:2px solid var(--ink)}
.strip .dlab{position:absolute;transform:translateX(-50%);font:600 .74rem var(--font-mono);color:var(--ink-2);white-space:nowrap}
.strip .dlab::after{content:"";position:absolute;left:50%;top:100%;width:1px;height:var(--h,10px);background:var(--line-2)}
/* timeline */
.tl{list-style:none;margin:0;padding:0;border-left:2px solid var(--line-2);margin-left:6px}
.tl li{position:relative;padding:0 0 18px 22px}
.tl li::before{content:"";position:absolute;left:-7px;top:9px;width:12px;height:12px;border-radius:50%;background:var(--surface);border:2px solid var(--accent)}
.tl .when{font:600 .78rem var(--font-mono);color:var(--accent-ink);letter-spacing:.04em}
.tl p{margin:2px 0 0;font-size:.98rem}
.tl .src{font-size:.8rem}
.decade{font:700 1.05rem var(--font-display);margin:26px 0 12px 0;color:var(--muted)}
.ledger-list{list-style:none;margin:0;padding:0}
.ledger-list li{padding:10px 0;border-bottom:1px solid var(--line)}
.ledger-list .when{font:600 .76rem var(--font-mono);color:var(--amber);letter-spacing:.04em}
.ledger-list .claim{margin:2px 0 2px;font-size:.97rem}
.ledger-list .status{margin:0;font-size:.86rem;color:var(--muted)}
/* teachings */
.frame{border:1px solid var(--line);border-radius:12px;background:var(--surface);margin-bottom:12px}
.frame summary{cursor:pointer;padding:14px 18px;font:650 1.05rem var(--font-display);list-style:none;display:flex;gap:12px;align-items:baseline}
.frame summary::-webkit-details-marker{display:none}
.frame summary .k{font:500 .72rem var(--font-mono);color:var(--muted);letter-spacing:.08em;text-transform:uppercase;min-width:80px}
.frame summary::after{content:"+";margin-left:auto;font-family:var(--font-mono);color:var(--muted)}
.frame[open] summary::after{content:"−"}
.frame .body{padding:0 18px 18px;border-top:1px solid var(--line)}
.frame .body p,.frame .body li{font-size:.98rem}
.frame ol,.frame ul{padding-left:1.2em}
.links{display:flex;flex-wrap:wrap;gap:6px;margin-top:10px}
.pill{display:inline-block;font:600 .74rem var(--font-display);padding:3px 9px;border-radius:999px;border:1px solid var(--line-2);color:var(--ink-2);text-decoration:none;background:var(--surface)}
.pill.acc{border-color:var(--accent);color:var(--accent-ink)}
.pill.amber{border-color:var(--amber);color:var(--amber)}
.pill:hover{border-color:var(--ink)}
.pill.tag{background:var(--accent-soft);border-color:transparent;color:var(--accent-ink)}
/* diagrams */
.filters{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:16px}
.dgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px}
figure.dgf{margin:0;background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:12px;display:flex;flex-direction:column;gap:8px;cursor:pointer}
figure.dgf:hover{border-color:var(--accent)}
figure.dgf svg.dg{width:100%;height:auto;display:block;background:var(--surface);border-radius:6px}
figure.dgf figcaption{display:flex;flex-direction:column;gap:4px}
figure.dgf figcaption b{font:650 .98rem var(--font-display)}
.badge{display:inline-block;font:600 .68rem var(--font-mono);letter-spacing:.06em;text-transform:uppercase;padding:2px 8px;border-radius:4px;background:var(--surface-2);color:var(--ink-2)}
.badge.k1{background:var(--accent-soft);color:var(--accent-ink)}
.badge.k2{background:var(--tint-2);color:var(--ink-2)}
.badge.k3{background:var(--surface-2)}
.badge.k4{background:var(--amber-soft);color:var(--amber)}
/* diagram svg theme classes */
.dg-line{fill:none;stroke:var(--ink);stroke-width:1.6;stroke-linecap:round;stroke-linejoin:round}
.dg-line-2{fill:none;stroke:var(--muted);stroke-width:1;stroke-dasharray:3 3}
.dg-fill{fill:var(--accent-soft)} .dg-fill-2{fill:var(--tint-2)}
.dg-text{fill:var(--ink);font-family:var(--font-display)} .dg-muted{fill:var(--muted);font-family:var(--font-display)} .dg-inv{fill:var(--surface);font-family:var(--font-display)}
.dg-accent{fill:none;stroke:var(--accent);stroke-width:2} .dg-accent-fill{fill:var(--accent)} .dg-ink-fill{fill:var(--ink)}
.dg-black{fill:#111;stroke:var(--line-2);stroke-width:.6} .dg-white{fill:#fff;stroke:#444;stroke-width:.6} .dg-grey{fill:#8a8a8a} .dg-red{fill:#c0392b} .dg-gold{fill:#d4a017} .dg-blue{fill:#2f6f8f} .dg-green{fill:#2e8b57} .dg-violet{fill:#7b4fa3} .dg-rose{fill:#e6a0b8} .dg-copper{fill:#b87333;stroke:#b87333;stroke-width:3} .dg-blue-stroke{fill:none;stroke:#4aa3df;stroke-width:1.5} .dg-white-text{fill:#fff;font-family:var(--font-display)}
.dg-marker{fill:var(--ink)} .dg-marker-2{fill:var(--muted)}
/* library */
.tabs{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:14px}
.tab{font:600 .86rem var(--font-display);padding:8px 14px;border-radius:999px;border:1px solid var(--line-2);background:var(--surface);color:var(--ink-2);cursor:pointer}
.tab[aria-selected="true"]{background:var(--ink);color:var(--bg);border-color:var(--ink)}
.panel[hidden]{display:none}
.fbar{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:14px;align-items:center}
.fbar input,.fbar select{font:500 .9rem var(--font-display);padding:7px 10px;border:1px solid var(--line-2);border-radius:8px;background:var(--surface);color:var(--ink);min-width:0}
.fbar input{flex:1 1 180px}
.vgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(270px,1fr));gap:12px}
.vcard{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:14px;cursor:pointer;display:flex;flex-direction:column;gap:6px}
.vcard:hover{border-color:var(--accent)}
.vcard b{font:650 .98rem var(--font-display);line-height:1.2}
.vcard .meta{font:.72rem var(--font-mono);color:var(--muted);letter-spacing:.02em;line-height:1.5}
.vcard .tags{display:flex;flex-wrap:wrap;gap:4px;margin-top:auto}
.vcard .tags span{font:600 .7rem var(--font-display);padding:2px 7px;border-radius:999px;background:var(--accent-soft);color:var(--accent-ink)}
.type-dot{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:5px;vertical-align:middle;background:var(--muted)}
.type-dot.t-full{background:var(--series)} .type-dot.t-int{background:var(--amber)} .type-dot.t-off{background:var(--ink)} .type-dot.t-clip{background:var(--series-muted)}
.cat tr.hid{display:none}
.cat td.t{font-weight:600;font-family:var(--font-display);font-size:.92rem}
.cat td.d{font-family:var(--font-mono);font-size:.78rem;white-space:nowrap;color:var(--muted)}
.cat td.desc{font-size:.86rem;color:var(--ink-2)}
.more{margin-top:12px;font:600 .86rem var(--font-display);padding:8px 14px;border-radius:999px;border:1px solid var(--line-2);background:var(--surface);color:var(--ink);cursor:pointer}
.pod{display:grid;grid-template-columns:1fr;gap:8px}
.pod .row{display:grid;grid-template-columns:120px 1fr;gap:12px;padding:10px 0;border-bottom:1px solid var(--line);font-size:.92rem}
.pod .row .d{font:.74rem var(--font-mono);color:var(--muted)}
.pod .row b{font:650 .95rem var(--font-display)}
.pod .row p{margin:2px 0 4px;font-size:.9rem;color:var(--ink-2)}
@media (max-width:520px){.pod .row{grid-template-columns:1fr}}
.chan{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px}
/* glossary */
.az{display:flex;flex-wrap:wrap;gap:4px;margin-bottom:14px}
.az a{font:600 .8rem var(--font-mono);padding:3px 7px;border-radius:5px;text-decoration:none;color:var(--ink-2);border:1px solid var(--line)}
.gl{columns:2;column-gap:28px}
@media (max-width:720px){.gl{columns:1}}
.gl dl{break-inside:avoid;margin:0 0 14px;padding:0 0 12px;border-bottom:1px solid var(--line)}
.gl dt{font:650 1rem var(--font-display);scroll-margin-top:110px}
.gl dd{margin:4px 0 0;font-size:.95rem;color:var(--ink-2)}
.gl dd .rel{display:block;margin-top:4px;font-size:.8rem;color:var(--muted)}
/* skeptics & sources */
.quoteblock{border-left:3px solid var(--line-2);padding-left:14px;margin:10px 0 16px;font-style:italic;color:var(--ink-2)}
.srcs{font-size:.86rem;color:var(--muted)}
.srcs a{color:var(--accent-ink)}
ol.plain{padding-left:1.2em;font-size:.95rem}
.kv{display:grid;grid-template-columns:max-content 1fr;gap:6px 14px;font-size:.95rem}
.kv b{font:600 .78rem var(--font-mono);color:var(--muted);letter-spacing:.06em;text-transform:uppercase;padding-top:3px}
@media (max-width:520px){.kv{grid-template-columns:1fr}.kv b{padding-top:6px}}
/* sheet */
.backdrop{position:fixed;inset:0;background:rgba(8,10,16,.55);z-index:60;opacity:0;pointer-events:none;transition:opacity .2s}
.backdrop.on{opacity:1;pointer-events:auto}
.sheet{position:fixed;left:0;right:0;bottom:0;z-index:70;background:var(--surface);border-radius:18px 18px 0 0;max-height:88vh;overflow:auto;transform:translateY(105%);transition:transform .25s ease;box-shadow:var(--shadow);border:1px solid var(--line)}
.sheet.on{transform:none}
@media (min-width:860px){.sheet{left:50%;right:auto;bottom:auto;top:6vh;width:min(820px,92vw);transform:translate(-50%,20px);opacity:0;border-radius:16px;max-height:88vh}.sheet.on{transform:translate(-50%,0);opacity:1}}
.sheet .sh{position:sticky;top:0;background:var(--surface);display:flex;gap:10px;align-items:center;padding:12px 18px;border-bottom:1px solid var(--line);z-index:1}
.sheet .sh h3{font-size:1.05rem;flex:1;min-width:0}
.sheet .sh button{border:1px solid var(--line-2);background:var(--surface);color:var(--ink);border-radius:999px;padding:6px 12px;font:600 .8rem var(--font-display);cursor:pointer}
.sheet .sb{padding:16px 18px 28px}
.sheet .sb p{font-size:.98rem}
.sheet .sb h4{margin:16px 0 6px}
.sheet .sb ul{padding-left:1.1em;font-size:.95rem}
.sheet .sb li{margin-bottom:.35em}
.sheet svg.dg{width:100%;height:auto;display:block;border:1px solid var(--line);border-radius:8px;background:var(--surface)}
.qa{border-left:2px solid var(--line-2);padding-left:12px;margin-bottom:10px}
.qa b{font:600 .95rem var(--font-display);display:block}
.qa p{margin:2px 0 0;font-size:.92rem;color:var(--ink-2)}
.quote{font-style:italic;color:var(--ink-2);margin:0 0 8px;padding-left:12px;border-left:2px solid var(--accent)}
.quote small{display:block;font-style:normal;font:.72rem var(--font-mono);color:var(--muted);margin-top:2px}
.mixbar{display:flex;height:12px;border-radius:4px;overflow:hidden;gap:2px;margin:8px 0 6px;background:transparent}
.mixbar span{display:block;background:var(--series);opacity:.9}
.mixbar span:nth-child(2){opacity:.7}.mixbar span:nth-child(3){opacity:.5}.mixbar span:nth-child(4){opacity:.35}.mixbar span:nth-child(5){opacity:.22}
.mixleg{font:.76rem var(--font-mono);color:var(--muted);display:flex;flex-wrap:wrap;gap:4px 12px}
.result{display:block;padding:10px 0;border-bottom:1px solid var(--line);text-decoration:none;color:var(--ink);cursor:pointer}
.result b{font:650 .95rem var(--font-display)}
.result .k{font:.7rem var(--font-mono);color:var(--muted);letter-spacing:.06em;text-transform:uppercase;margin-right:8px}
.result p{margin:2px 0 0;font-size:.88rem;color:var(--ink-2)}
.tip{position:fixed;z-index:80;pointer-events:none;background:var(--ink);color:var(--bg);font:500 .8rem var(--font-display);padding:6px 9px;border-radius:6px;max-width:260px;opacity:0;transition:opacity .12s}
.tip.on{opacity:1}
footer{padding:36px 0 60px;border-top:1px solid var(--line);font-size:.86rem;color:var(--muted)}
.callout{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:16px 18px;margin:16px 0}
.callout h4{margin-bottom:6px}
.callout ul{margin:0;padding-left:1.1em;font-size:.93rem}
.dlv{border:1px solid var(--line-2);border-radius:12px;padding:16px 18px;background:var(--surface);display:grid;grid-template-columns:1fr;gap:6px}
.dlv h3{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.twocol{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:20px 32px}
.hidden{display:none!important}
"""
