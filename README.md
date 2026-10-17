# ¿Está autorizado?

Buscador en español del registro MiCA de ESMA: comprueba si un exchange o plataforma cripto tiene licencia (Art. 59) o notificación (Art. 60) y si puede operar en España.

Web: https://fjgnpa.github.io/esta-autorizado/

## Uso
- `python3 scripts/refresh.py` — descarga datos, guarda instantánea en `data/snapshots/`, clasifica y genera `site/`.
- `python3 scripts/refresh.py --offline` — regenera con los datos ya descargados.
- `python3 scripts/build_site.py` — solo regenera el HTML desde `data/build.json`.
- Local: `python3 -m http.server 8765 -d site`
- GitHub Actions (`.github/workflows/pages.yml`) refresca cada lunes y bajo demanda, y publica en GitHub Pages.

## Fuentes y atribución
- **ESMA**, registro provisional MiCA (CASPS.csv, NCASP.csv) y registro MiFID/AIFMD/UCITS — fuente primaria.
- **BCE**, lista de instituciones financieras monetarias (entidades de crédito).
- **CNMV**, relación de proveedores de servicios de criptoactivos.
- **cryptocodes.eu**, análisis de notificaciones Art. 60 (30/09/2026).
- **CASP Tracker** (https://casptracker.eu) — fuente de respaldo e histórico de instantáneas, datos bajo licencia **CC BY 4.0**: "Source: CASP Tracker (casptracker.eu), based on the ESMA MiCA interim registers." https://creativecommons.org/licenses/by/4.0/

Información divulgativa, no asesoramiento financiero. Confirma siempre en ESMA y CNMV.
