# Registro MiCA

_Proyecto independiente; no es el registro oficial de ESMA ni de la CNMV. Antes llamado «¿Está autorizado?»._

Buscador en español del registro MiCA de ESMA: comprueba si un exchange o plataforma cripto tiene licencia (Art. 59) o notificación (Art. 60) y si puede operar en España.

Web: https://fjgnpa.github.io/esta-autorizado/

## Uso
- `python3 scripts/refresh.py` — descarga datos, guarda instantánea en `data/snapshots/`, clasifica y genera `site/`.
- `python3 scripts/refresh.py --offline` — regenera con los datos ya descargados.
- `python3 scripts/build_site.py` — solo regenera el HTML desde `data/build.json`.
- Local: `python3 -m http.server 8765 -d site`
- GitHub Actions (`.github/workflows/pages.yml`) refresca cada lunes y bajo demanda, y publica en GitHub Pages.

## Logos e identidad visual
- `python3 scripts/logos.py` — descarga una vez el icono oficial de cada dominio (portada: apple-touch-icon/icon/manifest; respaldo: favicon.ico, favicons de DuckDuckGo y Google), lo normaliza a PNG 128×128 en `site/assets/logos/` y guarda el mapa marca/ficha → dominio → logo en `data/logos.json`. Detecta iconos genéricos, vacíos, marcadores de posición o diminutos (<32 px) y deja monograma. Solo baja dominios nuevos (o fallidos hace >30 días; `--retry` fuerza, `--only=dominio,...` rehace). Lo llama `refresh.py` y nunca rompe el build.
- Dominios: los de la web del registro ESMA; para marcas sin web en el registro, `data/brand_domains.json` (verificados en su portada o anotados con `verifiedManual`). Para forzar monograma: `"overrides": {"Marca o slug": null}` en `data/logos.json`.
- La web no enlaza a terceros para logos ni tipografía (Inter, SIL OFL, en `site/assets/fonts/`).
- Marca y favicons: `/tmp/pwv/bin/python scripts/brand_assets.py`; imagen OG: `/tmp/pwv/bin/python scripts/og.py` (necesitan Playwright, se ejecutan a mano).
- Capturas: `/tmp/pwv/bin/python scripts/screens.py` con el sitio servido en `localhost:8765` → `screens/v2-*.png`.

## Fuentes y atribución
- **ESMA**, registro provisional MiCA (CASPS.csv, NCASP.csv) y registro MiFID/AIFMD/UCITS — fuente primaria.
- **BCE**, lista de instituciones financieras monetarias (entidades de crédito).
- **CNMV**, relación de proveedores de servicios de criptoactivos.
- **cryptocodes.eu**, análisis de notificaciones Art. 60 (30/09/2026).
- **CASP Tracker** (https://casptracker.eu) — fuente de respaldo e histórico de instantáneas, datos bajo licencia **CC BY 4.0**: "Source: CASP Tracker (casptracker.eu), based on the ESMA MiCA interim registers." https://creativecommons.org/licenses/by/4.0/

Información divulgativa, no asesoramiento financiero. Confirma siempre en ESMA y CNMV.

## Newsletter (Beehiiv) y datos legales
Edita `data/config.json`:
- `beehiivEmbedUrl`: URL del iframe del formulario de Beehiiv (Grow → Subscribe Forms → Embed). Con `null` se muestra el formulario de prueba.
- `email`: contacto del proyecto que aparece en Aviso legal y Privacidad (ahora `[EMAIL]`). No se publican datos personales del titular.
Haz push a `main`: el workflow regenera y publica.
