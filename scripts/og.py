"""Imagen OG (1200x630) de Registro MiCA: /tmp/pwv/bin/python scripts/og.py  (a mano; necesita Playwright)."""
import json, pathlib
from playwright.sync_api import sync_playwright
R = pathlib.Path(__file__).resolve().parent.parent
M = json.load(open(R/"data/build.json"))["meta"]; L = json.load(open(R/"data/logos.json"))["brands"]
h = (R/"scripts/og.html").read_text().replace("{{ES}}", str(M["es"])).replace("{{N}}", str(M["count"])).replace("{{B}}", str(M["brands"])).replace("{{LOGO}}", L["Bit2Me"]["logo"])
tmp = R/"scripts/_og.html"; tmp.write_text(h)
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1200, "height": 630}); pg.goto(tmp.as_uri()); pg.wait_for_timeout(600)
    pg.screenshot(path=str(R/"site/assets/og.png")); b.close()
tmp.unlink(); print("og.png ok")
