from playwright.sync_api import sync_playwright
B="http://localhost:8765/"
shots=[("home",""),("busqueda-coinbase","?q=coinbase"),("busqueda-binance","?q=binance"),("busqueda-bbva","?q=bbva"),("cambios","cambios.html"),("ficha-bit2me","p/bitcoinforme-s-l.html"),("metodologia","metodologia.html")]
with sync_playwright() as p:
    b=p.chromium.launch()
    for dev,vp,scheme in [("desktop",{"width":1280,"height":900},"light"),("mobile",{"width":390,"height":844},"light"),("desktop-dark",{"width":1280,"height":900},"dark")]:
        ctx=b.new_context(viewport=vp,color_scheme=scheme,device_scale_factor=2 if "mobile" in dev else 1,is_mobile="mobile" in dev)
        pg=ctx.new_page()
        for n,u in shots:
            if dev=="desktop-dark" and n not in("home","busqueda-coinbase","ficha-bit2me"):continue
            pg.goto(B+u);pg.wait_for_timeout(700);pg.screenshot(path=f"screens/{dev}-{n}.png",full_page=n not in("cambios",))
        if dev=="desktop":
            pg.goto(B);pg.fill("#q","bit");pg.wait_for_timeout(500);pg.screenshot(path="screens/desktop-autocomplete.png")
        ctx.close()
    b.close()
