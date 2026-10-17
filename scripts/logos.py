#!/usr/bin/env python3
"""Logos de marcas y proveedores (Registro MiCA).
Descarga UNA vez el icono oficial de cada dominio (portada: apple-touch-icon / icon / manifest; respaldo: favicon.ico,
favicons de DuckDuckGo y Google), lo normaliza a PNG 128x128 en site/assets/logos/ y guarda el mapa en data/logos.json.
La web nunca enlaza a terceros: solo sirve los ficheros descargados. Si no hay un icono decente (genérico, vacío o
diminuto), la web usa un monograma. Dominios: solo los del registro ESMA o, para marcas sin web en el registro, los de
data/brand_domains.json que se verifican (la portada se identifica como la marca). Nunca rompe el build.
Uso: python3 scripts/logos.py [--retry] [--only dominio,...]"""
import json, re, sys, io, time, hashlib, pathlib, datetime, urllib.request, urllib.parse, html as H, ssl, socket
from concurrent.futures import ThreadPoolExecutor
R = pathlib.Path(__file__).resolve().parent.parent
D, OUT = R/"data", R/"site/assets/logos"
MAP = D/"logos.json"
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36 RegistroMiCA-logos",
      "Accept-Language": "es-ES,es;q=0.9,en;q=0.8", "Accept": "text/html,application/xhtml+xml,image/avif,image/webp,image/*,*/*;q=0.8"}
SZ, MIN, LOW = 128, 32, 48  # salida 128 px (2x para 64 px CSS); 32-47 px -> «lowres» (se muestra más pequeño, sin inventar nitidez); <32 -> monograma
RETRY_DAYS = 30
try:
    from PIL import Image, ImageStat
    Image.MAX_IMAGE_PIXELS = 4_000_000   # contra bombas de descompresión
except Exception:
    Image = None
TODAY = datetime.date.today().isoformat()
# hosts de plataformas que a veces aparecen como «web» en el registro (prototipos, perfiles): su icono NO es el de la entidad
PLATFORM = ("figma.com", "linkedin.com", "facebook.com", "google.com", "sites.google.com", "notion.site", "wixsite.com", "webflow.io",
            "framer.website", "github.io", "wordpress.com", "carrd.co", "x.com", "twitter.com", "instagram.com", "medium.com")
# huellas (aHash 16x16) de iconos genéricos de CMS: WordPress, Joomla
GENERIC_AHASH = ("fffffffffc3ff00fe017f01bc893c883c483c443e447e267f02ffc1fffffffff",
                 "9ff90ff001808001cc33cc33c993e387e3c7c183c833cc73800101800ff09ff9")
def ahash(im):
    g = Image.new("RGB", im.size, (255, 255, 255)); g.paste(im, mask=im.getchannel("A")); g = g.convert("L").resize((16, 16), Image.LANCZOS)
    px = list(g.tobytes()); m = sum(px) / len(px); return int("".join("1" if p > m else "0" for p in px), 2)

def slug(s): return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
def hosts_in(w):
    """Todos los hosts que aparecen en el campo web del registro (el campo a veces trae basura o varias webs)."""
    w = re.sub(r"h?t?tps?[:.]//", " ", (w or "").lower())
    out = []
    for m in re.finditer(r"(?<![a-z0-9@-])((?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z]{2,})(?![a-z0-9-])", w):
        h = m.group(1)
        h = h[4:] if h.startswith("www.") else h
        if h not in out and "." in h and not any(h == p or h.endswith("." + p) for p in PLATFORM): out.append(h)
    return out
def pick_host(w, brand=None):
    hs = hosts_in(w)
    if brand and len(hs) > 1:
        t = re.sub(r"[^a-z0-9]", "", brand.lower())
        for h in hs:
            if t and t in h.replace("-", ""): return h
    return hs[0] if hs else None

def fetch(url, t=12, limit=2_000_000):
    ctx = ssl.create_default_context()
    r = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=t, context=ctx)
    return r.read(limit), r.geturl(), r.headers.get("Content-Type", "")

LINK = re.compile(r"<link\b[^>]*>", re.I | re.S)
def attr(tag, a):
    m = re.search(r'\b%s\s*=\s*("([^"]*)"|\'([^\']*)\'|([^\s>]+))' % a, tag, re.I)
    return H.unescape(m.group(2) or m.group(3) or m.group(4) or "") if m else ""
def page_info(host):
    """Portada del dominio: candidatos de icono declarados + texto de identificación (title, og:site_name)."""
    for base in (f"https://{host}/", f"https://www.{host}/"):
        try:
            raw, final, ct = fetch(base)
        except Exception:
            continue
        txt = raw.decode("utf-8", "ignore")
        head = txt[:400_000]
        title = re.search(r"<title[^>]*>(.*?)</title>", head, re.I | re.S)
        ids = [H.unescape(title.group(1)).strip()] if title else []
        for p in ("og:site_name", "og:title", "application-name", "apple-mobile-web-app-title"):
            m = re.search(r'<meta[^>]+(?:property|name)\s*=\s*["\']%s["\'][^>]*>' % p, head, re.I)
            if m: ids.append(attr(m.group(0), "content"))
        cands = []
        for tag in LINK.findall(head):
            rel = attr(tag, "rel").lower(); href = attr(tag, "href")
            if not href or href.startswith("data:"): continue
            u = urllib.parse.urljoin(final, href)
            if "apple-touch-icon" in rel: cands.append((180, u, "apple-touch-icon"))
            elif "icon" in rel and "mask-icon" not in rel:
                s = attr(tag, "sizes"); n = max([int(x) for x in re.findall(r"(\d+)x\d+", s)] or [0])
                cands.append((n or (64 if u.lower().split("?")[0].endswith(".svg") else 32), u, "icon"))
            elif rel == "manifest":
                try:
                    man = json.loads(fetch(u, 8, 300_000)[0].decode("utf-8", "ignore"))
                    for ic in man.get("icons", []):
                        n = max([int(x) for x in re.findall(r"(\d+)x\d+", ic.get("sizes", ""))] or [0])
                        if ic.get("src"): cands.append((n, urllib.parse.urljoin(u, ic["src"]), "manifest"))
                except Exception: pass
        origin = "{0.scheme}://{0.netloc}/".format(urllib.parse.urlparse(final))
        return {"ok": True, "final": final, "ids": [i for i in ids if i][:6], "cands": cands, "origin": origin}
    return {"ok": False, "final": None, "ids": [], "cands": [], "origin": f"https://{host}/"}

_generic = set()
def generic_hashes():
    """Iconos «por defecto» que devuelven los servicios de favicons cuando no tienen el dominio (globo, etc.)."""
    if _generic: return _generic
    for u in ("https://www.google.com/s2/favicons?domain=zz-no-existe-registromica.invalid&sz=128",
              "https://icons.duckduckgo.com/ip3/zz-no-existe-registromica.invalid.ico"):
        try: _generic.add(hashlib.sha1(fetch(u, 8)[0]).hexdigest())
        except Exception: pass
    return _generic

def is_svg(raw): return raw.lstrip()[:5] == b"<?xml" or b"<svg" in raw[:800]
def clean_svg(raw):
    """SVG servido como <img> (sin scripts). Lo saneamos igualmente y descartamos los que cambian con el tema del sistema."""
    t = raw.decode("utf-8", "ignore")
    if "prefers-color-scheme" in t or "<image" in t or not re.search(r"<(path|rect|circle|polygon|ellipse|g)\b", t): return None
    # rechazo (no limpieza) de cualquier contenido activo o externo: el fichero se sirve desde nuestro dominio
    if re.search(r"<script|<foreignObject|<iframe|<embed|<object|javascript:|data:text|@import|\son\w+\s*=|<!ENTITY|href\s*=\s*(?![\"']?#)", t, re.I): return None
    if len(t) > 60_000: return None
    return t
def load_img(raw, url):
    if is_svg(raw): return None
    im = Image.open(io.BytesIO(raw))
    if getattr(im, "format", "") == "ICO":
        sizes = sorted(im.info.get("sizes", [im.size]), key=lambda s: s[0] * s[1])
        try: im.size = sizes[-1]
        except Exception: pass
    im.load(); return im.convert("RGBA")

def quality(im):
    """Devuelve (motivo_de_rechazo | None)."""
    w, h = im.size
    if min(w, h) < MIN: return f"diminuto ({w}x{h})"
    hv = ahash(normalise(im)[0])
    if any(bin(hv ^ int(g, 16)).count("1") <= 8 for g in GENERIC_AHASH): return "icono genérico de CMS"
    if max(w, h) / min(w, h) > 1.15: return f"no cuadrado ({w}x{h}): suele ser un recorte del logotipo"
    a = im.getchannel("A")
    bbox = a.point(lambda v: 255 if v > 16 else 0).getbbox()
    if not bbox: return "vacío"
    rgb = Image.new("RGB", im.size, (255, 255, 255)); rgb.paste(im, mask=a)
    st = ImageStat.Stat(rgb.convert("L"))
    if st.stddev[0] < 4: return "liso (sin contenido)"
    # marcador de posición (p. ej. el cuadrado negro por defecto de algunos constructores web): un rectángulo de un solo color
    sm = rgb.resize((48, 48)); bgc = sm.getpixel((0, 0)); px = sm.load()
    idx = [(x, y) for y in range(48) for x in range(48) if sum(abs(px[x, y][k] - bgc[k]) for k in range(3)) > 60]
    if len(idx) > 48 * 48 * 0.15:
        x0, x1 = min(i[0] for i in idx) + 3, max(i[0] for i in idx) - 3; y0, y1 = min(i[1] for i in idx) + 3, max(i[1] for i in idx) - 3
        inner = [px[x, y] for y in range(y0, y1 + 1) for x in range(x0, x1 + 1)]
        if inner:
            med = [sorted(p[k] for p in inner)[len(inner) // 2] for k in range(3)]
            same = sum(1 for p in inner if sum(abs(p[k] - med[k]) for k in range(3)) < 80) / len(inner)
            if same > 0.985: return "marcador de posición (rectángulo liso)"
    cw, ch = bbox[2] - bbox[0], bbox[3] - bbox[1]
    if max(cw, ch) < MIN * 0.75: return f"contenido diminuto ({cw}x{ch})"
    return None

def normalise(im, SZ=SZ):
    """Cuadrado. Tres casos:
    - «full»: icono con fondo propio (esquinas opacas) o con forma de app (cuadrado redondeado / círculo que llena su caja):
      se escala a sangre y la web lo recorta con esquinas redondeadas.
    - «pad»: logotipo transparente (glifo suelto): se recorta y se centra con margen sobre una baldosa clara."""
    a = im.getchannel("A")
    bbox = a.point(lambda v: 255 if v > 16 else 0).getbbox()
    w, h = im.size
    corners = [a.getpixel(p) for p in ((1, 1), (w - 2, 1), (1, h - 2), (w - 2, h - 2))]
    if min(corners) > 230 and abs(w - h) <= max(2, w // 20):
        return_mode, src = "full", im
    else:
        c = im.crop(bbox); cw, ch = c.size
        fill = sum(1 for v in c.getchannel("A").resize((32, 32)).tobytes() if v > 200) / 1024
        if abs(cw - ch) <= max(2, cw // 12) and fill > 0.72:
            return_mode, src = "full", c          # forma de app o círculo: a sangre (el círculo queda inscrito)
        else:
            s_ = max(cw, ch); canvas = Image.new("RGBA", (s_, s_), (0, 0, 0, 0)); canvas.paste(c, ((s_ - cw) // 2, (s_ - ch) // 2))
            inner = int(SZ * 0.8); canvas = canvas.resize((inner, inner), Image.LANCZOS)
            src = Image.new("RGBA", (SZ, SZ), (0, 0, 0, 0)); src.paste(canvas, ((SZ - inner) // 2, (SZ - inner) // 2)); return_mode = "pad"
    out = src.resize((SZ, SZ), Image.LANCZOS) if src.size != (SZ, SZ) else src; mode = return_mode
    # color dominante (para acentos sutiles en la web)
    sm = out.resize((32, 32)).tobytes(); px = [tuple(sm[i:i + 4]) for i in range(0, len(sm), 4)]
    px = [p for p in px if p[3] > 200 and (max(p[:3]) - min(p[:3])) > 40]
    col = None
    if px:
        r, g, b = (sum(p[i] for p in px) // len(px) for i in range(3)); col = "#%02x%02x%02x" % (r, g, b)
    # ¿fondo claro? (en «full» con fondo blanco la web pone borde)
    bg = out.getpixel((3, 3)); light = mode == "full" and bg[3] > 200 and min(bg[:3]) > 235
    return out, mode, col, light

def candidates(host, info):
    c = sorted(info["cands"], key=lambda x: -x[0])
    o = info["origin"]
    c += [(180, urllib.parse.urljoin(o, "/apple-touch-icon.png"), "apple-touch-icon"), (32, urllib.parse.urljoin(o, "/favicon.ico"), "favicon.ico"),
          (128, f"https://www.google.com/s2/favicons?domain={host}&sz=256", "google-s2"), (64, f"https://icons.duckduckgo.com/ip3/{host}.ico", "duckduckgo")]
    seen, out = set(), []
    for x in c:
        if x[1] not in seen: seen.add(x[1]); out.append(x)
    return out[:10]

def get_logo(host, need_id=None, manual=None):
    rec = {"domain": host, "checked": TODAY}
    info = page_info(host)
    rec["home"] = info["final"]; rec["ids"] = info["ids"]
    if need_id:
        # verificación de dominio para marcas sin web en el registro
        tok = [t for t in re.split(r"[^a-z0-9.]+", need_id.lower()) if len(t) >= 2]
        blob = " ".join(info["ids"]).lower()
        ok = info["ok"] and any(t in blob for t in tok)
        rec["verified"] = "portada" if ok else ("manual: " + manual if manual else False)
        if not ok and manual: ok = True
        if not ok:
            rec.update(status="unverified", why="la portada no se identifica como la marca" if info["ok"] else "portada inaccesible"); return rec
    gen = generic_hashes(); best = None; rejects = []
    for decl, url, src in candidates(host, info):
        try:
            raw, final, ct = fetch(url, 10)
            if "text/html" in ct: rejects.append(f"{src}: html"); continue
            if hashlib.sha1(raw).hexdigest() in gen: rejects.append(f"{src}: genérico"); continue
            if is_svg(raw):
                sv = clean_svg(raw)
                if not sv: rejects.append(f"{src}: svg no apto"); continue
                if not best or best[0] < 150: best = (150, sv, src + " (svg)", url)
                continue
            im = load_img(raw, url)
            bad = quality(im)
            if bad: rejects.append(f"{src}: {bad}"); continue
            score = min(im.size) + (40 if src in ("apple-touch-icon", "manifest", "icon") else 0) - (200 if min(im.size) < LOW else 0)
            if not best or score > best[0]: best = (score, im, src, url)
            if min(im.size) >= 128 and src != "google-s2": break
        except Exception as ex:
            rejects.append(f"{src}: {type(ex).__name__}")
    if not best:
        rec.update(status="monogram", why="; ".join(rejects)[:400]); return rec
    OUT.mkdir(parents=True, exist_ok=True)
    if isinstance(best[1], str):
        fn = slug(host) + ".svg"; (OUT/fn).write_text(best[1])
        rec.update(status="ok", file=fn, src=best[2], url=best[3], orig="svg", mode="pad", color=None, light=False, lowres=False); return rec
    low = min(best[1].size) < LOW
    out, mode, col, light = normalise(best[1], 64 if low else SZ)
    fn = slug(host) + ".png"
    out.save(OUT/fn, optimize=True)
    rec.update(status="ok", file=fn, src=best[2], url=best[3], orig=list(best[1].size), mode=mode, color=col, light=light, lowres=low)
    return rec

def main():
    if Image is None:
        print("logos: Pillow no disponible, se omiten los logos"); return
    bj = json.load(open(D/"build.json")); E = {e["slug"]: e for e in bj["ents"]}
    extra = {k: v for k, v in json.load(open(D/"brand_domains.json")).items() if not k.startswith("_")}
    cache = json.load(open(MAP)) if MAP.exists() else {}
    doms = cache.get("domains", {})
    ents, brands, todo = {}, {}, {}
    for e in bj["ents"]:
        h = pick_host(e["w"])
        ents[e["slug"]] = {"domain": h, "from": "registro ESMA (web)"} if h else {"domain": None}
        if h: todo.setdefault(h, None)
    for b in bj["brands"]:
        h = None; frm = None
        for s in b["e"]:
            h = pick_host(E[s]["w"], b["b"])
            if h: frm = "registro ESMA (web de %s)" % E[s]["l"]; break
        verify = None
        if not h and b["b"] in extra:
            x = extra[b["b"]]; x = x if isinstance(x, dict) else {"domain": x}
            h, frm, verify = x["domain"], "data/brand_domains.json (verificado)", (b["b"], x.get("verifiedManual"))
        brands[b["b"]] = {"domain": h, "from": frm}
        if h: todo[h] = verify if verify else todo.get(h)
    retry = "--retry" in sys.argv
    only = next((a.split("=", 1)[1].split(",") for a in sys.argv if a.startswith("--only=")), None)
    def stale(h):
        r = doms.get(h)
        if only is not None: return h in only
        if not r: return True
        if r.get("status") == "ok": return not (OUT/r["file"]).exists()
        age = (datetime.date.today() - datetime.date.fromisoformat(r.get("checked", "2000-01-01"))).days
        return retry or age >= RETRY_DAYS
    work = [h for h in todo if stale(h)]
    print(f"logos: {len(todo)} dominios, {len(work)} por descargar")
    socket.setdefaulttimeout(15)
    def job(h):
        try: return h, get_logo(h, *(todo[h] or (None, None)))
        except Exception as ex: return h, {"domain": h, "checked": TODAY, "status": "error", "why": repr(ex)[:200]}
    with ThreadPoolExecutor(12) as ex:
        for h, r in ex.map(job, work):
            doms[h] = r; print(" ", r["status"].ljust(10), h, r.get("src") or r.get("why", "")[:90])
    # mapas finales: slug -> logo
    def res(x):
        h = x["domain"]; r = doms.get(h) if h else None
        ok = r and r.get("status") == "ok" and (OUT/r["file"]).exists()
        return {"domain": h, "from": x.get("from"), "logo": r["file"] if ok else None, "mode": r.get("mode") if ok else None, "lowres": r.get("lowres") if ok else None,
                "light": r.get("light") if ok else None, "color": r.get("color") if ok else None, "status": (r or {}).get("status", "sin dominio")}
    manual = cache.get("overrides", {})
    out = {"_ayuda": "Generado por scripts/logos.py. 'domains' es la caché por dominio (se reintenta a los %d días si falló). 'overrides': {\"marca o slug\": null} para forzar monograma." % RETRY_DAYS,
           "updated": TODAY, "overrides": manual,
           "brands": {k: res(v) for k, v in brands.items()}, "ents": {k: res(v) for k, v in ents.items()}, "domains": {k: v for k, v in sorted(doms.items()) if k in todo}}
    for grp in ("brands", "ents"):
        for k in list(out[grp]):
            if k in manual and manual[k] is None: out[grp][k].update(logo=None, status="override")
    used = {v["logo"] for g in ("brands", "ents") for v in out[g].values() if v["logo"]}
    for f in list(OUT.glob("*.png")) + list(OUT.glob("*.svg")):
        if f.name not in used: f.unlink()
    json.dump(out, open(MAP, "w"), ensure_ascii=False, indent=1)
    nb = sum(1 for v in out["brands"].values() if v["logo"]); ne = sum(1 for v in out["ents"].values() if v["logo"])
    print(f"logos: marcas {nb}/{len(brands)} con logo, proveedores {ne}/{len(ents)} con logo")

if __name__ == "__main__":
    try: main()
    except Exception as ex:
        print("logos: aviso, no se pudieron actualizar los logos:", repr(ex))
