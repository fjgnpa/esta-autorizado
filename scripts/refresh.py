#!/usr/bin/env python3
"""¿Está autorizado? — ingesta + clasificación + generación del sitio estático.
Fuentes: ESMA CASPS.csv (oficial, primaria) -> CASP Tracker JSON (respaldo); ECB MFI list; ESMA registro MiFID/AIFM/UCITS;
CNMV listado PDF; cryptocodes.eu. Uso: python3 scripts/refresh.py [--offline]"""
import csv, io, json, re, sys, gzip, urllib.request, email.utils, datetime, pathlib, subprocess, html, shutil, hashlib
R = pathlib.Path(__file__).resolve().parent.parent
D, SRC, SNAP, SITE = R/"data", R/"data/sources", R/"data/snapshots", R/"site"
for p in (SRC, SNAP, SITE): p.mkdir(parents=True, exist_ok=True)
OFF = "--offline" in sys.argv
UA = {"User-Agent": "Mozilla/5.0 (esta-autorizado refresh)"}
def get(url, t=90):
    r = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=t); return r.read(), r.headers
ESMA_CSV = "https://www.esma.europa.eu/sites/default/files/2024-12/CASPS.csv"
ESMA_NC = "https://www.esma.europa.eu/sites/default/files/2024-12/NCASP.csv"
CT_JSON = "https://raw.githubusercontent.com/CASP-Tracker/mica-register-data/main/data/casps.json"
ECB_PAGE = "https://www.ecb.europa.eu/stats/financial_corporations/list_of_financial_institutions/html/daily_list-MID.en.html"
UPREG = "https://registers.esma.europa.eu/solr/esma_registers_upreg/select?q=entity_type:ae&fq=ae_entityTypeCode:(mif%20OR%20MIF%20OR%20aif%20OR%20AIF%20OR%20uci%20OR%20UCI)&fl=ae_lei,ae_entityTypeLabel,ae_status,ae_officeType&rows=30000&wt=json"
CNMV_PDF = "https://www.cnmv.es/Docportal/Proveedores-Servicios-Criptoactivos/Listado_ProveedoresCriptoactivos.pdf"
CC_URL = "https://www.cryptocodes.eu/news/mica-register-authorised-or-just-notified"
def dmy(s):
    s = (s or "").strip()
    try: return datetime.datetime.strptime(s, "%d/%m/%Y").date().isoformat()
    except: return None
# ---------- 1. Registro CASP ----------
source_used = None
def from_esma():
    raw, h = get(ESMA_CSV); (SRC/"CASPS.csv").write_bytes(raw)
    lm = h.get("Last-Modified"); date = email.utils.parsedate_to_datetime(lm).date().isoformat() if lm else datetime.date.today().isoformat()
    return parse_esma(raw.decode("utf-8-sig")), date, raw
def parse_esma(text):
    rows = [{k: re.sub(r"\s+", " ", (v or "").replace("\xa0", " ")).strip() for k, v in r.items() if k} for r in csv.DictReader(io.StringIO(text))]; ents = {}
    for x in rows:
        k = (x["ae_lei"].strip() or x["ae_lei_name"].strip().lower())
        e = ents.setdefault(k, {"legalName": x["ae_lei_name"].strip(), "name": (x["ae_commercial_name"].strip() or x["ae_lei_name"].strip()),
            "authority": x["ae_competentAuthority"].strip(), "homeState": x["ae_homeMemberState"].strip(), "lei": x["ae_lei"].strip(),
            "address": x["ae_address"].strip(), "website": x["ae_website"].strip(), "services": set(), "countries": set(),
            "authDate": dmy(x["ac_authorisationNotificationDate"]), "endDate": dmy(x["ac_authorisationEndDate"]), "comments": [], "lastUpdate": dmy(x["ac_lastupdate"])})
        e["services"] |= {s.strip()[0] for s in x["ac_serviceCode"].split("|") if s.strip()}
        e["countries"] |= set(re.findall(r"\b[A-Z]{2}\b", x["ac_serviceCode_cou"].upper()))
        if x["ac_comments"].strip(): e["comments"].append(x["ac_comments"].strip())
    out = []
    for e in ents.values():
        e["services"] = sorted(e["services"]); e["countries"] = sorted(e["countries"]); e["comments"] = " | ".join(dict.fromkeys(e["comments"]))
        w = e["website"]; e["websiteHref"] = ("https://" + w if w and not w.startswith("http") else w); out.append(e)
    return out
def from_ct():
    raw, _ = get(CT_JSON); d = json.loads(raw); return d["items"], d["lastDataUpdate"], raw
if OFF:
    snaps = sorted(SNAP.glob("*.json")); cur = json.loads(snaps[-1].read_text()); items, date = cur["items"], cur["lastDataUpdate"]; source_used = cur.get("sourceUsed", "snapshot")
else:
    try: items, date, _ = from_esma(); source_used = "ESMA CASPS.csv (oficial)"
    except Exception as ex:
        print("ESMA falló, uso CASP Tracker:", ex); items, date, _ = from_ct(); source_used = "CASP Tracker (respaldo)"
    (SNAP/f"{date}.json").write_text(json.dumps({"lastDataUpdate": date, "sourceUsed": source_used, "items": items}, ensure_ascii=False))
# ---------- 2. Fuentes para Art.59/60 ----------
def cached(name, fetch):
    p = SRC/name
    if not OFF:
        try: p.write_bytes(fetch())
        except Exception as ex: print("aviso:", name, ex)
    return p.read_bytes() if p.exists() else b""
def ecb():
    page, _ = get(ECB_PAGE); m = re.search(rb'href="([^"]*mfi_csv_\d+\.csv\.gz)"', page); return get("https://www.ecb.europa.eu" + m.group(1).decode())[0]
mfi = {}
raw = cached("mfi.csv.gz", ecb)
if raw:
    for x in csv.DictReader(io.StringIO(gzip.decompress(raw).decode("utf-16")), delimiter="\t"):
        if x["LEI"]: mfi[x["LEI"]] = x["CATEGORY"]
upreg = {}
raw = cached("upreg.json", lambda: get(UPREG, 180)[0])
if raw:
    for x in json.loads(raw)["response"]["docs"]:
        if x.get("ae_lei") and x.get("ae_status") == "Active" and x.get("ae_officeType", "Head office") == "Head office": upreg.setdefault(x["ae_lei"], x["ae_entityTypeLabel"])
cnmv_txt = ""
raw = cached("cnmv.pdf", lambda: get(CNMV_PDF)[0])
if raw:
    cnmv_txt = subprocess.run(["pdftotext", "-layout", str(SRC/"cnmv.pdf"), "-"], capture_output=True, text=True).stdout
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
def slugify(s):
    s = re.sub(r"[^a-z0-9]+", "-", s.lower().encode("ascii", "ignore").decode()).strip("-"); return s or hashlib.md5(s.encode()).hexdigest()[:8]
ents, seen = [], set()
for e in items:
    k, conf, why, src = classify(e)
    sl = slugify(e["legalName"]);
    while sl in seen: sl += "-2"
    seen.add(sl)
    ents.append({"slug": sl, "n": e["name"].strip(), "l": e["legalName"].strip(), "h": e["homeState"], "a": e["authority"], "lei": e.get("lei", ""),
        "addr": e.get("address", ""), "w": e.get("websiteHref", ""), "s": e.get("services", []), "cs": e.get("countries", []),
        "es": "ES" in e.get("countries", []) or e["homeState"] == "ES", "d": e.get("authDate"), "end": e.get("endDate"), "cm": e.get("comments", ""),
        "k": k, "conf": conf, "why": why, "src": src, "srcUrl": SRCURL[src], "brands": []})
byL = {re.sub(r"\s+", " ", x["l"]).lower(): x for x in ents}
nc = []
raw = cached("NCASP.csv", lambda: get(ESMA_NC)[0])
if raw:
    for x in csv.DictReader(io.StringIO(raw.decode("utf-8-sig", "ignore"))): nc.append({"n": x["ae_commercial_name"] or x["ae_lei_name"], "l": x["ae_lei_name"], "a": x["ae_competentAuthority"], "w": x["ae_website"]})
brands = []
for b in json.loads((D/"brands.json").read_text())["brands"]:
    hits = [byL[l.lower()] for l in b["legalNames"] if l.lower() in byL]
    for h in hits: h["brands"].append(b["brand"])
    warn = [x for x in nc if b["brand"].split(" ")[0].lower() == (x["n"] or "").split(" ")[0].lower()]
    brands.append({"b": b["brand"], "cat": b["category"], "e": [h["slug"] for h in hits], "status": "ok" if hits else "nofigura",
                   "src": b["source"], "note": b["note"], "warn": warn[:3]})
# ---------- 4. Cambios ----------
def kl(x): return re.sub(r"\s+", " ", x["legalName"].replace("\xa0", " ")).strip().lower()
snaps = sorted(SNAP.glob("*.json")); changes = []
for a, b in zip(snaps, snaps[1:]):
    A = {kl(x): x for x in json.loads(a.read_text())["items"]}; B = {kl(x): x for x in json.loads(b.read_text())["items"]}
    def es(x): return "ES" in x.get("countries", []) or x.get("homeState") == "ES"
    changes.append({"from": a.stem, "to": b.stem, "total": len(B),
        "added": [[B[k]["legalName"].strip(), B[k]["homeState"], es(B[k]), byL.get(k, {}).get("slug")] for k in B if k not in A],
        "removed": [[A[k]["legalName"].strip(), A[k]["homeState"]] for k in A if k not in B],
        "es": [[B[k]["legalName"].strip(), es(B[k]), byL.get(k, {}).get("slug")] for k in B if k in A and es(A[k]) != es(B[k])]})
changes.reverse()
meta = {"date": date, "count": len(ents), "es": sum(x["es"] for x in ents), "source": source_used,
        "k": {k: sum(x["k"] == k for x in ents) for k in ("art59", "art60", "incierto")},
        "conf": {c: sum(x["conf"] == c for x in ents) for c in ("alta", "media", "baja")},
        "brands": len(brands), "brandsOk": sum(b["status"] == "ok" for b in brands), "snapshots": len(snaps), "nc": len(nc)}
json.dump({"meta": meta, "ents": ents, "brands": brands, "changes": changes}, open(D/"build.json", "w"), ensure_ascii=False)
print(json.dumps(meta, ensure_ascii=False))
subprocess.run([sys.executable, str(R/"scripts/build_site.py")], check=True)
