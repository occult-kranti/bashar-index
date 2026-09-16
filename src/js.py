JS = r"""
(function(){
'use strict';
const $=(s,r=document)=>r.querySelector(s), $$=(s,r=document)=>Array.from(r.querySelectorAll(s));
const esc=s=>String(s==null?'':s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function J(id){try{return JSON.parse($('#'+id).textContent);}catch(e){console.warn('bad json',id,e);return null;}}
const VIDEOS=J('d-videos')||[], DIAGRAMS=J('d-diagrams')||[], GLOSS=J('d-glossary')||[], INDEX=J('d-index')||[], TAGS=J('d-tags')||{};
const VID=Object.fromEntries(VIDEOS.map(v=>[v.video_id,v])), DG=Object.fromEntries(DIAGRAMS.map(d=>[d.id,d])), GL=Object.fromEntries(GLOSS.map(g=>[g.slug,g]));
const CLUSTERS=J('d-clusters')||[];

/* theme */
const root=document.documentElement;
try{const t=localStorage.getItem('bx-theme'); if(t==='dark'||t==='light') root.setAttribute('data-theme',t);}catch(e){}
$('#themeBtn')?.addEventListener('click',()=>{
  const cur=root.getAttribute('data-theme'); const sys=matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light';
  const now=(cur||sys)==='dark'?'light':'dark'; root.setAttribute('data-theme',now);
  try{localStorage.setItem('bx-theme',now);}catch(e){}
});

/* nav active */
const chips=$$('.chips a.chip'); const secs=chips.map(c=>$(c.getAttribute('href'))).filter(Boolean);
if('IntersectionObserver' in window){
  const io=new IntersectionObserver(es=>{es.forEach(e=>{if(e.isIntersecting){chips.forEach(c=>c.removeAttribute('aria-current'));const c=chips.find(x=>x.getAttribute('href')==='#'+e.target.id);if(c){c.setAttribute('aria-current','true');c.scrollIntoView({block:'nearest',inline:'center',behavior:'smooth'});}}});},{rootMargin:'-40% 0px -55% 0px'});
  secs.forEach(s=>io.observe(s));
}

/* tooltip */
const tip=$('#tip');
document.addEventListener('mouseover',e=>{const t=e.target.closest('[data-tip]'); if(!t){tip.classList.remove('on');return;} tip.textContent=t.getAttribute('data-tip'); tip.classList.add('on');});
document.addEventListener('mousemove',e=>{if(!tip.classList.contains('on'))return; const w=tip.offsetWidth,h=tip.offsetHeight; let x=e.clientX+14,y=e.clientY+14; if(x+w>innerWidth-8)x=e.clientX-w-10; if(y+h>innerHeight-8)y=e.clientY-h-10; tip.style.left=x+'px';tip.style.top=y+'px';});
document.addEventListener('mouseout',e=>{if(e.target.closest('[data-tip]'))tip.classList.remove('on');});

/* sheet + routing */
const sheet=$('#sheet'), back=$('#backdrop'), sb=$('#sheetBody'), st=$('#sheetTitle');
let lastFocus=null;
function openSheet(title,html){lastFocus=document.activeElement; st.textContent=title; sb.innerHTML=html; sheet.classList.add('on'); back.classList.add('on'); sheet.scrollTop=0; document.body.style.overflow='hidden'; $('#sheetClose').focus();}
function closeSheet(){sheet.classList.remove('on'); back.classList.remove('on'); document.body.style.overflow=''; if(location.hash.startsWith('#/')) history.replaceState(null,'',location.pathname+location.search); if(lastFocus&&lastFocus.focus) lastFocus.focus();}
$('#sheetClose').addEventListener('click',closeSheet); back.addEventListener('click',closeSheet);
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&sheet.classList.contains('on'))closeSheet();});
$('#sheetLink').addEventListener('click',()=>{const u=location.href; if(navigator.clipboard){navigator.clipboard.writeText(u).then(()=>{$('#sheetLink').textContent='Link copied';setTimeout(()=>$('#sheetLink').textContent='Copy link',1500);});}});
function go(h){history.replaceState(null,'',h); route();}
function route(){
  const h=location.hash||'';
  let m;
  if((m=h.match(/^#\/video\/([A-Za-z0-9_-]{11})/))){renderVideo(m[1]);return;}
  if((m=h.match(/^#\/diagram\/([a-z0-9-]+)/))){renderDiagram(m[1]);return;}
  if((m=h.match(/^#\/term\/([a-z0-9-]+)/))){renderTerm(m[1]);return;}
  if((m=h.match(/^#\/search\/(.+)/))){doSearch(decodeURIComponent(m[1]));return;}
  if((m=h.match(/^#\/cluster\/(\d+)/))){renderCluster(+m[1]);return;}
}
window.addEventListener('hashchange',route);
document.addEventListener('click',e=>{
  const a=e.target.closest('[data-go]'); if(a){e.preventDefault(); go(a.getAttribute('data-go'));}
});

const TAGL=TAGS;
function tagPills(tp,n=5){const arr=Object.entries(tp||{}).sort((a,b)=>b[1]-a[1]).slice(0,n).filter(x=>x[1]>0); return arr;}
function mixBar(tp){const arr=tagPills(tp,5); const tot=arr.reduce((s,x)=>s+x[1],0)||1; return '<div class="mixbar">'+arr.map(x=>`<span style="width:${(100*x[1]/tot).toFixed(1)}%" data-tip="${esc(TAGL[x[0]]||x[0])}: ${x[1]}%"></span>`).join('')+'</div><div class="mixleg">'+arr.map(x=>`<span>${esc(TAGL[x[0]]||x[0])} ${x[1]}%</span>`).join('')+'</div>';}
function termLink(t){const s=slug(t); if(GL[s]) return `<a class="pill" data-go="#/term/${s}">${esc(t)}</a>`; const k=Object.keys(GL).find(k=>k.includes(s)||s.includes(k)); return `<span class="pill">${esc(t)}</span>`;}
function slug(s){return String(s).toLowerCase().replace(/[’']/g,'').replace(/[^a-z0-9]+/g,'-').replace(/^-+|-+$/g,'');}

function renderVideo(id){
  const v=VID[id]; if(!v){openSheet('Not found','<p>No digest for that video id.</p>');return;}
  const cl=CLUSTERS.find(c=>c.id===v.cluster);
  const rel=cl?cl.members.filter(m=>m!==id).slice(0,4).map(m=>VID[m]).filter(Boolean):[];
  const qa=(v.qa_topics||[]).map(q=>`<div class="qa"><b>${esc(q.question)}</b><p>${esc(q.answer_gist)}</p></div>`).join('');
  const quotes=(v.quotes||[]).map(q=>`<p class="quote">“${esc(q.quote)}”<small>${esc(q.context||'')} · from the public auto-transcript, unverified against audio</small></p>`).join('');
  const terms=(v.key_terms||[]).slice(0,30).map(k=>termLink(k.term)).join(' ');
  const preds=(v.predictions_and_dates||[]).map(p=>`<li>${esc(typeof p==='string'?p:JSON.stringify(p))}</li>`).join('');
  const tools=(v.tools_or_exercises||[]).map(p=>`<li>${esc(typeof p==='string'?p:(p.tool||JSON.stringify(p)))}</li>`).join('');
  const ents=(v.named_entities||[]).map(p=>esc(typeof p==='string'?p:JSON.stringify(p))).join(' · ');
  const meta=[v.content_type, v.channel?('channel: '+v.channel):'', v.show?('show: '+v.show):'', v.year?(`${v.year_reliable?'':'~'}${v.year} (${v.year_basis})`):'year unknown', v.approx_word_count?('~'+Number(v.approx_word_count).toLocaleString()+' transcript words'):''].filter(Boolean).join(' · ');
  const html=`<p class="mono" style="letter-spacing:.04em;text-transform:none;font-size:.78rem">${esc(meta)}</p>
  <p><a href="${esc(v.url)}" target="_blank" rel="noopener">Watch on YouTube ↗</a>${v.official?' · <span class="badge k1">official channel</span>':' · <span class="badge k3">third-party upload</span>'}${cl?` · <a data-go="#/cluster/${cl.id}">archetype: ${esc(cl.name)}</a>`:''}</p>
  ${v.researcher_note?`<div class="notice" style="margin-top:0;font-size:.88rem"><b>Researcher note.</b> ${esc(v.researcher_note)}</div>`:''}
  <h4>Topic mix (model estimate)</h4>${mixBar(v.topic_percentages)}
  <h4>Opening / summary</h4><p>${esc(v.opening_summary)}</p>
  ${qa?`<h4>Questions & answers (${(v.qa_topics||[]).length} paraphrased)</h4>${qa}`:''}
  ${quotes?`<h4>Short quotes</h4>${quotes}`:''}
  ${terms?`<h4>Key terms</h4><div class="links">${terms}</div>`:''}
  ${preds?`<h4>Dates & predictions mentioned</h4><ul>${preds}</ul>`:''}
  ${tools?`<h4>Tools & exercises referenced</h4><ul>${tools}</ul>`:''}
  ${ents?`<h4>Named beings, places, civilizations</h4><p class="small">${ents}</p>`:''}
  ${rel.length?`<h4>Related recordings (same archetype)</h4>${rel.map(r=>`<a class="result" data-go="#/video/${r.video_id}"><span class="k">${esc(r.content_type)}</span><b>${esc(r.title)}</b></a>`).join('')}`:''}
  <p class="small" style="margin-top:18px">This digest is an AI-generated structured summary of a public auto-transcript. It is not a transcript and not affiliated with Bashar Communications; full recordings are sold on BasharTV.</p>`;
  openSheet(v.title,html);
}
function renderDiagram(slugId){
  const d=DG[slugId]; if(!d){openSheet('Not found','<p>No diagram with that id.</p>');return;}
  const fig=$('#dg-'+slugId+' svg'); const svg=fig?fig.outerHTML:'';
  const labels=(d.key_labels||[]).slice(0,20).map(l=>`<li>${esc(l)}</li>`).join('');
  const steps=(d.steps_or_layers||[]).map(l=>`<li>${esc(l)}</li>`).join('');
  const srcs=(d.sources||[]).slice(0,8).map(u=>`<li><a href="${esc(u)}" target="_blank" rel="noopener">${esc(u.replace(/^https?:\/\//,'').slice(0,70))}</a></li>`).join('');
  const html=`<p><span class="badge ${d.kind_class}">${esc(d.kind)}</span> <span class="badge">confidence: ${esc(d.confidence)}</span></p>
  ${svg}
  ${d.session?`<p class="mono" style="text-transform:none;letter-spacing:.02em;font-size:.78rem;margin-top:10px">${esc(d.session)}</p>`:''}
  <h4>What it means</h4><p>${esc(d.concept_summary)}</p>
  <h4>How to read it / what is known about the original</h4><p>${esc(d.visual_structure)}</p>
  ${steps?`<h4>Steps or layers</h4><ol>${steps}</ol>`:''}
  ${labels?`<h4>Labels attested in sources</h4><ul>${labels}</ul>`:''}
  ${d.notes?`<h4>Notes</h4><p>${esc(d.notes)}</p>`:''}
  ${d.official_handout_url?`<p><a href="${esc(d.official_handout_url)}" target="_blank" rel="noopener">Official handout PDF on bashar.org ↗</a></p>`:''}
  ${srcs?`<h4>Sources</h4><ul class="srcs">${srcs}</ul>`:''}
  <p class="small">Original redrawing of the concept for study purposes; not a reproduction of the copyrighted handout artwork. © concepts Bashar Communications.</p>`;
  openSheet(d.name,html);
}
function renderTerm(s){
  const g=GL[s]; if(!g){openSheet('Not found','<p>No glossary entry.</p>');return;}
  const rel=(g.related||[]).map(r=>{const rs=slug(r); return GL[rs]?`<a class="pill" data-go="#/term/${rs}">${esc(r)}</a>`:`<span class="pill">${esc(r)}</span>`;}).join(' ');
  const vids=VIDEOS.filter(v=>(v.key_terms||[]).some(k=>slug(k.term)===s)||(v.title||'').toLowerCase().includes(g.term.toLowerCase())).slice(0,6);
  const srcs=(g.sources||[]).slice(0,5).map(u=>`<li><a href="${esc(u)}" target="_blank" rel="noopener">${esc(u.replace(/^https?:\/\//,'').slice(0,70))}</a></li>`).join('');
  const dg=DIAGRAMS.filter(d=>d.name.toLowerCase().includes(g.term.toLowerCase().split(' ')[0])&&g.term.length>4).slice(0,3);
  openSheet(g.term,`<p>${esc(g.definition)}</p>${rel?`<h4>Related</h4><div class="links">${rel}</div>`:''}${dg.length?`<h4>Diagrams</h4>${dg.map(d=>`<a class="result" data-go="#/diagram/${d.id}"><b>${esc(d.name)}</b></a>`).join('')}`:''}${vids.length?`<h4>Appears in</h4>${vids.map(v=>`<a class="result" data-go="#/video/${v.video_id}"><span class="k">${esc(v.content_type)}</span><b>${esc(v.title)}</b></a>`).join('')}`:''}${srcs?`<h4>Sources</h4><ul class="srcs">${srcs}</ul>`:''}`);
}
function renderCluster(id){
  const c=CLUSTERS.find(x=>x.id===id); if(!c)return;
  const mem=c.members.map(m=>VID[m]).filter(Boolean);
  openSheet('Archetype: '+c.name,`<p class="small">${mem.length} recordings · mean length ~${Number(c.mean_words).toLocaleString()} words · dominant tags: ${c.top_tags.map(t=>esc(t.label)+' '+t.mean_pct+'%').join(', ')}</p><p class="small">Top vocabulary: ${c.top_terms.slice(0,10).map(esc).join(', ')}</p>${mem.map(v=>`<a class="result" data-go="#/video/${v.video_id}"><span class="k">${esc(v.content_type)}</span><b>${esc(v.title)}</b><p>${esc((v.opening_summary||'').slice(0,140))}…</p></a>`).join('')}`);
}

/* search */
function doSearch(q){
  q=q.trim(); if(!q){return;}
  const terms=q.toLowerCase().split(/\s+/).filter(Boolean);
  const hits=INDEX.map(it=>{const hay=(it.t+' '+(it.s||'')+' '+(it.x||'')).toLowerCase(); let sc=0; for(const t of terms){ if(!hay.includes(t)) return null; sc+= it.t.toLowerCase().includes(t)?3:1; } return {it,sc};}).filter(Boolean).sort((a,b)=>b.sc-a.sc);
  const groups={}; hits.forEach(h=>{(groups[h.it.k]=groups[h.it.k]||[]).push(h.it);});
  const order=['glossary','diagram','video','teaching','podcast','session','timeline'];
  let html=`<p class="small">${hits.length} results for “${esc(q)}”</p>`;
  const GN={glossary:'Glossary terms',diagram:'Diagrams',video:'Recordings',teaching:'Teachings',podcast:'Podcasts',session:'Session catalog',timeline:'Timeline'};
  const cutw=(t,n)=>t.length<=n?t:t.slice(0,n).replace(/\s+\S*$/,'')+'…';
  order.forEach(k=>{const g=groups[k]; if(!g)return; html+=`<h4>${GN[k]||k} (${g.length})</h4>`+g.slice(0,12).map(it=>`<a class="result" ${it.h.startsWith('#/')?`data-go="${it.h}"`:`href="${esc(it.h)}" ${it.h.startsWith('http')?'target="_blank" rel="noopener"':''}`}><span class="k">${esc(it.s||'')}</span><b>${esc(it.t)}</b>${it.x?`<p>${esc(cutw(it.x,150))}</p>`:''}</a>`).join(''); if(g.length>12) html+=`<p class="small">…and ${g.length-12} more</p>`;});
  if(!hits.length) html+='<p>Nothing matched. Try a Bashar term (e.g. “permission slip”, “Yahyel”, “2027”) or a session title.</p>';
  openSheet('Search',html);
}
const sin=$('#q'); let stimer;
sin.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault(); if(sin.value.trim()) go('#/search/'+encodeURIComponent(sin.value.trim()));}});
sin.addEventListener('input',()=>{clearTimeout(stimer); const v=sin.value.trim(); if(v.length>=3) stimer=setTimeout(()=>go('#/search/'+encodeURIComponent(v)),350);});

/* timeline show all */
$('#tlmore')?.addEventListener('click',()=>{$$('.tl-more').forEach(e=>e.hidden=false); $('#tlmore').hidden=true;});
/* library tabs */
$$('.tab').forEach(t=>t.addEventListener('click',()=>{$$('.tab').forEach(x=>x.setAttribute('aria-selected','false')); t.setAttribute('aria-selected','true'); $$('.panel').forEach(p=>p.hidden=(p.id!==t.getAttribute('data-panel')));}));
/* video filters */
function vfilter(){
  const q=($('#vq').value||'').toLowerCase(), ty=$('#vtype').value, yr=$('#vyear').value, tg=$('#vtag').value; let n=0;
  $$('#vgrid .vcard').forEach(c=>{const ok=(!ty||c.dataset.type===ty)&&(!yr||c.dataset.year===yr)&&(!tg||c.dataset.tags.includes(tg))&&(!q||c.dataset.text.includes(q)); c.hidden=!ok; if(ok)n++;});
  $('#vcount').textContent=n+' of '+VIDEOS.length;
}
['vq','vtype','vyear','vtag'].forEach(id=>$('#'+id)?.addEventListener('input',vfilter)); vfilter();
/* catalog */
const PAGE=60; let shown=PAGE;
function cfilter(){const q=($('#cq').value||'').toLowerCase(), dec=$('#cdec').value; let n=0, vis=0;
  $$('#cat tbody tr').forEach(tr=>{const ok=(!dec||tr.dataset.dec===dec)&&(!q||tr.dataset.text.includes(q)); if(ok){n++; tr.classList.toggle('hid',vis>=shown); if(vis<shown)vis++; tr.dataset.match='1';} else {tr.classList.add('hid'); tr.dataset.match='0';}});
  $('#ccount').textContent=n+' sessions'; $('#cmore').hidden=(vis>=n);}
$('#cq').addEventListener('input',()=>{shown=PAGE;cfilter();}); $('#cdec').addEventListener('input',()=>{shown=PAGE;cfilter();});
$('#cmore').addEventListener('click',()=>{shown+=PAGE;cfilter();}); cfilter();
/* podcasts */
$('#pq')?.addEventListener('input',()=>{const q=$('#pq').value.toLowerCase(); $$('#pod .row').forEach(r=>r.hidden=!(r.dataset.text.includes(q)));});
/* diagram filter */
$$('#dfilters .chip').forEach(b=>b.addEventListener('click',()=>{$$('#dfilters .chip').forEach(x=>x.classList.remove('on')); b.classList.add('on'); const k=b.dataset.k; $$('#dgrid figure').forEach(f=>f.hidden=!!(k&&f.dataset.k!==k));}));
$$('#dgrid figure').forEach(f=>{f.addEventListener('click',()=>go('#/diagram/'+f.dataset.id)); f.setAttribute('tabindex','0'); f.addEventListener('keydown',e=>{if(e.key==='Enter')go('#/diagram/'+f.dataset.id);});});
$$('.vcard').forEach(c=>{c.addEventListener('click',()=>go('#/video/'+c.dataset.id)); c.setAttribute('tabindex','0'); c.addEventListener('keydown',e=>{if(e.key==='Enter')go('#/video/'+c.dataset.id);});});
$$('.map .pt.hi').forEach(p=>p.addEventListener('click',()=>{const v=p.getAttribute('data-vid'); if(v)go('#/video/'+v);}));
route();
})();
"""
