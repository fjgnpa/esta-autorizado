#!/usr/bin/env python3
import json, pathlib, html, shutil, hashlib, re
import os
R = pathlib.Path(__file__).resolve().parent.parent; S = R/"site"
BASE = os.environ.get("SITE_BASE", "https://fjgnpa.github.io/esta-autorizado/")
CFG = json.load(open(R/"data/config.json"))
d = json.load(open(R/"data/build.json")); M = d["meta"]; E = d["ents"]; B = d["brands"]; CH = d["changes"]
bySlug = {e["slug"]: e for e in E}
for p in [S/"p", S/"marca"]: shutil.rmtree(p, ignore_errors=True); p.mkdir(parents=True)
for f in S.glob("*.html"): f.unlink()
esc = lambda s: html.escape(str(s or ""), quote=True)
C = {"AT":"Austria","BE":"Bélgica","BG":"Bulgaria","CY":"Chipre","CZ":"Chequia","DE":"Alemania","DK":"Dinamarca","EE":"Estonia","ES":"España","FI":"Finlandia","FR":"Francia","GR":"Grecia","EL":"Grecia","HR":"Croacia","HU":"Hungría","IE":"Irlanda","IS":"Islandia","IT":"Italia","LI":"Liechtenstein","LT":"Lituania","LU":"Luxemburgo","LV":"Letonia","MT":"Malta","NL":"Países Bajos","NO":"Noruega","PL":"Polonia","PT":"Portugal","RO":"Rumanía","SE":"Suecia","SI":"Eslovenia","SK":"Eslovaquia"}
SV = {"a":"Custodia y administración","b":"Gestión de plataforma de negociación","c":"Canje de cripto por fondos","d":"Canje de cripto por cripto","e":"Ejecución de órdenes","f":"Colocación","g":"Recepción y transmisión de órdenes","h":"Asesoramiento","i":"Gestión de carteras","j":"Servicios de transferencia"}
def kind(e):
    if e["k"] == "art59": return ("lic", "Licencia MiCA completa", "Art. 59")
    if e["k"] == "art60" and e["conf"] == "alta": return ("ntf", "Notificación de entidad financiera", "Art. 60")
    if e["k"] == "art60": return ("ntf", "Probable notificación", "Art. 60 · probable")
    return ("unk", "Vía no determinada", "59 / 60 ?")
CONF = {"alta":"Confianza alta","media":"Confianza media","baja":"Confianza baja"}
def hue(s): return int(hashlib.md5(s.encode()).hexdigest()[:4], 16) % 360
def initials(s):
    w = [x for x in s.replace("(", " ").split() if x[:1].isalnum()]; return esc(("".join(x[0] for x in w[:2]) or "?").upper())
def avatar(name, big=False): return f'<span class="av{" av-lg" if big else ""}" style="--h:{hue(name)}" aria-hidden="true">{initials(name)}</span>'
ICON = {"check":'<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M3.5 8.5l3 3 6-7" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
 "x":'<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M4.5 4.5l7 7m0-7l-7 7" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
 "search":'<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7" fill="none" stroke="currentColor" stroke-width="2"/><path d="M20 20l-3.5-3.5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
 "moon":'<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20 14.5A8 8 0 019.5 4a8 8 0 1010.5 10.5z" fill="currentColor"/></svg>'}
def esb(e): return f'<span class="pill {"ok" if e["es"] else "no"}">{ICON["check"] if e["es"] else ICON["x"]}{"Puede operar en España" if e["es"] else "España no notificada"}</span>'
def kb(e): c, t, a = kind(e); return f'<span class="pill {c}" title="{esc(e["why"])}">{t}<em>{a}</em></span>'
def page(title, desc, body, depth=0, path="", ld=None, otype="website"):
    up = "../" * depth
    canon = BASE + path
    ldj = "".join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>' for x in (ld or []))
    return f'''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title><meta name="description" content="{esc(desc)}"><link rel="canonical" href="{esc(canon)}">
<meta property="og:type" content="{otype}"><meta property="og:site_name" content="¿Está autorizado?"><meta property="og:locale" content="es_ES"><meta property="og:url" content="{esc(canon)}"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:image" content="{BASE}assets/og.png"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta property="og:image:alt" content="¿Está autorizado? Buscador del registro MiCA para España">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{esc(title)}"><meta name="twitter:description" content="{esc(desc)}"><meta name="twitter:image" content="{BASE}assets/og.png">{ldj}
<meta name="color-scheme" content="light dark"><link rel="stylesheet" href="{up}assets/app.css"><link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 32 32%22><rect width=%2232%22 height=%2232%22 rx=%228%22 fill=%22%2310b981%22/><path d=%22M9 16.5l4.5 4.5L23 11%22 stroke=%22white%22 stroke-width=%223.2%22 fill=%22none%22 stroke-linecap=%22round%22/></svg>">
<script>try{{const t=localStorage.getItem("theme");if(t)document.documentElement.dataset.theme=t}}catch(e){{}}</script></head><body>
<a class="skip" href="#main">Saltar al contenido</a>
<header class="nav"><div class="wrap nav-in"><a class="logo" href="{up}index.html"><span class="logo-mk">{ICON["check"]}</span>¿Está autorizado?</a>
<nav aria-label="Principal"><a href="{up}index.html#buscar">Buscar</a><a href="{up}marcas.html">Marcas</a><a href="{up}cambios.html">Cambios</a><a href="{up}metodologia.html">Metodología</a>
<button class="theme" type="button" aria-label="Cambiar tema claro/oscuro" onclick="const r=document.documentElement,n=(r.dataset.theme||(matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light'))==='dark'?'light':'dark';r.dataset.theme=n;try{{localStorage.setItem('theme',n)}}catch(e){{}}">{ICON["moon"]}</button></nav></div></header>
<main id="main">{body}</main>
<footer class="foot"><div class="wrap"><p><strong>¿Está autorizado?</strong> reproduce, con fecha, el registro provisional MiCA de ESMA (actualizado {esc(M["date"])}). No es asesoramiento financiero ni una determinación oficial. Confirma siempre en <a href="https://www.esma.europa.eu/esmas-activities/digital-finance-and-innovation/markets-crypto-assets-regulation-mica" rel="noopener">ESMA</a> y en la <a href="https://www.cnmv.es/portal/consultas/proveedores-servicios-criptoactivos?lang=es" rel="noopener">CNMV</a>.</p>
<p class="disc"><strong>Aviso:</strong> proyecto informativo sin ánimo de lucro, sin publicidad ni enlaces de afiliado. Nada de lo publicado es asesoramiento financiero, fiscal ni jurídico, ni recomendación de inversión. Los criptoactivos son de alto riesgo y puedes perder todo lo invertido.</p>
<p class="flinks"><a href="{up}marcas.html">Todas las marcas</a><a href="{up}aviso-legal.html">Aviso legal</a><a href="{up}privacidad.html">Política de privacidad</a><a href="{up}metodologia.html">Metodología</a></p>
<p class="muted">Fuentes: ESMA (CASPS.csv, NCASP.csv, registro MiFID), BCE (lista de IFM), CNMV, cryptocodes.eu. Respaldo e histórico: <a href="https://casptracker.eu" rel="noopener">CASP Tracker</a> (CC BY 4.0).</p></div></footer>
<script src="{up}assets/app.js" defer></script></body></html>'''
def newsletter(up=""):
    head = '<div><h2>Los cambios del registro, cada lunes</h2><p class="muted">Altas, bajas y quién gana o pierde el permiso para operar en España. Un correo, sin ruido.</p></div>'
    legal = f'<p class="news-legal">Al suscribirte aceptas recibir la newsletter. Tus datos los gestiona Beehiiv como encargado del tratamiento. Más información en la <a href="{up}privacidad.html">política de privacidad</a>. Puedes darte de baja en cualquier momento.</p>'
    if CFG.get("beehiivEmbedUrl"):
        return f'<section class="news card">{head}<div><iframe src="{esc(CFG["beehiivEmbedUrl"])}" title="Formulario de suscripción (Beehiiv)" loading="lazy" style="width:100%;height:120px;border:0;background:transparent"></iframe>{legal}</div></section>'
    return f'''<section class="news card">{head}
<form class="news-f" data-beehiiv-slot onsubmit="event.preventDefault();this.querySelector('.news-msg').hidden=false;this.querySelector('button').disabled=true"><label class="sr" for="em">Email</label><input id="em" type="email" required placeholder="tu@email.com" autocomplete="email"><button class="btn">Suscribirme</button><p class="news-msg" role="status" hidden>Formulario de prueba: todavía no hay herramienta de newsletter conectada.</p>{legal}</form></section>'''
def bslug(b): return slugify(b["b"])
def slugify(x):
    import unicodedata
    x = unicodedata.normalize("NFKD", x).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", x).strip("-")
for b in B: b["slug"] = bslug(b); b["es"] = any(bySlug[x]["es"] for x in b["e"])
brandsOf = {}
for b in B:
    for x in b["e"]: brandsOf.setdefault(x, []).append(b)
def brandlinks(e):
    bs = brandsOf.get(e["slug"], [])
    if not bs: return ""
    return '<section class="card"><h2>Marcas de esta sociedad</h2><p>' + " · ".join(f'<a href="../marca/{b["slug"]}.html">¿Está {esc(b["b"])} autorizado en España?</a>' for b in bs) + '</p></section>'
# ---- home
popular = [b for b in B if b["cat"] in ("exchange", "bróker", "banco/neobanco/pagos")][:16]
def bcard(b):
    if b["status"] == "ok":
        e = bySlug[b["e"][0]]; return f'<a class="bc" href="marca/{b["slug"]}.html">{avatar(b["b"])}<span class="bc-t"><b>{esc(b["b"])}</b><small>{esc(C.get(e["h"], e["h"]))}</small></span><span class="dot {"ok" if e["es"] else "no"}" aria-label="{"Opera en España" if e["es"] else "No notificada en España"}"></span></a>'
    return f'<a class="bc" href="marca/{b["slug"]}.html">{avatar(b["b"])}<span class="bc-t"><b>{esc(b["b"])}</b><small>No figura</small></span><span class="dot no" aria-label="No figura en el registro"></span></a>'
home = f'''<section class="hero"><div class="glow" aria-hidden="true"></div><div class="wrap">
<p class="eyebrow"><span class="live"></span>Registro ESMA · actualizado {esc(M["date"])}</p>
<h1>¿Tu exchange está <span class="grad">autorizado</span> en España?</h1>
<p class="lede">Comprueba en segundos si una plataforma cripto tiene licencia MiCA, quién está detrás y si puede operar legalmente aquí.</p>
<div class="search" id="buscar" role="search"><span class="s-ic">{ICON["search"]}</span>
<label class="sr" for="q">Buscar marca o sociedad</label>
<input id="q" type="search" autocomplete="off" spellcheck="false" placeholder="Coinbase, Bit2Me, Binance, Revolut…" role="combobox" aria-expanded="false" aria-controls="ac" aria-autocomplete="list">
<kbd class="k">/</kbd><ul id="ac" class="ac" role="listbox" hidden></ul></div>
<div class="chips" aria-label="Búsquedas populares">{"".join(f'<button type="button" class="chip" data-q="{esc(x)}">{esc(x)}</button>' for x in ["Binance","Coinbase","Bit2Me","Revolut","Kraken","Trade Republic","BBVA"])}</div>
<section id="res" class="results" aria-live="polite"></section><dl class="stats"><div><dt>Proveedores MiCA en la UE</dt><dd>{M["count"]}</dd></div><div><dt>Pueden operar en España</dt><dd>{M["es"]}</dd></div><div><dt>Licencia completa (Art. 59)</dt><dd>{M["k"]["art59"]}</dd></div><div><dt>Marcas mapeadas</dt><dd>{M["brands"]}</dd></div></dl>
</div></section>
<div class="wrap">
<section class="sec"><div class="sec-h"><h2>Marcas populares</h2><p class="muted">Punto verde: puede operar en España. Rojo: no figura o no tiene España notificada.</p></div><div class="grid">{"".join(bcard(b) for b in popular)}</div></section>
<section class="sec how"><div class="sec-h"><h2>Qué significa cada etiqueta</h2></div><div class="grid3">
<div class="card"><span class="pill lic">Licencia MiCA completa<em>Art. 59</em></span><p>Autorización como proveedor de servicios de criptoactivos (CASP) concedida por un supervisor de la UE.</p></div>
<div class="card"><span class="pill ntf">Notificación de entidad financiera<em>Art. 60</em></span><p>Bancos, empresas de inversión y gestoras ya supervisados que notifican servicios cripto sin licencia CASP aparte.</p></div>
<div class="card"><span class="pill ok">{ICON["check"]}Puede operar en España</span><p>La sociedad está autorizada en España o ha notificado España en su pasaporte europeo.</p></div></div>
<p class="muted center"><a href="metodologia.html">Cómo lo determinamos y con qué confianza →</a></p></section>
{newsletter()}</div>'''
(S/"index.html").write_text(page("¿Está autorizado? · Comprueba si un exchange cripto tiene licencia MiCA en España", f"Buscador del registro MiCA de ESMA: {M['count']} proveedores autorizados, {M['es']} pueden operar en España. Actualizado {M['date']}.", home, 0, "", [{"@context":"https://schema.org","@type":"WebSite","name":"¿Está autorizado?","url":BASE,"inLanguage":"es","potentialAction":{"@type":"SearchAction","target":BASE+"?q={search_term_string}","query-input":"required name=search_term_string"}}]))
def crumbs(items): return {"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":i+1,"name":n,"item":BASE+u} for i,(n,u) in enumerate(items)]}
# ---- provider pages
for e in E:
    c, t, a = kind(e); hs = C.get(e["h"], e["h"])
    others = ", ".join(C.get(x, x) for x in e["cs"])
    body = f'''<div class="wrap narrow"><nav class="crumbs" aria-label="Migas"><a href="../index.html">Inicio</a><span>/</span><span>{esc(e["n"])}</span></nav>
<section class="phead card">{avatar(e["n"], True)}<div><h1>{esc(e["n"])}</h1><p class="muted">{esc(e["l"])}{f' · marcas: {esc(", ".join(e["brands"]))}' if e["brands"] else ""}</p>
<div class="pills">{esb(e)}{kb(e)}{'<span class="pill no">Autorización retirada '+esc(e["end"])+'</span>' if e["end"] else ''}</div></div></section>
<section class="verdict {"v-ok" if e["es"] else "v-no"}"><h2>{"Sí: puede prestar servicios cripto en España" if e["es"] else "No consta que pueda operar en España"}</h2><p>{"Figura en el registro MiCA con España entre sus países de servicio." if e["es"] else "Tiene autorización MiCA, pero España no aparece entre sus países notificados."} Datos del registro ESMA a {esc(M["date"])}.</p></section>
<section class="card"><h2>Tipo de habilitación</h2><p><span class="pill {c}">{t}<em>{a}</em></span> <span class="conf conf-{e["conf"]}">{CONF[e["conf"]]}</span></p><p>{esc(e["why"])}.</p><p class="muted">Fuente: <a href="{esc(e["srcUrl"])}" rel="noopener">{esc(e["src"])}</a></p></section>
<section class="card"><h2>Ficha del registro</h2><dl class="kv">
<dt>Sociedad</dt><dd>{esc(e["l"])}</dd><dt>País de origen</dt><dd>{esc(hs)}</dd><dt>Supervisor</dt><dd>{esc(e["a"])}</dd>
<dt>En el registro desde</dt><dd>{esc(e["d"] or "—")}</dd><dt>LEI</dt><dd><code>{esc(e["lei"] or "—")}</code></dd><dt>Dirección</dt><dd>{esc(e["addr"] or "—")}</dd>
<dt>Web</dt><dd>{f'<a href="{esc(e["w"])}" rel="nofollow noopener">{esc(e["w"])}</a>' if e["w"] else "—"}</dd>{f'<dt>Comentarios ESMA</dt><dd>{esc(e["cm"])}</dd>' if e["cm"] else ""}</dl></section>
<section class="card"><h2>Servicios MiCA autorizados</h2><ul class="svc">{"".join(f'<li><b>{s}</b>{esc(SV.get(s, s))}</li>' for s in e["s"])}</ul></section>
<section class="card"><h2>Países donde puede operar <span class="muted">({len(e["cs"])})</span></h2><p class="countries">{esc(others or "—")}</p></section>
{brandlinks(e)}</div>'''
    (S/"p"/f'{e["slug"]}.html').write_text(page(f'{e["n"]}: ¿está autorizado en España? Licencia MiCA', f'{e["l"]} ({hs}). {"Puede" if e["es"] else "No consta que pueda"} operar en España. {t} ({a}). Registro ESMA {M["date"]}.', body, 1, f'p/{e["slug"]}.html', [crumbs([("Inicio",""),(e["n"],f'p/{e["slug"]}.html')])]))
# ---- cambios
def li(x, kind_):
    nm = f'<a href="p/{x[-1]}.html">{esc(x[0])}</a>' if x[-1] else esc(x[0])
    return f'<li>{avatar(x[0])}<span>{nm}</span>{"" if kind_!="add" else (" <span class=\"pill ok sm\">España</span>" if x[2] else "")}</li>'
tl = "".join(f'''<li class="tl-i"><span class="tl-dot" aria-hidden="true"></span><div class="card"><div class="tl-h"><time>{esc(c["to"])}</time><span class="muted">desde {esc(c["from"])} · total {c["total"]}</span>
<span class="delta"><span class="pill ok sm">+{len(c["added"])}</span><span class="pill no sm">−{len(c["removed"])}</span></span></div>
{('<h3>Altas</h3><ul class="ent">'+"".join(li(x,"add") for x in c["added"])+'</ul>') if c["added"] else ""}
{('<h3>Bajas</h3><ul class="ent">'+"".join(li(x+[None],"rem") for x in c["removed"])+'</ul>') if c["removed"] else ""}
{('<h3>Cambio de pasaporte a España</h3><ul class="ent">'+"".join(f'<li>{avatar(x[0])}<span>{esc(x[0])}</span><span class="pill {"ok" if x[1] else "no"} sm">{"Añade España" if x[1] else "Retira España"}</span></li>' for x in c["es"])+'</ul>') if c["es"] else ""}
{'' if (c["added"] or c["removed"] or c["es"]) else '<p class="muted">Sin altas ni bajas (puede haber cambios de formato o actualización de fichas).</p>'}</div></li>''' for c in CH)
(S/"cambios.html").write_text(page("Cambios recientes en el registro MiCA · ¿Está autorizado?", "Altas, bajas y cambios de pasaporte a España en el registro MiCA de ESMA, instantánea a instantánea.",
 f'<div class="wrap narrow"><header class="ph"><p class="eyebrow">Historial · {M["snapshots"]} instantáneas</p><h1>Cambios recientes</h1><p class="lede">Lo que se ha movido en el registro MiCA de ESMA entre cada instantánea.</p></header><ol class="tl">{tl}</ol>{newsletter()}</div>', 0, "cambios.html"))
# ---- metodologia
met = f'''<div class="wrap narrow"><header class="ph"><p class="eyebrow">Metodología</p><h1>Cómo clasificamos cada proveedor</h1><p class="lede">ESMA mezcla en el mismo archivo las licencias CASP (Art. 59) y las notificaciones de entidades ya supervisadas (Art. 60) sin una columna que las distinga. Cruzamos fuentes oficiales, por este orden:</p></header>
<ol class="steps card"><li><b>Comentario del registro ESMA</b> que menciona el artículo 60 → Art. 60, confianza alta.</li>
<li><b>cryptocodes.eu</b>, que cruzó el registro con las listas de AFM, BaFin, CNMV y CySEC → Art. 60, confianza alta.</li>
<li><b>Listado de la CNMV</b> (entidades españolas): «Entidad de crédito» → Art. 60; «PSC» → Art. 59. Confianza alta.</li>
<li><b>Lista de IFM del BCE</b>: si el LEI es una entidad de crédito → Art. 60, confianza alta.</li>
<li><b>Registro MiFID/AIFMD/UCITS de ESMA</b>: si el LEI es empresa de inversión o gestora → probable Art. 60, confianza media (algunas piden licencia completa).</li>
<li>Si no es ninguna de las anteriores → solo puede operar con licencia CASP: Art. 59, confianza media.</li>
<li>Entidades de dinero electrónico u otras IFM → vía no determinada, confianza baja.</li></ol>
<section class="card"><h2>Resultado actual</h2><dl class="kv"><dt>Art. 59</dt><dd>{M["k"]["art59"]}</dd><dt>Art. 60</dt><dd>{M["k"]["art60"]}</dd><dt>No determinado</dt><dd>{M["k"]["incierto"]}</dd><dt>Confianza alta / media / baja</dt><dd>{M["conf"]["alta"]} / {M["conf"]["media"]} / {M["conf"]["baja"]}</dd><dt>Fuente del registro</dt><dd>{esc(M["source"])}</dd></dl></section></div>'''
(S/"metodologia.html").write_text(page("Metodología · ¿Está autorizado?", "Cómo distinguimos licencias MiCA (Art. 59) y notificaciones (Art. 60).", met, 0, "metodologia.html"))

# ---- legales
EM = esc(CFG.get("email") or "[EMAIL]")
PH = lambda x: f'<mark class="ph-mark">{x}</mark>' if x.startswith("[") else f'<a href="mailto:{x}">{x}</a>'
SITE = "https://fjgnpa.github.io/esta-autorizado/"
aviso = f"""<div class="wrap narrow legal"><header class="ph"><p class="eyebrow">Legal</p><h1>Aviso legal</h1><p class="muted">Última actualización: 17/10/2026</p></header>
<section class="card"><h2>1. Qué es este sitio</h2><p>«¿Está autorizado?» ({SITE}) es un <strong>proyecto personal, informativo y sin ánimo de lucro</strong>. No vende productos ni servicios, no contiene publicidad, patrocinios ni enlaces de afiliado, y no recibe ninguna remuneración de las entidades que aparecen en él.</p>
<p>Contacto del proyecto: {PH(EM)}</p></section>
<section class="card"><h2>2. Contenido</h2><p>La web reproduce y ordena, con fecha, información pública de registros oficiales (ESMA, CNMV, BCE) sobre proveedores de servicios de criptoactivos bajo el Reglamento (UE) 2023/1114 (MiCA).</p></section>
<section class="card"><h2>3. No es asesoramiento</h2><p>Nada de lo publicado constituye asesoramiento financiero, de inversión, fiscal ni jurídico, ni una recomendación de contratar o no con ninguna entidad. El proyecto no es una entidad supervisada. La clasificación entre licencia (art. 59 MiCA) y notificación (art. 60 MiCA) es una <strong>inferencia</strong> a partir de fuentes públicas y puede contener errores. La información oficial y vinculante es la de los registros de <a href="https://www.esma.europa.eu/esmas-activities/digital-finance-and-innovation/markets-crypto-assets-regulation-mica" rel="noopener">ESMA</a> y la <a href="https://www.cnmv.es/portal/consultas/proveedores-servicios-criptoactivos?lang=es" rel="noopener">CNMV</a>: compruébala siempre antes de tomar decisiones.</p>
<p>Los criptoactivos son productos complejos y de alto riesgo: puedes perder todo el capital invertido.</p></section>
<section class="card"><h2>4. Exactitud y responsabilidad</h2><p>Los datos se actualizan periódicamente de forma automática, pero pueden contener errores o estar desfasados respecto a los registros oficiales. No se garantiza su exactitud ni se asume responsabilidad por decisiones tomadas a partir de ellos ni por el contenido de sitios de terceros enlazados. Si detectas un error, escríbenos a {PH(EM)} y lo corregiremos.</p></section>
<section class="card"><h2>5. Fuentes, marcas y licencia de datos</h2><p>Los datos proceden de fuentes públicas (ESMA, CNMV, BCE), de cryptocodes.eu y de <a href="https://casptracker.eu" rel="noopener">CASP Tracker</a> (licencia <a href="https://creativecommons.org/licenses/by/4.0/" rel="noopener">CC BY 4.0</a>). Las marcas y nombres comerciales citados pertenecen a sus titulares y se mencionan únicamente para identificarlos; su mención no implica relación ni respaldo. El código del proyecto es público en <a href="https://github.com/fjgnpa/esta-autorizado" rel="noopener">GitHub</a>.</p></section>
<p class="muted">Texto orientativo; no sustituye a un asesoramiento jurídico.</p></div>"""
(S/"aviso-legal.html").write_text(page("Aviso legal · ¿Está autorizado?", "Aviso legal de ¿Está autorizado?, proyecto informativo y sin ánimo de lucro sobre el registro MiCA.", aviso, 0, "aviso-legal.html"))
priv = f"""<div class="wrap narrow legal"><header class="ph"><p class="eyebrow">Legal</p><h1>Política de privacidad</h1><p class="muted">Última actualización: 17/10/2026</p></header>
<section class="card"><h2>1. Responsable y contacto</h2><p>Responsable: el proyecto «¿Está autorizado?», de carácter personal y no comercial. Para cualquier cuestión sobre tus datos, incluido el ejercicio de tus derechos, escribe a {PH(EM)}.</p></section>
<section class="card"><h2>2. Qué datos tratamos y para qué</h2>
<p><strong>Newsletter.</strong> Si te suscribes, tratamos tu dirección de correo electrónico (y los datos técnicos de entrega, apertura y clics que genera la plataforma de envío) solo para enviarte la newsletter sobre cambios en el registro MiCA. <em>Base jurídica:</em> tu consentimiento (art. 6.1.a RGPD y art. 21 LSSI-CE), que puedes retirar en cualquier momento con el enlace de baja de cada correo o escribiendo a {PH(EM)}. No usamos tu correo para nada más ni lo cedemos.</p>
<p><strong>Navegación.</strong> La web no tiene registro de usuarios ni formularios propios que guarden datos. El buscador funciona íntegramente en tu navegador.</p></section>
<section class="card"><h2>3. Cookies y almacenamiento local</h2><p>No usamos cookies, ni analítica, ni publicidad. Si eliges manualmente el tema claro u oscuro, tu navegador guarda esa preferencia en su almacenamiento local (<code>localStorage</code>, clave «theme»): es un ajuste que tú solicitas, no se envía a ningún servidor y puedes borrarlo desde tu navegador. Si algún día se añadiera algo que requiera consentimiento, se pediría antes.</p></section>
<section class="card"><h2>4. Proveedores (encargados del tratamiento)</h2>
<p><strong>Beehiiv, Inc.</strong> (EE. UU.): plataforma de envío de la newsletter. Actúa como encargado del tratamiento; las transferencias internacionales se amparan en las garantías que ofrezca el proveedor (Marco de Privacidad de Datos UE-EE. UU. si está adherido, o cláusulas contractuales tipo). <a href="https://www.beehiiv.com/privacy" rel="noopener">Política de privacidad de Beehiiv</a>.</p>
<p><strong>GitHub, Inc.</strong> (EE. UU.): alojamiento de la web (GitHub Pages). Al visitarla, GitHub puede registrar tu dirección IP con fines técnicos y de seguridad. <a href="https://docs.github.com/es/site-policy/privacy-policies/github-general-privacy-statement" rel="noopener">Declaración de privacidad de GitHub</a>.</p></section>
<section class="card"><h2>5. Conservación</h2><p>Conservamos tu correo mientras sigas suscrito. Al darte de baja se elimina, salvo el tiempo imprescindible para atender obligaciones legales.</p></section>
<section class="card"><h2>6. Tus derechos</h2><p>Puedes ejercer los derechos de acceso, rectificación, supresión, oposición, limitación y portabilidad escribiendo a {PH(EM)}. Si consideras que no se han atendido correctamente, puedes reclamar ante la <a href="https://www.aepd.es" rel="noopener">Agencia Española de Protección de Datos</a>.</p></section>
<section class="card"><h2>7. Menores</h2><p>La newsletter no está dirigida a menores de 14 años.</p></section>
<p class="muted">Texto orientativo; no sustituye a un asesoramiento jurídico.</p></div>"""
(S/"privacidad.html").write_text(page("Política de privacidad · ¿Está autorizado?", "Política de privacidad y cookies de ¿Está autorizado?: sin cookies, newsletter con Beehiiv.", priv, 0, "privacidad.html"))
# ---- brand pages
CATN = {"exchange":"Exchange","bróker":"Bróker","banco/neobanco/pagos":"Banco, neobanco o pagos","wallet":"Monedero","compra/rampa/app":"App de compra","institucional/custodia":"Institucional / custodia"}
def faq(qas): return {"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a in qas]}
def related(b, n=8):
    pool = [x for x in B if x is not b and x["cat"] == b["cat"]] + [x for x in B if x is not b and x["cat"] != b["cat"]]
    return '<div class="grid">' + "".join(bcard_m(x) for x in pool[:n]) + '</div>'
def bcard_m(b):
    sub = ("Puede operar en España" if b["es"] else ("Sin España notificada" if b["e"] else "No figura"))
    return f'<a class="bc" href="../marca/{b["slug"]}.html">{avatar(b["b"])}<span class="bc-t"><b>{esc(b["b"])}</b><small>{sub}</small></span><span class="dot {"ok" if b["es"] else "no"}" aria-hidden="true"></span></a>'
for b in B:
    nm = esc(b["b"]); ents = [bySlug[x] for x in b["e"]]; dt = M["date"]
    if b["es"]:
        e0 = next(x for x in ents if x["es"]); ver = ("v-ok", f"Sí. {nm} puede prestar servicios cripto en España")
        vtxt = f'Opera a través de <b>{esc(e0["l"])}</b> ({esc(C.get(e0["h"], e0["h"]))}), que figura en el registro MiCA de ESMA con España entre sus países de servicio.'
        a1 = f'Sí. Según el registro MiCA de ESMA a {dt}, {b["b"]} opera en la UE a través de {e0["l"]} ({C.get(e0["h"], e0["h"])}), que tiene España entre sus países notificados.'
        desc = f'Sí: {b["b"]} figura en el registro MiCA de ESMA ({e0["l"]}, {C.get(e0["h"], e0["h"])}) y puede operar en España. {kind(e0)[1]} ({kind(e0)[2]}). Datos a {dt}.'
    elif ents:
        e0 = ents[0]; ver = ("v-no", f"{nm} tiene autorización MiCA, pero no consta para España")
        vtxt = f'Su sociedad <b>{esc(e0["l"])}</b> ({esc(C.get(e0["h"], e0["h"]))}) figura en el registro MiCA, pero España no aparece entre sus países notificados.'
        a1 = f'No consta. {e0["l"]} figura en el registro MiCA de ESMA a {dt}, pero España no está entre sus países notificados, por lo que no consta que pueda prestar servicios a residentes en España.'
        desc = f'{b["b"]} tiene autorización MiCA ({e0["l"]}), pero España no figura entre sus países notificados en el registro de ESMA a {dt}.'
    else:
        ver = ("v-no", f"No. {nm} no figura en el registro MiCA")
        vtxt = f'No hemos encontrado ninguna sociedad de {nm} en el registro de proveedores autorizados de ESMA a {esc(dt)}.'
        a1 = f'No consta. A {dt}, {b["b"]} no figura en el registro de proveedores de servicios de criptoactivos autorizados de ESMA, por lo que no consta que pueda prestar servicios cripto en España bajo MiCA.'
        desc = f'No: {b["b"]} no figura en el registro MiCA de ESMA a {dt}. Qué significa para usuarios en España y cómo comprobarlo.'
    if b["cat"] == "wallet": a1 += " Es un monedero de autocustodia: el software de autocustodia no suele requerir licencia CASP."
    warn = "".join(f'<p class="pill no">En la lista de entidades no conformes de ESMA: {esc(w["l"])} ({esc(w["a"])})</p>' for w in b["warn"])
    qas = [(f"¿Está {b['b']} autorizado en España?", a1),
           (f"¿Qué es la licencia MiCA?", "MiCA es el Reglamento (UE) 2023/1114. Desde el fin del periodo transitorio en España (1 de julio de 2026), para prestar servicios de criptoactivos a residentes en España hay que figurar en el registro MiCA con España notificada, ya sea con autorización CASP (art. 59) o mediante notificación de una entidad financiera ya supervisada (art. 60)."),
           (f"¿Cómo compruebo si {b['b']} está autorizado?", f"Busca el nombre jurídico de la sociedad que te presta el servicio (aparece en los términos legales de la app) en el registro MiCA de ESMA y en el listado de la CNMV, y comprueba que España figure entre sus países. Este buscador lo hace por ti con datos a {dt}.")]
    if not b["es"]: qas.append((f"¿Es ilegal usar {b['b']} desde España?", "Para el usuario no: la obligación de estar autorizado es del proveedor. Pero un proveedor sin autorización para España no ofrece las protecciones de MiCA y puede tener que dejar de prestar servicio."))
    faqh = "".join(f'<details class="faq"{" open" if i==0 else ""}><summary>{esc(q)}</summary><p>{esc(a)}</p></details>' for i,(q,a) in enumerate(qas))
    body = f"""<div class="wrap narrow"><nav class="crumbs" aria-label="Migas"><a href="../index.html">Inicio</a><span>/</span><a href="../marcas.html">Marcas</a><span>/</span><span>{nm}</span></nav>
<section class="phead card">{avatar(b["b"], True)}<div><p class="eyebrow">{esc(CATN.get(b["cat"], b["cat"]))} · registro ESMA a {esc(dt)}</p><h1>¿Está {nm} autorizado en España?</h1>
<div class="pills">{('<span class="pill ok">'+ICON["check"]+'Puede operar en España</span>') if b["es"] else ('<span class="pill no">'+ICON["x"]+('España no notificada' if ents else 'No figura en el registro MiCA')+'</span>')}</div></div></section>
<section class="verdict {ver[0]}"><h2>{ver[1]}</h2><p>{vtxt}</p>{('<p class="muted" style="margin-top:.5em">'+esc(b["note"])+'</p>') if b["note"] else ""}{warn}</section>
{('<section class="card"><h2>Sociedades en el registro</h2>' + "".join(f'<a class="rc" href="../p/{x["slug"]}.html">{avatar(x["n"])}<div class="b"><h3>{esc(x["l"])}</h3><div class="sub">{esc(C.get(x["h"], x["h"]))} · {esc(x["a"])}</div><div class="pills">{esb(x)}{kb(x)}</div></div><span class="go" aria-hidden="true">→</span></a>' for x in ents) + '</section>') if ents else ''}
<section class="card"><h2>Preguntas frecuentes</h2>{faqh}</section>
<section class="card"><h2>Fuente del mapeo</h2><p>{esc(b["src"])}. Comprobado el {esc(dt)}.</p><p class="muted">Confirma siempre en <a href="https://www.esma.europa.eu/esmas-activities/digital-finance-and-innovation/markets-crypto-assets-regulation-mica" rel="noopener">ESMA</a> y en la <a href="https://www.cnmv.es/portal/consultas/proveedores-servicios-criptoactivos?lang=es" rel="noopener">CNMV</a>.</p></section>
<section class="sec"><div class="sec-h"><h2>Comprueba otras marcas</h2><a href="../marcas.html">Ver todas →</a></div>{related(b)}</section>
{newsletter("../")}</div>"""
    title = f"¿Está {b['b']} autorizado en España? Licencia MiCA ({dt[:7]})"
    (S/"marca"/f'{b["slug"]}.html').write_text(page(title, desc, body, 1, f'marca/{b["slug"]}.html', [faq(qas), crumbs([("Inicio",""),("Marcas","marcas.html"),(b["b"],f'marca/{b["slug"]}.html')])], "article"))
# ---- marcas index
groups = {}
for b in B: groups.setdefault(b["cat"], []).append(b)
mi = f"""<div class="wrap"><header class="ph"><p class="eyebrow">{len(B)} marcas · registro ESMA a {esc(M["date"])}</p><h1>¿Qué plataformas cripto están autorizadas en España?</h1><p class="lede">Exchanges, brókers, neobancos, apps y monederos populares en España, con su estado en el registro MiCA.</p></header>
""" + "".join(f'<section class="sec"><div class="sec-h"><h2>{esc(CATN.get(k, k))}</h2></div><div class="grid">' + "".join(bcard_m(x).replace("../marca/","marca/") for x in sorted(v, key=lambda x: x["b"].lower())) + '</div></section>' for k, v in groups.items()) + newsletter() + "</div>"
(S/"marcas.html").write_text(page("¿Qué exchanges cripto están autorizados en España? Lista MiCA de marcas", f"Estado en el registro MiCA de {len(B)} exchanges, brókers, neobancos y apps cripto populares en España: quién puede operar y quién no. Datos ESMA a {M['date']}.", mi, 0, "marcas.html"))
# ---- data for search
idx = {"m": {"date": M["date"]}, "e": [[e["slug"], e["n"], e["l"], e["h"], int(e["es"]), kind(e)[0], kind(e)[1], kind(e)[2], e["brands"]] for e in E],
       "b": [[b["b"], b["e"], b["note"], [w["l"] for w in b["warn"]], b["cat"], b["slug"]] for b in B]}
(S/"assets").mkdir(exist_ok=True); (S/"assets/data.js").write_text("window.DB=" + json.dumps(idx, ensure_ascii=False, separators=(",", ":")) + ";")
for f in ["data.js", "common.js", "style.css"]: (S/f).unlink(missing_ok=True)
urls = [("", "1.0", "daily"), ("marcas.html", "0.9", "weekly"), ("cambios.html", "0.8", "weekly"), ("metodologia.html", "0.4", "monthly"), ("aviso-legal.html", "0.1", "yearly"), ("privacidad.html", "0.1", "yearly")] + [(f'marca/{b["slug"]}.html', "0.8", "weekly") for b in B] + [(f'p/{e["slug"]}.html', "0.6", "weekly") for e in E]
(S/"sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + "".join(f"<url><loc>{BASE}{u}</loc><lastmod>{M['date']}</lastmod><changefreq>{f}</changefreq><priority>{pr}</priority></url>" for u, pr, f in urls) + "</urlset>\n")
print("site:", len(E), "fichas,", len(B), "marcas")
