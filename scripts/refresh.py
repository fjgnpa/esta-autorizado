#!/usr/bin/env python3
"""Registro MiCA — ingesta + clasificación + generación del sitio estático.
Fuentes: ESMA CASPS.csv (oficial, primaria) -> CASP Tracker JSON (respaldo); ECB MFI list; ESMA registro MiFID/AIFM/UCITS;
CNMV listado PDF; cryptocodes.eu. Uso: python3 scripts/refresh.py [--offline] [--force] [--allow-fallback]
--force acepta cambios que los controles de cordura bloquean; --allow-fallback publica datos de CASP Tracker si ESMA falla.
Las fuentes de clasificación (BCE MFI, registro ESMA MiFID/AIFM/UCITS, CNMV) son obligatorias: si faltan o no se leen, incluso en
--offline se intenta descargarlas una vez y, si no se puede, se aborta antes de escribir nada (nunca se publica una clasificación degradada)."""
import csv, io, json, re, sys, gzip, urllib.request, urllib.parse, email.utils, datetime, pathlib, subprocess, html, shutil, hashlib
R = pathlib.Path(__file__).resolve().parent.parent
D, SRC, SNAP, SITE = R/"data", R/"data/sources", R/"data/snapshots", R/"site"
for p in (SRC, SNAP, SITE): p.mkdir(parents=True, exist_ok=True)
OFF = "--offline" in sys.argv
UA = {"User-Agent": "Mozilla/5.0 (Registro MiCA refresh)"}
def get(url, t=90):
    r = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=t); return r.read(), r.headers
ESMA_CSV = "https://www.esma.europa.eu/sites/default/files/2024-12/CASPS.csv"
ESMA_NC = "https://www.esma.europa.eu/sites/default/files/2024-12/NCASP.csv"
CT_JSON = "https://raw.githubusercontent.com/CASP-Tracker/mica-register-data/main/data/casps.json"
ECB_PAGE = "https://www.ecb.europa.eu/stats/financial_corporations/list_of_financial_institutions/html/daily_list-MID.en.html"
UPREG = "https://registers.esma.europa.eu/solr/esma_registers_upreg/select?q=entity_type:ae&fq=ae_entityTypeCode:(mif%20OR%20MIF%20OR%20aif%20OR%20AIF%20OR%20uci%20OR%20UCI)&fl=ae_lei,ae_entityTypeLabel,ae_status,ae_officeType&rows=30000&wt=json"
CNMV_PDF = "https://www.cnmv.es/Docportal/Proveedores-Servicios-Criptoactivos/Listado_ProveedoresCriptoactivos.pdf"
CC_URL = "https://www.cryptocodes.eu/news/mica-register-authorised-or-just-notified"
COUNTRIES = {"AT","BE","BG","CY","CZ","DE","DK","EE","ES","FI","FR","GR","EL","HR","HU","IE","IS","IT","LI","LT","LU","LV","MT","NL","NO","PL","PT","RO","SE","SI","SK"}
REQ_COLS = {"ae_competentAuthority","ae_homeMemberState","ae_lei_name","ae_lei","ae_commercial_name","ae_address","ae_website","ac_authorisationNotificationDate",
            "ac_authorisationEndDate","ac_serviceCode","ac_serviceCode_cou","ac_comments","ac_lastupdate","ac_legal_basis"}
ANCHORS = ["bitcoinforme s.l.", "bitpanda gmbh", "coinbase luxembourg s.a.", "payward europe solutions limited", "banco bilbao vizcaya argentaria s.a."]
FLOOR, MAXDROP, MAXGROW = 250, 0.15, 0.30
# deriva de la clasificación no oficial (inferida/verificada) frente a la última publicada: aborta si cambian > max(KDRIFT_MIN, KDRIFT·común)
KDRIFT, KDRIFT_MIN = 0.05, 10
MIN_MFI, MIN_UPREG = 1000, 1000   # entradas mínimas para dar por buena cada fuente (hoy ~4.700 LEI BCE y ~12.600 docs ESMA)
FORCE, ALLOW_FB = "--force" in sys.argv, "--allow-fallback" in sys.argv
try:
    from zoneinfo import ZoneInfo; TODAY = datetime.datetime.now(ZoneInfo("Europe/Madrid")).date()
except Exception: TODAY = datetime.date.today()
BAD = re.compile(r"[<>\x00-\x08\x0b-\x1f\x7f]")
STATS = {"dates": 0, "badDates": [], "badNames": [], "approxDates": []}
def clean(s):
    """Texto de origen: sin caracteres de control ni < >, comillas rotas (U+FFFD) reparadas, espacios normalizados."""
    s = str(s or "").replace("\xa0", " ")
    s = re.sub("\ufffd([^\ufffd]{1,60})\ufffd", "«\\1»", s).replace("\ufffd", "")
    return re.sub(r"\s+", " ", BAD.sub("", s)).strip()
MON = {m: i + 1 for i, m in enumerate(["jan","feb","mar","apr","may","jun","jul","aug","sep","oct","nov","dec"])}
def pdate(s, ref=None, field=""):
    """dd/mm/aaaa (ESMA), aaaa-mm-dd, dd.mm.aaaa; «30-Jun» (sin año) se fecha en el año de la última actualización o el anterior."""
    s = (s or "").strip()
    if not s: return None
    STATS["dates"] += 1
    for f in ("%d/%m/%Y", "%Y-%m-%d", "%d.%m.%Y", "%d-%m-%Y"):
        try:
            d = datetime.datetime.strptime(s, f).date()
            if 2000 < d.year < 2100: return d.isoformat()
        except ValueError: pass
    m = re.fullmatch(r"(\d{1,2})[-/ ]([A-Za-z]{3})[a-z]*", s)
    if m and m.group(2).lower() in MON:
        refd = datetime.date.fromisoformat(ref) if ref else TODAY
        for y in (refd.year, refd.year - 1):
            try:
                d = datetime.date(y, MON[m.group(2).lower()], int(m.group(1)))
                if d <= refd: STATS["approxDates"].append((field, s)); return None   # sin año: no se inventa; se muestra el texto original
            except ValueError: pass
    STATS["badDates"].append((field, s)); return None
def pdate_quiet(s, ref):
    n, b, a = STATS["dates"], len(STATS["badDates"]), len(STATS["approxDates"])
    r = pdate(s, ref); STATS["dates"] = n; del STATS["badDates"][b:]; del STATS["approxDates"][a:]; return r
NONSITE = {"figma.com", "docs.google.com", "drive.google.com", "linktr.ee", "canva.com", "notion.site"}
def urls(w):
    """Campo «web» del registro: puede traer varias URL, texto libre o «https.//». Solo http/https con host válido."""
    w = (w or "").replace("https.//", "https://").replace("http.//", "http://").replace("https://ttps://", "https://")
    w = re.sub(r"(?<=[a-z0-9/])(?=https?://)", " ", w, flags=re.I); w = re.sub(r"(\.[a-z]{2,4})(?=www\.)", r"\1 ", w, flags=re.I)
    out = []
    for tok in re.split(r"[|,;\s]+", w):
        tok = tok.strip().strip("()[]<>\"'")
        if not tok or "." not in tok: continue
        if not re.match(r"https?://", tok, re.I): tok = "https://" + tok
        try: u = urllib.parse.urlsplit(tok)
        except ValueError: continue
        host = (u.hostname or "").lower()
        if u.scheme.lower() not in ("http", "https") or not re.fullmatch(r"(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z]{2,}", host): continue
        url = urllib.parse.urlunsplit((u.scheme.lower(), u.netloc.lower(), u.path, u.query, ""))
        if not re.fullmatch(r"https?://[^\s\"'<>`]+", url): continue
        if any(host == d or host.endswith("." + d) for d in NONSITE): continue   # enlaces de diseño/documentos, no la web de la entidad
        if url not in out: out.append(url)
    return out
def basis(s):
    s = clean(s)
    if re.match(r"article\s*60", s, re.I): return "Article 60"
    if re.match(r"article\s*63", s, re.I): return "Article 63"
    return ""
def sanitize(e):
    """Mismo validador para ESMA y para el respaldo (CASP Tracker): solo campos conocidos, texto limpio, URL http/https."""
    raw_names = [str(e.get("legalName") or ""), str(e.get("name") or "")]
    if any(re.search(r"[<>]", x) for x in raw_names): STATS["badNames"].append(raw_names[0][:80])
    lu = pdate(e.get("lastUpdateRaw") or e.get("lastUpdate"), None, "lastUpdate")
    hs = clean(e.get("homeState")).upper()
    ws = urls(" ".join(e["websites"]) if isinstance(e.get("websites"), list) else (e.get("website") or e.get("websiteHref") or ""))
    return {"legalName": clean(e.get("legalName")), "name": clean(e.get("name")) or clean(e.get("legalName")), "authority": clean(e.get("authority")),
            "homeState": hs if re.fullmatch(r"[A-Z]{2}", hs) else "", "lei": (clean(e.get("lei")).upper() if re.fullmatch(r"[A-Z0-9]{20}", clean(e.get("lei")).upper()) else ""),
            "address": clean(e.get("address")), "websites": ws, "websiteHref": ws[0] if ws else "",
            "platforms": urls(" ".join(e["platforms"]) if isinstance(e.get("platforms"), list) else (e.get("websitePlatform") or "")),
            "services": sorted({x for x in (e.get("services") or []) if isinstance(x, str) and re.fullmatch(r"[a-j]", x)}),
            "countries": sorted({x for x in (e.get("countries") or []) if isinstance(x, str) and x in COUNTRIES}),
            "authDate": pdate(e.get("authDateRaw") or e.get("authDate"), lu, "authDate"), "endDate": pdate(e.get("endDateRaw") or e.get("endDate"), None, "endDate"),
            "authDateText": (clean(e.get("authDateRaw") or e.get("authDate"))[:20] if not pdate_quiet(e.get("authDateRaw") or e.get("authDate"), lu) else ""),
            "comments": clean(e.get("comments"))[:600], "lastUpdate": lu, "legalBasis": basis(e.get("legalBasis") or e.get("legalBasisRaw") or "")}
# ---------- 1. Registro CASP ----------
source_used = None
def from_esma():
    raw, h = get(ESMA_CSV)
    lm = h.get("Last-Modified"); date = email.utils.parsedate_to_datetime(lm).date().isoformat() if lm else TODAY.isoformat()
    return parse_esma(raw.decode("utf-8-sig")), date, raw
COLS = set()
def parse_esma(text):
    rd = csv.DictReader(io.StringIO(text)); COLS.update(k for k in (rd.fieldnames or []) if k)
    rows = [{k: (v or "") for k, v in r.items() if k} for r in rd]; ents = {}
    if REQ_COLS - COLS: return []
    for x in rows:
        k = (x["ae_lei"].strip() or x["ae_lei_name"].strip().lower())
        e = ents.setdefault(k, {"legalName": x["ae_lei_name"], "name": (x["ae_commercial_name"].strip() or x["ae_lei_name"]),
            "authority": x["ae_competentAuthority"], "homeState": x["ae_homeMemberState"], "lei": x["ae_lei"].strip(), "address": x["ae_address"],
            "website": x["ae_website"], "websitePlatform": x.get("ae_website_platform", ""), "services": set(), "countries": set(),
            "authDateRaw": x["ac_authorisationNotificationDate"], "endDateRaw": x["ac_authorisationEndDate"], "comments": [], "lastUpdateRaw": x["ac_lastupdate"],
            "legalBasisRaw": x["ac_legal_basis"]})
        e["services"] |= {s.strip()[0].lower() for s in x["ac_serviceCode"].split("|") if s.strip()}
        e["countries"] |= set(re.findall(r"\b[A-Z]{2}\b", x["ac_serviceCode_cou"].upper()))
        if x["ac_comments"].strip(): e["comments"].append(re.sub(r"\s+", " ", x["ac_comments"]).strip())
        if not e["legalBasisRaw"].strip(): e["legalBasisRaw"] = x["ac_legal_basis"]
    out = []
    for e in ents.values():
        e["services"] = sorted(e["services"]); e["countries"] = sorted(e["countries"]); e["comments"] = " | ".join(dict.fromkeys(e["comments"]))
        out.append(sanitize(e))
    return out
def from_ct():
    raw, _ = get(CT_JSON); d = json.loads(raw)
    if not isinstance(d, dict) or not isinstance(d.get("items"), list): raise ValueError("CASP Tracker: formato inesperado")
    date = str(d.get("lastDataUpdate", ""))
    if not re.fullmatch(r"\d{4}-\d\d-\d\d", date): raise ValueError("CASP Tracker: fecha inválida")
    return [sanitize(x) for x in d["items"] if isinstance(x, dict)], date, raw
def keyof(x): return (x.get("lei") or "").strip().upper() or "name:" + re.sub(r"\s+", " ", (x.get("legalName") or "").replace("\xa0", " ")).strip().lower()
def es_of(x):
    end = x.get("endDate"); active = not end or end > TODAY.isoformat()
    return active and ("ES" in (x.get("countries") or []) or x.get("homeState") == "ES")
def validate(items, prev, cols=None):
    """Controles de cordura ANTES de escribir la instantánea o publicar. Devuelve la lista de problemas."""
    errs = []
    if cols is not None and REQ_COLS - cols: errs.append("faltan columnas: " + ", ".join(sorted(REQ_COLS - cols)))
    if len(items) < FLOOR: errs.append(f"solo {len(items)} proveedores (mínimo {FLOOR})")
    if STATS["badNames"]: errs.append(f"{len(STATS['badNames'])} nombres con < o >: {STATS['badNames'][:3]}")
    if STATS["dates"] and len(STATS["badDates"]) > 0.2 * STATS["dates"]: errs.append(f"{len(STATS['badDates'])} fechas ilegibles de {STATS['dates']}")
    names = {re.sub(r"\s+", " ", x["legalName"]).lower() for x in items}
    miss = [a for a in ANCHORS if a not in names]
    if miss: errs.append("faltan entidades ancla: " + ", ".join(miss))
    if prev:
        n0 = len(prev)
        if len(items) < (1 - MAXDROP) * n0: errs.append(f"el recuento cae de {n0} a {len(items)} (>{int(MAXDROP*100)} %)")
        if len(items) > (1 + MAXGROW) * n0: errs.append(f"el recuento sube de {n0} a {len(items)} (>{int(MAXGROW*100)} %)")
        A = {keyof(x): x for x in prev}; Bk = {keyof(x): x for x in items}
        gone = [k for k in A if k not in Bk]; gone_es = [k for k in gone if es_of(A[k])]
        lost_es = [k for k in Bk if k in A and es_of(A[k]) and not es_of(Bk[k])]
        if len(gone) > 10: errs.append(f"desaparecen {len(gone)} entidades")
        if len(gone_es) > 3: errs.append(f"desaparecen {len(gone_es)} entidades con España")
        if len(lost_es) > 10: errs.append(f"{len(lost_es)} entidades pierden España")
    return errs
PENDING = None
def abort(msg):
    print("ABORTADO (no se escribe instantánea ni se publica):\n  - " + msg.replace("\n", "\n  - ")); sys.exit(1)
snaps = sorted(SNAP.glob("*.json"))
csv_items = parse_esma((SRC/"CASPS.csv").read_text(encoding="utf-8-sig")) if (SRC/"CASPS.csv").exists() else []
if OFF:
    cur = json.loads(snaps[-1].read_text()); date, source_used = cur["lastDataUpdate"], cur.get("sourceUsed", "snapshot")
    # la instantánea ESMA se generó desde data/sources/CASPS.csv: se re-parsea con el validador actual (incluye ac_legal_basis)
    items = csv_items if (csv_items and source_used.startswith("ESMA")) else [sanitize(x) for x in cur["items"]]
    prev = json.loads(snaps[-2].read_text())["items"] if len(snaps) > 1 else None
    errs = validate(items, [sanitize(x) for x in prev] if prev else None, COLS if items is csv_items else None)
    if errs: print("aviso (offline):", errs)
else:
    raw_csv = None
    try:
        COLS.clear(); items, date, raw_csv = from_esma(); source_used = "ESMA CASPS.csv (oficial)"
        if REQ_COLS - COLS: abort("faltan columnas en CASPS.csv: " + ", ".join(sorted(REQ_COLS - COLS)))
    except SystemExit: raise
    except Exception as ex:
        print("ESMA falló:", ex)
        if not ALLOW_FB: abort("ESMA no disponible; el respaldo CASP Tracker requiere revisión manual (--allow-fallback)")
        items, date, _ = from_ct(); source_used = "CASP Tracker (respaldo)"
    prev = json.loads(snaps[-1].read_text())["items"] if snaps else None
    if snaps and snaps[-1].stem == date and len(snaps) > 1: prev = json.loads(snaps[-2].read_text())["items"]
    errs = validate(items, [sanitize(x) for x in prev] if prev else None, COLS if raw_csv else None)
    if errs and not FORCE: abort("\n".join(errs))
    if raw_csv: csv_items = items
    # la escritura de CASPS.csv y de la instantánea se aplaza hasta pasar todos los controles (ver write_snapshot)
    PENDING = (raw_csv, f"{date}.json", json.dumps({"lastDataUpdate": date, "sourceUsed": source_used, "items": items}, ensure_ascii=False))
# base legal oficial también para filas sin ella (p. ej. respaldo): por LEI desde el último CASPS.csv
LB = {keyof(x): x["legalBasis"] for x in csv_items if x.get("legalBasis")}
for x in items:
    if not x.get("legalBasis"): x["legalBasis"] = LB.get(keyof(x), "")
# ---------- 2. Fuentes para Art.59/60 ----------
TMP = {}   # descargas aún no escritas en data/sources (se guardan solo si todo el run pasa los controles)
def cached(name, fetch, required=False):
    """Online: descarga (si falla, usa la copia local). Offline: copia local; si una fuente obligatoria falta, se descarga una vez.
    Nada se escribe en data/sources hasta write_snapshot()."""
    p = SRC/name
    if not OFF or (required and not (p.exists() and p.stat().st_size)):
        if OFF: print(f"aviso (offline): falta data/sources/{name}; se descarga porque es obligatoria para clasificar")
        for i in range(3 if required else 1):   # las obligatorias se reintentan (p. ej. 504 puntuales del registro ESMA)
            try: TMP[name] = fetch(); break
            except Exception as ex:
                print(f"aviso: {name} (intento {i+1}):", ex)
                if required and i < 2: import time; time.sleep(15 * (i + 1))
    if name in TMP: return TMP[name]
    return p.read_bytes() if p.exists() else b""
def need(ok, name, why):
    if not ok: abort(f"fuente obligatoria data/sources/{name} no disponible o ilegible ({why}): la clasificación Art. 59/60 empeoraría. "
                     "Comprueba la red o restaura la caché; no se ha escrito nada.")
def ecb():
    page, _ = get(ECB_PAGE); m = re.search(rb'href="([^"]*mfi_csv_\d+\.csv\.gz)"', page); return get("https://www.ecb.europa.eu" + m.group(1).decode())[0]
mfi = {}
raw = cached("mfi.csv.gz", ecb, required=True)
try:
    for x in csv.DictReader(io.StringIO(gzip.decompress(raw).decode("utf-16")), delimiter="\t"):
        if x["LEI"]: mfi[x["LEI"]] = x["CATEGORY"]
except Exception as ex: mfi = {}; print("aviso: mfi.csv.gz ilegible:", ex)
need(len(mfi) >= MIN_MFI, "mfi.csv.gz", f"{len(mfi)} LEI, mínimo {MIN_MFI}")
upreg = {}
raw = cached("upreg.json", lambda: get(UPREG, 180)[0], required=True)
try:
    docs = json.loads(raw)["response"]["docs"]
    for x in docs:
        if x.get("ae_lei") and x.get("ae_status") == "Active" and x.get("ae_officeType", "Head office") == "Head office": upreg.setdefault(x["ae_lei"], x["ae_entityTypeLabel"])
except Exception as ex: docs = []; print("aviso: upreg.json ilegible:", ex)
need(len(docs) >= MIN_UPREG, "upreg.json", f"{len(docs)} registros, mínimo {MIN_UPREG}")
cnmv_txt = ""
raw = cached("cnmv.pdf", lambda: get(CNMV_PDF)[0], required=True)
if raw:
    try: cnmv_txt = subprocess.run(["pdftotext", "-layout", "-", "-"], input=raw, capture_output=True).stdout.decode("utf-8", "ignore")
    except FileNotFoundError: abort("falta pdftotext (poppler-utils): sin él no se lee el listado CNMV y la clasificación empeoraría")
need("PROVEEDORES" in cnmv_txt.upper() or len(cnmv_txt) > 5000, "cnmv.pdf", f"texto extraído: {len(cnmv_txt)} caracteres")
def cnmv_type(legal):
    w = re.sub(r"[^A-Z0-9 ]", "", legal.upper()).split()[:2]
    if not w: return None
    L = cnmv_txt.splitlines()
    for i, l in enumerate(L):
        if all(t in re.sub(r"[^A-Z0-9 ]", "", l.upper()) for t in w):
            ctx = " ".join(L[max(0, i-2): i+3])
            if "ENTIDAD DE CR" in ctx: return "ENTIDAD DE CRÉDITO"
            if re.search(r"\bPSC\b(?! EN)", ctx): return "PSC"
    return None
# cryptocodes.eu: entidades citadas como notificación (Art. 60) según su supervisor (30/09/2026)
CC_ART60 = {"trade republic bank gmbh", "n26 bank se", "flatexdegiro bank ag", "scalable capital bank gmbh", "banco bilbao vizcaya argentaria s.a.",
            "open bank s.a.", "vivid money b.v.", "one trading exchange b.v.", "change securities b.v.", "webull securities (europe) b.v.", "trading 212 markets ltd", "xtb limited"}
SRCURL = {"ESMA": "https://www.esma.europa.eu/esmas-activities/digital-finance-and-innovation/markets-crypto-assets-regulation-mica",
          "ECB": ECB_PAGE, "ESMA-MiFID": "https://registers.esma.europa.eu/publication/searchRegister?core=esma_registers_upreg",
          "CNMV": "https://www.cnmv.es/portal/consultas/proveedores-servicios-criptoactivos?lang=es", "cryptocodes": CC_URL}
def classify(e):
    """1) Campo oficial ac_legal_basis de ESMA (Art. 60 = notificación; Art. 63 = autorización CASP, la «licencia» del art. 59).
    2) Solo si está vacío: inferencia con comentarios ESMA, cryptocodes.eu, CNMV, BCE y registro MiFID (heuristic())."""
    lb = e.get("legalBasis", "")
    if lb == "Article 60": return "art60", "oficial", "Campo oficial «base legal» del registro ESMA: Art. 60 (notificación de una entidad financiera ya supervisada)", "ESMA"
    if lb == "Article 63": return "art59", "oficial", "Campo oficial «base legal» del registro ESMA: Art. 63 (autorización como proveedor de servicios de criptoactivos, la licencia que exige el art. 59)", "ESMA"
    o = OVR.get(keyof(e))
    if o and o.get("k") in ("art59", "art60"): return o["k"], "verificado", o["why"], "verificado"
    return heuristic(e)
OVR = json.loads((D/"overrides.json").read_text()).get("items", {}) if (D/"overrides.json").exists() else {}
def heuristic(e):
    c, ln = e.get("comments", "") or "", e["legalName"].strip().lower()
    if re.search(r"article\s*60|art\.?\s*60", c, re.I): return "art60", "alta", "Comentario del propio registro ESMA: «%s»" % c[:140], "ESMA"
    if ln in CC_ART60: return "art60", "alta", "cryptocodes.eu identifica la entrada como notificación según la lista de su supervisor", "cryptocodes"
    if e["homeState"] == "ES" and cnmv_txt:
        t = cnmv_type(e["legalName"])
        if t == "ENTIDAD DE CRÉDITO": return "art60", "alta", "Listado CNMV: tipo «Entidad de crédito»", "CNMV"
        if t == "PSC": return "art59", "alta", "Listado CNMV: tipo «PSC» (proveedor de servicios de criptoactivos autorizado)", "CNMV"
    cat = mfi.get(e.get("lei", ""))
    if cat == "Credit Institution": return "art60", "alta", "LEI en la lista de entidades de crédito del BCE (MFI): las entidades de crédito prestan servicios cripto por notificación (Art. 60.1)", "ECB"
    up = upreg.get(e.get("lei", ""))
    if up: return "art60", "media", f"LEI en el registro ESMA como «{up}»: puede haber notificado (Art. 60) o pedido autorización completa", "ESMA-MiFID"
    if cat: return "incierto", "baja", f"LEI en la lista del BCE como «{cat}» (p. ej. entidad de dinero electrónico): vía no determinable", "ECB"
    return "art59", "media", "No figura como banco (BCE) ni como empresa de inversión/gestora (ESMA): solo puede operar con autorización CASP (Art. 59)", "ESMA"
# ---------- 3. Modelo ----------
def slugify(s, salt=""):
    t = re.sub(r"[^a-z0-9]+", "-", s.lower().encode("ascii", "ignore").decode()).strip("-")
    return t or "e-" + hashlib.md5((salt or s or "x").encode()).hexdigest()[:8]
SLUGS = D/"slugs.json"
slugmap = json.loads(SLUGS.read_text()) if SLUGS.exists() else {}
def slug_for(x):
    k = keyof(x)
    if k in slugmap: return slugmap[k]
    used = set(slugmap.values()); sl = slugify(x["legalName"], x.get("lei") or x["legalName"])
    while sl in used: sl += "-2"
    slugmap[k] = sl; return sl
ents, corrections = [], []
for e in items:
    k, conf, why, src = classify(e)
    if conf == "oficial":
        hk = heuristic(e)
        if hk[0] != k: corrections.append({"l": e["legalName"], "from": hk[0], "fromConf": hk[1], "to": k, "basis": e["legalBasis"]})
    active = not e.get("endDate") or e["endDate"] > TODAY.isoformat()
    cs = e.get("countries", []); home_only = not cs and bool(e["homeState"])
    ents.append({"slug": slug_for(e), "n": e["name"], "l": e["legalName"], "h": e["homeState"], "a": e["authority"], "lei": e.get("lei", ""),
        "addr": e.get("address", ""), "w": e.get("websiteHref", ""), "ws": e.get("websites", []), "wp": e.get("platforms", []),
        "s": e.get("services", []), "cs": cs or ([e["homeState"]] if e["homeState"] else []), "homeOnly": home_only,
        "es": active and ("ES" in cs or e["homeState"] == "ES"), "active": active, "d": e.get("authDate"), "dt": e.get("authDateText", ""), "end": e.get("endDate"), "cm": e.get("comments", ""),
        "lu": e.get("lastUpdate"), "lb": e.get("legalBasis", ""),
        "k": k, "conf": conf, "why": why, "src": src, "srcUrl": (OVR.get(keyof(e)) or {}).get("url") if src == "verificado" else SRCURL[src], "brands": []})
assert not any(x["es"] and x["end"] and x["end"] <= TODAY.isoformat() for x in ents), "regresión: autorización retirada marcada como operativa"
byL = {re.sub(r"\s+", " ", x["l"]).lower(): x for x in ents}
nc = []
raw = cached("NCASP.csv", lambda: get(ESMA_NC)[0])
if raw:
    for x in csv.DictReader(io.StringIO(raw.decode("utf-8-sig", "ignore"))):
        nc.append({"n": clean(x.get("ae_commercial_name") or x.get("ae_lei_name")), "l": clean(x.get("ae_lei_name")), "a": clean(x.get("ae_competentAuthority")), "w": " ".join(urls(x.get("ae_website")))})
def nrm(s): return re.sub(r"[^a-z0-9]+", "", (s or "").lower())
brands = []
for b in json.loads((D/"brands.json").read_text())["brands"]:
    hits = [byL[l.lower()] for l in b["legalNames"] if l.lower() in byL]
    for h in hits: h["brands"].append(b["brand"])
    # aviso NCASP: solo coincidencia exacta del nombre comercial o legal, o lista revisada a mano en brands.json ("ncasp")
    want = {nrm(b["brand"])} | {nrm(x) for x in b.get("ncasp", [])}
    warn = [x for x in nc if nrm(x["n"]) in want or nrm(x["l"]) in want]
    if hits: st = "ok"
    elif b.get("state"): st = b["state"]
    elif b["category"] == "wallet": st = "autocustodia"
    elif b["category"] == "banco/neobanco/pagos": st = "sincripto"
    else: st = "nofigura"
    brands.append({"b": b["brand"], "cat": b["category"], "e": [h["slug"] for h in hits], "status": st, "aliases": b.get("aliases", []),
                   "src": b["source"], "note": b["note"], "warn": warn[:3]})
# ---------- 4. Cambios (clave: LEI) y fichas dadas de baja ----------
snaps = sorted(set(SNAP.glob("*.json")) | ({SNAP/PENDING[1]} if PENDING else set())); changes = []   # incluye la instantánea aún no escrita
def rd(p): return PENDING[2] if PENDING and p == SNAP/PENDING[1] else p.read_text()
cur_keys = {keyof(x) for x in items}; bySlugKey = {keyof(x): slug_for(x) for x in items}
gone = {}
def es(x): return es_of(x)
for a, b in zip(snaps, snaps[1:]):
    A = {keyof(x): x for x in json.loads(rd(a))["items"]}; B = {keyof(x): x for x in json.loads(rd(b))["items"]}
    if b == snaps[-1]: B = {keyof(x): x for x in items}
    for k in A:
        if k not in B and k not in cur_keys:
            x = sanitize(A[k]); gone[k] = {"slug": slug_for(x), "n": x["name"], "l": x["legalName"], "h": x["homeState"], "a": x["authority"], "lei": x["lei"],
                                          "last": a.stem, "removed": b.stem, "w": x["websiteHref"]}
    changes.append({"from": a.stem, "to": b.stem, "total": len(B),
        "added": [[clean(B[k]["legalName"]), B[k]["homeState"], es(B[k]), bySlugKey.get(k)] for k in B if k not in A],
        "removed": [[clean(A[k]["legalName"]), A[k]["homeState"], (gone.get(k) or {}).get("slug") or bySlugKey.get(k)] for k in A if k not in B],
        "es": [[clean(B[k]["legalName"]), es(B[k]), bySlugKey.get(k)] for k in B if k in A and es(A[k]) != es(B[k])]})
for k in list(gone):
    if k in cur_keys: del gone[k]
changes.reverse()
act = [x for x in ents if x["active"]]
try: prev_meta = json.loads((D/"build.json").read_text())["meta"]
except Exception: prev_meta = {}
checked = TODAY.isoformat() if not OFF else (prev_meta.get("checked") or (snaps[-1].stem if snaps else date))   # última consulta correcta a ESMA
meta = {"date": date, "count": len(act), "countAll": len(ents), "inactive": len(ents) - len(act), "es": sum(x["es"] for x in ents), "source": source_used,
        "k": {k: sum(x["k"] == k for x in act) for k in ("art59", "art60", "incierto")},
        "conf": {c: sum(x["conf"] == c for x in act) for c in ("oficial", "verificado", "alta", "media", "baja")},
        "official": sum(1 for x in act if x["conf"] == "oficial"),
        "brands": len(brands), "brandsOk": sum(b["status"] == "ok" for b in brands), "snapshots": len(snaps), "nc": len(nc),
        "built": TODAY.isoformat(), "checked": checked, "corrections": corrections, "approxDates": STATS["approxDates"], "badDates": STATS["badDates"][:20]}
# ---------- control de deriva de la clasificación frente a la última versión publicada (data/build.json) ----------
def ekey(x): return (x.get("lei") or "").upper() or re.sub(r"\s+", " ", x.get("l", "")).lower()
try: prev_ents = {ekey(x): x for x in json.loads((D/"build.json").read_text())["ents"] if x.get("active")}
except Exception: prev_ents = {}
if prev_ents:
    common = [(prev_ents[ekey(x)], x) for x in act if ekey(x) in prev_ents]
    moved = [(a, b) for a, b in common if a["k"] != b["k"]]
    off_moved = [(a, b) for a, b in moved if b["conf"] == "oficial"]           # el campo oficial de ESMA manda: se acepta
    inf_moved = [(a, b) for a, b in moved if b["conf"] != "oficial"]
    lim = max(KDRIFT_MIN, int(KDRIFT * len(common)))
    print(f"deriva de clasificación: {len(moved)} de {len(common)} cambian ({len(off_moved)} por base legal oficial, {len(inf_moved)} inferidas; límite {lim})")
    if len(inf_moved) > lim:
        ej = "; ".join(f'{b["l"]}: {a["k"]}→{b["k"]}' for a, b in inf_moved[:8])
        msg = (f"{len(inf_moved)} clasificaciones no oficiales cambian frente a la versión publicada (límite {lim}). "
               f"Antes {prev_meta.get('k')}, ahora {meta['k']}. Ejemplos: {ej}")
        if FORCE: print("aviso (--force):", msg)
        else: abort(msg + "\nSi el cambio es legítimo, revísalo y repite con --force.")
def write_snapshot():
    for name, b in TMP.items(): (SRC/name).write_bytes(b)
    if PENDING:
        raw_csv, fn, js = PENDING
        if raw_csv: (SRC/"CASPS.csv").write_bytes(raw_csv)
        (SNAP/fn).write_text(js)
write_snapshot()
SLUGS.write_text(json.dumps(dict(sorted(slugmap.items())), ensure_ascii=False, indent=0))
json.dump({"meta": meta, "ents": ents, "brands": brands, "changes": changes, "gone": sorted(gone.values(), key=lambda x: x["removed"], reverse=True)}, open(D/"build.json", "w"), ensure_ascii=False)
print(json.dumps({k: v for k, v in meta.items() if k not in ("corrections", "approxDates", "badDates")}, ensure_ascii=False))
print("correcciones por base legal oficial:", json.dumps(corrections, ensure_ascii=False))
# ---------- 5. Logos (solo dominios nuevos o fallidos hace >30 días; nunca rompe el build) ----------
if not OFF and "--no-logos" not in sys.argv:
    try: subprocess.run([sys.executable, str(R/"scripts/logos.py")], check=False, timeout=1200)
    except Exception as ex: print("aviso: logos", ex)
subprocess.run([sys.executable, str(R/"scripts/build_site.py")], check=True)
