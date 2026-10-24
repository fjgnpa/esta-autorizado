(()=>{
"use strict";
/* tema claro/oscuro (aria-pressed = oscuro activo) */
const root=document.documentElement,dark=()=>(root.dataset.theme||(matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light"))==="dark";
const tb=document.querySelector(".theme");
if(tb){const sync=()=>tb.setAttribute("aria-pressed",String(dark()));sync();
 tb.addEventListener("click",()=>{const n=dark()?"light":"dark";root.dataset.theme=n;try{localStorage.setItem("theme",n)}catch(e){}sync()});}
/* aviso de datos desactualizados (>10 días desde la última comprobación) */
const stl=document.getElementById("stale");
if(stl&&stl.dataset.checked){const d=Math.floor((Date.now()-Date.parse(stl.dataset.checked+"T00:00:00Z"))/864e5);if(d>10){stl.hidden=false;const b=stl.querySelector("b");if(b)b.textContent="Datos posiblemente desactualizados (hace "+d+" días)."}}
/* normalización y coincidencia tolerante: sin acentos, sin espacios, 1-2 errores de tecleo */
const N=x=>(x||"").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g,"").replace(/[^a-z0-9]+/g," ").trim();
const osa=(a,b,max)=>{if(Math.abs(a.length-b.length)>max)return max+1;const m=a.length,n=b.length;let p2=[],p=Array.from({length:n+1},(_,j)=>j);
 for(let i=1;i<=m;i++){const c=[i];let lo=i;for(let j=1;j<=n;j++){const k=a[i-1]===b[j-1]?0:1;let v=Math.min(p[j]+1,c[j-1]+1,p[j-1]+k);if(i>1&&j>1&&a[i-1]===b[j-2]&&a[i-2]===b[j-1])v=Math.min(v,p2[j-2]+1);c[j]=v;if(v<lo)lo=v}
  if(lo>max)return max+1;p2=p;p=c}return p[n]};
const mk=s=>{const k=N(s);return{k,c:k.replace(/ /g,""),w:k.split(" ")}};
function score(keys,v){const vs=N(v),vc=vs.replace(/ /g,"");if(vc.length<2)return null;let best=null;const lim=vc.length>=8?2:vc.length>=5?1:0;
 for(const K of keys){let s=null;
  if(K.k.startsWith(vs))s=0;else if((" "+K.k).includes(" "+vs))s=1;else if(K.c.includes(vc))s=2;
  else if(lim){let d=lim+1;for(const w of K.w)if(w.length>=3)d=Math.min(d,osa(vc,w,lim));d=Math.min(d,osa(vc,K.c.slice(0,vc.length),lim),osa(vc,K.c,lim));if(d<=lim)s=3+d}
  if(s!==null&&(best===null||s<best))best=s}return best}
/* filtro de marcas.html */
const mf=document.getElementById("mf");
if(mf){const cards=[...document.querySelectorAll(".bc[data-st]")],secs=[...document.querySelectorAll("main .sec")],mc=document.getElementById("mc");let f="all";
 const keys=cards.map(c=>[mk(c.dataset.n),mk(c.querySelector("b").textContent)]);
 const grp=st=>st=="ok"?"ok":(st=="auto"||st=="nocr")?"neu":"no";
 const apply=()=>{const v=mf.value.slice(0,60);let n=0;cards.forEach((c,i)=>{const okf=f=="all"||grp(c.dataset.st)==f,okq=N(v).length<2||score(keys[i],v)!==null;const show=okf&&okq;c.classList.toggle("hidden",!show);if(show)n++});
  secs.forEach(s=>{if(s.querySelector(".bc[data-st]"))s.classList.toggle("hidden",!s.querySelector(".bc[data-st]:not(.hidden)"))});mc.textContent=n==cards.length?"":n+" de "+cards.length};
 mf.addEventListener("input",apply);document.querySelectorAll(".seg button").forEach(b=>b.addEventListener("click",()=>{f=b.dataset.f;document.querySelectorAll(".seg button").forEach(x=>x.setAttribute("aria-pressed",String(x===b)));apply()}))}
/* buscador (portada) */
const q=document.getElementById("q");if(!q)return;
const form=document.getElementById("buscar");if(form)form.addEventListener("submit",e=>{e.preventDefault();const x=cur[sel>=0?sel:0];if(x&&!ac.hidden&&sel>=0)pick(sel);else run(q.value,true)});
let loading=false;const pending=[];
function load(cb){if(cb)pending.push(cb);if(window.DB){init();return}if(loading)return;loading=true;const s=document.createElement("script");s.src="assets/data.js";s.onload=init;document.head.appendChild(s)}
let inited=false;
const C={AT:"Austria",BE:"Bélgica",BG:"Bulgaria",CY:"Chipre",CZ:"Chequia",DE:"Alemania",DK:"Dinamarca",EE:"Estonia",ES:"España",FI:"Finlandia",FR:"Francia",GR:"Grecia",EL:"Grecia",HR:"Croacia",HU:"Hungría",IE:"Irlanda",IS:"Islandia",IT:"Italia",LI:"Liechtenstein",LT:"Lituania",LU:"Luxemburgo",LV:"Letonia",MT:"Malta",NL:"Países Bajos",NO:"Noruega",PL:"Polonia",PT:"Portugal",RO:"Rumanía",SE:"Suecia",SI:"Eslovenia",SK:"Eslovaquia"};
const E=t=>String(t).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const SLUG=s=>/^[a-z0-9-]+$/.test(s)?s:"";
const STOP=new Set(["de","the","and","y"]);
const ini=s=>{const w=s.replace(/[()\/.,·]/g," ").split(/\s+/).filter(x=>/^[\p{L}\p{N}]/u.test(x)&&!STOP.has(x.toLowerCase()));
 if(w.length==1&&w[0].length>1&&!/^\d+$/.test(w[0])){const t=w[0].slice(0,2);return E(t===t.toUpperCase()?t:t[0].toUpperCase()+t[1].toLowerCase())}
 return E((w.slice(0,2).map(x=>x[0]).join("")||"?").toUpperCase())};
const PX={xs:24,sm:32,md:44};
const lg=(ref,name,sz)=>Array.isArray(ref)?`<span class="lg lg-${sz} lg-${E(ref[1])}"><img src="assets/logos/${E(ref[0])}" alt="" width="${PX[sz]}" height="${PX[sz]}" decoding="async"></span>`
 :`<span class="lg lg-${sz} mono" style="--a:${E(DB.pal[ref|0][0])};--b:${E(DB.pal[ref|0][1])}" aria-hidden="true">${ini(name)}</span>`;
const ck='<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M3.5 8.5l3 3 6-7" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',xx='<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M4.5 4.5l7 7m0-7l-7 7" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',mi='<svg viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="6" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M5.5 8h5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>';
const BL={nofig:["no",xx,"No figura en el registro MiCA","No figura"],auto:["neu",mi,"No aplica · monedero de autocustodia","No aplica"],nocr:["neu",mi,"Sin servicios cripto MiCA en el registro","Sin cripto MiCA"]};
let ents,brands,bySlug={},docs=[];
function init(){if(!inited){inited=true;ents=DB.e;brands=DB.b;ents.forEach(e=>bySlug[e[0]]=e);
 brands.forEach(b=>docs.push({t:"b",keys:[mk(b[0]),...b[8].map(mk)],n:b[0],d:b}));ents.forEach(e=>docs.push({t:"e",keys:[mk(e[1]),mk(e[2]),...e[8].map(mk)],n:e[1],d:e}));
 const p=(new URLSearchParams(location.search).get("q")||"").slice(0,60);if(p){q.value=p;run(p,true)}}
 while(pending.length)pending.shift()()}
function find(v){const sc=[];for(const x of docs){const s=score(x.keys,v);if(s===null)continue;sc.push([s*10+(x.t=="e"?3:0)+(x.t=="b"&&!x.d[1].length?1:0)+(x.keys[0].k.length/200),x])}
 sc.sort((a,b)=>a[0]-b[0]);const out=[],seen=new Set();for(const[,x]of sc){if(x.t=="b"){out.push(x);x.d[1].forEach(s=>seen.add(s))}else if(!seen.has(x.d[0])){seen.add(x.d[0]);out.push(x)}if(out.length>=12)break}return out}
function suggest(v){const vc=N(v).replace(/ /g,"");if(vc.length<3)return null;let best=null,bd=99;const max=Math.max(2,Math.floor(vc.length*.4));
 for(const x of docs){if(x.t=="e"&&x.d[8].length)continue;for(const K of x.keys){const d=Math.min(osa(vc,K.c,max),osa(vc,K.c.slice(0,vc.length),max)+1);if(d<bd){bd=d;best=x.n}}}return bd<=max?best:null}
const esP=e=>e[10]=="pend"?`<span class="pill pend">${cl}Autorizado, empieza el ${E(e[11])}</span>`:e[10]=="ret"?`<span class="pill no">${xx}Autorización retirada${e[11]?" · "+E(e[11]):""}</span>`:e[4]?`<span class="pill ok">${ck}Puede operar en España</span>`:`<span class="pill no">${xx}España no notificada</span>`;
const kP=e=>`<span class="pill ${E(e[5])}">${E(e[6])}<em>${E(e[7])}</em></span>`;
const vcls=e=>e[4]?"ok":e[10]=="pend"?"pend":"no";
const cl='<svg viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="6" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M8 4.8V8l2.2 1.5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>';
function ecard(e,b){const nm=b?b[0]:e[1];return `<a class="rc" href="${b?"marca/"+SLUG(b[5]):"p/"+SLUG(e[0])}.html"><span class="rc-v ${vcls(e)}" aria-hidden="true"></span>${lg(b?b[6]:e[9],nm,"md")}<div class="b"><h3>${E(nm)}</h3><div class="sub">${E(e[2])} · ${E(C[e[3]]||e[3])}</div><div class="pills">${esP(e)}${kP(e)}</div></div><span class="go" aria-hidden="true">→</span></a>`}
function bmiss(b){const s=BL[b[7]]||BL.nofig;return `<a class="rc miss" href="marca/${SLUG(b[5])}.html"><span class="rc-v ${s[0]}" aria-hidden="true"></span>${lg(b[6],b[0],"md")}<div class="b"><h3>${E(b[0])}</h3><div class="sub">${b[7]=="auto"?"Monedero de autocustodia":"Sin sociedad en el registro"} · registro ESMA a ${E(DB.m.date)}</div><div class="pills"><span class="pill ${s[0]}">${s[1]}${s[2]}</span>${b[3].length?`<span class="pill no">En la lista de no conformes de ESMA</span>`:""}</div>${b[2]?`<p class="muted" style="margin:.7em 0 0;font-size:14px">${E(b[2])}</p>`:""}</div><span class="go" aria-hidden="true">→</span></a>`}
const res=document.getElementById("res"),ac=document.getElementById("ac"),rcount=document.getElementById("rcount");let sel=-1,cur=[],tmr=0;
function announce(n,v){clearTimeout(tmr);tmr=setTimeout(()=>{if(rcount)rcount.textContent=!v||N(v).length<2?"":n?n+(n==1?" resultado":" resultados")+" para «"+v+"»":"Sin resultados para «"+v+"»"},600)}
function render(list,v){if(!v||N(v).length<2){res.innerHTML="";announce(0,"");return}
 if(!list.length){const sg=suggest(v);res.innerHTML=`<div class="rc empty"><div class="b"><h3>Sin resultados para «${E(v)}»</h3>${sg?`<p class="dym">¿Quisiste decir <button type="button" data-q="${E(sg)}">${E(sg)}</button>?</p>`:""}<div class="sub">No figura en el registro con ese nombre. La app puede operar con otra sociedad: busca el nombre jurídico en sus términos legales y compruébalo en el <a href="https://www.esma.europa.eu/esmas-activities/digital-finance-and-innovation/markets-crypto-assets-regulation-mica" rel="nofollow noopener noreferrer">registro de ESMA</a> y en la <a href="https://www.cnmv.es/portal/consultas/proveedores-servicios-criptoactivos?lang=es" rel="nofollow noopener noreferrer">CNMV</a>.</div></div></div>`;
  const bt=res.querySelector(".dym button");if(bt)bt.addEventListener("click",()=>{q.value=bt.dataset.q;run(bt.dataset.q,true);q.focus()});announce(0,v);return}
 const html=list.map(x=>x.t=="b"?(x.d[1].length?x.d[1].map(s=>ecard(bySlug[s],x.d)).join(""):bmiss(x.d)):ecard(x.d));res.innerHTML=html.join("");announce(res.children.length,v)}
function acr(list){cur=list.slice(0,7);sel=-1;if(!cur.length){ac.hidden=true;q.setAttribute("aria-expanded","false");return}
 ac.innerHTML=cur.map((x,i)=>{const nm=x.t=="b"?x.d[0]:x.d[1];let sub,st;if(x.t=="b"&&!x.d[1].length){const s=BL[x.d[7]]||BL.nofig;sub=x.d[7]=="auto"?"Monedero de autocustodia":"No figura en el registro";st=`<span class="st ${s[0]}">${s[1]}${s[3]}</span>`}else{const e=x.t=="b"?(x.d[1].map(s=>bySlug[s]).find(e=>e[4])||bySlug[x.d[1][0]]):x.d;sub=e[2]+" · "+(C[e[3]]||e[3]);st=e[10]=="pend"?`<span class="st pend">${cl}Empieza ${E(e[11])}</span>`:e[10]=="ret"?`<span class="st no">${xx}Retirada</span>`:e[4]?`<span class="st ok">${ck}España</span>`:`<span class="st no">${xx}Sin España</span>`}
  return `<li role="option" id="o${i}" aria-selected="false" data-i="${i}">${lg(x.t=="b"?x.d[6]:x.d[9],nm,"sm")}<span class="t"><b>${E(nm)}</b><small>${E(sub)}</small></span>${st}</li>`}).join("");ac.hidden=false;q.setAttribute("aria-expanded","true")}
function pick(i){const x=cur[i];if(!x)return;location.href=x.t=="b"?"marca/"+SLUG(x.d[5])+".html":"p/"+SLUG(x.d[0])+".html"}
function run(v,noac){v=(v||"").slice(0,60);if(!window.DB||!inited){load(()=>run(v,noac));return}const l=find(v);render(l,v);if(!noac)acr(l);else{ac.hidden=true;q.setAttribute("aria-expanded","false")}const u=new URL(location);v?u.searchParams.set("q",v):u.searchParams.delete("q");history.replaceState(null,"",u)}
q.addEventListener("input",()=>run(q.value));
["focus","pointerenter","touchstart"].forEach(ev=>q.addEventListener(ev,()=>load(),{once:true,passive:true}));
if(new URLSearchParams(location.search).get("q"))load();else (window.requestIdleCallback||(f=>setTimeout(f,2500)))(()=>load(),{timeout:4000});
q.addEventListener("keydown",e=>{if(ac.hidden)return;if(e.key=="ArrowDown"||e.key=="ArrowUp"){e.preventDefault();sel=(sel+(e.key=="ArrowDown"?1:-1)+cur.length)%cur.length;[...ac.children].forEach((li,i)=>li.setAttribute("aria-selected",String(i==sel)));q.setAttribute("aria-activedescendant","o"+sel)}else if(e.key=="Enter"&&sel>=0){e.preventDefault();pick(sel)}else if(e.key=="Escape"){ac.hidden=true;q.setAttribute("aria-expanded","false")}});
ac.addEventListener("mousedown",e=>{const li=e.target.closest("li");if(li){e.preventDefault();pick(+li.dataset.i)}});
q.addEventListener("blur",()=>setTimeout(()=>{ac.hidden=true;q.setAttribute("aria-expanded","false")},100));
document.addEventListener("keydown",e=>{if(e.key=="/"&&document.activeElement!==q&&!/input|textarea/i.test(document.activeElement.tagName)){e.preventDefault();q.focus()}});
document.querySelectorAll(".chip").forEach(c=>c.addEventListener("click",()=>{q.value=c.dataset.q;run(c.dataset.q,true);q.focus();ac.hidden=true;res.scrollIntoView({behavior:matchMedia("(prefers-reduced-motion: reduce)").matches?"auto":"smooth",block:"nearest"})}));
})();
