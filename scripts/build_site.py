#!/usr/bin/env python3
"""Registro MiCA: genera el sitio estático (site/) desde data/build.json y data/logos.json."""
import json, pathlib, html, shutil, hashlib, re, os, unicodedata
R = pathlib.Path(__file__).resolve().parent.parent; S = R/"site"
BASE = os.environ.get("SITE_BASE", "https://fjgnpa.github.io/esta-autorizado/")
CFG = json.load(open(R/"data/config.json"))
d = json.load(open(R/"data/build.json")); M = d["meta"]; E = d["ents"]; B = d["brands"]; CH = d["changes"]
try: LG = json.load(open(R/"data/logos.json"))
except Exception: LG = {"brands": {}, "ents": {}}
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
# ---- logos y monogramas
PAL = [("#6366f1","#4338ca"),("#0ea5e9","#0369a1"),("#14b8a6","#0f766e"),("#10b981","#047857"),("#f59e0b","#c2410c"),
       ("#f43f5e","#be123c"),("#8b5cf6","#6d28d9"),("#d946ef","#a21caf"),("#64748b","#334155"),("#06b6d4","#4f46e5")]
def pal(s): return int(hashlib.md5(s.encode()).hexdigest()[:6], 16) % len(PAL)
def initials(s):
    w = [x for x in re.sub(r"[()/.,·]", " ", s).split() if x[:1].isalnum() and x.lower() not in ("de", "the", "and", "y")]
    if len(w) == 1 and len(w[0]) > 1 and not w[0].isdigit(): return esc(w[0][:2].capitalize() if not w[0][:2].isupper() else w[0][:2])
    return esc(("".join(x[0] for x in w[:2]) or "?").upper())
SZ = {"xs": 24, "sm": 32, "md": 44, "lg": 84}
def linfo(kind_, key): return (LG.get(kind_) or {}).get(key) or {}
def lgfile(info): return info.get("logo") if info.get("logo") and (S/"assets/logos"/info["logo"]).exists() else None
def tile(info, name, size="md", up="", eager=False):
    f = lgfile(info); px = SZ[size]
    if f:
        cls = f'lg lg-{size} lg-{info.get("mode") or "pad"}' + (" lg-light" if info.get("light") else "") + (" lg-low" if info.get("lowres") else "")
        return f'<span class="{cls}"><img src="{up}assets/logos/{esc(f)}" alt="" width="{px}" height="{px}"{"" if eager else " loading=\"lazy\""} decoding="async"></span>'
    a, b = PAL[pal(name)]
    return f'<span class="lg lg-{size} mono" style="--a:{a};--b:{b}" aria-hidden="true">{initials(name)}</span>'
def blogo(b, size="md", up="", eager=False):
    info = linfo("brands", b["b"])
    if not lgfile(info) and b["e"]: info = linfo("ents", b["e"][0])
    return tile(info, b["b"], size, up, eager)
def elogo(e, size="md", up="", eager=False):
    info = linfo("ents", e["slug"])
    if not lgfile(info):
        for bb in brandsOf.get(e["slug"], []):
            if lgfile(linfo("brands", bb["b"])): info = linfo("brands", bb["b"]); break
    return tile(info, e["n"], size, up, eager)
def bcolor(b):
    c = linfo("brands", b["b"]).get("color")
    return c if c and lgfile(linfo("brands", b["b"])) else None
ICON = {"check":'<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M3.5 8.5l3 3 6-7" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
 "x":'<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M4.5 4.5l7 7m0-7l-7 7" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
 "minus":'<svg viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="6" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M5.5 8h5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>',
 "search":'<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7" fill="none" stroke="currentColor" stroke-width="2"/><path d="M20 20l-3.5-3.5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
 "moon":'<svg class="moon" viewBox="0 0 24 24" aria-hidden="true"><path d="M20 14.5A8 8 0 019.5 4a8 8 0 1010.5 10.5z" fill="currentColor"/></svg>',
 "sun":'<svg class="sun" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4.2" fill="currentColor"/><path d="M12 2.5v2.2M12 19.3v2.2M4.6 4.6l1.6 1.6M17.8 17.8l1.6 1.6M2.5 12h2.2M19.3 12h2.2M4.6 19.4l1.6-1.6M17.8 6.2l1.6-1.6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>',
 "shield":'<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3l7.5 3v5.5c0 4.6-3.2 8.4-7.5 9.5-4.3-1.1-7.5-4.9-7.5-9.5V6L12 3z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/><path d="M8.5 12l2.4 2.4 4.6-5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>',
 "bank":'<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3.5 9.5L12 4l8.5 5.5M5 10v8M9.5 10v8M14.5 10v8M19 10v8M3.5 20.5h17" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>',
 "es":'<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 21s-6.5-5.6-6.5-11a6.5 6.5 0 0113 0c0 5.4-6.5 11-6.5 11z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/><circle cx="12" cy="10" r="2.4" fill="currentColor"/></svg>',
 "mail":'<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="5.5" width="18" height="13" rx="2.5" fill="none" stroke="currentColor" stroke-width="1.9"/><path d="M4 7.5l8 6 8-6" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linejoin="round"/></svg>'}
def esb(e): return f'<span class="pill {"ok" if e["es"] else "no"}">{ICON["check"] if e["es"] else ICON["x"]}{"Puede operar en España" if e["es"] else "España no notificada"}</span>'
def kb(e): c, t, a = kind(e); return f'<span class="pill {c}" title="{esc(e["why"])}">{t}<em>{a}</em></span>'
def page(title, desc, body, depth=0, path="", ld=None, otype="website", cur=""):
    up = "../" * depth
    canon = BASE + path
    ldj = "".join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>' for x in (ld or []))
    nav = [("index.html#buscar", "Buscar", "buscar", ""), ("marcas.html", "Marcas", "marcas", ""), ("cambios.html", "Cambios", "cambios", "hide-m"), ("metodologia.html", "Metodología", "metodologia", "hide-m")]
    navh = "".join(f'<a href="{up}{u}"{" aria-current=\"page\"" if cur == k else ""}{f" class=\"{c}\"" if c else ""}>{t}</a>' for u, t, k, c in nav)
    return f'''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title><meta name="description" content="{esc(desc)}"><link rel="canonical" href="{esc(canon)}">
<meta property="og:type" content="{otype}"><meta property="og:site_name" content="Registro MiCA"><meta property="og:locale" content="es_ES"><meta property="og:url" content="{esc(canon)}"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:image" content="{BASE}assets/og.png"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta property="og:image:alt" content="Registro MiCA: buscador del registro MiCA para España">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{esc(title)}"><meta name="twitter:description" content="{esc(desc)}"><meta name="twitter:image" content="{BASE}assets/og.png">{ldj}
<meta name="color-scheme" content="light dark"><meta name="theme-color" content="#f6f8fb" media="(prefers-color-scheme: light)"><meta name="theme-color" content="#06090e" media="(prefers-color-scheme: dark)"><meta name="application-name" content="Registro MiCA"><meta name="apple-mobile-web-app-title" content="Registro MiCA">
<link rel="preload" href="{up}assets/fonts/inter-var.woff2" as="font" type="font/woff2" crossorigin><link rel="stylesheet" href="{up}assets/app.css">
<link rel="icon" href="{up}favicon.ico" sizes="48x48"><link rel="icon" href="{up}assets/favicon.svg" type="image/svg+xml"><link rel="apple-touch-icon" href="{up}assets/brand/apple-touch-icon.png"><link rel="manifest" href="{up}site.webmanifest">
<script>try{{const t=localStorage.getItem("theme");if(t)document.documentElement.dataset.theme=t}}catch(e){{}}</script></head><body>
<a class="skip" href="#main">Saltar al contenido</a>
<header class="nav"><div class="wrap nav-in"><a class="logo" href="{up}index.html" aria-label="Registro MiCA, inicio"><img src="{up}assets/brand/mark.svg" alt="" width="32" height="32"><span>Registro <b>MiCA</b></span></a>
<nav aria-label="Principal">{navh}
<button class="theme" type="button" aria-label="Cambiar tema claro/oscuro">{ICON["moon"]}{ICON["sun"]}</button></nav></div></header>
<main id="main">{body}</main>
<footer class="foot"><div class="wrap"><div class="foot-g"><div><a class="logo" href="{up}index.html"><img src="{up}assets/brand/mark.svg" alt="" width="28" height="28" loading="lazy"><span>Registro <b>MiCA</b></span></a>
<p><strong>Registro MiCA</strong> es un proyecto independiente: <strong>no es el registro oficial</strong> de ESMA ni de la CNMV. Reproduce, con fecha, el registro provisional MiCA de ESMA (actualizado {esc(M["date"])}). No es asesoramiento financiero ni una determinación oficial. Confirma siempre en <a href="https://www.esma.europa.eu/esmas-activities/digital-finance-and-innovation/markets-crypto-assets-regulation-mica" rel="noopener">ESMA</a> y en la <a href="https://www.cnmv.es/portal/consultas/proveedores-servicios-criptoactivos?lang=es" rel="noopener">CNMV</a>.</p></div>
<p class="flinks"><a href="{up}index.html#buscar">Buscador</a><a href="{up}marcas.html">Todas las marcas</a><a href="{up}cambios.html">Cambios recientes</a><a href="{up}metodologia.html">Metodología</a><a href="{up}aviso-legal.html">Aviso legal</a><a href="{up}privacidad.html">Política de privacidad</a></p></div>
<p class="disc"><strong>Aviso:</strong> proyecto informativo sin ánimo de lucro, sin publicidad ni enlaces de afiliado. Nada de lo publicado es asesoramiento financiero, fiscal ni jurídico, ni recomendación de inversión. Los criptoactivos son de alto riesgo y puedes perder todo lo invertido.</p>
<p class="src">Fuentes: ESMA (CASPS.csv, NCASP.csv, registro MiFID), BCE (lista de IFM), CNMV, cryptocodes.eu. Respaldo e histórico: <a href="https://casptracker.eu" rel="noopener">CASP Tracker</a> (CC BY 4.0). Los logotipos pertenecen a sus titulares y solo identifican a cada entidad.</p></div></footer>
<script src="{up}assets/app.js" defer></script></body></html>'''
def newsletter(up=""):
    head = f'<div><span class="news-ic">{ICON["mail"]}</span><h2>Los cambios del registro, cada lunes</h2><p class="muted">Altas, bajas y quién gana o pierde el permiso para operar en España. Un correo, sin ruido.</p></div>'
    legal = f'<p class="news-legal">Al suscribirte aceptas recibir la newsletter. Tus datos los gestiona Beehiiv como encargado del tratamiento. Más información en la <a href="{up}privacidad.html">política de privacidad</a>. Puedes darte de baja en cualquier momento.</p>'
    fid, sub = CFG.get("beehiivFormId"), CFG.get("beehiivSubscribeUrl")
    fb = f'<p class="news-fb">¿No ves el formulario? <a href="{esc(sub)}" rel="noopener">Suscríbete en Beehiiv →</a></p>' if sub else ""
    if fid:
        return f'<section class="news card" id="newsletter">{head}<div class="news-r"><div class="bh-wrap"><script async src="https://subscribe-forms.beehiiv.com/v3/loader.js" data-beehiiv-form="{esc(fid)}"></script><noscript><a class="btn" href="{esc(sub)}">Suscribirme</a></noscript></div>{fb}{legal}</div></section>'
    return f'<section class="news card" id="newsletter">{head}<div class="news-r"><a class="btn" href="{esc(sub)}" rel="noopener">Suscribirme</a>{legal}</div></section>'
def slugify(x):
    x = unicodedata.normalize("NFKD", x).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", x).strip("-")
def bslug(b): return slugify(b["b"])
for b in B: b["slug"] = bslug(b); b["es"] = any(bySlug[x]["es"] for x in b["e"])
brandsOf = {}
for b in B:
    for x in b["e"]: brandsOf.setdefault(x, []).append(b)
def brandlinks(e):
    bs = brandsOf.get(e["slug"], [])
    if not bs: return ""
    return '<section class="card"><h2>Marcas de esta sociedad</h2><div class="grid" style="margin-top:12px">' + "".join(bcard(b, "../") for b in bs) + '</div></section>'
def bstatus(b):
    if b["es"]: return f'<span class="st ok">{ICON["check"]}Puede operar en España</span>'
    if b["e"]: return f'<span class="st no">{ICON["minus"]}Sin España notificada</span>'
    return f'<span class="st no">{ICON["x"]}No figura</span>'
def bcard(b, up="", eager=False):
    sub = ""
    if b["e"]:
        e = bySlug[next((x for x in b["e"] if bySlug[x]["es"]), b["e"][0])]; sub = f'{C.get(e["h"], e["h"])} · {kind(e)[2] if kind(e)[0] != "unk" else "vía por confirmar"}'
    else: sub = "Sin sociedad en el registro"
    st = "ok" if b["es"] else ("sin" if b["e"] else "nofig")
    return f'<a class="bc" href="{up}marca/{b["slug"]}.html" data-st="{st}" data-n="{esc(slugify(b["b"]))}">{blogo(b, "md", up, eager)}<span class="bc-t"><b>{esc(b["b"])}</b><small>{esc(sub)}</small>{bstatus(b)}</span></a>'
# ---- home
popular = [b for b in B if b["cat"] in ("exchange", "bróker", "banco/neobanco/pagos")][:16]
chipsB = {x["b"]: x for x in B}
chipnames = ["Binance","Coinbase","Bit2Me","Revolut","Kraken","Trade Republic","BBVA"]
chips = "".join(f'<button type="button" class="chip" data-q="{esc(x)}">{blogo(chipsB[x], "xs", "", True) if x in chipsB else ""}{esc(x)}</button>' for x in chipnames)
mqb = [b for b in B if b["es"] and lgfile(linfo("brands", b["b"]))]
def mqrow(items, cls=""):
    one = "".join(f'<a href="marca/{b["slug"]}.html">{blogo(b, "sm")}{esc(b["b"])}<span class="ck">{ICON["check"]}</span></a>' for b in items)
    dup = "".join(f'<a href="marca/{b["slug"]}.html" tabindex="-1" aria-hidden="true">{blogo(b, "sm")}{esc(b["b"])}<span class="ck">{ICON["check"]}</span></a>' for b in items)
    return f'<div class="mq-row {cls}">{one}{dup}</div>'
half = (len(mqb) + 1) // 2
marquee = f'<p class="mq-h">{len([b for b in B if b["es"]])} marcas populares <b>pueden operar en España</b></p><div class="mq" aria-label="Marcas que pueden operar en España">{mqrow(mqb[:half])}{mqrow(mqb[half:], "r2")}</div>' if mqb else ""
last = CH[0] if CH else None
def chg_teaser():
    if not last: return ""
    items = [x for x in last["added"]][:6]
    if not items: return ""
    cards = "".join(f'<a class="bc" href="p/{x[3]}.html">{elogo(bySlug[x[3]], "md") if x[3] in bySlug else tile({}, x[0])}<span class="bc-t"><b>{esc(bySlug[x[3]]["n"] if x[3] in bySlug else x[0])}</b><small>{esc(C.get(x[1], x[1]))} · alta {esc(last["to"])}</small>{(f"<span class=\"st ok\">{ICON["check"]}Puede operar en España</span>") if x[2] else (f"<span class=\"st no\">{ICON["minus"]}Sin España notificada</span>")}</span></a>' for x in items if x[3])
    return f'<section class="sec"><div class="sec-h"><div><span class="kick">Novedades</span><h2>Últimas altas en el registro</h2><p class="muted">Instantánea del {esc(last["to"])}: +{len(last["added"])} altas, −{len(last["removed"])} bajas.</p></div><a href="cambios.html">Ver el historial →</a></div><div class="grid chg">{cards}</div></section>'
home = f'''<section class="hero"><div class="aurora" aria-hidden="true"><i></i><i></i><i></i></div><div class="wrap">
<p class="eyebrow"><span class="live"></span>Registro ESMA · actualizado {esc(M["date"])}</p>
<h1>¿Tu exchange está <span class="grad">autorizado</span> en España?</h1>
<p class="lede">Comprueba en segundos si una plataforma cripto tiene licencia MiCA, quién está detrás y si puede operar legalmente aquí.</p>
<div class="search" id="buscar" role="search"><div class="s-box"><span class="s-ic">{ICON["search"]}</span>
<label class="sr" for="q">Buscar marca o sociedad</label>
<input id="q" type="search" autocomplete="off" spellcheck="false" placeholder="Coinbase, Bit2Me, Binance, Revolut…" role="combobox" aria-expanded="false" aria-controls="ac" aria-autocomplete="list">
<kbd class="k">/</kbd></div><ul id="ac" class="ac" role="listbox" aria-label="Sugerencias" hidden></ul></div>
<div class="chips" aria-label="Búsquedas populares">{chips}</div>
<section id="res" class="results" aria-live="polite"></section><dl class="stats"><div class="hl"><dt>Pueden operar en España</dt><dd>{M["es"]}</dd></div><div><dt>Proveedores MiCA en la UE</dt><dd>{M["count"]}</dd></div><div><dt>Licencia completa (Art. 59)</dt><dd>{M["k"]["art59"]}</dd></div><div><dt>Marcas revisadas</dt><dd>{M["brands"]}</dd></div></dl>
</div>{marquee}</section>
<div class="wrap">
<section class="sec"><div class="sec-h"><div><span class="kick">Lo más buscado</span><h2>Marcas populares</h2><p class="muted">Estado de cada marca en el registro MiCA de ESMA a {esc(M["date"])}.</p></div><a href="marcas.html">Ver las {len(B)} marcas →</a></div><div class="grid">{"".join(bcard(b) for b in popular)}</div></section>
{chg_teaser()}
<section class="sec how"><div class="sec-h"><div><span class="kick">Guía rápida</span><h2>Qué significa cada etiqueta</h2></div></div><div class="grid3">
<div class="card"><span class="ic lic">{ICON["shield"]}</span><h3>Licencia MiCA completa</h3><p>Autorización como proveedor de servicios de criptoactivos (CASP) concedida por un supervisor de la UE.</p><p><span class="pill lic">Licencia MiCA completa<em>Art. 59</em></span></p></div>
<div class="card"><span class="ic ntf">{ICON["bank"]}</span><h3>Notificación de entidad financiera</h3><p>Bancos, empresas de inversión y gestoras ya supervisados que notifican servicios cripto sin licencia CASP aparte.</p><p><span class="pill ntf">Notificación de entidad financiera<em>Art. 60</em></span></p></div>
<div class="card"><span class="ic ok">{ICON["es"]}</span><h3>Puede operar en España</h3><p>La sociedad está autorizada en España o ha notificado España en su pasaporte europeo.</p><p><span class="pill ok">{ICON["check"]}Puede operar en España</span></p></div></div>
<p class="muted center" style="margin-top:22px"><a href="metodologia.html">Cómo lo determinamos y con qué confianza →</a></p></section>
{newsletter()}</div>'''
(S/"index.html").write_text(page("Registro MiCA · Comprueba si un exchange cripto tiene licencia MiCA en España", f"Buscador del registro MiCA de ESMA: {M['count']} proveedores autorizados, {M['es']} pueden operar en España. Actualizado {M['date']}.", home, 0, "",
    [{"@context":"https://schema.org","@type":"WebSite","name":"Registro MiCA","url":BASE,"inLanguage":"es","potentialAction":{"@type":"SearchAction","target":BASE+"?q={search_term_string}","query-input":"required name=search_term_string"}},
     {"@context":"https://schema.org","@type":"Organization","name":"Registro MiCA","url":BASE,"logo":BASE+"assets/brand/icon-512.png"}], cur="buscar"))
def crumbs(items): return {"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":i+1,"name":n,"item":BASE+u} for i,(n,u) in enumerate(items)]}
def verdict(cls, h, p, extra=""):
    return f'<section class="verdict {cls}"><span class="vi">{ICON["check"] if cls == "v-ok" else ICON["x"]}</span><div><h2>{h}</h2><p>{p}</p>{extra}</div></section>'
# ---- provider pages
for e in E:
    c, t, a = kind(e); hs = C.get(e["h"], e["h"])
    cty = "".join(f'<span class="{"es" if x == "ES" else ""}">{esc(C.get(x, x))}</span>' for x in e["cs"]) or "—"
    bc = next((bcolor(b) for b in brandsOf.get(e["slug"], []) if bcolor(b)), None) or linfo("ents", e["slug"]).get("color")
    body = f'''<div class="wrap narrow"><nav class="crumbs" aria-label="Migas"><a href="../index.html">Inicio</a><span>/</span><span>{esc(e["n"])}</span></nav>
<section class="phead card"{f' style="--brand:{bc}"' if bc else ""}>{elogo(e, "lg", "../", True)}<div><h1>{esc(e["n"])}</h1><p class="muted">{esc(e["l"])}{f' · marcas: {esc(", ".join(e["brands"]))}' if e["brands"] else ""}</p>
<div class="pills">{esb(e)}{kb(e)}{'<span class="pill no">Autorización retirada '+esc(e["end"])+'</span>' if e["end"] else ''}</div></div></section>
{verdict("v-ok" if e["es"] else "v-no", "Sí: puede prestar servicios cripto en España" if e["es"] else "No consta que pueda operar en España", ("Figura en el registro MiCA con España entre sus países de servicio." if e["es"] else "Tiene autorización MiCA, pero España no aparece entre sus países notificados.") + f' Datos del registro ESMA a {esc(M["date"])}.')}
<dl class="facts"><div><dt>País de origen</dt><dd>{esc(hs)}</dd></div><div><dt>En el registro desde</dt><dd>{esc(e["d"] or "—")}</dd></div><div><dt>Servicios MiCA</dt><dd>{len(e["s"])}</dd></div><div><dt>Países donde opera</dt><dd>{len(e["cs"])}</dd></div></dl>
<section class="card"><h2>Tipo de habilitación</h2><p><span class="pill {c}">{t}<em>{a}</em></span> <span class="conf conf-{e["conf"]}">{CONF[e["conf"]]}</span></p><p>{esc(e["why"])}.</p><p class="muted">Fuente: <a href="{esc(e["srcUrl"])}" rel="noopener">{esc(e["src"])}</a></p></section>
<section class="card"><h2>Ficha del registro</h2><dl class="kv">
<dt>Sociedad</dt><dd>{esc(e["l"])}</dd><dt>País de origen</dt><dd>{esc(hs)}</dd><dt>Supervisor</dt><dd>{esc(e["a"])}</dd>
<dt>En el registro desde</dt><dd>{esc(e["d"] or "—")}</dd><dt>LEI</dt><dd><code>{esc(e["lei"] or "—")}</code></dd><dt>Dirección</dt><dd>{esc(e["addr"] or "—")}</dd>
<dt>Web</dt><dd>{f'<a href="{esc(e["w"])}" rel="nofollow noopener">{esc(e["w"])}</a>' if e["w"] else "—"}</dd>{f'<dt>Comentarios ESMA</dt><dd>{esc(e["cm"])}</dd>' if e["cm"] else ""}</dl></section>
<section class="card"><h2>Servicios MiCA autorizados <span class="n">{len(e["s"])}</span></h2><ul class="svc">{"".join(f'<li><b>{s}</b>{esc(SV.get(s, s))}</li>' for s in e["s"])}</ul></section>
<section class="card"><h2>Países donde puede operar <span class="n">{len(e["cs"])}</span></h2><div class="cty">{cty}</div></section>
{brandlinks(e)}</div>'''
    (S/"p"/f'{e["slug"]}.html').write_text(page(f'{e["n"]}: ¿está autorizado en España? Licencia MiCA', f'{e["l"]} ({hs}). {"Puede" if e["es"] else "No consta que pueda"} operar en España. {t} ({a}). Registro ESMA {M["date"]}.', body, 1, f'p/{e["slug"]}.html', [crumbs([("Inicio",""),(e["n"],f'p/{e["slug"]}.html')])]))
# ---- cambios
def li(x, kind_):
    e = bySlug.get(x[-1]) if x[-1] else None
    nm = f'<a href="p/{x[-1]}.html">{esc(x[0])}</a>' if x[-1] else esc(x[0])
    return f'<li>{elogo(e, "xs") if e else tile({}, x[0], "xs")}<span>{nm}</span>{"" if kind_!="add" else (" <span class=\"pill ok sm\">España</span>" if x[2] else "")}</li>'
tl = "".join(f'''<li class="tl-i"><span class="tl-dot" aria-hidden="true"></span><div class="card"><div class="tl-h"><time>{esc(c["to"])}</time><span class="muted">desde {esc(c["from"])} · total {c["total"]}</span>
<span class="delta"><span class="pill ok sm">+{len(c["added"])}</span><span class="pill no sm">−{len(c["removed"])}</span></span></div>
{('<h3>Altas</h3><ul class="ent">'+"".join(li(x,"add") for x in c["added"])+'</ul>') if c["added"] else ""}
{('<h3>Bajas</h3><ul class="ent">'+"".join(li(x+[None],"rem") for x in c["removed"])+'</ul>') if c["removed"] else ""}
{('<h3>Cambio de pasaporte a España</h3><ul class="ent">'+"".join(f'<li>{elogo(bySlug[x[2]], "xs") if x[2] in bySlug else tile({}, x[0], "xs")}<span>{esc(x[0])}</span><span class="pill {"ok" if x[1] else "no"} sm">{"Añade España" if x[1] else "Retira España"}</span></li>' for x in c["es"])+'</ul>') if c["es"] else ""}
{'' if (c["added"] or c["removed"] or c["es"]) else '<p class="muted">Sin altas ni bajas (puede haber cambios de formato o actualización de fichas).</p>'}</div></li>''' for c in CH)
(S/"cambios.html").write_text(page("Cambios recientes en el registro MiCA · Registro MiCA", "Altas, bajas y cambios de pasaporte a España en el registro MiCA de ESMA, instantánea a instantánea.",
 f'<div class="wrap narrow"><header class="ph"><p class="eyebrow">Historial · {M["snapshots"]} instantáneas</p><h1>Cambios recientes</h1><p class="lede">Lo que se ha movido en el registro MiCA de ESMA entre cada instantánea.</p></header><ol class="tl">{tl}</ol>{newsletter()}</div>', 0, "cambios.html", cur="cambios"))
# ---- metodologia
met = f'''<div class="wrap narrow"><header class="ph"><p class="eyebrow">Metodología</p><h1>Cómo clasificamos cada proveedor</h1><p class="lede">ESMA mezcla en el mismo archivo las licencias CASP (Art. 59) y las notificaciones de entidades ya supervisadas (Art. 60) sin una columna que las distinga. Cruzamos fuentes oficiales, por este orden:</p></header>
<ol class="steps card"><li><b>Comentario del registro ESMA</b> que menciona el artículo 60 → Art. 60, confianza alta.</li>
<li><b>cryptocodes.eu</b>, que cruzó el registro con las listas de AFM, BaFin, CNMV y CySEC → Art. 60, confianza alta.</li>
<li><b>Listado de la CNMV</b> (entidades españolas): «Entidad de crédito» → Art. 60; «PSC» → Art. 59. Confianza alta.</li>
<li><b>Lista de IFM del BCE</b>: si el LEI es una entidad de crédito → Art. 60, confianza alta.</li>
<li><b>Registro MiFID/AIFMD/UCITS de ESMA</b>: si el LEI es empresa de inversión o gestora → probable Art. 60, confianza media (algunas piden licencia completa).</li>
<li>Si no es ninguna de las anteriores → solo puede operar con licencia CASP: Art. 59, confianza media.</li>
<li>Entidades de dinero electrónico u otras IFM → vía no determinada, confianza baja.</li></ol>
<section class="card"><h2>Resultado actual</h2><dl class="kv"><dt>Art. 59</dt><dd>{M["k"]["art59"]}</dd><dt>Art. 60</dt><dd>{M["k"]["art60"]}</dd><dt>No determinado</dt><dd>{M["k"]["incierto"]}</dd><dt>Confianza alta / media / baja</dt><dd>{M["conf"]["alta"]} / {M["conf"]["media"]} / {M["conf"]["baja"]}</dd><dt>Fuente del registro</dt><dd>{esc(M["source"])}</dd></dl></section>
<section class="card"><h2>Logotipos</h2><p>Los logotipos se descargan una sola vez del icono público de la web oficial de cada entidad (la que figura en el registro de ESMA o, para marcas sin sociedad en el registro, su dominio oficial comprobado) y se sirven desde esta web: tu navegador no se conecta a terceros para mostrarlos. Si no hay un icono de calidad suficiente, se muestra un monograma con las iniciales. Los logotipos solo identifican a cada entidad y no implican relación ni respaldo.</p></section></div>'''
(S/"metodologia.html").write_text(page("Metodología · Registro MiCA", "Cómo distinguimos licencias MiCA (Art. 59) y notificaciones (Art. 60).", met, 0, "metodologia.html", cur="metodologia"))


# ---- legales
EM = esc(CFG.get("email") or "[EMAIL]")
PH = lambda x: f'<mark class="ph-mark">{x}</mark>' if x.startswith("[") else f'<a href="mailto:{x}">{x}</a>'
SITE = "https://fjgnpa.github.io/esta-autorizado/"
aviso = f"""<div class="wrap narrow legal"><header class="ph"><p class="eyebrow">Legal</p><h1>Aviso legal</h1><p class="muted">Última actualización: 17/10/2026</p></header>
<section class="card"><h2>1. Qué es este sitio</h2><p>«Registro MiCA» ({SITE}) es un <strong>proyecto personal, informativo y sin ánimo de lucro</strong>, independiente de ESMA, la CNMV y cualquier autoridad: pese a su nombre, <strong>no es un registro oficial</strong> ni tiene relación con ellas. No vende productos ni servicios, no contiene publicidad, patrocinios ni enlaces de afiliado, y no recibe ninguna remuneración de las entidades que aparecen en él.</p>
<p>Contacto del proyecto: {PH(EM)}</p></section>
<section class="card"><h2>2. Contenido</h2><p>La web reproduce y ordena, con fecha, información pública de registros oficiales (ESMA, CNMV, BCE) sobre proveedores de servicios de criptoactivos bajo el Reglamento (UE) 2023/1114 (MiCA).</p></section>
<section class="card"><h2>3. No es asesoramiento</h2><p>Nada de lo publicado constituye asesoramiento financiero, de inversión, fiscal ni jurídico, ni una recomendación de contratar o no con ninguna entidad. El proyecto no es una entidad supervisada. La clasificación entre licencia (art. 59 MiCA) y notificación (art. 60 MiCA) es una <strong>inferencia</strong> a partir de fuentes públicas y puede contener errores. La información oficial y vinculante es la de los registros de <a href="https://www.esma.europa.eu/esmas-activities/digital-finance-and-innovation/markets-crypto-assets-regulation-mica" rel="noopener">ESMA</a> y la <a href="https://www.cnmv.es/portal/consultas/proveedores-servicios-criptoactivos?lang=es" rel="noopener">CNMV</a>: compruébala siempre antes de tomar decisiones.</p>
<p>Los criptoactivos son productos complejos y de alto riesgo: puedes perder todo el capital invertido.</p></section>
<section class="card"><h2>4. Exactitud y responsabilidad</h2><p>Los datos se actualizan periódicamente de forma automática, pero pueden contener errores o estar desfasados respecto a los registros oficiales. No se garantiza su exactitud ni se asume responsabilidad por decisiones tomadas a partir de ellos ni por el contenido de sitios de terceros enlazados. Si detectas un error, escríbenos a {PH(EM)} y lo corregiremos.</p></section>
<section class="card"><h2>5. Fuentes, marcas y licencia de datos</h2><p>Los datos proceden de fuentes públicas (ESMA, CNMV, BCE), de cryptocodes.eu y de <a href="https://casptracker.eu" rel="noopener">CASP Tracker</a> (licencia <a href="https://creativecommons.org/licenses/by/4.0/" rel="noopener">CC BY 4.0</a>). Las marcas y nombres comerciales citados pertenecen a sus titulares y se mencionan únicamente para identificarlos; su mención no implica relación ni respaldo. Los logotipos se muestran solo para identificar a cada entidad: proceden del icono público de su web oficial y se sirven desde esta web, sin enlazar a terceros. El código del proyecto es público en <a href="https://github.com/fjgnpa/esta-autorizado" rel="noopener">GitHub</a>.</p></section>
<p class="muted">Texto orientativo; no sustituye a un asesoramiento jurídico.</p></div>"""
(S/"aviso-legal.html").write_text(page("Aviso legal · Registro MiCA", "Aviso legal de Registro MiCA, proyecto informativo y sin ánimo de lucro sobre el registro MiCA.", aviso, 0, "aviso-legal.html", cur="legal"))
priv = f"""<div class="wrap narrow legal"><header class="ph"><p class="eyebrow">Legal</p><h1>Política de privacidad</h1><p class="muted">Última actualización: 17/10/2026</p></header>
<section class="card"><h2>1. Responsable y contacto</h2><p>Responsable: el proyecto «Registro MiCA», de carácter personal y no comercial. Para cualquier cuestión sobre tus datos, incluido el ejercicio de tus derechos, escribe a {PH(EM)}.</p></section>
<section class="card"><h2>2. Qué datos tratamos y para qué</h2>
<p><strong>Newsletter.</strong> Si te suscribes, tratamos tu dirección de correo electrónico (y los datos técnicos de entrega, apertura y clics que genera la plataforma de envío) solo para enviarte la newsletter sobre cambios en el registro MiCA. <em>Base jurídica:</em> tu consentimiento (art. 6.1.a RGPD y art. 21 LSSI-CE), que puedes retirar en cualquier momento con el enlace de baja de cada correo o escribiendo a {PH(EM)}. No usamos tu correo para nada más ni lo cedemos.</p>
<p><strong>Formulario de suscripción.</strong> El formulario de la newsletter lo sirve Beehiiv mediante un script incrustado (subscribe-forms.beehiiv.com): al cargar la página, tu navegador se conecta a Beehiiv, que puede recibir datos técnicos como tu IP y, si te suscribes, tu correo. Beehiiv puede usar almacenamiento técnico propio para el funcionamiento del formulario; consulta su política de privacidad.</p>
<p><strong>Navegación.</strong> La web no tiene registro de usuarios ni formularios propios que guarden datos. El buscador funciona íntegramente en tu navegador. La tipografía y los logotipos se sirven desde esta misma web: tu navegador no se conecta a terceros para mostrarlos.</p></section>
<section class="card"><h2>3. Cookies y almacenamiento local</h2><p>Esta web no instala cookies propias, ni analítica, ni publicidad. El formulario incrustado de Beehiiv podría usar cookies o almacenamiento técnico necesarios para su funcionamiento; no los controlamos. Si eliges manualmente el tema claro u oscuro, tu navegador guarda esa preferencia en su almacenamiento local (<code>localStorage</code>, clave «theme»): es un ajuste que tú solicitas, no se envía a ningún servidor y puedes borrarlo desde tu navegador. Si algún día se añadiera algo que requiera consentimiento, se pediría antes.</p></section>
<section class="card"><h2>4. Proveedores (encargados del tratamiento)</h2>
<p><strong>Beehiiv, Inc.</strong> (EE. UU.): plataforma de envío de la newsletter. Actúa como encargado del tratamiento; las transferencias internacionales se amparan en las garantías que ofrezca el proveedor (Marco de Privacidad de Datos UE-EE. UU. si está adherido, o cláusulas contractuales tipo). <a href="https://www.beehiiv.com/privacy" rel="noopener">Política de privacidad de Beehiiv</a>.</p>
<p><strong>GitHub, Inc.</strong> (EE. UU.): alojamiento de la web (GitHub Pages). Al visitarla, GitHub puede registrar tu dirección IP con fines técnicos y de seguridad. <a href="https://docs.github.com/es/site-policy/privacy-policies/github-general-privacy-statement" rel="noopener">Declaración de privacidad de GitHub</a>.</p></section>
<section class="card"><h2>5. Conservación</h2><p>Conservamos tu correo mientras sigas suscrito. Al darte de baja se elimina, salvo el tiempo imprescindible para atender obligaciones legales.</p></section>
<section class="card"><h2>6. Tus derechos</h2><p>Puedes ejercer los derechos de acceso, rectificación, supresión, oposición, limitación y portabilidad escribiendo a {PH(EM)}. Si consideras que no se han atendido correctamente, puedes reclamar ante la <a href="https://www.aepd.es" rel="noopener">Agencia Española de Protección de Datos</a>.</p></section>
<section class="card"><h2>7. Menores</h2><p>La newsletter no está dirigida a menores de 14 años.</p></section>
<p class="muted">Texto orientativo; no sustituye a un asesoramiento jurídico.</p></div>"""
(S/"privacidad.html").write_text(page("Política de privacidad · Registro MiCA", "Política de privacidad y cookies de Registro MiCA: sin cookies, newsletter con Beehiiv.", priv, 0, "privacidad.html"))
# ---- brand pages
CATN = {"exchange":"Exchange","bróker":"Bróker","banco/neobanco/pagos":"Banco, neobanco o pagos","wallet":"Monedero","compra/rampa/app":"App de compra","institucional/custodia":"Institucional / custodia"}
def faq(qas): return {"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a in qas]}
def related(b, n=8):
    pool = [x for x in B if x is not b and x["cat"] == b["cat"]] + [x for x in B if x is not b and x["cat"] != b["cat"]]
    return '<div class="grid">' + "".join(bcard(x, "../") for x in pool[:n]) + '</div>'
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
    bc = bcolor(b)
    pills = ('<span class="pill ok">'+ICON["check"]+'Puede operar en España</span>') if b["es"] else ('<span class="pill no">'+ICON["x"]+('España no notificada' if ents else 'No figura en el registro MiCA')+'</span>')
    if ents:
        e0k = next((x for x in ents if x["es"]), ents[0]); pills += kb(e0k)
    entl = "".join(f'<a class="rc" href="../p/{x["slug"]}.html"><span class="rc-v {"ok" if x["es"] else "no"}" aria-hidden="true"></span>{elogo(x, "md", "../")}<div class="b"><h3>{esc(x["l"])}</h3><div class="sub">{esc(C.get(x["h"], x["h"]))} · {esc(x["a"])}</div><div class="pills">{esb(x)}{kb(x)}</div></div><span class="go" aria-hidden="true">→</span></a>' for x in ents)
    body = f"""<div class="wrap narrow"><nav class="crumbs" aria-label="Migas"><a href="../index.html">Inicio</a><span>/</span><a href="../marcas.html">Marcas</a><span>/</span><span>{nm}</span></nav>
<section class="phead card"{f' style="--brand:{bc}"' if bc else ""}>{blogo(b, "lg", "../", True)}<div><p class="eyebrow">{esc(CATN.get(b["cat"], b["cat"]))} · registro ESMA a {esc(dt)}</p><h1>¿Está {nm} autorizado en España?</h1>
<div class="pills">{pills}</div></div></section>
{verdict(ver[0], ver[1], vtxt, (('<p class="muted" style="margin-top:.5em">'+esc(b["note"])+'</p>') if b["note"] else "") + warn)}
{('<section class="card"><h2>Sociedades en el registro <span class="n">'+str(len(ents))+'</span></h2><div class="ent-list">' + entl + '</div></section>') if ents else ''}
<section class="card"><h2>Preguntas frecuentes</h2>{faqh}</section>
<section class="card"><h2>Fuente del mapeo</h2><p>{esc(b["src"])}. Comprobado el {esc(dt)}.</p><p class="muted">Confirma siempre en <a href="https://www.esma.europa.eu/esmas-activities/digital-finance-and-innovation/markets-crypto-assets-regulation-mica" rel="noopener">ESMA</a> y en la <a href="https://www.cnmv.es/portal/consultas/proveedores-servicios-criptoactivos?lang=es" rel="noopener">CNMV</a>.</p></section>
<section class="sec"><div class="sec-h"><h2>Comprueba otras marcas</h2><a href="../marcas.html">Ver todas →</a></div>{related(b)}</section>
{newsletter("../")}</div>"""
    title = f"¿Está {b['b']} autorizado en España? Licencia MiCA ({dt[:7]})"
    (S/"marca"/f'{b["slug"]}.html').write_text(page(title, desc, body, 1, f'marca/{b["slug"]}.html', [faq(qas), crumbs([("Inicio",""),("Marcas","marcas.html"),(b["b"],f'marca/{b["slug"]}.html')])], "article", cur="marcas"))
# ---- marcas index
groups = {}
for b in B: groups.setdefault(b["cat"], []).append(b)
nok = sum(b["es"] for b in B)
tools = f'''<div class="tools" role="search"><label class="flt"><span class="sr">Filtrar marcas</span>{ICON["search"]}<input id="mf" type="search" placeholder="Filtrar {len(B)} marcas…" autocomplete="off"></label>
<div class="seg" role="group" aria-label="Filtrar por estado"><button type="button" data-f="all" aria-pressed="true">Todas</button><button type="button" data-f="ok" aria-pressed="false">Pueden operar ({nok})</button><button type="button" data-f="no" aria-pressed="false">Sin permiso ({len(B) - nok})</button></div><span class="cnt" id="mc" aria-live="polite"></span></div>'''
mi = f"""<div class="wrap"><header class="ph"><p class="eyebrow">{len(B)} marcas · registro ESMA a {esc(M["date"])}</p><h1>¿Qué plataformas cripto están autorizadas en España?</h1><p class="lede">Exchanges, brókers, neobancos, apps y monederos populares en España, con su estado en el registro MiCA.</p></header>{tools}
""" + "".join(f'<section class="sec" style="margin:34px 0"><div class="sec-h"><h2>{esc(CATN.get(k, k))} <span class="muted" style="font-weight:600;font-size:.7em">{len(v)}</span></h2></div><div class="grid">' + "".join(bcard(x) for x in sorted(v, key=lambda x: x["b"].lower())) + '</div></section>' for k, v in groups.items()) + newsletter() + "</div>"
(S/"marcas.html").write_text(page("¿Qué exchanges cripto están autorizados en España? Lista MiCA de marcas", f"Estado en el registro MiCA de {len(B)} exchanges, brókers, neobancos y apps cripto populares en España: quién puede operar y quién no. Datos ESMA a {M['date']}.", mi, 0, "marcas.html", cur="marcas"))
# ---- data for search (logo: [fichero, modo] o índice de paleta para el monograma)
def lgref(info, name):
    f = lgfile(info)
    if f: return [f, (info.get("mode") or "pad") + (" lg-light" if info.get("light") else "") + (" lg-low" if info.get("lowres") else "")]
    return pal(name)
def elg(e):
    info = linfo("ents", e["slug"])
    if not lgfile(info):
        for bb in brandsOf.get(e["slug"], []):
            if lgfile(linfo("brands", bb["b"])): info = linfo("brands", bb["b"]); break
    return lgref(info, e["n"])
def blg(b):
    info = linfo("brands", b["b"])
    if not lgfile(info) and b["e"]: info = linfo("ents", b["e"][0])
    return lgref(info, b["b"])
idx = {"m": {"date": M["date"]}, "pal": PAL, "e": [[e["slug"], e["n"], e["l"], e["h"], int(e["es"]), kind(e)[0], kind(e)[1], kind(e)[2], e["brands"], elg(e)] for e in E],
       "b": [[b["b"], b["e"], b["note"], [w["l"] for w in b["warn"]], b["cat"], b["slug"], blg(b)] for b in B]}
(S/"assets").mkdir(exist_ok=True); (S/"assets/data.js").write_text("window.DB=" + json.dumps(idx, ensure_ascii=False, separators=(",", ":")) + ";")
for f in ["data.js", "common.js", "style.css"]: (S/f).unlink(missing_ok=True)
urls = [("", "1.0", "daily"), ("marcas.html", "0.9", "weekly"), ("cambios.html", "0.8", "weekly"), ("metodologia.html", "0.4", "monthly"), ("aviso-legal.html", "0.1", "yearly"), ("privacidad.html", "0.1", "yearly")] + [(f'marca/{b["slug"]}.html', "0.8", "weekly") for b in B] + [(f'p/{e["slug"]}.html', "0.6", "weekly") for e in E]
(S/"sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + "".join(f"<url><loc>{BASE}{u}</loc><lastmod>{M['date']}</lastmod><changefreq>{f}</changefreq><priority>{pr}</priority></url>" for u, pr, f in urls) + "</urlset>\n")
nl = sum(1 for b in B if lgfile(linfo("brands", b["b"]))); ne = sum(1 for e in E if lgfile(linfo("ents", e["slug"])))
print("site:", len(E), "fichas,", len(B), "marcas · logos:", nl, "marcas,", ne, "fichas")
