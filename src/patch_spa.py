#!/usr/bin/env python3
import re
P = "/sessions/upbeat-practical-goldberg/mnt/outputs/src/template.html"
t = open(P, encoding="utf-8").read()

def rep(old, new, label):
    global t
    assert old in t, f"ANCHOR NOT FOUND: {label}"
    t = t.replace(old, new, 1)
    print("patched:", label)

# 1. CSS additions
rep("footer{border-top:1px solid var(--border)", """mark.hl{background:var(--warn);color:#111;border-radius:3px;padding:0 2px}
.content h2{cursor:pointer;user-select:none}
.content h2 .caret{color:var(--muted);font-size:.8em}
.secbody.collapsed{display:none}
.opt.sel{border-color:var(--accent);background:color-mix(in srgb,var(--accent) 12%,var(--panel2))}
.ostep{display:flex;align-items:center;gap:10px;background:var(--panel2);border:1px solid var(--border);border-radius:10px;padding:10px 12px;margin:8px 0;font-size:.93rem}
.ostep .num{background:var(--accent);color:#fff;border-radius:6px;min-width:24px;height:24px;display:flex;align-items:center;justify-content:center;font-size:.8rem;font-weight:700}
.ostep.ok{border-color:var(--good)} .ostep.ko{border-color:var(--bad)}
.ostep .omv{padding:4px 10px}
.dbadge{margin-left:6px}
.mermaid{background:var(--panel2);border:1px solid var(--border);border-radius:10px;padding:14px;margin:14px 0;text-align:center;overflow:auto}
footer{border-top:1px solid var(--border)""", "css")

# 2. Search bar above study content
rep('    <div class="studywrap">', '''    <div class="card" style="margin-bottom:14px;display:flex;gap:8px;align-items:center;padding:10px 14px">
      <span>🔎</span>
      <input id="searchInp" placeholder="Search the study guide… (min 2 chars)" style="flex:1;background:var(--panel2);border:1px solid var(--border);border-radius:8px;padding:8px 12px;color:var(--text);font-family:inherit">
      <button class="btn" id="searchPrev" title="Previous match">↑</button>
      <button class="btn" id="searchNext" title="Next match">↓</button>
      <span id="searchCnt" style="color:var(--muted);font-size:.85rem;min-width:86px;text-align:right"></span>
    </div>
    <div class="studywrap">''', "searchbar")

# 3. Replace TOC IIFE with collapsible + TOC version
old_toc = """(function(){
  const toc=document.getElementById("toc");
  document.querySelectorAll("#content h2").forEach((h,i)=>{
    h.id="sec-"+i;
    const a=document.createElement("a");a.href="#sec-"+i;a.textContent=h.textContent;toc.appendChild(a);
  });
  const links=[...toc.querySelectorAll("a")];"""
new_toc = """(function(){
  const toc=document.getElementById("toc");
  const content=document.getElementById("content");
  [...content.querySelectorAll("h2")].forEach((h,i)=>{
    h.id="sec-"+i;
    const a=document.createElement("a");a.href="#sec-"+i;a.textContent=h.textContent;toc.appendChild(a);
    const body=document.createElement("div");body.className="secbody";
    let n=h.nextSibling;
    while(n&&!(n.nodeType===1&&n.tagName==="H2")){const nx=n.nextSibling;body.appendChild(n);n=nx}
    h.parentNode.insertBefore(body,h.nextSibling);
    const caret=document.createElement("span");caret.className="caret";caret.textContent=" ▾";h.appendChild(caret);
    h.addEventListener("click",()=>{body.classList.toggle("collapsed");caret.textContent=body.classList.contains("collapsed")?" ▸":" ▾"});
    a.addEventListener("click",()=>{body.classList.remove("collapsed");caret.textContent=" ▾"});
  });
  const links=[...toc.querySelectorAll("a")];"""
rep(old_toc, new_toc, "toc+collapsible")

# 4. Replace renderQ with multi-type engine
old_rq_start = 'function renderQ(){\n  if(qIdx>=qSet.length){return renderScore()}\n  const q=qSet[qIdx];\n  const opts=shuffle(q.o.map((t,i)=>({t,ok:i===q.a})));'
assert old_rq_start in t, "renderQ anchor"
start = t.index("function renderQ(){")
end = t.index("function renderScore(){")
new_rq = '''function qHead(q){
  const db=q.d?(q.d===1?'<span class="dbadge" title="easy">🟢</span>':q.d===2?'<span class="dbadge" title="medium">🟡</span>':'<span class="dbadge" title="hard">🔴</span>'):"";
  return `<div class="progressbar"><div style="width:${(qIdx/qSet.length)*100}%"></div></div>
    <div class="qmeta"><span>Question ${qIdx+1} / ${qSet.length} · ${CATNAMES[q.c]||q.c}${db}</span><span>Score: ${qScore}</span></div>
    <div class="qtext">${q.q}</div>`;
}
function qFoot(){return `<div class="explain" id="explain"></div>
    <div style="margin-top:16px;text-align:right"><button class="btn primary" id="qNext" disabled>Next →</button></div>`}
function wireNext(){document.getElementById("qNext").addEventListener("click",()=>{qIdx++;renderQ()})}
function showExplain(right,extra,q){
  const ex=document.getElementById("explain");
  ex.innerHTML=(right?"✅ <strong>Correct.</strong> ":"❌ <strong>Not quite.</strong> ")+(extra||"")+q.e;
  ex.style.display="block";
  document.getElementById("qNext").disabled=false;
}
function renderQ(){
  if(qIdx>=qSet.length){return renderScore()}
  const q=qSet[qIdx];
  if(q.t==="multi")return renderMulti(q);
  if(q.t==="order")return renderOrder(q);
  const opts=shuffle(q.o.map((t,i)=>({t,ok:i===q.a})));
  quizArea.innerHTML=qHead(q)+
    `<div id="opts">${opts.map((o,i)=>`<button class="opt" data-ok="${o.ok?1:0}">${String.fromCharCode(65+i)}. ${o.t}</button>`).join("")}`+qFoot();
  const btns=[...quizArea.querySelectorAll(".opt")];
  btns.forEach(b=>b.addEventListener("click",()=>{
    btns.forEach(x=>{x.disabled=true;if(x.dataset.ok==="1")x.classList.add("correct")});
    const right=b.dataset.ok==="1";
    if(right)qScore++;else{b.classList.add("wrong");qWrong.push(q)}
    showExplain(right,"",q);
  }));
  wireNext();
}
function renderMulti(q){
  const opts=shuffle(q.o.map((t,i)=>({t,i})));
  quizArea.innerHTML=qHead(q)+
    `<p style="color:var(--muted);font-size:.85rem;margin-bottom:8px">Multi-select — choose all that apply, then submit.</p>
     <div id="opts">${opts.map((o,i)=>`<button class="opt" data-i="${o.i}">${String.fromCharCode(65+i)}. ${o.t}</button>`).join("")}</div>
     <div style="margin-top:12px"><button class="btn primary" id="qSubmit">Submit answer</button></div>`+qFoot();
  const btns=[...quizArea.querySelectorAll(".opt")];
  btns.forEach(b=>b.addEventListener("click",()=>{if(!b.disabled)b.classList.toggle("sel")}));
  document.getElementById("qSubmit").addEventListener("click",()=>{
    const sel=new Set(btns.filter(b=>b.classList.contains("sel")).map(b=>+b.dataset.i));
    const ans=new Set(q.a);
    const right=sel.size===ans.size&&[...sel].every(x=>ans.has(x));
    btns.forEach(b=>{b.disabled=true;const i=+b.dataset.i;
      if(ans.has(i))b.classList.add("correct");else if(sel.has(i))b.classList.add("wrong")});
    document.getElementById("qSubmit").disabled=true;
    if(right)qScore++;else qWrong.push(q);
    showExplain(right,"",q);
  });
  wireNext();
}
function renderOrder(q){
  let arr=shuffle(q.o.map((t,i)=>({t,i})));
  if(arr.every((x,k)=>x.i===k))arr=arr.slice().reverse();
  quizArea.innerHTML=qHead(q)+
    `<p style="color:var(--muted);font-size:.85rem;margin-bottom:8px">Ordering — arrange the steps with ▲▼, then check.</p>
     <div id="osteps"></div>
     <div style="margin-top:12px"><button class="btn primary" id="qCheck">Check order</button></div>`+qFoot();
  const box=document.getElementById("osteps");
  function draw(){
    box.innerHTML=arr.map((s,k)=>`<div class="ostep"><span class="num">${k+1}</span><span style="flex:1">${s.t}</span>
      <button class="btn omv" data-k="${k}" data-d="-1" ${k===0?"disabled":""}>▲</button>
      <button class="btn omv" data-k="${k}" data-d="1" ${k===arr.length-1?"disabled":""}>▼</button></div>`).join("");
    [...box.querySelectorAll(".omv")].forEach(b=>b.addEventListener("click",()=>{
      const k=+b.dataset.k,d=+b.dataset.d;[arr[k],arr[k+d]]=[arr[k+d],arr[k]];draw();
    }));
  }
  draw();
  document.getElementById("qCheck").addEventListener("click",()=>{
    const right=arr.every((x,k)=>x.i===k);
    [...box.querySelectorAll(".ostep")].forEach((el,k)=>el.classList.add(arr[k].i===k?"ok":"ko"));
    [...box.querySelectorAll(".omv")].forEach(b=>b.disabled=true);
    document.getElementById("qCheck").disabled=true;
    if(right)qScore++;else qWrong.push(q);
    showExplain(right,right?"":"Correct order:<br>"+q.o.map((s,i)=>(i+1)+". "+s).join("<br>")+"<br><br>",q);
  });
  wireNext();
}
'''
t = t[:start] + new_rq + t[end:]
print("patched: renderQ engine")

# 5. Search + Mermaid, inserted before buildDeck(true);
extra_js = '''
/* ---------- SEARCH ---------- */
(function(){
  const inp=document.getElementById("searchInp"),cnt=document.getElementById("searchCnt");
  let marks=[],pos=-1,tm;
  function clear(){marks.forEach(m=>{const p=m.parentNode;if(p){p.replaceChild(document.createTextNode(m.textContent),m);p.normalize()}});marks=[];pos=-1;cnt.textContent=""}
  function run(){
    clear();
    const qy=inp.value.trim().toLowerCase();
    if(qy.length<2)return;
    document.querySelectorAll(".secbody").forEach(s=>s.classList.remove("collapsed"));
    document.querySelectorAll("#content h2 .caret").forEach(c=>c.textContent=" ▾");
    const walker=document.createTreeWalker(document.getElementById("content"),NodeFilter.SHOW_TEXT);
    const nodes=[];let n;
    while(n=walker.nextNode()){if(n.textContent.toLowerCase().includes(qy))nodes.push(n)}
    nodes.forEach(node=>{
      const txt=node.textContent,lower=txt.toLowerCase();
      const frag=document.createDocumentFragment();let i=0,j;
      while((j=lower.indexOf(qy,i))!==-1){
        frag.appendChild(document.createTextNode(txt.slice(i,j)));
        const mk=document.createElement("mark");mk.className="hl";mk.textContent=txt.slice(j,j+qy.length);
        frag.appendChild(mk);marks.push(mk);i=j+qy.length;
      }
      frag.appendChild(document.createTextNode(txt.slice(i)));
      node.parentNode.replaceChild(frag,node);
    });
    cnt.textContent=marks.length?marks.length+" matches":"no matches";
    if(marks.length)go(0);
  }
  function go(k){
    if(!marks.length)return;
    if(pos>=0&&marks[pos])marks[pos].style.outline="";
    pos=(k+marks.length)%marks.length;
    marks[pos].style.outline="2px solid var(--accent)";
    marks[pos].scrollIntoView({block:"center"});
    cnt.textContent=(pos+1)+" / "+marks.length;
  }
  inp.addEventListener("input",()=>{clearTimeout(tm);tm=setTimeout(run,300)});
  inp.addEventListener("keydown",e=>{if(e.key==="Enter"){e.preventDefault();go(pos+1)}});
  document.getElementById("searchNext").addEventListener("click",()=>go(pos+1));
  document.getElementById("searchPrev").addEventListener("click",()=>go(pos-1));
})();
/* ---------- MERMAID ---------- */
(function(){
  const blocks=[...document.querySelectorAll("#content code.language-mermaid, #content code.mermaid")];
  if(!blocks.length)return;
  const s=document.createElement("script");
  s.src="https://cdnjs.cloudflare.com/ajax/libs/mermaid/10.9.3/mermaid.min.js";
  s.onload=()=>{
    try{
      blocks.forEach(c=>{
        const d=document.createElement("div");d.className="mermaid";d.textContent=c.textContent;
        const pre=c.closest("pre");pre.parentNode.replaceChild(d,pre);
      });
      window.mermaid.initialize({startOnLoad:false,theme:document.body.dataset.theme==="dark"?"dark":"neutral",securityLevel:"loose"});
      window.mermaid.run({querySelector:".mermaid"});
    }catch(e){console.warn("mermaid render skipped",e)}
  };
  s.onerror=()=>console.warn("mermaid CDN unavailable — diagrams shown as code");
  document.head.appendChild(s);
})();
buildDeck(true);'''
rep("buildDeck(true);", extra_js, "search+mermaid")

open(P, "w", encoding="utf-8").write(t)
print("template.html updated:", len(t), "chars")
