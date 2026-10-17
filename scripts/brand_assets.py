#!/usr/bin/env python3
"""Identidad visual de Registro MiCA: marca SVG, favicons (svg, ico, apple-touch-icon, PWA) y manifest.
Se ejecuta a mano cuando cambia la marca (necesita Playwright para rasterizar): python scripts/brand_assets.py
La imagen OG la genera scripts/og.py (también a mano)."""
import json, pathlib, io
R = pathlib.Path(__file__).resolve().parent.parent; A = R/"site/assets"; (A/"brand").mkdir(parents=True, exist_ok=True)
GRAD = '<linearGradient id="g" x1="8" y1="4" x2="58" y2="62" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#34d399"/><stop offset=".5" stop-color="#0ea371"/><stop offset="1" stop-color="#0369a1"/></linearGradient><radialGradient id="h" cx="16" cy="6" r="46" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#fff" stop-opacity=".32"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>'
GLYPH = '<rect x="14" y="15" width="24" height="6" rx="3" fill="#fff" fill-opacity=".62"/><rect x="14" y="26" width="15" height="6" rx="3" fill="#fff" fill-opacity=".62"/><path d="M21 41.5l7.5 7.5L49 25" fill="none" stroke="#fff" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/>'
GLYPH_S = '<path d="M17 33l10 10L48 21" fill="none" stroke="#fff" stroke-width="9" stroke-linecap="round" stroke-linejoin="round"/>'
def mark(rx=16, glyph=GLYPH, pad=0):
    inner = f'<g transform="translate({pad} {pad}) scale({(64 - 2 * pad) / 64})">{glyph}</g>' if pad else glyph
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><defs>{GRAD}</defs><rect width="64" height="64" rx="{rx}" fill="url(#g)"/><rect width="64" height="64" rx="{rx}" fill="url(#h)"/>{inner}</svg>'
WORD = lambda dark: f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 64"><defs>{GRAD}<linearGradient id="t" x1="0" x2="1"><stop offset="0" stop-color="{'#34d399' if dark else '#059669'}"/><stop offset="1" stop-color="{'#38bdf8' if dark else '#0284c7'}"/></linearGradient></defs>
<rect width="64" height="64" rx="16" fill="url(#g)"/><rect width="64" height="64" rx="16" fill="url(#h)"/>{GLYPH}
<text x="80" y="43" font-family="Inter,ui-sans-serif,system-ui,sans-serif" font-size="31" font-weight="700" letter-spacing="-1" fill="{'#eef2f7' if dark else '#0b1220'}">Registro <tspan fill="url(#t)" font-weight="800">MiCA</tspan></text></svg>'''
files = {"brand/mark.svg": mark(), "favicon.svg": mark(), "brand/wordmark.svg": WORD(False), "brand/wordmark-dark.svg": WORD(True)}
for k, v in files.items(): (A/k).write_text(v)
from playwright.sync_api import sync_playwright
from PIL import Image
def render(svg, size):
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={"width": size, "height": size})
        pg.set_content(f'<html><body style="margin:0;background:transparent">{svg.replace("<svg ", f"<svg width=\"{size}\" height=\"{size}\" ", 1)}</body></html>')
        png = pg.screenshot(omit_background=True, clip={"x": 0, "y": 0, "width": size, "height": size}); b.close()
    return Image.open(io.BytesIO(png)).convert("RGBA")
render(mark(rx=0), 180).save(A/"brand/apple-touch-icon.png", optimize=True)          # iOS redondea las esquinas
render(mark(), 192).save(A/"brand/icon-192.png", optimize=True)
render(mark(), 512).save(A/"brand/icon-512.png", optimize=True)
render(mark(rx=0, pad=10), 512).save(A/"brand/icon-maskable-512.png", optimize=True)
ico = [render(mark(rx=4, glyph=GLYPH_S), 16), render(mark(rx=8), 32), render(mark(rx=12), 48)]
ico[2].save(R/"site/favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)], append_images=ico[:2])
(R/"site/site.webmanifest").write_text(json.dumps({"name": "Registro MiCA", "short_name": "Registro MiCA",
    "description": "Comprueba si un exchange o app cripto puede operar en España según el registro MiCA de ESMA.", "lang": "es",
    "start_url": "./", "scope": "./", "display": "standalone", "background_color": "#ffffff", "theme_color": "#059669",
    "icons": [{"src": "assets/brand/icon-192.png", "sizes": "192x192", "type": "image/png"}, {"src": "assets/brand/icon-512.png", "sizes": "512x512", "type": "image/png"},
              {"src": "assets/brand/icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"}]}, ensure_ascii=False, indent=1))
print("ok: marca, favicons y manifest")
