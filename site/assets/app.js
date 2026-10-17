(()=>{
/* tema claro/oscuro */
const tb=document.querySelector(".theme");if(tb)tb.addEventListener("click",()=>{const r=document.documentElement,n=(r.dataset.theme||(matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light"))==="dark"?"light":"dark";r.dataset.theme=n;try{localStorage.setItem("theme",n)}catch(e){}});
const N=x=>(x||"").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g,"").replace(/[^a-z0-9]+/g," ").trim();
/* filtro de marcas.html */
const mf=document.getElementById("mf");
if(mf){const cards=[...document.querySelectorAll(".bc[data-st]")],secs=[...document.querySelectorAll("main .sec")],mc=document.getElementById("mc");let f="all";
 const apply=()=>{const v=N(mf.value);let n=0;cards.forEach(c=>{const st=c.dataset.st,okf=f=="all"||(f=="ok"?st=="ok":st!="ok"),okq=!v||N(c.dataset.n+" "+c.textContent).includes(v);const show=okf&&okq;c.classList.toggle("hidden",!show);if(show)n++});
  secs.forEach(s=>{if(s.querySelector(".bc[data-st]"))s.classList.toggle("hidden",!s.querySelector(".bc[data-st]:not(.hidden)"))});mc.textContent=n==cards.length?"":n+" de "+cards.length};
 mf.addEventListener("input",apply);document.querySelectorAll(".seg button").forEach(b=>b.addEventListener("click",()=>{f=b.dataset.f;document.querySelectorAll(".seg button").forEach(x=>x.setAttribute("aria-pressed",x===b));apply()}))}
/* buscador (portada) */
const q=document.getElementById("q");if(!q)return;
const s=document.createElement("script");s.src="assets/data.js";s.onload=init;document.head.appendChild(s);
const C={AT:"Austria",BE:"Bélgica",BG:"Bulgaria",CY:"Chipre",CZ:"Chequia",DE:"Alemania",DK:"Dinamarca",EE:"Estonia",ES:"España",FI:"Finlandia",FR:"Francia",GR:"Grecia",EL:"Grecia",HR:"Croacia",HU:"Hungría",IE:"Irlanda",IS:"Islandia",IT:"Italia",LI:"Liechtenstein",LT:"Lituania",LU:"Luxemburgo",LV:"Letonia",MT:"Malta",NL:"Países Bajos",NO:"Noruega",PL:"Polonia",PT:"Portugal",RO:"Rumanía",SE:"Suecia",SI:"Eslovenia",SK:"Eslovaquia"};
const E=t=>String(t).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const STOP=new Set(["de","the","and","y"]);
const ini=s=>{const w=s.replace(/[()\/.,·]/g," ").split(/\s+/).filter(x=>/^[\p{L}\p{N}]/u.test(x)&&!STOP.has(x.toLowerCase()));
 if(w.length==1&&w[0].length>1&&!/^\d+$/.test(w[0])){const t=w[0].slice(0,2);return E(t===t.toUpperCase()?t:t[0].toUpperCase()+t[1].toLowerCase())}
 return E((w.slice(0,2).map(x=>x[0]).join("")||"?").toUpperCase())};
const PX={xs:24,sm:32,md:44};
const lg=(ref,name,sz)=>Array.isArray(ref)?`<span class="lg lg-${sz} lg-${ref[1]}"><img src="assets/logos/${E(ref[0])}" alt="" width="${PX[sz]}" height="${PX[sz]}" decoding="async"></span>`
 :`<span class="lg lg-${sz} mono" style="--a:${DB.pal[ref][0]};--b:${DB.pal[ref][1]}" aria-hidden="true">${ini(name)}</span>`;
const ck='<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M3.5 8.5l3 3 6-7" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',xx='<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M4.5 4.5l7 7m0-7l-7 7" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>';
let ents,brands,bySlug={},docs=[];
function init(){ents=DB.e;brands=DB.b;ents.forEach(e=>bySlug[e[0]]=e);
 brands.forEach(b=>docs.push({t:"b",k:N(b[0]),d:b}));ents.forEach(e=>docs.push({t:"e",k:N(e[1]+" "+e[2]+" "+e[8].join(" ")),d:e}));
 const p=new URLSearchParams(location.search).get("q");if(p){q.value=p;run(p,true)}}
function find(v){v=N(v);if(v.length<2)return[];const sc=[];for(const x of docs){const i=x.k.indexOf(v);if(i<0)continue;sc.push([(x.t=="b"?0:2)+(i==0?0:1)+(x.t=="b"&&!x.d[1].length?.5:0)+(x.k.length/200),x])}
 sc.sort((a,b)=>a[0]-b[0]);const out=[],seen=new Set();for(const[,x]of sc){if(x.t=="b"){out.push(x);x.d[1].forEach(s=>seen.add(s))}else if(!seen.has(x.d[0])){seen.add(x.d[0]);out.push(x)}if(out.length>=12)break}return out}
const esP=e=>e[4]?`<span class="pill ok">${ck}Puede operar en España</span>`:`<span class="pill no">${xx}España no notificada</span>`;
const kP=e=>`<span class="pill ${e[5]}">${E(e[6])}<em>${E(e[7])}</em></span>`;
function ecard(e,b){const nm=b?b[0]:e[1];return `<a class="rc" href="${b?"marca/"+b[5]:"p/"+e[0]}.html"><span class="rc-v ${e[4]?"ok":"no"}" aria-hidden="true"></span>${lg(b?b[6]:e[9],nm,"md")}<div class="b"><h3>${E(nm)}</h3><div class="sub">${E(e[2])} · ${E(C[e[3]]||e[3])}</div><div class="pills">${esP(e)}${kP(e)}</div></div><span class="go" aria-hidden="true">→</span></a>`}
function bmiss(b){return `<a class="rc miss" href="marca/${b[5]}.html"><span class="rc-v no" aria-hidden="true"></span>${lg(b[6],b[0],"md")}<div class="b"><h3>${E(b[0])}</h3><div class="sub">Sociedad: desconocida · búsqueda en el registro ESMA a ${E(DB.m.date)}</div><div class="pills"><span class="pill no">${xx}No figura en el registro MiCA</span>${b[3].length?`<span class="pill no">En la lista de no conformes de ESMA</span>`:""}</div>${b[2]?`<p class="muted" style="margin:.7em 0 0;font-size:14px">${E(b[2])}</p>`:""}</div><span class="go" aria-hidden="true">→</span></a>`}
const res=document.getElementById("res"),ac=document.getElementById("ac");let sel=-1,cur=[];
function render(list,v){if(!v||N(v).length<2){res.innerHTML="";return}
 if(!list.length){res.innerHTML=`<div class="rc empty"><div class="b"><h3>Sin resultados para «${E(v)}»</h3><div class="sub">No figura en el registro con ese nombre. La app puede operar con otra sociedad: busca el nombre jurídico en sus términos legales.</div><div class="pills" style="justify-content:center"><span class="pill unk">Desconocido</span></div></div></div>`;return}
 res.innerHTML=list.map(x=>x.t=="b"?(x.d[1].length?x.d[1].map(s=>ecard(bySlug[s],x.d)).join(""):bmiss(x.d)):ecard(x.d)).join("")}
function acr(list){cur=list.slice(0,7);sel=-1;if(!cur.length){ac.hidden=true;q.setAttribute("aria-expanded","false");return}
 ac.innerHTML=cur.map((x,i)=>{const nm=x.t=="b"?x.d[0]:x.d[1];let sub,st;if(x.t=="b"&&!x.d[1].length){sub="No figura en el registro";st=`<span class="st no">${xx}No figura</span>`}else{const e=x.t=="b"?bySlug[x.d[1][0]]:x.d;sub=e[2]+" · "+(C[e[3]]||e[3]);st=e[4]?`<span class="st ok">${ck}España</span>`:`<span class="st no">${xx}Sin España</span>`}
  return `<li role="option" id="o${i}" aria-selected="false" data-i="${i}">${lg(x.t=="b"?x.d[6]:x.d[9],nm,"sm")}<span class="t"><b>${E(nm)}</b><small>${E(sub)}</small></span>${st}</li>`}).join("");ac.hidden=false;q.setAttribute("aria-expanded","true")}
function pick(i){const x=cur[i];if(!x)return;location.href=x.t=="b"?"marca/"+x.d[5]+".html":"p/"+x.d[0]+".html"}
function run(v,noac){if(!window.DB)return;const l=find(v);render(l,v);if(!noac)acr(l);const u=new URL(location);v?u.searchParams.set("q",v):u.searchParams.delete("q");history.replaceState(null,"",u)}
q.addEventListener("input",()=>run(q.value));
q.addEventListener("keydown",e=>{if(ac.hidden)return;if(e.key=="ArrowDown"||e.key=="ArrowUp"){e.preventDefault();sel=(sel+(e.key=="ArrowDown"?1:-1)+cur.length)%cur.length;[...ac.children].forEach((li,i)=>li.setAttribute("aria-selected",i==sel));q.setAttribute("aria-activedescendant","o"+sel)}else if(e.key=="Enter"&&sel>=0){e.preventDefault();pick(sel)}else if(e.key=="Escape"){ac.hidden=true;q.setAttribute("aria-expanded","false")}});
ac.addEventListener("mousedown",e=>{const li=e.target.closest("li");if(li){e.preventDefault();pick(+li.dataset.i)}});
q.addEventListener("blur",()=>setTimeout(()=>{ac.hidden=true;q.setAttribute("aria-expanded","false")},100));
document.addEventListener("keydown",e=>{if(e.key=="/"&&document.activeElement!==q&&!/input|textarea/i.test(document.activeElement.tagName)){e.preventDefault();q.focus()}});
document.querySelectorAll(".chip").forEach(c=>c.onclick=()=>{q.value=c.dataset.q;run(c.dataset.q,true);q.focus();ac.hidden=true;res.scrollIntoView({behavior:matchMedia("(prefers-reduced-motion: reduce)").matches?"auto":"smooth",block:"nearest"})});
})();
