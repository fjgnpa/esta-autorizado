# Registro MiCA

_Proyecto independiente; no es el registro oficial de ESMA ni de la CNMV. Antes llamado «¿Está autorizado?»._

Buscador en español del registro MiCA de ESMA: comprueba si un exchange o plataforma cripto tiene licencia (Art. 59) o notificación (Art. 60) y si puede operar en España.

Web: https://fjgnpa.github.io/esta-autorizado/

## Uso
- `python3 scripts/refresh.py` — descarga datos, **los valida** y solo entonces guarda la instantánea en `data/snapshots/`, clasifica y genera `site/`.
  Aborta sin escribir nada (y el workflow no publica) si faltan columnas obligatorias, hay menos de 250 proveedores, el recuento cae más de un 15 % o sube más de un 30 %, desaparecen entidades ancla (Bitcoinforme, Bitpanda, Coinbase, Payward, BBVA), desaparecen muchas entidades con España o hay nombres con `<`/`>`.
  `--force` publica pese a esos avisos; `--allow-fallback` permite usar CASP Tracker si ESMA no responde (por defecto se aborta).
- `python3 scripts/refresh.py --offline` — regenera con los datos ya descargados (re-lee `data/sources/CASPS.csv`, incluida la base legal).
- `python3 scripts/build_site.py` — solo regenera el HTML desde `data/build.json`.
- Local: `python3 -m http.server 8765 -d site`
- GitHub Actions (`.github/workflows/pages.yml`) refresca cada lunes y bajo demanda (opciones `offline` y `force`), y publica en GitHub Pages.
  Permisos mínimos por job (build: solo lectura; commit: escritura de contenido; deploy: Pages), acciones fijadas por SHA (Dependabot las actualiza).

## Clasificación (resumen; detalle en metodologia.html)
1. `ac_legal_basis` de ESMA: «Article 63» → licencia CASP (Art. 59); «Article 60» → notificación (Art. 60). Prevalece siempre.
2. Si está vacío: `data/overrides.json` (correcciones verificadas con fuente) y después la inferencia (comentarios ESMA, cryptocodes.eu, CNMV, BCE, registro MiFID).
3. «Puede operar en España» exige autorización vigente (sin fecha de fin pasada), ya iniciada (fecha de inicio de ESMA alcanzada; si es futura: «autorizado, empieza el dd/mm», fuera de los activos y de las descargas como `activo`, con `inicio_pendiente`) y España como origen o país notificado. `build_site.py` recalcula este estado con la fecha del build.
- `data/editorial.json`: fichas editoriales de las marcas más buscadas (solo hechos con fuente primaria y fecha; el estado MiCA, el supervisor y la fecha salen de ESMA). Revisa `reviewed` al editarlas.
4. Marcas sin sociedad: monederos de autocustodia → «No aplica»; bancos/pagos → «Sin servicios cripto MiCA en el registro»; resto → «No figura».
- `data/slugs.json` fija la URL de cada ficha por LEI (o nombre legal): no cambia aunque cambie el orden del registro. Las sociedades que desaparecen conservan su ficha («ya no figura», `noindex`).

## Dominio
- `data/config.json`: `useCustomDomain: false` → `siteBaseGithub` (github.io). Para pasar a `registromica.es` basta `useCustomDomain: true` (o la variable de repositorio `SITE_BASE`), **después** de configurar el dominio en Pages y el DNS. Canónicas, sitemap, robots.txt, OG y textos legales salen de esa base. `deploy/CNAME` no se usa todavía.

## Logos e identidad visual
- `python3 scripts/logos.py` — descarga una vez el icono oficial de cada dominio (portada: apple-touch-icon/icon/manifest; respaldo: favicon.ico, favicons de DuckDuckGo y Google), lo normaliza a PNG 128×128 en `site/assets/logos/` y guarda el mapa marca/ficha → dominio → logo en `data/logos.json`. Detecta iconos genéricos, vacíos, marcadores de posición o diminutos (<32 px) y deja monograma. Solo baja dominios nuevos (o fallidos hace >30 días; `--retry` fuerza, `--only=dominio,...` rehace). Lo llama `refresh.py` y nunca rompe el build.
- Dominios: los de la web del registro ESMA; para marcas sin web en el registro, `data/brand_domains.json` (verificados en su portada o anotados con `verifiedManual`). Para forzar monograma: `"overrides": {"Marca o slug": null}` en `data/logos.json`.
- La web no enlaza a terceros para logos ni tipografía (Inter, SIL OFL, en `site/assets/fonts/`).
- Analítica: GoatCounter sin cookies (`registromica.goatcounter.com`), script versionado `count.v5.js` con SRI y CSP limitada a `gc.zgo.at` (script) y `registromica.goatcounter.com` (connect/img). Constantes `GC_*` en `scripts/build_site.py`.
- Marca y favicons: `/tmp/pwv/bin/python scripts/brand_assets.py`; imagen OG: `/tmp/pwv/bin/python scripts/og.py` (necesitan Playwright, se ejecutan a mano).
- Capturas: `/tmp/pwv/bin/python scripts/screens.py` con el sitio servido en `localhost:8765` → `screens/v3-*.png`.

## Fuentes y atribución
- **ESMA**, registro provisional MiCA (CASPS.csv, NCASP.csv) y registro MiFID/AIFMD/UCITS — fuente primaria.
- **BCE**, lista de instituciones financieras monetarias (entidades de crédito).
- **CNMV**, relación de proveedores de servicios de criptoactivos.
- **cryptocodes.eu**, análisis de notificaciones Art. 60 (30/09/2026).
- **CASP Tracker** (https://casptracker.eu) — fuente de respaldo e histórico de instantáneas, datos bajo licencia **CC BY 4.0**: "Source: CASP Tracker (casptracker.eu), based on the ESMA MiCA interim registers." https://creativecommons.org/licenses/by/4.0/

Información divulgativa, no asesoramiento financiero. Confirma siempre en ESMA y CNMV.

## Newsletter (Beehiiv) y datos legales
Edita `data/config.json`:
- `beehiivSubscribeUrl`: página pública de suscripción. La web solo enlaza a ella (pestaña nueva): no carga scripts, iframes ni cookies de Beehiiv. Beehiiv no rellena el correo por URL, así que no se pide aquí.
- `email`: contacto del proyecto que aparece en Aviso legal y Privacidad. No se publican datos personales del titular.
- LSSI: el proyecto es personal, sin ánimo de lucro ni actividad económica; por decisión del titular el aviso legal no publica nombre ni domicilio y da un correo de contacto. Si el sitio pasara a tener actividad económica (publicidad, afiliación, patrocinio), habría que añadir los datos del art. 10 LSSI-CE.
- `data/casps.json`: copia del JSON de CASP Tracker (CC BY 4.0) usada como referencia del formato del respaldo; no se publica en la web.
Haz push a `main`: el workflow regenera y publica.

## SEO
- Páginas: portada, `marcas.html`, `proveedores.html` (lista completa con enlaces a todas las fichas), `guia-mica.html` (guía con fuentes oficiales; revisar `GUIDE_REV` en `scripts/build_site.py` si se edita), fichas `p/` y `marca/`. Todas en `sitemap.xml`; las bajas llevan `noindex`.
- IndexNow: la clave está en `data/config.json` (`indexNowKey`) y se publica en `https://registromica.es/<clave>.txt`. No se envía ningún aviso automáticamente. Para avisar a mano tras un cambio:
  `curl "https://api.indexnow.org/indexnow?url=https://registromica.es/&key=<clave>"`
