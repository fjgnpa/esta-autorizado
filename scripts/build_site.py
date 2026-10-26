#!/usr/bin/env python3
"""Registro MiCA: genera el sitio estático (site/) desde data/build.json y data/logos.json.
SITE_BASE (variable de entorno) o data/config.json → useCustomDomain decide la URL canónica."""
import json, pathlib, html, shutil, hashlib, re, os, unicodedata, base64, datetime, urllib.parse
R = pathlib.Path(__file__).resolve().parent.parent; S = R/"site"
CFG = json.load(open(R/"data/config.json"))
BASE = (os.environ.get("SITE_BASE") or "").strip() or (CFG.get("siteBaseCustom") if CFG.get("useCustomDomain") else CFG.get("siteBaseGithub")) or "https://fjgnpa.github.io/esta-autorizado/"
if not BASE.endswith("/"): BASE += "/"
BPATH = urllib.parse.urlsplit(BASE).path or "/"
d = json.load(open(R/"data/build.json")); M = d["meta"]; E = d["ents"]; B = d["brands"]; CH = d["changes"]; GONE = d.get("gone", [])
try: LG = json.load(open(R/"data/logos.json"))
except Exception: LG = {"brands": {}, "ents": {}}
bySlug = {e["slug"]: e for e in E}
GONE = [g for g in GONE if g["slug"] not in bySlug]; goneBy = {g["slug"]: g for g in GONE}
for p in [S/"p", S/"marca"]: shutil.rmtree(p, ignore_errors=True); p.mkdir(parents=True)
for f in S.glob("*.html"): f.unlink()
esc = lambda s: html.escape(str(s or ""), quote=True)
def fmt(x):
    try: return datetime.date.fromisoformat(x).strftime("%d/%m/%Y")
    except Exception: return x or "—"
def safe_url(u): return u if isinstance(u, str) and re.fullmatch(r"https?://[^\s\"'<>`]+", u) else ""
def ldjson(x): return json.dumps(x, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
def fit(cands, n=60):
    for c in cands:
        if len(c) <= n: return c
    c = cands[-1]; return c[:n-1].rsplit(" ", 1)[0] + "…"
def clip(s, n=160): return s if len(s) <= n else s[:n-1].rsplit(" ", 1)[0].rstrip(",.;:") + "…"
try:
    from zoneinfo import ZoneInfo; TODAY = datetime.datetime.now(ZoneInfo("Europe/Madrid")).date()
except Exception: TODAY = datetime.date.today()
# Estado a la fecha del build (no solo del refresco): retirada si la fecha de fin ya pasó; «pendiente» si la autorización
# empieza en el futuro (autorizada, pero aún no puede operar). Así un build posterior activa a los pendientes sin refrescar.
_TD = TODAY.isoformat()
for _e in E:
    _e["active"] = not (_e.get("end") and _e["end"] <= _TD)
    _e["pending"] = _e["active"] and bool(_e.get("d")) and _e["d"] > _TD
    _e["es"] = _e["active"] and not _e["pending"] and ("ES" in (_e.get("cs") or []) or _e["h"] == "ES")
_op = [x for x in E if x["active"] and not x["pending"]]
M.update({"count": len(_op), "pending": sum(x["pending"] for x in E), "inactive": sum(not x["active"] for x in E), "es": sum(x["es"] for x in E),
          "k": {k: sum(x["k"] == k for x in _op) for k in ("art59", "art60", "incierto")},
          "conf": {c: sum(x["conf"] == c for x in _op) for c in ("oficial", "verificado", "alta", "media", "baja")},
          "official": sum(x["conf"] == "oficial" for x in _op)})
assert not any(x["es"] and (x["pending"] or not x["active"]) for x in E)
CHECKED = M.get("checked") or M["date"]
STALE_DAYS = (TODAY - datetime.date.fromisoformat(CHECKED)).days
C = {"AT":"Austria","BE":"Bélgica","BG":"Bulgaria","CY":"Chipre","CZ":"Chequia","DE":"Alemania","DK":"Dinamarca","EE":"Estonia","ES":"España","FI":"Finlandia","FR":"Francia","GR":"Grecia","EL":"Grecia","HR":"Croacia","HU":"Hungría","IE":"Irlanda","IS":"Islandia","IT":"Italia","LI":"Liechtenstein","LT":"Lituania","LU":"Luxemburgo","LV":"Letonia","MT":"Malta","NL":"Países Bajos","NO":"Noruega","PL":"Polonia","PT":"Portugal","RO":"Rumanía","SE":"Suecia","SI":"Eslovenia","SK":"Eslovaquia"}
SV = {"a":"Custodia y administración","b":"Gestión de plataforma de negociación","c":"Canje de cripto por fondos","d":"Canje de cripto por cripto","e":"Ejecución de órdenes","f":"Colocación","g":"Recepción y transmisión de órdenes","h":"Asesoramiento","i":"Gestión de carteras","j":"Servicios de transferencia"}
def kind(e):
    off = "" if e.get("active", True) else " off"
    if e["k"] == "art59" and e["conf"] == "media": return ("lic inf" + off, "Licencia MiCA (inferida)", "Art. 59 · inferido")
    if e["k"] == "art59": return ("lic" + off, "Licencia MiCA completa", "Art. 59")
    if e["k"] == "art60" and e["conf"] in ("oficial", "verificado", "alta"): return ("ntf" + off, "Notificación de entidad financiera", "Art. 60")
    if e["k"] == "art60": return ("ntf inf" + off, "Probable notificación", "Art. 60 · probable")
    return ("unk" + off, "Vía no determinada", "59 / 60 ?")
CONF = {"oficial": "Dato oficial ESMA", "verificado": "Verificado manualmente", "alta": "Inferencia · confianza alta", "media": "Inferencia · confianza media", "baja": "Inferencia · confianza baja"}
SRCN = {"ESMA": "Registro MiCA de ESMA (CASPS.csv)", "ECB": "Lista de IFM del BCE", "ESMA-MiFID": "Registro MiFID/AIFMD/UCITS de ESMA", "CNMV": "Listado de la CNMV", "cryptocodes": "cryptocodes.eu", "verificado": "Fuente pública verificada"}
ESMA_URL = "https://www.esma.europa.eu/esmas-activities/digital-finance-and-innovation/markets-crypto-assets-regulation-mica"
CNMV_URL = "https://www.cnmv.es/portal/consultas/proveedores-servicios-criptoactivos?lang=es"
EXT = 'rel="nofollow noopener noreferrer"'
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
ICON["clock"] = '<svg viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="6" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M8 4.8V8l2.2 1.5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>'
ICON["ext"] = '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M9 3h4v4M13 3L7.5 8.5M11.5 9.5V13h-8.5V4.5H7" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>'
# ---- estados (nunca solo por color: siempre icono + texto)
def est(e):
    if not e.get("active", True): return "ret"
    if e.get("pending"): return "pend"
    return "ok" if e["es"] else "no"
def esb(e):
    s = est(e)
    if s == "ret": return f'<span class="pill no">{ICON["x"]}Autorización retirada{(" · " + esc(fmt(e["end"]))) if e.get("end") else ""}</span>'
    if s == "pend": return f'<span class="pill pend">{ICON["clock"]}Autorizado, empieza el {esc(fmt(e["d"]))}</span>'
    return f'<span class="pill {"ok" if e["es"] else "no"}">{ICON["check"] if e["es"] else ICON["x"]}{"Puede operar en España" if e["es"] else "España no notificada"}</span>'
def kb(e): c, t, a = kind(e); return f'<span class="pill {c}" title="{esc(e["why"])}">{t}<em>{a}</em></span>'
BST = {"ok": ("ok", "check", "Puede operar en España", "Puede operar en España"),
       "sin": ("no", "minus", "España no notificada", "Sin España notificada"),
       "ret": ("no", "x", "Autorización retirada", "Autorización retirada"),
       "pend": ("pend", "clock", "Autorizado, aún no empieza", "Empieza más adelante"),
       "nofig": ("no", "x", "No figura en el registro MiCA", "No figura"),
       "auto": ("neu", "minus", "No aplica · monedero de autocustodia", "No aplica · autocustodia"),
       "nocr": ("neu", "minus", "Sin servicios cripto MiCA en el registro", "Sin servicios cripto MiCA")}
THEME_JS = 'try{const t=localStorage.getItem("theme");if(t)document.documentElement.dataset.theme=t}catch(e){}'
THEME_H = base64.b64encode(hashlib.sha256(THEME_JS.encode()).digest()).decode()
# Estadísticas de visitas sin cookies (GoatCounter). Script versionado con SRI publicado por GoatCounter
# (https://www.goatcounter.com/help/countjs-versions); el contador envía la visita por sendBeacon (connect-src)
# o, si falla, con una imagen (img-src).
GC_HOST = "https://registromica.goatcounter.com"
GC_SRC, GC_SRI = "https://gc.zgo.at/count.v5.js", "sha384-atnOLvQb9t+jTSipvd75X2yginT4PjVbqDdlJAmxMm+wYElFmeR6EmLP5bYeoRVQ"
GC_TAG = f'<script data-goatcounter="{GC_HOST}/count" async src="{GC_SRC}" crossorigin="anonymous" integrity="{GC_SRI}"></script>'
CSP = (f"default-src 'self'; script-src 'self' 'sha256-{THEME_H}' https://gc.zgo.at; style-src 'self' 'unsafe-inline'; img-src 'self' data: {GC_HOST}; font-src 'self'; "
       f"connect-src 'self' {GC_HOST}; manifest-src 'self'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'self'; upgrade-insecure-requests")
def page(title, desc, body, depth=0, path="", ld=None, otype="website", cur="", up=None, robots=None):
    up = "../" * depth if up is None else up
    canon = BASE + path
    ldj = "".join(f'<script type="application/ld+json">{ldjson(x)}</script>' for x in (ld or []))
    nav = [("index.html#buscar", "Buscar", "buscar", ""), ("marcas.html", "Marcas", "marcas", ""), ("cambios.html", "Cambios", "cambios", "hide-m"), ("metodologia.html", "Metodología", "metodologia", "hide-m")]
    navh = "".join(f'<a href="{up}{u}"{" aria-current=\"page\"" if cur == k else ""}{f" class=\"{c}\"" if c else ""}>{t}</a>' for u, t, k, c in nav)
    nsr = "" if cur == "buscar" else f'<form class="nsr" action="{up}index.html" method="get" role="search"><label class="sr" for="nq">Buscar marca o sociedad</label>{ICON["search"]}<input id="nq" name="q" type="search" maxlength="60" placeholder="Buscar…" autocomplete="off" spellcheck="false"></form>'
    stale = f'<div class="stale" id="stale" data-checked="{esc(CHECKED)}"{"" if STALE_DAYS > 10 else " hidden"}><div class="wrap"><b>Datos posiblemente desactualizados.</b> La última comprobación del registro de ESMA fue el {esc(fmt(CHECKED))}. Confirma en <a href="{ESMA_URL}" {EXT}>ESMA</a> y la <a href="{CNMV_URL}" {EXT}>CNMV</a> antes de decidir.</div></div>'
    return f'''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="{CSP}"><meta name="referrer" content="strict-origin-when-cross-origin">
<title>{esc(title)}</title><meta name="description" content="{esc(desc)}"><link rel="canonical" href="{esc(canon)}">{f'<meta name="robots" content="{robots}">' if robots else ""}
<meta property="og:type" content="{otype}"><meta property="og:site_name" content="Registro MiCA"><meta property="og:locale" content="es_ES"><meta property="og:url" content="{esc(canon)}"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:image" content="{BASE}assets/og.png"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta property="og:image:alt" content="Registro MiCA: buscador del registro MiCA para España">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{esc(title)}"><meta name="twitter:description" content="{esc(desc)}"><meta name="twitter:image" content="{BASE}assets/og.png">{ldj}
<meta name="color-scheme" content="light dark"><meta name="theme-color" content="#f6f8fb" media="(prefers-color-scheme: light)"><meta name="theme-color" content="#06090e" media="(prefers-color-scheme: dark)"><meta name="application-name" content="Registro MiCA"><meta name="apple-mobile-web-app-title" content="Registro MiCA">
<link rel="preload" href="{up}assets/fonts/inter-var.woff2" as="font" type="font/woff2" crossorigin><link rel="stylesheet" href="{up}assets/app.css">
<link rel="icon" href="{up}favicon.ico" sizes="48x48"><link rel="icon" href="{up}assets/favicon.svg" type="image/svg+xml"><link rel="apple-touch-icon" href="{up}assets/brand/apple-touch-icon.png"><link rel="manifest" href="{up}site.webmanifest">
<script>{THEME_JS}</script></head><body>
<a class="skip" href="#main">Saltar al contenido</a>
<header class="nav"><div class="wrap nav-in"><a class="logo" href="{up}index.html" aria-label="Registro MiCA, inicio"><img src="{up}assets/brand/mark.svg" alt="" width="32" height="32"><span>Registro <b>MiCA</b></span></a>
{nsr}<nav aria-label="Principal">{navh}
<button class="theme" type="button" aria-label="Tema oscuro" aria-pressed="false">{ICON["moon"]}{ICON["sun"]}</button></nav></div></header>{stale}
<main id="main">{body}</main>
<footer class="foot"><div class="wrap"><div class="foot-g"><div><a class="logo" href="{up}index.html"><img src="{up}assets/brand/mark.svg" alt="" width="28" height="28" loading="lazy"><span>Registro <b>MiCA</b></span></a>
<p><strong>Registro MiCA</strong> es un proyecto independiente: <strong>no es el registro oficial</strong> de ESMA ni de la CNMV. Reproduce, con fecha, el registro provisional MiCA de ESMA (actualizado {esc(fmt(M["date"]))}). No es asesoramiento financiero ni una determinación oficial. Confirma siempre en <a href="{ESMA_URL}" {EXT}>ESMA</a> y en la <a href="{CNMV_URL}" {EXT}>CNMV</a>.</p></div>
<p class="flinks"><a href="{up}index.html#buscar">Buscador</a><a href="{up}marcas.html">Todas las marcas</a><a href="{up}proveedores.html">Lista de proveedores</a><a href="{up}guia-mica.html">Guía MiCA</a><a href="{up}cambios.html">Cambios recientes</a><a href="{up}metodologia.html">Metodología</a><a href="{up}aviso-legal.html">Aviso legal</a><a href="{up}privacidad.html">Política de privacidad</a></p></div>
<p class="disc"><strong>Aviso:</strong> proyecto informativo sin ánimo de lucro, sin publicidad ni enlaces de afiliado. Nada de lo publicado es asesoramiento financiero, fiscal ni jurídico, ni recomendación de inversión. Los criptoactivos son de alto riesgo y puedes perder todo lo invertido.</p>
<p class="src">Fuentes: ESMA (CASPS.csv, NCASP.csv, registro MiFID), BCE (lista de IFM), CNMV, cryptocodes.eu. Histórico hasta el 06/10/2026: <a href="https://casptracker.eu" {EXT}>CASP Tracker</a>, licencia <a href="https://creativecommons.org/licenses/by/4.0/deed.es" {EXT}>CC BY 4.0</a>, datos transformados. Los logotipos pertenecen a sus titulares y solo identifican a cada entidad.</p></div></footer>
<script src="{up}assets/app.js" defer></script>{GC_TAG}</body></html>'''
def newsletter(up=""):
    sub = safe_url(CFG.get("beehiivSubscribeUrl"))
    if not sub: return ""
    return f'''<section class="news card" id="newsletter"><div><span class="news-ic">{ICON["mail"]}</span><h2>Los cambios del registro, cada lunes</h2><p class="muted">Altas, bajas, retiradas y quién gana o pierde el permiso para operar en España. Un correo, sin ruido.</p>
<ul class="news-pts"><li>{ICON["check"]}Gratis</li><li>{ICON["check"]}Un correo a la semana</li><li>{ICON["check"]}Baja en un clic</li></ul></div>
<div class="news-r"><a class="btn btn-lg" href="{esc(sub)}" target="_blank" rel="noopener noreferrer">Suscribirme gratis{ICON["ext"]}</a>
<p class="news-legal">Se abre la página de suscripción de Beehiiv en una pestaña nueva: esta web no carga nada de Beehiiv ni recoge tu correo. Allí Beehiiv trata tu dirección como encargado del tratamiento. Más información en la <a href="{up}privacidad.html">política de privacidad</a>.</p></div></section>'''
def slugify(x):
    x = unicodedata.normalize("NFKD", x).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", x).strip("-")
STMAP = {"autocustodia": "auto", "sincripto": "nocr"}
for b in B:
    b["slug"] = slugify(b["b"]); ents_ = [bySlug[x] for x in b["e"]]
    b["es"] = any(x["es"] for x in ents_)
    if b["es"]: b["st"] = "ok"
    elif ents_ and not any(x.get("active", True) for x in ents_): b["st"] = "ret"
    elif any(x.get("pending") for x in ents_): b["st"] = "pend"
    elif ents_: b["st"] = "sin"
    else: b["st"] = STMAP.get(b.get("status"), "nofig")
brandsOf = {}
for b in B:
    for x in b["e"]: brandsOf.setdefault(x, []).append(b)
def brandlinks(e):
    bs = brandsOf.get(e["slug"], [])
    if not bs: return ""
    return '<section class="card"><h2>Marcas de esta sociedad</h2><div class="grid" style="margin-top:12px">' + "".join(bcard(b, "../") for b in bs) + '</div></section>'
def bstatus(b, big=False):
    c, ic, long_, short = BST[b["st"]]
    return f'<span class="{"pill" if big else "st"} {c}">{ICON[ic]}{long_ if big else short}</span>'
def bsub(b):
    if not b["e"]: return {"auto": "No custodia tus fondos", "nocr": "Sin sociedad cripto en el registro"}.get(b["st"], "Sin sociedad en el registro")
    e = bySlug[next((x for x in b["e"] if bySlug[x]["es"]), b["e"][0])]
    if not e.get("active", True): return f'{C.get(e["h"], e["h"])} · retirada {fmt(e["end"])}'
    if e.get("pending"): return f'{C.get(e["h"], e["h"])} · empieza el {fmt(e["d"])}'
    return f'{C.get(e["h"], e["h"])} · {kind(e)[2] if not kind(e)[0].startswith("unk") else "vía por confirmar"}'
def bcard(b, up="", eager=False):
    return f'<a class="bc" href="{up}marca/{b["slug"]}.html" data-st="{b["st"]}" data-n="{esc(slugify(b["b"]) + " " + " ".join(b.get("aliases", [])))}">{blogo(b, "md", up, eager)}<span class="bc-t"><b>{esc(b["b"])}</b><small>{esc(bsub(b))}</small>{bstatus(b)}</span></a>'
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
def stsmall(e):
    if e is None: return ""
    s = est(e)
    if s == "ok": return f'<span class="st ok">{ICON["check"]}Puede operar en España</span>'
    if s == "ret": return f'<span class="st no">{ICON["x"]}Autorización retirada</span>'
    if s == "pend": return f'<span class="st pend">{ICON["clock"]}Autorizado, empieza el {esc(fmt(e["d"]))}</span>'
    return f'<span class="st no">{ICON["minus"]}Sin España notificada</span>'
def chg_teaser():
    if not last: return ""
    items = [x for x in last["added"] if x[3] in bySlug][:6]
    if not items: return ""
    cards = "".join(f'<a class="bc" href="p/{x[3]}.html">{elogo(bySlug[x[3]], "md")}<span class="bc-t"><b>{esc(bySlug[x[3]]["n"])}</b><small>{esc(C.get(x[1], x[1]))} · alta {esc(fmt(last["to"]))}</small>{stsmall(bySlug[x[3]])}</span></a>' for x in items)
    return f'<section class="sec"><div class="sec-h"><div><span class="kick">Novedades</span><h2>Últimas altas en el registro</h2><p class="muted">Instantánea del {esc(fmt(last["to"]))}: +{len(last["added"])} altas, −{len(last["removed"])} bajas.</p></div><a href="cambios.html">Ver el historial →</a></div><div class="grid chg">{cards}</div></section>'
RET = [e for e in E if not e.get("active", True)]
def ret_block():
    if not RET: return ""
    cards = "".join(f'<a class="bc" href="p/{e["slug"]}.html" data-st="ret">{elogo(e, "md")}<span class="bc-t"><b>{esc(e["n"])}</b><small>{esc(C.get(e["h"], e["h"]))} · desde {esc(fmt(e["end"]))}</small><span class="st no">{ICON["x"]}Autorización retirada</span></span></a>' for e in sorted(RET, key=lambda x: x["end"], reverse=True))
    return f'<section class="sec"><div class="sec-h"><div><span class="kick kick-no">Atención</span><h2>Autorizaciones retiradas</h2><p class="muted">Siguen en el archivo de ESMA, pero con fecha de fin: ya no pueden operar con esa autorización.</p></div></div><div class="grid chg">{cards}</div></section>'
home = f'''<section class="hero"><div class="aurora" aria-hidden="true"><i></i><i></i><i></i></div><div class="wrap">
<p class="eyebrow"><span class="live"></span>Registro ESMA · actualizado {esc(fmt(M["date"]))}</p>
<h1>¿Tu exchange está <span class="grad">autorizado</span> en España?</h1>
<p class="lede">Comprueba en segundos si una plataforma cripto tiene licencia MiCA, quién está detrás y si puede operar legalmente aquí.</p>
<form class="search" id="buscar" role="search" action="index.html" method="get"><div class="s-box"><span class="s-ic">{ICON["search"]}</span>
<label class="sr" for="q">Buscar marca o sociedad</label>
<input id="q" name="q" type="search" maxlength="60" autocomplete="off" spellcheck="false" placeholder="Coinbase, Bit2Me, Binance, Revolut…" role="combobox" aria-expanded="false" aria-controls="ac" aria-autocomplete="list" aria-describedby="rcount">
<kbd class="k">/</kbd></div><ul id="ac" class="ac" role="listbox" aria-label="Sugerencias" hidden></ul></form>
<div class="chips" aria-label="Búsquedas populares">{chips}</div><p id="rcount" class="sr" aria-live="polite"></p>
<section id="res" class="results" aria-label="Resultados"></section><dl class="stats"><div class="hl"><dt>Pueden operar en España</dt><dd>{M["es"]}</dd></div><div><dt>Proveedores MiCA activos (UE/EEE)</dt><dd>{M["count"]}</dd></div><div><dt>Licencia completa (Art. 59)</dt><dd>{M["k"]["art59"]}</dd></div><div><dt>Notificaciones (Art. 60)</dt><dd>{M["k"]["art60"]}</dd></div></dl>
</div>{marquee}</section>
<div class="wrap">
<section class="sec"><div class="sec-h"><div><span class="kick">Lo más buscado</span><h2>Marcas populares</h2><p class="muted">Estado de cada marca en el registro MiCA de ESMA a {esc(fmt(M["date"]))}.</p></div><a href="marcas.html">Ver las {len(B)} marcas →</a></div><div class="grid">{"".join(bcard(b) for b in popular)}</div></section>
{chg_teaser()}
{ret_block()}
<section class="sec how"><div class="sec-h"><div><span class="kick">Guía rápida</span><h2>Qué significa cada etiqueta</h2></div></div><div class="grid3">
<div class="card"><span class="ic lic">{ICON["shield"]}</span><h3>Licencia MiCA completa</h3><p>Autorización como proveedor de servicios de criptoactivos (CASP) concedida por un supervisor de la UE/EEE. Si ESMA no publica la base legal y la deducimos, se marca como «inferida».</p><p><span class="pill lic">Licencia MiCA completa<em>Art. 59</em></span></p></div>
<div class="card"><span class="ic ntf">{ICON["bank"]}</span><h3>Notificación de entidad financiera</h3><p>Bancos, empresas de inversión y gestoras ya supervisados que notifican servicios cripto sin licencia CASP aparte.</p><p><span class="pill ntf">Notificación de entidad financiera<em>Art. 60</em></span></p></div>
<div class="card"><span class="ic ok">{ICON["es"]}</span><h3>Puede operar en España</h3><p>Autorización vigente y España como país de origen o entre los países notificados. Una autorización retirada o que aún no ha empezado nunca cuenta.</p><p><span class="pill ok">{ICON["check"]}Puede operar en España</span></p></div></div>
<p class="muted center" style="margin-top:22px"><a href="proveedores.html">Lista completa de proveedores</a> · <a href="guia-mica.html">Guía MiCA: licencia, notificación y periodo transitorio</a> · <a href="metodologia.html">Cómo lo determinamos →</a></p></section>
{newsletter()}</div>'''
ORG = {"@context":"https://schema.org","@type":"Organization","name":"Registro MiCA","url":BASE,"logo":BASE+"assets/brand/icon-512.png"}
ESMA_LEGAL = "https://www.esma.europa.eu/about-esma/legal-notice-and-data-protection"
ESMA_REG_LEGAL = "https://registers.esma.europa.eu/publication/legalNoticePage"
SNAPD = sorted(f.stem for f in (R/"data/snapshots").glob("*.json"))
DATASET = {"@context":"https://schema.org","@type":"Dataset","name":"Proveedores de servicios de criptoactivos MiCA con acceso a España",
    "description":"Copia fechada y clasificada del registro provisional MiCA de ESMA: autorizaciones CASP (Art. 59/63), notificaciones (Art. 60), países notificados y retiradas.",
    "url":BASE,"inLanguage":"es","dateModified":M["date"],"creator":ORG,"publisher":ORG,"isAccessibleForFree":True,
    # sin licencia propia: reutilización según las condiciones de cada fuente (ESMA: citar la fuente e indicar la transformación), explicadas aquí
    "license":BASE+"metodologia.html#licencia",
    "keywords":["MiCA","CASP","criptoactivos","proveedores de servicios de criptoactivos","registro MiCA","ESMA","CNMV","España","exchanges autorizados","Art. 59","Art. 60"],
    "spatialCoverage":{"@type":"Place","name":"Unión Europea y Espacio Económico Europeo (UE/EEE), con el acceso a España"},
    "isBasedOn":[ESMA_URL,"https://casptracker.eu"],"creditText":"Fuente: ESMA (registro provisional MiCA), datos transformados; histórico hasta 06/10/2026: CASP Tracker (CC BY 4.0), datos transformados",
    "distribution":[{"@type":"DataDownload","encodingFormat":"application/json","contentUrl":BASE+"datos/proveedores.json"},
                    {"@type":"DataDownload","encodingFormat":"text/csv","contentUrl":BASE+"datos/proveedores.csv"}]}
if SNAPD: DATASET["temporalCoverage"] = f"{SNAPD[0]}/{M['date']}"
(S/"index.html").write_text(page("Registro MiCA · ¿Exchange cripto autorizado en España?", clip(f"Buscador del registro MiCA de ESMA: {M['count']} proveedores activos en la UE/EEE, {M['es']} pueden operar en España. Datos a {fmt(M['date'])}."), home, 0, "",
    [{"@context":"https://schema.org","@type":"WebSite","name":"Registro MiCA","url":BASE,"inLanguage":"es"}, ORG, DATASET], cur="buscar"))
def crumbs(items): return {"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":i+1,"name":n,"item":BASE+u} for i,(n,u) in enumerate(items)]}
def verdict(cls, h, p, extra=""):
    ic = ICON["check"] if cls == "v-ok" else (ICON["minus"] if cls == "v-neu" else ICON["x"])
    return f'<section class="verdict {cls}"><span class="vi">{ic}</span><div><h2>{h}</h2><p>{p}</p>{extra}</div></section>'
# ---- provider pages
ncount, nhcount = {}, {}
for e in E: ncount[e["n"].lower()] = ncount.get(e["n"].lower(), 0) + 1; nhcount[(e["n"].lower(), e["h"])] = nhcount.get((e["n"].lower(), e["h"]), 0) + 1
def weblinks(e):
    ws = [safe_url(u) for u in (e.get("ws") or ([e["w"]] if e.get("w") else []))]; wp = [safe_url(u) for u in e.get("wp", [])]
    ws = [u for u in ws if u]; wp = [u for u in wp if u and u not in ws]
    h = "".join(f'<a href="{esc(u)}" {EXT}>{esc(re.sub(r"^https?://(www\.)?", "", u).rstrip("/"))}</a>' for u in ws)
    if wp: h += '<span class="muted"> · plataforma: </span>' + "".join(f'<a href="{esc(u)}" {EXT}>{esc(re.sub(r"^https?://(www\.)?", "", u).rstrip("/"))}</a>' for u in wp)
    return f'<span class="wl">{h}</span>' if h else "—"
def ecard(e, up="../"):
    return f'<a class="bc" href="{up}p/{e["slug"]}.html">{elogo(e, "md", up)}<span class="bc-t"><b>{esc(e["n"])}</b><small>{esc(C.get(e["h"], e["h"]))} · {esc(kind(e)[2])}</small>{stsmall(e)}</span></a>'
def related_ents(e, n=6):
    """Enlaces internos rastreables: otros proveedores activos del mismo país (primero los que pueden operar en España)."""
    pool = [x for x in E if x is not e and x["h"] == e["h"] and x.get("active", True)]
    pool.sort(key=lambda x: (not x["es"], x["n"].lower()))
    if not pool: return ""
    hs = C.get(e["h"], e["h"])
    return f'<section class="sec"><div class="sec-h"><h2>Otros proveedores con sede en {esc(hs)}</h2><a href="../proveedores.html">Ver la lista completa →</a></div><div class="grid chg">{"".join(ecard(x) for x in pool[:n])}</div><p class="muted" style="margin-top:14px">¿Dudas sobre licencias, notificaciones o el periodo transitorio? Lee la <a href="../guia-mica.html">guía MiCA para España</a>.</p></section>'
def entld(e, title, desc):
    org = {"@type": "Organization", "name": e["n"], "legalName": e["l"]}
    if e.get("lei"): org["leiCode"] = e["lei"]
    if e.get("addr"): org["address"] = e["addr"]
    w = safe_url(e.get("w") or "")
    if w: org["url"] = w
    if e.get("active", True) and not e.get("pending") and e["cs"]: org["areaServed"] = [C.get(x, x) for x in e["cs"]]
    return {"@context": "https://schema.org", "@type": "WebPage", "name": title, "description": desc, "url": BASE + f'p/{e["slug"]}.html', "inLanguage": "es",
            "dateModified": M["date"], "isPartOf": {"@type": "WebSite", "name": "Registro MiCA", "url": BASE}, "about": org}
for e in E:
    c, t, a = kind(e); hs = C.get(e["h"], e["h"]); act = e.get("active", True)
    cty = "".join(f'<span class="{"es" if x == "ES" else ""}">{esc(C.get(x, x))}</span>' for x in e["cs"]) or "—"
    bc = next((bcolor(b) for b in brandsOf.get(e["slug"], []) if bcolor(b)), None) or linfo("ents", e["slug"]).get("color")
    since = esc(fmt(e["d"]) if e.get("d") else (f'{e["dt"]} (año no indicado en el registro)' if e.get("dt") else "—"))
    if not act:
        cm = f' Comentario de ESMA: «{esc(e["cm"])}».' if e.get("cm") else ""
        vd = verdict("v-no", f'Autorización retirada el {esc(fmt(e["end"]))}: ya no puede operar', f'El registro de ESMA indica que su autorización terminó el {esc(fmt(e["end"]))}.{cm} Desde esa fecha no puede prestar servicios cripto con esta autorización, tampoco en España. Datos del registro ESMA a {esc(fmt(M["date"]))}.')
        meta_d = f'Autorización MiCA retirada el {fmt(e["end"])}: ya no puede operar.'
    elif e.get("pending"):
        vd = verdict("v-neu", f'Autorizado, empieza el {esc(fmt(e["d"]))}: aún no puede operar', f'El registro de ESMA indica que su autorización empieza a aplicarse el {esc(fmt(e["d"]))}. Hasta esa fecha no cuenta como proveedor activo ni puede prestar servicios cripto con esta autorización{"" if not ("ES" in e["cs"] or e["h"] == "ES") else ", tampoco en España"}. Datos del registro ESMA a {esc(fmt(M["date"]))}.')
        meta_d = f'Autorizado, empieza el {fmt(e["d"])}: aún no puede operar.'
    elif e["es"]:
        vd = verdict("v-ok", "Sí: puede prestar servicios cripto en España", ("Su país de origen es España." if e["h"] == "ES" else "Figura en el registro MiCA con España entre sus países de servicio.") + f' Datos del registro ESMA a {esc(fmt(M["date"]))}.')
        meta_d = "Puede operar en España."
    else:
        vd = verdict("v-no", "No consta que pueda operar en España", ("Tiene autorización MiCA, pero España no aparece entre sus países notificados." if not e.get("homeOnly") else "Tiene autorización MiCA solo en su país de origen: el registro no indica otros países.") + f' Datos del registro ESMA a {esc(fmt(M["date"]))}.')
        meta_d = "No consta que pueda operar en España."
    dup = ncount[e["n"].lower()] > 1
    tag = (f" ({hs})" if nhcount[(e["n"].lower(), e["h"])] == 1 else f" ({hs}, LEI …{(e['lei'] or e['slug'])[-4:]})") if dup else ""
    nm_t = e["n"] + tag
    title = fit([f"{nm_t}: ¿autorizado en España? MiCA", f"{nm_t} · registro MiCA", nm_t]) if not dup else (e["n"][:60 - len(tag) - 1].rstrip() + ("…" if len(e["n"]) > 60 - len(tag) - 1 else "") + tag)
    if dup and len(title) <= 34: title = fit([title + ": ¿autorizado en España?", title + " · registro MiCA", title])
    srcu = safe_url(e.get("srcUrl"))
    ctyh = "Países notificados (antes de la retirada)" if not act else ("Solo en su país de origen" if e.get("homeOnly") else "Países donde puede operar")
    body = f'''<div class="wrap narrow"><nav class="crumbs" aria-label="Migas"><a href="../index.html">Inicio</a><span>/</span><span>{esc(e["n"])}</span></nav>
<section class="phead card"{f' style="--brand:{bc}"' if bc else ""}>{elogo(e, "lg", "../", True)}<div><h1>{esc(e["n"])}</h1><p class="muted">{esc(e["l"])}{f' · marcas: {esc(", ".join(e["brands"]))}' if e["brands"] else ""}</p>
<div class="pills">{esb(e)}{kb(e)}</div></div></section>
{vd}
<dl class="facts"><div><dt>País de origen</dt><dd>{esc(hs)}</dd></div><div><dt>{"Autorización hasta" if not act else ("Empieza el" if e.get("pending") else "En el registro desde")}</dt><dd>{esc(fmt(e["end"])) if not act else since}</dd></div><div><dt>Servicios MiCA</dt><dd>{len(e["s"])}</dd></div><div><dt>Países donde opera</dt><dd>{0 if not act else len(e["cs"])}</dd></div></dl>
<section class="card"><h2>Tipo de habilitación</h2><p><span class="pill {c}">{t}<em>{a}</em></span> <span class="conf conf-{esc(e["conf"])}">{CONF.get(e["conf"], e["conf"])}</span></p><p>{esc(e["why"])}.</p><p class="muted">Fuente: {f'<a href="{esc(srcu)}" {EXT}>{esc(SRCN.get(e["src"], e["src"]))}</a>' if srcu else esc(SRCN.get(e["src"], e["src"]))}</p></section>
<section class="card"><h2>Ficha del registro</h2><dl class="kv">
<dt>Sociedad</dt><dd>{esc(e["l"])}</dd><dt>País de origen</dt><dd>{esc(hs)}</dd><dt>Supervisor</dt><dd>{esc(e["a"])}</dd>
<dt>En el registro desde</dt><dd>{since}</dd>{f'<dt>Fin de la autorización</dt><dd>{esc(fmt(e["end"]))}</dd>' if e.get("end") else ""}<dt>Base legal (ESMA)</dt><dd>{esc({"Article 63": "Art. 63 · autorización CASP", "Article 60": "Art. 60 · notificación"}.get(e.get("lb"), "No indicada"))}</dd>
<dt>LEI</dt><dd><code>{esc(e["lei"] or "—")}</code></dd><dt>Dirección</dt><dd>{esc(e["addr"] or "—")}</dd>
<dt>Web</dt><dd>{weblinks(e)}</dd>{f'<dt>Comentarios ESMA</dt><dd>{esc(e["cm"])}</dd>' if e["cm"] else ""}<dt>Última actualización</dt><dd>{esc(fmt(e.get("lu")))}</dd></dl></section>
<section class="card"><h2>Servicios MiCA {"que tenía autorizados" if not act else "autorizados"} <span class="n">{len(e["s"])}</span></h2><ul class="svc">{"".join(f'<li><b>{esc(s)}</b>{esc(SV.get(s, s))}</li>' for s in e["s"] if s in SV)}</ul></section>
<section class="card"><h2>{ctyh} <span class="n">{len(e["cs"])}</span></h2><div class="cty">{cty}</div></section>
{brandlinks(e)}
{related_ents(e)}</div>'''
    desc = clip(f'{e["l"]} ({hs}). {meta_d} {t} ({a}). Registro ESMA a {fmt(M["date"])}.')
    (S/"p"/f'{e["slug"]}.html').write_text(page(title, desc, body, 1, f'p/{e["slug"]}.html', [entld(e, title, desc), crumbs([("Inicio",""),("Proveedores","proveedores.html"),(e["n"],f'p/{e["slug"]}.html')])]))
for g in GONE:
    body = f'''<div class="wrap narrow"><nav class="crumbs" aria-label="Migas"><a href="../index.html">Inicio</a><span>/</span><span>{esc(g["n"])}</span></nav>
<section class="phead card">{tile({}, g["n"], "lg")}<div><h1>{esc(g["n"])}</h1><p class="muted">{esc(g["l"])}</p><div class="pills"><span class="pill no">{ICON["x"]}Ya no figura en el registro</span></div></div></section>
{verdict("v-no", f'Ya no figura en el registro MiCA desde el {esc(fmt(g["removed"]))}', f'Aparecía en la instantánea del {esc(fmt(g["last"]))} y no en la del {esc(fmt(g["removed"]))}. Sin entrada en el registro no consta que pueda prestar servicios cripto bajo MiCA. Si crees que es un error, compruébalo en ESMA.')}
<section class="card"><h2>Último dato conocido</h2><dl class="kv"><dt>Sociedad</dt><dd>{esc(g["l"])}</dd><dt>País de origen</dt><dd>{esc(C.get(g["h"], g["h"]))}</dd><dt>Supervisor</dt><dd>{esc(g["a"])}</dd><dt>LEI</dt><dd><code>{esc(g["lei"] or "—")}</code></dd></dl></section></div>'''
    (S/"p"/f'{g["slug"]}.html').write_text(page(fit([f'{g["n"]}: ya no figura en el registro MiCA', f'{g["n"]} · baja del registro MiCA']) if len(g["n"]) < 40 else g["n"][:38].rstrip() + "… · baja del registro", clip(f'{g["l"]} ya no figura en el registro MiCA de ESMA desde el {fmt(g["removed"])}.'), body, 1, f'p/{g["slug"]}.html', robots="noindex"))
# ---- cambios
def li(name, slug, extra=""):
    e = bySlug.get(slug) if slug else None
    has = slug and (slug in bySlug or slug in goneBy)
    nm = f'<a href="p/{slug}.html">{esc(name)}</a>' if has else esc(name)
    return f'<li>{elogo(e, "xs") if e else tile({}, name, "xs")}<span>{nm}</span>{extra}</li>'
# notas editoriales por instantánea (data/notas.json): texto revisado a mano; [[slug|texto]] enlaza a la ficha (el build falla si no existe)
try: NOTAS = json.load(open(R/"data/notas.json")).get("notes", {})
except FileNotFoundError: NOTAS = {}
def nlinks(t):
    def rep(m):
        tgt, txt = m.group(1), m.group(2)
        if re.fullmatch(r"[a-z0-9-]+\.html(#[a-z0-9-]+)?", tgt): return f'<a href="{esc(tgt)}">{esc(txt)}</a>'
        if tgt not in bySlug and tgt not in goneBy: raise SystemExit(f"notas.json: ficha inexistente {tgt}")
        return f'<a href="p/{esc(tgt)}.html">{esc(txt)}</a>'
    parts = re.split(r"(\[\[[^\]|]+\|[^\]]+\]\])", t)
    return "".join(rep(re.fullmatch(r"\[\[([^\]|]+)\|([^\]]+)\]\]", x)) if x.startswith("[[") else esc(x) for x in parts)
def nota(c):
    n = NOTAS.get(c["to"])
    if not n: return ""
    figs = "".join(f'<div><dt>{esc(a)}</dt><dd><span class="was">{esc(b)}</span><span class="arr" aria-label="pasa a">→</span><b>{esc(d)}</b></dd></div>' for a, b, d in n.get("figures", []))
    return (f'<section class="tl-note" id="nota-{esc(c["to"])}" aria-labelledby="nota-h-{esc(c["to"])}"><p class="kick">Nota · {esc(fmt(c["to"]))}</p><h3 id="nota-h-{esc(c["to"])}">{esc(n["title"])}</h3>'
            + (f'<dl class="tl-figs">{figs}</dl>' if figs else "") + "".join(f"<p>{nlinks(x)}</p>" for x in n.get("p", []))
            + (f'<p class="tl-foot">{nlinks(n["foot"])}</p>' if n.get("foot") else "") + "</section>")
tl = "".join(f'''<li class="tl-i"><span class="tl-dot" aria-hidden="true"></span><div class="card"><div class="tl-h"><time datetime="{esc(c["to"])}">{esc(fmt(c["to"]))}</time><span class="muted">desde {esc(fmt(c["from"]))} · total {c["total"]}</span>
<span class="delta"><span class="pill ok sm">+{len(c["added"])}<span class="sr"> altas</span></span><span class="pill no sm">−{len(c["removed"])}<span class="sr"> bajas</span></span></span></div>
{nota(c)}{('<h3>Altas</h3><ul class="ent">'+"".join(li(x[0], x[3], ' <span class="pill ok sm">España</span>' if x[2] else "") for x in c["added"])+'</ul>') if c["added"] else ""}
{('<h3>Bajas</h3><ul class="ent">'+"".join(li(x[0], x[2] if len(x) > 2 else None) for x in c["removed"])+'</ul>') if c["removed"] else ""}
{('<h3>Cambio de acceso a España</h3><ul class="ent">'+"".join(li(x[0], x[2], f'<span class="pill {"ok" if x[1] else "no"} sm">{"Añade España" if x[1] else ("Retirada" if (bySlug.get(x[2]) or {}).get("active", True) is False else "Retira España")}</span>') for x in c["es"])+'</ul>') if c["es"] else ""}
{'' if (c["added"] or c["removed"] or c["es"]) else '<p class="muted">Sin altas ni bajas (puede haber cambios de formato o actualización de fichas).</p>'}</div></li>''' for c in CH)
SNAPSRC = {}
for f in sorted((R/"data/snapshots").glob("*.json")):
    try: SNAPSRC[f.stem] = json.loads(f.read_text()).get("sourceUsed") or "CASP Tracker"
    except Exception: pass
ct_last = max([k for k, v in SNAPSRC.items() if v.startswith("CASP Tracker")] or [""])
attr = f'<p class="muted">Histórico hasta el {esc(fmt(ct_last))}: <a href="https://casptracker.eu" {EXT}>CASP Tracker</a>, licencia <a href="https://creativecommons.org/licenses/by/4.0/deed.es" {EXT}>CC BY 4.0</a>, datos transformados (normalizados y comparados por LEI). Desde entonces: archivo CASPS.csv de ESMA.</p>' if ct_last else ""
(S/"cambios.html").write_text(page("Cambios en el registro MiCA · Registro MiCA", "Altas, bajas, retiradas y cambios de acceso a España en el registro MiCA de ESMA, instantánea a instantánea.",
 f'<div class="wrap narrow"><header class="ph"><p class="eyebrow">Historial · {M["snapshots"]} instantáneas</p><h1>Cambios recientes</h1><p class="lede">Lo que se ha movido en el registro MiCA de ESMA entre cada instantánea.</p>{attr}</header><ol class="tl">{tl}</ol>{newsletter()}</div>', 0, "cambios.html", [crumbs([("Inicio",""),("Cambios","cambios.html")])], cur="cambios"))
# ---- metodologia
K = M["k"]; CF = M["conf"]; nb = sum(1 for e in E if e.get("lb")); ne_ = len(E)
met = f'''<div class="wrap narrow"><header class="ph"><p class="eyebrow">Metodología</p><h1>Cómo clasificamos cada proveedor</h1><p class="lede">El archivo de ESMA mezcla autorizaciones CASP y notificaciones de entidades ya supervisadas. Usamos primero el dato oficial y solo deducimos cuando falta.</p></header>
<section class="card"><h2>1. Dato oficial: la base legal de ESMA</h2><p>El archivo CASPS.csv de ESMA incluye la columna <code>ac_legal_basis</code>. Hoy viene informada en {nb} de {ne_} entidades:</p>
<ul class="steps"><li><b>«Article 63»</b> → <span class="pill lic">Licencia MiCA completa<em>Art. 59</em></span>. El art. 59 de MiCA exige estar autorizado como proveedor de servicios de criptoactivos (CASP); el art. 62 regula la solicitud y el art. 63 su evaluación y concesión. ESMA etiqueta estas autorizaciones con el art. 63; las mostramos como «Art. 59» porque es la licencia que exige ese artículo.</li>
<li><b>«Article 60»</b> → <span class="pill ntf">Notificación de entidad financiera<em>Art. 60</em></span>: bancos, empresas de inversión, gestoras, entidades de dinero electrónico y otras ya supervisadas que notifican servicios cripto sin licencia CASP aparte.</li></ul>
<p>Este dato prevalece siempre sobre cualquier deducción y se marca como «Dato oficial ESMA».</p></section>
<section class="card"><h2>2. Si ESMA no indica la base legal: inferencia</h2><p>Para el resto cruzamos fuentes públicas, por este orden:</p><ol class="steps">
<li><b>Corrección verificada</b> a mano con una fuente pública citada en la ficha (<code>data/overrides.json</code>) → «Verificado manualmente».</li>
<li><b>Comentario del registro ESMA</b> que menciona el artículo 60 → Art. 60, confianza alta.</li>
<li><b>cryptocodes.eu</b>, que cruzó el registro con las listas de AFM, BaFin, CNMV y CySEC → Art. 60, confianza alta.</li>
<li><b>Listado de la CNMV</b> (entidades españolas): «Entidad de crédito» → Art. 60; «PSC» → Art. 59. Confianza alta.</li>
<li><b>Lista de IFM del BCE</b>: si el LEI es una entidad de crédito → Art. 60, confianza alta.</li>
<li><b>Registro MiFID/AIFMD/UCITS de ESMA</b>: si el LEI es empresa de inversión o gestora → probable Art. 60, confianza media.</li>
<li>Si no es ninguna de las anteriores → <span class="pill lic inf">Licencia MiCA (inferida)<em>Art. 59 · inferido</em></span>, confianza media.</li>
<li>Entidades de dinero electrónico u otras IFM → vía no determinada, confianza baja.</li></ol></section>
<section class="card"><h2>3. ¿Puede operar en España?</h2><p>Solo si la autorización está <b>vigente</b> (sin fecha de fin, o con fecha de fin futura), <b>ya ha empezado</b> (si ESMA indica una fecha de inicio futura, se muestra «autorizado, empieza el dd/mm» y no cuenta como activo hasta ese día) y España es su país de origen o figura entre sus países notificados. Una entidad con fecha de fin pasada aparece como <span class="pill no">{ICON["x"]}Autorización retirada</span> y no cuenta en ningún total. Si el registro no indica países, se entiende que solo opera en su país de origen.</p></section>
<section class="card"><h2>4. Marcas sin sociedad en el registro</h2><p>Una marca sin sociedad en el registro aparece como <span class="pill no">{ICON["x"]}No figura en el registro MiCA</span>, salvo dos casos neutros:</p><ul class="steps">
<li><b>Monederos de autocustodia</b> (Ledger, Trezor, MetaMask…): <span class="pill neu">{ICON["minus"]}No aplica · monedero de autocustodia</span>. El software o hardware que no custodia tus fondos no es un servicio cripto de MiCA; las compras o canjes dentro de la app los presta un tercero, que sí debe figurar.</li>
<li><b>Bancos y servicios de pago</b> sin entidad en el registro: <span class="pill neu">{ICON["minus"]}Sin servicios cripto MiCA en el registro</span>. Es un hecho del registro, no un juicio: si te ofrecen cripto, ese servicio no está autorizado bajo MiCA.</li></ul>
<p>El aviso de la lista de entidades no conformes de ESMA solo se muestra si el nombre comercial o legal coincide exactamente, o si la coincidencia se ha revisado a mano.</p></section>
<section class="card"><h2>Resultado actual</h2><dl class="kv"><dt>Proveedores activos</dt><dd>{M["count"]} (más {M.get("pending", 0)} autorizados que empiezan más adelante y {M.get("inactive", 0)} con autorización retirada)</dd><dt>Pueden operar en España</dt><dd>{M["es"]}</dd><dt>Art. 59</dt><dd>{K["art59"]}</dd><dt>Art. 60</dt><dd>{K["art60"]}</dd><dt>No determinado</dt><dd>{K["incierto"]}</dd>
<dt>Dato oficial / verificado</dt><dd>{CF.get("oficial", 0)} / {CF.get("verificado", 0)}</dd><dt>Inferencia alta / media / baja</dt><dd>{CF["alta"]} / {CF["media"]} / {CF["baja"]}</dd><dt>Fuente del registro</dt><dd>{esc(M["source"])}</dd><dt>Última comprobación</dt><dd>{esc(fmt(CHECKED))}</dd></dl></section>
<section class="card"><h2>Calidad de los datos</h2><p>Antes de publicar, cada actualización pasa controles automáticos: columnas obligatorias, un mínimo de proveedores, variaciones bruscas respecto a la semana anterior (más de un 15 % menos o un 30 % más), entidades de referencia que deben seguir presentes y nombres con caracteres sospechosos. Si algo falla, no se publica nada y se mantiene la versión anterior. Si los datos tienen más de 10 días, la web muestra un aviso.</p>
<p>Las webs del registro se normalizan (por ejemplo, «https.//» o varias URL en un mismo campo) y solo se enlazan direcciones http/https válidas. Las fechas sin año del registro se muestran tal cual, sin inventar el año.</p></section>
<section class="card"><h2>Fuentes y licencias</h2><p>Registro MiCA de <a href="{ESMA_URL}" {EXT}>ESMA</a> (CASPS.csv y NCASP.csv), registro MiFID/AIFMD/UCITS de ESMA, lista de IFM del BCE, listado de la <a href="{CNMV_URL}" {EXT}>CNMV</a> y cryptocodes.eu. Histórico hasta el {esc(fmt(ct_last) if ct_last else "—")}: <a href="https://casptracker.eu" {EXT}>CASP Tracker</a>, licencia <a href="https://creativecommons.org/licenses/by/4.0/deed.es" {EXT}>CC BY 4.0</a>, datos transformados.</p></section>
<section class="card" id="licencia"><h2>Licencia y reutilización</h2><p>Esta web no aplica una licencia propia a los datos: se reutilizan en las condiciones de cada fuente.</p><ul class="steps">
<li><b>Registro MiCA de ESMA</b> (CASPS.csv, NCASP.csv) y registro MiFID/AIFMD/UCITS: ESMA autoriza su reproducción siempre que se cite la fuente y, si se transforman, se indique expresamente. Condiciones en el <a href="{ESMA_LEGAL}" {EXT}>aviso legal de la web de ESMA</a> y en el <a href="{ESMA_REG_LEGAL}" {EXT}>aviso legal de sus registros</a>.</li>
<li><b>Histórico hasta el {esc(fmt(ct_last) if ct_last else "06/10/2026")}</b>: <a href="https://casptracker.eu" {EXT}>CASP Tracker</a>, licencia <a href="https://creativecommons.org/licenses/by/4.0/deed.es" {EXT}>CC BY 4.0</a>.</li>
<li><b>Clasificación Art. 59/60</b>: se apoya además en la lista de IFM del BCE, el listado de la CNMV y cryptocodes.eu, según las condiciones de cada uno.</li></ul>
<p>Esta web se ha elaborado con material descargado de la web de ESMA, transformado (normalizado, clasificado, traducido y comparado entre fechas). ESMA no respalda esta publicación y no es responsable de infracciones de derechos de autor u otros derechos de propiedad intelectual ni de los daños causados a terceros por esta publicación.</p>
<p>Si reutilizas estos datos, cita la fuente original (ESMA y, para el histórico, CASP Tracker) e indica que están transformados. Descarga: <a href="datos/proveedores.json">JSON</a> · <a href="datos/proveedores.csv">CSV</a>.</p></section>
<section class="card"><h2>Logotipos</h2><p>Los logotipos se descargan una sola vez del icono público de la web oficial de cada entidad (la que figura en el registro de ESMA o, para marcas sin sociedad en el registro, su dominio oficial comprobado) y se sirven desde esta web: tu navegador no se conecta a terceros para mostrarlos. Si no hay un icono de calidad suficiente, se muestra un monograma con las iniciales. Los logotipos solo identifican a cada entidad y no implican relación ni respaldo.</p></section></div>'''
(S/"metodologia.html").write_text(page("Metodología · Registro MiCA", "Cómo distinguimos licencias MiCA (Art. 59/63) y notificaciones (Art. 60): dato oficial de ESMA primero, inferencia solo si falta.", met, 0, "metodologia.html", [crumbs([("Inicio",""),("Metodología","metodologia.html")])], cur="metodologia"))
# ---- legales
EM = esc(CFG.get("email") or "")
PH = lambda x: f'<a href="mailto:{x}">{x}</a>' if x else "el formulario de contacto del repositorio"
SITE = BASE
aviso = f"""<div class="wrap narrow legal"><header class="ph"><p class="eyebrow">Legal</p><h1>Aviso legal</h1><p class="muted">Última actualización: 17/10/2026</p></header>
<section class="card"><h2>1. Qué es este sitio</h2><p>«Registro MiCA» ({esc(SITE)}) es un <strong>proyecto personal, informativo y sin ánimo de lucro</strong>, independiente de ESMA, la CNMV y cualquier autoridad: pese a su nombre, <strong>no es un registro oficial</strong> ni tiene relación con ellas. No vende productos ni servicios, no contiene publicidad, patrocinios ni enlaces de afiliado, y no recibe ninguna remuneración de las entidades que aparecen en él.</p>
<p>Contacto del proyecto: {PH(EM)}</p></section>
<section class="card"><h2>2. Contenido</h2><p>La web reproduce y ordena, con fecha, información pública de registros oficiales (ESMA, CNMV, BCE) sobre proveedores de servicios de criptoactivos bajo el Reglamento (UE) 2023/1114 (MiCA).</p></section>
<section class="card"><h2>3. No es asesoramiento</h2><p>Nada de lo publicado constituye asesoramiento financiero, de inversión, fiscal ni jurídico, ni una recomendación de contratar o no con ninguna entidad. El proyecto no es una entidad supervisada. La clasificación entre licencia (art. 59 MiCA) y notificación (art. 60 MiCA) usa el dato oficial de ESMA cuando lo publica; si no, es una <strong>inferencia</strong> a partir de fuentes públicas, se indica como tal y puede contener errores. La información oficial y vinculante es la de los registros de <a href="{ESMA_URL}" {EXT}>ESMA</a> y la <a href="{CNMV_URL}" {EXT}>CNMV</a>: compruébala siempre antes de tomar decisiones.</p>
<p>Los criptoactivos son productos complejos y de alto riesgo: puedes perder todo el capital invertido.</p></section>
<section class="card"><h2>4. Exactitud y responsabilidad</h2><p>Los datos se actualizan periódicamente de forma automática, con controles que bloquean la publicación si detectan datos anómalos, pero pueden contener errores o estar desfasados respecto a los registros oficiales. No se garantiza su exactitud ni se asume responsabilidad por decisiones tomadas a partir de ellos ni por el contenido de sitios de terceros enlazados. Si detectas un error, escríbenos a {PH(EM)} y lo corregiremos.</p></section>
<section class="card"><h2>5. Fuentes, marcas y licencia de datos</h2><p>Los datos proceden de fuentes públicas (ESMA, CNMV, BCE) y de cryptocodes.eu. El histórico hasta el 06/10/2026 procede de <a href="https://casptracker.eu" {EXT}>CASP Tracker</a> (licencia <a href="https://creativecommons.org/licenses/by/4.0/deed.es" {EXT}>CC BY 4.0</a>), con datos transformados. Las marcas y nombres comerciales citados pertenecen a sus titulares y se mencionan únicamente para identificarlos; su mención no implica relación ni respaldo. Los logotipos se muestran solo para identificar a cada entidad: proceden del icono público de su web oficial y se sirven desde esta web, sin enlazar a terceros. El código del proyecto es público en <a href="https://github.com/fjgnpa/esta-autorizado" {EXT}>GitHub</a>.</p></section>
<p class="muted">Texto orientativo; no sustituye a un asesoramiento jurídico.</p></div>"""
(S/"aviso-legal.html").write_text(page("Aviso legal · Registro MiCA", "Aviso legal de Registro MiCA, proyecto informativo y sin ánimo de lucro sobre el registro MiCA.", aviso, 0, "aviso-legal.html", cur="legal"))
SUBH = esc(urllib.parse.urlsplit(CFG.get("beehiivSubscribeUrl") or "").hostname or "beehiiv.com")
priv = f"""<div class="wrap narrow legal"><header class="ph"><p class="eyebrow">Legal</p><h1>Política de privacidad</h1><p class="muted">Última actualización: 24/10/2026</p></header>
<section class="card"><h2>1. Responsable y contacto</h2><p>Responsable: el proyecto «Registro MiCA», de carácter personal y no comercial. Para cualquier cuestión sobre tus datos, incluido el ejercicio de tus derechos, escribe a {PH(EM)}.</p></section>
<section class="card"><h2>2. Qué datos tratamos y para qué</h2>
<p><strong>Navegación.</strong> Esta web no carga fuentes, formularios incrustados ni publicidad de terceros. La tipografía, los logotipos y el buscador se sirven desde esta misma web y el buscador funciona íntegramente en tu navegador. No hay registro de usuarios ni formularios que guarden datos. El único recurso externo es el contador de visitas que se describe a continuación.</p>
<p><strong>Estadísticas de visitas.</strong> Para saber cuántas personas usan la web y qué páginas consultan, usamos <a href="https://www.goatcounter.com" {EXT}>GoatCounter</a>, una herramienta de analítica respetuosa con la privacidad: no usa cookies ni guarda nada en tu navegador, no almacena tu dirección IP ni datos personales y solo cuenta visitas de forma agregada (página visitada, web de procedencia, navegador, sistema operativo, idioma, ancho de pantalla y país aproximado). No sirve para identificarte ni para seguirte entre webs, y no se cede a terceros. <em>Base jurídica:</em> nuestro interés legítimo en conocer, de forma agregada y anónima, el uso de la web para mejorarla (art. 6.1.f RGPD). Si tu navegador bloquea el contador, la web funciona igual.</p>
<p><strong>Newsletter.</strong> El botón «Suscribirme» solo abre, en una pestaña nueva, la página de suscripción de Beehiiv ({SUBH}). Esta web no recoge ni transmite tu correo: lo escribes directamente en la página de Beehiiv. Al visitar esa página, Beehiiv y sus proveedores pueden usar cookies y tecnologías similares (por ejemplo, de medición, de protección antibots o de su red de distribución) bajo su propia política. Si te suscribes, tratamos tu dirección de correo (y los datos técnicos de entrega, apertura y clics que genera la plataforma) solo para enviarte la newsletter sobre cambios en el registro MiCA. <em>Base jurídica:</em> tu consentimiento (art. 6.1.a RGPD y art. 21 LSSI-CE), que puedes retirar en cualquier momento con el enlace de baja de cada correo o escribiendo a {PH(EM)}. No usamos tu correo para nada más ni lo cedemos.</p></section>
<section class="card"><h2>3. Cookies y almacenamiento local</h2><p>Esta web no instala cookies ni publicidad. Las estadísticas de visitas se cuentan con GoatCounter sin cookies ni almacenamiento en tu navegador. Si eliges manualmente el tema claro u oscuro, tu navegador guarda esa preferencia en su almacenamiento local (<code>localStorage</code>, clave «theme»): es un ajuste que tú solicitas, no se envía a ningún servidor y puedes borrarlo desde tu navegador. Las cookies que pueda usar la página de Beehiiv solo se instalan si decides abrirla, y las gestiona Beehiiv. Si algún día se añadiera algo que requiera consentimiento, se pediría antes.</p></section>
<section class="card"><h2>4. Proveedores (encargados del tratamiento)</h2>
<p><strong>Beehiiv, Inc.</strong> (EE. UU.): plataforma de envío de la newsletter. Actúa como encargado del tratamiento; las transferencias internacionales se amparan en las garantías que ofrezca el proveedor (Marco de Privacidad de Datos UE-EE. UU. si está adherido, o cláusulas contractuales tipo). <a href="https://www.beehiiv.com/privacy" {EXT}>Política de privacidad de Beehiiv</a>.</p>
<p><strong>GoatCounter</strong> (goatcounter.com, operado por Martin Tournoij, Irlanda; servidores de Hetzner en Finlandia y Alemania): estadísticas agregadas de visitas, sin cookies ni almacenamiento de direcciones IP. <a href="https://www.goatcounter.com/help/privacy" {EXT}>Política de privacidad de GoatCounter</a>.</p>
<p><strong>GitHub, Inc.</strong> (EE. UU.): alojamiento de la web (GitHub Pages). Al visitarla, GitHub puede registrar tu dirección IP con fines técnicos y de seguridad. <a href="https://docs.github.com/es/site-policy/privacy-policies/github-general-privacy-statement" {EXT}>Declaración de privacidad de GitHub</a>.</p></section>
<section class="card"><h2>5. Conservación</h2><p>Conservamos tu correo mientras sigas suscrito. Al darte de baja se elimina, salvo el tiempo imprescindible para atender obligaciones legales.</p></section>
<section class="card"><h2>6. Tus derechos</h2><p>Puedes ejercer los derechos de acceso, rectificación, supresión, oposición, limitación y portabilidad escribiendo a {PH(EM)}. Si consideras que no se han atendido correctamente, puedes reclamar ante la <a href="https://www.aepd.es" {EXT}>Agencia Española de Protección de Datos</a>.</p></section>
<section class="card"><h2>7. Menores</h2><p>La newsletter no está dirigida a menores de 14 años.</p></section>
<p class="muted">Texto orientativo; no sustituye a un asesoramiento jurídico.</p></div>"""
(S/"privacidad.html").write_text(page("Política de privacidad · Registro MiCA", "Privacidad de Registro MiCA: sin cookies; visitas contadas de forma agregada con GoatCounter; la newsletter se gestiona en Beehiiv solo si decides abrirla.", priv, 0, "privacidad.html"))
# ---- brand pages
CATN = {"exchange":"Exchange","bróker":"Bróker","banco/neobanco/pagos":"Banco, neobanco o pagos","wallet":"Monedero","compra/rampa/app":"App de compra","institucional/custodia":"Institucional / custodia"}
def faq(qas, dm=None): return {"@context":"https://schema.org","@type":"FAQPage","inLanguage":"es","dateModified":dm or M["date"],"mainEntity":[{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a in qas]}
def related(b, n=8):
    pool = [x for x in B if x is not b and x["cat"] == b["cat"]] + [x for x in B if x is not b and x["cat"] != b["cat"]]
    return '<div class="grid">' + "".join(bcard(x, "../") for x in pool[:n]) + '</div>'
# ---- fichas editoriales (data/editorial.json): solo hechos con fuente primaria; estado, fecha y supervisor salen de ESMA
try: ED = json.load(open(R/"data/editorial.json"))
except Exception: ED = {"brands": {}}
try: CNMV_TXT = (R/"data/sources/cnmv.txt").read_text(encoding="utf-8", errors="ignore").upper()
except Exception: CNMV_TXT = ""
CNMV_PDF = "https://www.cnmv.es/Docportal/Proveedores-Servicios-Criptoactivos/Listado_ProveedoresCriptoactivos.pdf"
CNMV_WARN = "https://www.cnmv.es/portal/advertencias?lang=es"
EDK = {"datos": "datos del", "doc": "documento del", "consulta": "consultado el"}
def editorial(b, ents):
    x = (ED.get("brands") or {}).get(b["b"])
    if not x: return "", None
    rev = ED.get("reviewed") or M["date"]
    src = {"esma": {"t": "ESMA: registro provisional MiCA (CASPS.csv)", "u": ESMA_URL, "d": M["date"], "k": "datos"},
           "cnmv": {"t": "CNMV: relación de proveedores de servicios de criptoactivos (PDF)", "u": CNMV_PDF, "d": ED.get("cnmvListDate") or CHECKED, "k": "doc"},
           **(x.get("sources") or {})}
    order = []
    def cite(ids):
        out = []
        for i in ids:
            if i not in src: raise SystemExit(f"editorial.json: fuente desconocida {i} en {b['b']}")
            if i not in order: order.append(i)
            n = order.index(i) + 1; out.append(f'<a href="#f-{b["slug"]}-{n}" aria-label="Fuente {n}">{n}</a>')
        return f'<sup class="cite">{",".join(out)}</sup>' if out else ""
    e0 = next((e for e in ents if e["es"]), None) or next((e for e in ents if e.get("active", True)), None) or (ents[0] if ents else None)
    if e0:
        f_ent = f'<b>{esc(e0["l"])}</b>{cite(["esma"])}<small>LEI <code>{esc(e0["lei"] or "—")}</code></small>'
        f_sup = f'{esc(e0["a"])}{cite(["esma"])}<small>{esc(C.get(e0["h"], e0["h"]))}</small>'
        c, t, a = kind(e0)
        base = {"Article 63": "base legal ESMA: Art. 63", "Article 60": "base legal ESMA: Art. 60"}.get(e0.get("lb"), "ESMA no publica la base legal · " + CONF.get(e0["conf"], e0["conf"]).lower())
        f_st = f'{esb(e0)}{cite(["esma"])}<small>{esc(t)} ({esc(a)}) · en el registro desde {esc(fmt(e0["d"])) if e0.get("d") else "—"} · {esc(base)}</small>'
    else:
        f_ent = f'<b>Ninguna en el registro</b>{cite(["esma"])}<small>Ninguna sociedad de la marca figura en el registro MiCA</small>'
        f_sup = f'—<small>Sin sociedad en el registro</small>'
        f_st = f'<span class="pill no">{ICON["x"]}No figura en el registro MiCA</span>{cite(["esma"])}<small>Registro de ESMA a {esc(fmt(M["date"]))}</small>'
    cn = x.get("cnmv")
    if cn and cn.get("key", "").upper() not in CNMV_TXT:
        print(f"aviso editorial: {b['b']} ya no aparece en el listado CNMV descargado ({cn.get('key')}); se muestra como «no figura»"); cn = None
        src["cnmv"]["d"] = CHECKED; src["cnmv"]["k"] = "consulta"
    if cn: f_cn = f'<span class="pill ok">{ICON["check"]}Figura</span>{cite(["cnmv"])}<small>Como «{esc(cn["name"])}» · {esc(cn["type"])} · puede prestar servicios desde el {esc(fmt(cn["from"]))}</small>'
    else: f_cn = f'<span class="pill no">{ICON["x"]}No figura</span>{cite(["cnmv"])}<small>Relación de proveedores de la CNMV del {esc(fmt(src["cnmv"]["d"]))}</small>'
    con = x.get("contract") or {}
    note = x.get("note")
    checks = "".join(f"<li>{esc(t)}{cite(x.get('checkSrc') or []) if i == 0 else ''}</li>" for i, t in enumerate(x.get("check") or []))
    checks += f'<li>Si una web o un intermediario te ofrece la marca con otro nombre, búscalo en las <a href="{CNMV_WARN}" {EXT}>advertencias de la CNMV sobre entidades no autorizadas</a> («chiringuitos»).</li>'
    srcs = "".join(f'<li id="f-{b["slug"]}-{n}"><a href="{esc(src[i]["u"])}" {EXT}>{esc(src[i]["t"])}</a> <span class="muted">· {EDK.get(src[i].get("k"), "consultado el")} {esc(fmt(src[i]["d"]))}</span></li>' for n, i in enumerate(order, 1))
    h = f"""<section class="ed card" aria-labelledby="ed-{b["slug"]}"><div class="ed-h"><span class="ed-ic">{ICON["shield"]}</span><div><p class="kick">Ficha editorial · revisada el <time datetime="{esc(rev)}">{esc(fmt(rev))}</time></p><h2 id="ed-{b["slug"]}">{esc(b["b"])} en España: quién presta el servicio</h2></div></div>
<dl class="ed-g"><div><dt>Sociedad para la UE y España</dt><dd>{f_ent}</dd></div><div><dt>Supervisor de origen</dt><dd>{f_sup}</dd></div><div><dt>Estado MiCA</dt><dd>{f_st}</dd></div><div><dt>Listado de la CNMV</dt><dd>{f_cn}</dd></div></dl>
{f'<p class="ed-p">{esc(con["t"])}{cite(con.get("src") or [])}</p>' if con.get("t") else ""}{f'<p class="ed-note">{esc(note["t"])}{cite(note.get("src") or [])}</p>' if note else ""}
<div class="ed-chk"><h3>{ICON["search"]}Qué comprobar si usas {esc(b["b"])} desde España</h3><ul>{checks}</ul><p class="ed-cta"><a class="btn btn-ghost" href="{CNMV_WARN}" {EXT}>Advertencias de la CNMV (chiringuitos){ICON["ext"]}</a> <a class="btn btn-ghost" href="{CNMV_PDF}" {EXT}>Listado de proveedores de la CNMV{ICON["ext"]}</a></p></div>
<details class="ed-src" open><summary>Fuentes <span class="n">{len(order)}</span></summary><ol>{srcs}</ol></details>
<p class="ed-disc">Información objetiva sobre el registro, no asesoramiento de inversión ni recomendación de ninguna plataforma. Si un dato no se ha podido comprobar en una fuente oficial o en la propia empresa, no aparece.</p></section>"""
    return h, {"rev": rev, "contract": con.get("t")}
LASTMOD = {}
for b in B:
    nm = esc(b["b"]); ents = [bySlug[x] for x in b["e"]]; dt = fmt(M["date"]); bn = b["b"]; st = b["st"]
    act = [x for x in ents if x.get("active", True)]
    if st == "ok":
        e0 = next(x for x in ents if x["es"]); ver = ("v-ok", f"Sí. {nm} puede prestar servicios cripto en España")
        vtxt = f'Opera a través de <b>{esc(e0["l"])}</b> ({esc(C.get(e0["h"], e0["h"]))}), que figura en el registro MiCA de ESMA con autorización vigente y {"España como país de origen" if e0["h"] == "ES" else "España entre sus países de servicio"}.'
        a1 = f'Sí. Según el registro MiCA de ESMA a {dt}, {bn} opera en la UE a través de {e0["l"]} ({C.get(e0["h"], e0["h"])}), con autorización vigente y acceso a España. Tipo: {kind(e0)[1]} ({kind(e0)[2]}).'
        desc = f'Sí: {bn} figura en el registro MiCA de ESMA ({e0["l"]}, {C.get(e0["h"], e0["h"])}) y puede operar en España. {kind(e0)[1]} ({kind(e0)[2]}). Datos a {dt}.'
    elif st == "ret":
        e0 = max(ents, key=lambda x: x["end"] or ""); ver = ("v-no", f"No. La autorización MiCA de {nm} fue retirada")
        cm = f' Comentario de ESMA: «{esc(e0["cm"])}».' if e0.get("cm") else ""
        vtxt = f'Su sociedad <b>{esc(e0["l"])}</b> ({esc(C.get(e0["h"], e0["h"]))}) tuvo autorización MiCA, pero el registro de ESMA indica que terminó el <b>{esc(fmt(e0["end"]))}</b>.{cm} Ya no puede prestar servicios cripto con esa autorización, tampoco en España.'
        a1 = f'No. La autorización MiCA de {e0["l"]} terminó el {fmt(e0["end"])} según el registro de ESMA a {dt}: ya no puede prestar servicios cripto con ella en España.'
        desc = f'No: la autorización MiCA de {bn} ({e0["l"]}) fue retirada el {fmt(e0["end"])} según ESMA. Ya no puede operar en España. Datos a {dt}.'
    elif st == "pend":
        e0 = min((x for x in ents if x.get("pending")), key=lambda x: x["d"]); ver = ("v-neu", f"{nm} está autorizado, pero aún no puede operar: empieza el {esc(fmt(e0['d']))}")
        vtxt = f'Su sociedad <b>{esc(e0["l"])}</b> ({esc(C.get(e0["h"], e0["h"]))}) figura en el registro MiCA de ESMA con una autorización que empieza a aplicarse el <b>{esc(fmt(e0["d"]))}</b>. Hasta entonces no cuenta como proveedor activo.'
        a1 = f'Todavía no. {e0["l"]} figura en el registro MiCA de ESMA a {dt} con una autorización que empieza el {fmt(e0["d"])}; hasta esa fecha no puede prestar servicios cripto con ella.'
        desc = f'{bn} ({e0["l"]}) está autorizado en el registro MiCA de ESMA, pero su autorización empieza el {fmt(e0["d"])}. Datos a {dt}.'
    elif st == "sin":
        e0 = act[0] if act else ents[0]; ver = ("v-no", f"{nm} tiene autorización MiCA, pero no consta para España")
        vtxt = f'Su sociedad <b>{esc(e0["l"])}</b> ({esc(C.get(e0["h"], e0["h"]))}) figura en el registro MiCA, pero España no aparece entre sus países notificados.'
        a1 = f'No consta. {e0["l"]} figura en el registro MiCA de ESMA a {dt}, pero España no está entre sus países notificados, por lo que no consta que pueda prestar servicios a residentes en España.'
        desc = f'{bn} tiene autorización MiCA ({e0["l"]}), pero España no figura entre sus países notificados en el registro de ESMA a {dt}.'
    elif st == "auto":
        ver = ("v-neu", f"No aplica: {nm} es un monedero de autocustodia")
        vtxt = f'No hemos encontrado ninguna sociedad de {nm} en el registro MiCA de ESMA a {esc(dt)}. Un monedero de autocustodia, en el que solo tú controlas las claves, no presta un servicio cripto de MiCA y no necesita esa licencia. Si compras, vendes o canjeas dentro de la app, ese servicio lo presta un tercero que sí debe figurar en el registro con España.'
        a1 = f'{bn} es un monedero de autocustodia y no figura en el registro MiCA de ESMA a {dt}. El software de autocustodia, en el que solo tú controlas las claves, no es un servicio cripto de MiCA; las compras o canjes dentro de la app las presta un tercero que sí debe estar autorizado.'
        desc = f'{bn} es un monedero de autocustodia: no figura en el registro MiCA de ESMA ({dt}) y no necesita licencia CASP. Qué comprobar si compras dentro de la app.'
    elif st == "nocr":
        ver = ("v-neu", f"{nm} no tiene servicios cripto MiCA en el registro")
        vtxt = f'No hemos encontrado ninguna sociedad de {nm} en el registro MiCA de ESMA a {esc(dt)}: no ha notificado servicios cripto bajo MiCA. Si te ofrece comprar o custodiar criptoactivos, ese servicio no está autorizado bajo MiCA.'
        a1 = f'{bn} no figura en el registro MiCA de ESMA a {dt}: no ha notificado servicios de criptoactivos bajo MiCA. Si te ofrece cripto, ese servicio no está autorizado bajo MiCA.'
        desc = f'{bn} no figura en el registro MiCA de ESMA a {dt}: sin servicios cripto MiCA notificados. Qué significa para usuarios en España.'
    else:
        ver = ("v-no", f"No. {nm} no figura en el registro MiCA")
        vtxt = f'No hemos encontrado ninguna sociedad de {nm} en el registro de proveedores autorizados de ESMA a {esc(dt)}.'
        a1 = f'No consta. A {dt}, {bn} no figura en el registro de proveedores de servicios de criptoactivos autorizados de ESMA, por lo que no consta que pueda prestar servicios cripto en España bajo MiCA.'
        desc = f'No: {bn} no figura en el registro MiCA de ESMA a {dt}. Qué significa para usuarios en España y cómo comprobarlo.'
    warn = "".join(f'<p class="pill no">En la lista de entidades no conformes de ESMA: {esc(w["l"])} ({esc(w["a"])})</p>' for w in b["warn"])
    qas = [(f"¿Está {bn} autorizado en España?", a1),
           ("¿Qué es la licencia MiCA?", "MiCA es el Reglamento (UE) 2023/1114. Desde el fin del periodo transitorio en España (1 de julio de 2026), para prestar servicios de criptoactivos a residentes en España hay que figurar en el registro MiCA con autorización vigente y España notificada, ya sea con autorización CASP (art. 59) o mediante notificación de una entidad financiera ya supervisada (art. 60).")]
    if ents:
        e0q = next((x for x in ents if x["es"]), ents[0])
        qas.append((f"¿Qué sociedad presta el servicio de {bn}?", f'{e0q["l"]}, con sede en {C.get(e0q["h"], e0q["h"])} y supervisada por {e0q["a"]}.' + (f' Tiene España entre {len(e0q["cs"])} países notificados.' if e0q["es"] else "")))
    qas.append((f"¿Cómo compruebo si {bn} está autorizado?", f"Busca el nombre jurídico de la sociedad que te presta el servicio (aparece en los términos legales de la app) en el registro MiCA de ESMA y en el listado de la CNMV, y comprueba que la autorización siga vigente y que España figure entre sus países. Este buscador lo hace por ti con datos a {dt}."))
    if st == "ok":
        qas.insert(1, (f"¿Es legal {bn} en España?", f'Sí. {bn} puede prestar servicios de criptoactivos en España: su sociedad {e0["l"]} figura en el registro MiCA de ESMA a {dt} con autorización vigente y {"España como país de origen" if e0["h"] == "ES" else "España entre sus países notificados"}.'))
    if ents:
        e0c = next((x for x in ents if x["es"]), ents[0]); hc = C.get(e0c["h"], e0c["h"])
        if not e0c.get("active", True) or e0c.get("pending"): pass
        elif e0c["h"] == "ES": qas.append((f"¿Está {bn} registrado en la CNMV?", f'Sí. {e0c["l"]} tiene su sede en España y figura en el registro MiCA de ESMA a {dt} con supervisor: {e0c["a"]}.'))
        elif e0c["es"]: qas.append((f"¿Necesita {bn} una licencia de la CNMV?", f'No una aparte. {e0c["l"]} está autorizada en {hc} ({e0c["a"]}) y España figura entre sus países notificados: una autorización MiCA vale en toda la UE y se extiende a otros países mediante notificación (pasaporte europeo). La CNMV publica en su web un listado de proveedores que incluye también a los que operan en España desde otro país.'))
        else: qas.append((f"¿Está {bn} registrado en la CNMV?", f'No consta para España. {e0c["l"]} está autorizada en {hc} ({e0c["a"]}), pero España no figura entre sus países notificados en el registro de ESMA a {dt}.'))
    elif st == "nofig":
        qas.append((f"¿Está {bn} registrado en la CNMV?", f"No consta. A {dt}, ninguna sociedad de {bn} figura en el registro MiCA de ESMA, que recoge a todos los proveedores autorizados en la UE, también a los autorizados por la CNMV."))
    if st in ("sin", "ret", "nofig"): qas.insert(1, (f"¿Es legal {bn} en España?", f"No consta que {bn} pueda prestar servicios cripto en España: a {dt} no figura con autorización MiCA vigente para España en el registro de ESMA. Para el usuario no es ilegal usarlo, porque la obligación de estar autorizado es del proveedor, pero un proveedor sin autorización para España no ofrece las protecciones de MiCA y puede tener que dejar de prestar servicio."))
    elif st == "nocr": qas.append((f"¿Es ilegal usar {bn} desde España?", "Para el usuario no: la obligación de estar autorizado es del proveedor. Pero un proveedor sin autorización para España no ofrece las protecciones de MiCA y puede tener que dejar de prestar servicio."))
    edh, edm = editorial(b, ents)
    if edm and edm["contract"] and ents: qas.insert(2, (f"¿Con qué sociedad contrato si uso {bn} en España?", edm["contract"]))
    faqh = "".join(f'<details class="faq"{" open" if i==0 else ""}><summary>{esc(q)}</summary><p>{esc(a)}</p></details>' for i,(q,a) in enumerate(qas))
    bc = bcolor(b)
    pills = bstatus(b, True)
    if ents:
        e0k = next((x for x in ents if x["es"]), ents[0]); pills += kb(e0k)
    entl = "".join(f'<a class="rc" href="../p/{x["slug"]}.html"><span class="rc-v {"ok" if x["es"] else "no"}" aria-hidden="true"></span>{elogo(x, "md", "../")}<div class="b"><h3>{esc(x["l"])}</h3><div class="sub">{esc(C.get(x["h"], x["h"]))} · {esc(x["a"])}</div><div class="pills">{esb(x)}{kb(x)}</div></div><span class="go" aria-hidden="true">→</span></a>' for x in ents)
    body = f"""<div class="wrap narrow"><nav class="crumbs" aria-label="Migas"><a href="../index.html">Inicio</a><span>/</span><a href="../marcas.html">Marcas</a><span>/</span><span>{nm}</span></nav>
<section class="phead card"{f' style="--brand:{bc}"' if bc else ""}>{blogo(b, "lg", "../", True)}<div><p class="eyebrow">{esc(CATN.get(b["cat"], b["cat"]))} · registro ESMA a {esc(dt)}{f' · revisado el <time datetime="{esc(edm["rev"])}">{esc(fmt(edm["rev"]))}</time>' if edm else ""}</p><h1>¿Está {nm} autorizado en España?</h1>
<div class="pills">{pills}</div></div></section>
{verdict(ver[0], ver[1], vtxt, (('<p class="muted" style="margin-top:.5em">'+esc(b["note"])+'</p>') if b["note"] else "") + warn)}
{edh}
{('<section class="card"><h2>Sociedades en el registro <span class="n">'+str(len(ents))+'</span></h2><div class="ent-list">' + entl + '</div></section>') if ents else ''}
<section class="card"><h2>Preguntas frecuentes</h2>{faqh}<p class="muted" style="margin-top:14px">Más contexto en la <a href="../guia-mica.html">guía MiCA para España</a> y en la <a href="../proveedores.html">lista completa de proveedores</a>.</p></section>
<section class="card"><h2>Fuente del mapeo</h2><p>{esc(b["src"])}. Registro de ESMA a {esc(dt)}, comprobado el {esc(fmt(CHECKED))}.</p><p class="muted">Confirma siempre en <a href="{ESMA_URL}" {EXT}>ESMA</a> y en la <a href="{CNMV_URL}" {EXT}>CNMV</a>.</p></section>
<section class="sec"><div class="sec-h"><h2>Comprueba otras marcas</h2><a href="../marcas.html">Ver todas →</a></div>{related(b)}</section>
{newsletter("../")}</div>"""
    title = fit([f"¿Está {bn} autorizado en España? MiCA y CNMV", f"¿Está {bn} autorizado en España? Licencia MiCA", f"¿Está {bn} autorizado en España? MiCA", f"{bn}: ¿autorizado en España? MiCA", f"{bn} · MiCA España"])
    LASTMOD[f'marca/{b["slug"]}.html'] = max([x.get("lu") or "" for x in ents] + [edm["rev"] if edm else ""]) or M["date"]
    (S/"marca"/f'{b["slug"]}.html').write_text(page(title, clip(desc), body, 1, f'marca/{b["slug"]}.html', [faq(qas, max(M["date"], edm["rev"]) if edm else None), crumbs([("Inicio",""),("Marcas","marcas.html"),(bn,f'marca/{b["slug"]}.html')])], "article", cur="marcas"))
# ---- marcas index
groups = {}
for b in B: groups.setdefault(b["cat"], []).append(b)
nok = sum(b["st"] == "ok" for b in B); nneu = sum(b["st"] in ("auto", "nocr") for b in B)
tools = f'''<div class="tools" role="search"><label class="flt"><span class="sr">Filtrar marcas</span>{ICON["search"]}<input id="mf" type="search" maxlength="60" placeholder="Filtrar {len(B)} marcas…" autocomplete="off"></label>
<div class="seg" role="group" aria-label="Filtrar por estado"><button type="button" data-f="all" aria-pressed="true">Todas</button><button type="button" data-f="ok" aria-pressed="false">Pueden operar ({nok})</button><button type="button" data-f="no" aria-pressed="false">Sin permiso ({len(B) - nok - nneu})</button><button type="button" data-f="neu" aria-pressed="false">No aplica ({nneu})</button></div><span class="cnt" id="mc" aria-live="polite"></span></div>'''
mi = f"""<div class="wrap"><header class="ph"><p class="eyebrow">{len(B)} marcas · registro ESMA a {esc(fmt(M["date"]))}</p><h1>¿Qué plataformas cripto están autorizadas en España?</h1><p class="lede">Exchanges, brókers, neobancos, apps y monederos populares en España, con su estado en el registro MiCA.</p></header>{tools}
""" + "".join(f'<section class="sec" style="margin:34px 0"><div class="sec-h"><h2>{esc(CATN.get(k, k))} <span class="muted" style="font-weight:600;font-size:.7em">{len(v)}</span></h2></div><div class="grid">' + "".join(bcard(x) for x in sorted(v, key=lambda x: x["b"].lower())) + '</div></section>' for k, v in groups.items()) + newsletter() + "</div>"
(S/"marcas.html").write_text(page("Exchanges cripto autorizados en España: lista MiCA", clip(f"Estado en el registro MiCA de {len(B)} exchanges, brókers, neobancos y apps cripto populares en España: quién puede operar y quién no. Datos ESMA a {fmt(M['date'])}."), mi, 0, "marcas.html", [crumbs([("Inicio",""),("Marcas","marcas.html")])], cur="marcas"))
# ---- lista completa de proveedores (enlaces rastreables a todas las fichas activas y retiradas)
def pli(e):
    c, t, a = kind(e)
    return f'<li>{elogo(e, "xs")}<span><a href="p/{e["slug"]}.html">{esc(e["n"])}</a>{f" <small class=\"muted\">{esc(e["l"])}</small>" if e["l"] != e["n"] else ""}</span> <span class="pill {c} sm">{esc(a)}</span></li>'
def bycountry(L):
    g = {}
    for e in sorted(L, key=lambda x: x["n"].lower()): g.setdefault(C.get(e["h"], e["h"]), []).append(e)
    return sorted(g.items(), key=lambda kv: (-len(kv[1]), kv[0]))
ACT = [e for e in E if e.get("active", True) and not e.get("pending")]
PEND = sorted([e for e in E if e.get("pending")], key=lambda x: (x["d"], x["n"].lower()))
P_ES = [e for e in ACT if e["es"] and e["h"] == "ES"]; P_PASS = [e for e in ACT if e["es"] and e["h"] != "ES"]; P_NO = [e for e in ACT if not e["es"]]
def pgroup(L, hid):
    return "".join(f'<h3 id="{hid}-{slugify(k)}">{esc(k)} <span class="muted" style="font-weight:600">{len(v)}</span></h3><ul class="ent">{"".join(pli(x) for x in v)}</ul>' for k, v in bycountry(L))
pv = f"""<div class="wrap narrow"><nav class="crumbs" aria-label="Migas"><a href="index.html">Inicio</a><span>/</span><span>Proveedores</span></nav><header class="ph"><p class="eyebrow">Registro ESMA a {esc(fmt(M["date"]))} · {M["count"]} proveedores activos</p><h1>Lista de proveedores cripto autorizados en España</h1>
<p class="lede">Los {M["es"]} proveedores de servicios de criptoactivos (CASP) que, según el registro MiCA de ESMA, pueden operar en España: {len(P_ES)} con sede en España y {len(P_PASS)} autorizados en otro país de la UE/EEE con España notificada.</p>
<p class="muted">Busca por el nombre de la sociedad, que es el que aparece en los términos legales de cada app. Si buscas por marca (Coinbase, Bit2Me, Revolut…), usa la <a href="marcas.html">lista de marcas</a>. Qué significa cada etiqueta: <a href="guia-mica.html">guía MiCA</a>.</p>
<p class="pills"><a class="pill ok" href="#sede-espana">{ICON["check"]}Sede en España · {len(P_ES)}</a> <a class="pill ok" href="#pasaporte">{ICON["check"]}Con pasaporte a España · {len(P_PASS)}</a> <a class="pill no" href="#sin-espana">{ICON["minus"]}Sin España · {len(P_NO)}</a>{f' <a class="pill pend" href="#empiezan">{ICON["clock"]}Empiezan más adelante · {len(PEND)}</a>' if PEND else ""}{f' <a class="pill no" href="#retiradas">{ICON["x"]}Retiradas · {len(RET)}</a>' if RET else ""}</p></header>
<section class="card" id="sede-espana"><h2>Con sede en España <span class="n">{len(P_ES)}</span></h2><p class="muted">Autorizados o notificados ante la CNMV, su supervisor según el registro de ESMA.</p><ul class="ent">{"".join(pli(x) for x in sorted(P_ES, key=lambda x: x["n"].lower()))}</ul></section>
<section class="card" id="pasaporte"><h2>Autorizados en otro país, con España notificada <span class="n">{len(P_PASS)}</span></h2><p class="muted">Una autorización MiCA vale en toda la UE/EEE; para operar en España el proveedor debe incluirla entre sus países notificados (pasaporte europeo). Agrupados por país de origen.</p>{pgroup(P_PASS, "pas")}</section>
<section class="card" id="sin-espana"><h2>En el registro MiCA, pero sin España <span class="n">{len(P_NO)}</span></h2><p class="muted">Tienen autorización MiCA vigente, pero España no figura entre sus países: no consta que puedan prestar servicios a residentes en España.</p>{pgroup(P_NO, "sin")}</section>
{f'<section class="card" id="empiezan"><h2>Autorizados que empiezan más adelante <span class="n">{len(PEND)}</span></h2><p class="muted">Figuran en el registro de ESMA con una fecha de inicio futura: hasta ese día no cuentan como activos ni pueden operar.</p><ul class="ent">{"".join(pli(x).replace("</li>", f' <span class="pill pend sm">{ICON["clock"]}empieza el {esc(fmt(x["d"]))}</span></li>') for x in PEND)}</ul></section>' if PEND else ""}
{f'<section class="card" id="retiradas"><h2>Autorizaciones retiradas <span class="n">{len(RET)}</span></h2><ul class="ent">{"".join(pli(x) for x in sorted(RET, key=lambda x: x["n"].lower()))}</ul></section>' if RET else ""}
<p class="muted">Fuente: registro provisional MiCA de <a href="{ESMA_URL}" {EXT}>ESMA</a> (CASPS.csv), actualizado el {esc(fmt(M["date"]))}. La base legal (Art. 59 o 60) es el dato oficial de ESMA cuando lo publica; si no, una inferencia explicada en la <a href="metodologia.html">metodología</a>. Confirma siempre en ESMA y en la <a href="{CNMV_URL}" {EXT}>CNMV</a>.</p>
{newsletter()}</div>"""
(S/"proveedores.html").write_text(page("Proveedores cripto autorizados en España: lista MiCA (CASP)", clip(f"Lista de los {M['es']} proveedores de criptoactivos (CASP) que pueden operar en España según el registro MiCA de ESMA: {len(P_ES)} con sede en España y {len(P_PASS)} con pasaporte. Datos a {fmt(M['date'])}."),
    pv, 0, "proveedores.html", [crumbs([("Inicio",""),("Proveedores","proveedores.html")])], cur="proveedores"))
# ---- guía MiCA (solo hechos verificados en fuentes oficiales citadas; revisada el GUIDE_REV)
GUIDE_REV = "2026-10-17"
CNMV_MICA = "https://www.cnmv.es/portal/mica/regulacion-criptoactivos?lang=es"
CNMV_FAQ = "https://www.cnmv.es/docportal/Legislacion/FAQ/FAQ_MICA.pdf"
MICA_TXT = "https://eur-lex.europa.eu/eli/reg/2023/1114/oj?locale=es"
GQ = [("¿Qué es MiCA?", "MiCA es el Reglamento (UE) 2023/1114, de 31 de mayo de 2023, relativo a los mercados de criptoactivos. Regula, entre otras cosas, a los proveedores de servicios de criptoactivos (CASP): custodia, plataformas de negociación, canje, ejecución de órdenes, asesoramiento, gestión de carteras o transferencias."),
      ("¿Qué diferencia hay entre el artículo 59 y el artículo 60 de MiCA?", "El artículo 59 exige estar autorizado como proveedor de servicios de criptoactivos (la «licencia» CASP). El artículo 60 permite a entidades financieras ya supervisadas, como bancos, empresas de servicios de inversión, entidades de dinero electrónico o gestoras, prestar servicios cripto notificándolo a su supervisor, sin una autorización CASP aparte. En el registro de ESMA las autorizaciones CASP aparecen con la base legal «Article 63», el artículo que regula su concesión."),
      ("¿Cuándo terminó el periodo transitorio de MiCA en España?", "El artículo 143.3 de MiCA permitía a cada Estado un periodo transitorio de hasta 18 meses. Según la CNMV, en España terminó el 1 de julio de 2026: desde entonces solo pueden operar en España proveedores autorizados por la CNMV o por otra autoridad competente de la UE."),
      ("¿Quién pudo acogerse al periodo transitorio en España?", "Según la CNMV, quienes ya prestaban servicios con criptoactivos conforme a la normativa española antes de la aplicación de MiCA, en particular los inscritos en el registro del Banco de España a 30 de diciembre de 2024, que pudieron seguir prestando los mismos servicios hasta el 1 de julio de 2026 o hasta que se les denegara la autorización, si era antes."),
      ("¿Puede operar en España un exchange autorizado en otro país de la UE?", "Sí, si España figura entre sus países notificados. Una autorización MiCA es válida en toda la UE y el proveedor la extiende a otros países mediante notificación a su supervisor (pasaporte europeo). Por eso en este buscador «Puede operar en España» exige autorización vigente y España como país de origen o notificado."),
      ("¿Qué pasa si mi plataforma no está autorizada?", "La CNMV indicó que los proveedores sin autorización deben tener un plan de migración que permita a los clientes mover sus criptoactivos a otras direcciones y sus fondos a cuentas de efectivo, o aceptar un traspaso a otro proveedor que sí esté autorizado. Los clientes de una entidad no autorizada no cuentan con las protecciones de MiCA."),
      ("¿Cómo compruebo si un exchange está autorizado en España?", "Mira en los términos legales de la app qué sociedad te presta el servicio y búscala en el registro MiCA de ESMA: debe tener autorización vigente y España como país de origen o entre sus países notificados. La CNMV publica también un listado de proveedores. Este buscador reproduce el registro de ESMA con fecha y lo actualiza cada semana.")]
gl = [("CASP", "Proveedor de servicios de criptoactivos (crypto-asset service provider): la entidad que te presta el servicio, no la marca de la app."),
      ("Art. 59 · licencia CASP", "Autorización como proveedor de servicios de criptoactivos concedida por un supervisor de la UE/EEE. En el registro de ESMA aparece como «Article 63»."),
      ("Art. 60 · notificación", "Vía para entidades financieras ya supervisadas (bancos, empresas de inversión, entidades de dinero electrónico, gestoras…) que añaden servicios cripto notificándolo a su supervisor."),
      ("Pasaporte europeo", "Extensión de una autorización MiCA a otros países de la UE/EEE mediante notificación. Para operar en España, España debe figurar entre los países notificados."),
      ("Periodo transitorio", "Plazo en que quienes ya operaban con la normativa nacional podían seguir sin autorización MiCA. En España terminó el 1 de julio de 2026."),
      ("Registro de ESMA", "Registro provisional MiCA que publica la Autoridad Europea de Valores y Mercados (archivo CASPS.csv), con todos los proveedores autorizados o notificados en la UE/EEE."),
      ("Entidades no conformes", "Lista de ESMA (NCASP.csv) con entidades que prestan servicios cripto sin autorización, según los supervisores nacionales."),
      ("LEI", "Código identificador de entidad jurídica (20 caracteres). Es la forma más fiable de distinguir dos sociedades con nombres parecidos.")]
gu = f"""<div class="wrap narrow"><nav class="crumbs" aria-label="Migas"><a href="index.html">Inicio</a><span>/</span><span>Guía MiCA</span></nav><header class="ph"><p class="eyebrow">Guía · revisada el {esc(fmt(GUIDE_REV))} · datos ESMA a {esc(fmt(M["date"]))}</p><h1>Guía MiCA en España: licencia CASP, notificación y fin del periodo transitorio</h1>
<p class="lede">Qué exige MiCA para ofrecer servicios cripto en España, qué significan «Art. 59» y «Art. 60» y cómo comprobar si tu exchange está autorizado.</p></header>
<section class="card"><h2>En cifras</h2><dl class="kv"><dt>Pueden operar en España</dt><dd><a href="proveedores.html">{M["es"]} proveedores</a> ({len(P_ES)} con sede en España)</dd><dt>Proveedores MiCA activos en la UE/EEE</dt><dd>{M["count"]}</dd><dt>Con licencia CASP (Art. 59)</dt><dd>{M["k"]["art59"]}</dd><dt>Por notificación (Art. 60)</dt><dd>{M["k"]["art60"]}</dd><dt>Vía no determinada</dt><dd>{M["k"]["incierto"]}</dd></dl><p class="muted">Registro de ESMA a {esc(fmt(M["date"]))}. Cómo se clasifica cada proveedor: <a href="metodologia.html">metodología</a>.</p></section>
{"".join(f'<section class="card"><h2>{esc(q)}</h2><p>{esc(a)}</p></section>' for q, a in GQ)}
<section class="card"><h2>Glosario</h2><dl class="kv">{"".join(f"<dt>{esc(k)}</dt><dd>{esc(v)}</dd>" for k, v in gl)}</dl></section>
<section class="card"><h2>Fuentes oficiales</h2><ul class="steps"><li><a href="{MICA_TXT}" {EXT}>Reglamento (UE) 2023/1114 (MiCA), texto en EUR-Lex</a></li><li><a href="{CNMV_MICA}" {EXT}>CNMV: MiCA, nueva regulación de criptoactivos</a></li><li><a href="{CNMV_FAQ}" {EXT}>CNMV: preguntas y respuestas sobre el Reglamento MiCA (PDF)</a></li><li><a href="{CNMV_URL}" {EXT}>CNMV: proveedores de servicios de criptoactivos</a></li><li><a href="{ESMA_URL}" {EXT}>ESMA: registro provisional MiCA</a></li></ul><p class="muted">Esta guía resume fuentes públicas y no es asesoramiento jurídico ni financiero.</p></section>
<section class="sec"><div class="sec-h"><h2>Comprueba las marcas más buscadas</h2><a href="marcas.html">Ver todas →</a></div><div class="grid">{"".join(bcard(b) for b in popular[:8])}</div></section>
{newsletter()}</div>"""
(S/"guia-mica.html").write_text(page("Guía MiCA en España: licencia CASP, Art. 60 y transitorio", "Qué exige MiCA para ofrecer servicios cripto en España: licencia CASP (art. 59), notificación (art. 60), pasaporte europeo y fin del periodo transitorio.",
    gu, 0, "guia-mica.html", [faq(GQ), crumbs([("Inicio",""),("Guía MiCA","guia-mica.html")])], "article"))
# ---- IndexNow: clave autoalojada (no requiere cuenta); el aviso a buscadores no se envía desde aquí
INK = CFG.get("indexNowKey") or ""
for f in S.glob("*.txt"):
    if f.name != "robots.txt" and f.name != f"{INK}.txt" and re.fullmatch(r"[0-9a-f]{32}\.txt", f.name): f.unlink()
if re.fullmatch(r"[0-9a-f]{32}", INK): (S/f"{INK}.txt").write_text(INK)
# ---- 404 (rutas absolutas: funciona a cualquier profundidad)
nf = f'''<div class="wrap narrow"><section class="nf card"><p class="nf-c" aria-hidden="true">404</p><h1>Esta página no existe</h1><p class="lede">Puede que la ficha haya cambiado de dirección o que la sociedad ya no figure en el registro. Busca la marca o la sociedad:</p>
<form class="nf-s" action="{BPATH}index.html" method="get" role="search"><label class="sr" for="q404">Buscar marca o sociedad</label><input id="q404" name="q" type="search" maxlength="60" placeholder="Coinbase, Bit2Me, Binance…" autocomplete="off"><button class="btn" type="submit">Buscar</button></form>
<p class="muted"><a href="{BPATH}index.html">Ir a la portada</a> · <a href="{BPATH}marcas.html">Ver todas las marcas</a> · <a href="{BPATH}cambios.html">Cambios recientes</a></p></section></div>'''
(S/"404.html").write_text(page("Página no encontrada · Registro MiCA", "La página que buscas no existe en Registro MiCA.", nf, 0, "404.html", up=BPATH, robots="noindex"))
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
idx = {"m": {"date": M["date"], "checked": CHECKED}, "pal": PAL,
       "e": [[e["slug"], e["n"], e["l"], e["h"], int(e["es"]), kind(e)[0], kind(e)[1], kind(e)[2], e["brands"], elg(e), est(e), fmt(e["d"]) if e.get("pending") else (fmt(e.get("end")) if e.get("end") else "")] for e in E],
       "b": [[b["b"], b["e"], b["note"], [w["l"] for w in b["warn"]], b["cat"], b["slug"], blg(b), b["st"], b.get("aliases", [])] for b in B]}
(S/"assets").mkdir(exist_ok=True); (S/"assets/data.js").write_text("window.DB=" + json.dumps(idx, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c") + ";")
for f in ["data.js", "common.js", "style.css"]: (S/f).unlink(missing_ok=True)
# ---- descargas del conjunto de datos (enlazadas desde metodología y el JSON-LD Dataset)
import csv as _csv, io as _io
DL_F = ["slug", "nombre", "sociedad", "lei", "pais_origen", "supervisor", "activo", "inicio_pendiente", "fin_autorizacion", "puede_operar_en_espana", "via", "base_legal_esma", "confianza", "paises", "servicios", "en_registro_desde", "ficha"]
def dlrow(e): return [e["slug"], e["n"], e["l"], e["lei"], e["h"], e["a"], e.get("active", True) and not e.get("pending"), bool(e.get("pending")), e.get("end") or "", e["es"], {"art59": "Art. 59", "art60": "Art. 60"}.get(e["k"], "no determinada"),
                      e.get("lb") or "", e["conf"], " ".join(e["cs"]), " ".join(e["s"]), e.get("d") or "", BASE + f'p/{e["slug"]}.html']
(S/"datos").mkdir(exist_ok=True)
DL_NOTE = "Fuente: ESMA, registro provisional MiCA (CASPS.csv), datos transformados por Registro MiCA. ESMA no respalda esta publicación. Histórico hasta 06/10/2026: CASP Tracker (CC BY 4.0). Condiciones: " + BASE + "metodologia.html#licencia"
(S/"datos/proveedores.json").write_text(json.dumps({"fuente": DL_NOTE, "registroEsma": M["date"], "comprobado": CHECKED, "campos": DL_F, "proveedores": [dict(zip(DL_F, dlrow(e))) for e in E]}, ensure_ascii=False, indent=0))
_b = _io.StringIO(); _w = _csv.writer(_b); _w.writerow(DL_F); [_w.writerow(dlrow(e)) for e in E]
(S/"datos/proveedores.csv").write_text(_b.getvalue(), encoding="utf-8")
(S/"meta.json").write_text(json.dumps({"lastSuccessfulRefresh": CHECKED, "esmaFileDate": M["date"], "source": M["source"], "active": M["count"], "startingLater": M.get("pending", 0), "withdrawn": M.get("inactive", 0),
    "canOperateInSpain": M["es"], "art59": M["k"]["art59"], "art60": M["k"]["art60"], "undetermined": M["k"]["incierto"], "built": TODAY.isoformat()}, ensure_ascii=False, indent=1))
# dominio propio: deploy/CNAME entra en el artefacto de Pages solo si coincide con la URL base (si no, se retira)
_cn = (R/"deploy/CNAME").read_text().strip() if (R/"deploy/CNAME").exists() else ""
if _cn and urllib.parse.urlsplit(BASE).hostname == _cn: (S/"CNAME").write_text(_cn + "\n")
elif (S/"CNAME").exists(): (S/"CNAME").unlink()
(S/"robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {BASE}sitemap.xml\n")
urls = [("", "1.0", "daily", M["date"]), ("marcas.html", "0.9", "weekly", M["date"]), ("cambios.html", "0.8", "weekly", M["date"]), ("proveedores.html", "0.9", "weekly", M["date"]), ("guia-mica.html", "0.7", "monthly", max(GUIDE_REV, M["date"])), ("metodologia.html", "0.4", "monthly", M["date"]), ("aviso-legal.html", "0.1", "yearly", "2026-10-17"), ("privacidad.html", "0.1", "yearly", "2026-10-17")] \
     + [(f'marca/{b["slug"]}.html', "0.8", "weekly", LASTMOD.get(f'marca/{b["slug"]}.html', M["date"])) for b in B] + [(f'p/{e["slug"]}.html', "0.6", "weekly", e.get("lu") or M["date"]) for e in E]
(S/"sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + "".join(f"<url><loc>{esc(BASE + u)}</loc><lastmod>{lm}</lastmod><changefreq>{f}</changefreq><priority>{pr}</priority></url>" for u, pr, f, lm in urls) + "</urlset>\n")
nl = sum(1 for b in B if lgfile(linfo("brands", b["b"]))); ne = sum(1 for e in E if lgfile(linfo("ents", e["slug"])))
print("site:", len(E), "fichas,", len(GONE), "bajas,", len(B), "marcas · logos:", nl, "marcas,", ne, "fichas · BASE", BASE)
