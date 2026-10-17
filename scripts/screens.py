"""Capturas v3: python scripts/screens.py (con el sitio servido en localhost:8765). Uso: /tmp/pwv/bin/python scripts/screens.py [nombre...]"""
import sys
from playwright.sync_api import sync_playwright
B = "http://localhost:8765/"
SHOTS = [("home", ""), ("busqueda-binance", "?q=binance"), ("busqueda-bit", "?q=bit"), ("marca-binance", "marca/binance.html"), ("marca-bit2me", "marca/bit2me.html"),
         ("ficha-bit2me", "p/bitcoinforme-s-l.html"), ("marcas", "marcas.html"),
         ("ficha-decubate", "p/decubate-b-v.html"), ("ficha-tradu", "p/stratos-europe-ltd.html"), ("marca-ledger", "marca/ledger.html"), ("marca-coinbase", "marca/coinbase.html"),
         ("busqueda-binanse", "?q=binanse"), ("busqueda-sin-resultados", "?q=bitpandq%20xx"), ("metodologia", "metodologia.html"), ("cambios", "cambios.html"), ("404", "404.html")]
only = sys.argv[1:]
with sync_playwright() as p:
    b = p.chromium.launch()
    for dev, vp, scheme in [("desktop", {"width": 1280, "height": 900}, "light"), ("desktop-dark", {"width": 1280, "height": 900}, "dark"),
                            ("mobile", {"width": 390, "height": 844}, "light"), ("mobile-dark", {"width": 390, "height": 844}, "dark")]:
        m = "mobile" in dev
        ctx = b.new_context(viewport=vp, color_scheme=scheme, device_scale_factor=2 if m else 1, is_mobile=m, has_touch=m, reduced_motion="no-preference")
        pg = ctx.new_page()
        for n, u in SHOTS:
            if only and n not in only: continue
            pg.goto(B + u, wait_until="networkidle"); pg.wait_for_timeout(2500)
            pg.evaluate("document.querySelectorAll('.mq-row').forEach(r=>r.style.animationPlayState='paused')")
            pg.screenshot(path=f"screens/v3-{dev}-{n}.png", full_page=True)
            if n == "home": pg.screenshot(path=f"screens/v3-{dev}-home-viewport.png")
        if not only or "autocomplete" in only:
            pg.goto(B, wait_until="networkidle"); pg.fill("#q", "bit"); pg.wait_for_timeout(600); pg.screenshot(path=f"screens/v3-{dev}-autocomplete.png")
        ctx.close()
    b.close()
