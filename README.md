# PitaSmart — despliegue de rescate sin requirements.txt

Este paquete elimina deliberadamente `requirements.txt` para evitar que
Streamlit Community Cloud quede detenido en **Processing dependencies**.

## Archivos a subir

- `app.py`
- `README.md`

No debe existir en el repositorio ningún archivo llamado:

- `requirements.txt`
- `uv.lock`
- `Pipfile`
- `environment.yml`
- `pyproject.toml`
- `packages.txt`

## Configuración en Streamlit

- Branch: `main`
- Main file path: `app.py`

La app inicia con el entorno base de Streamlit. La evaluación clínica,
la carga manual, la clasificación y el seguimiento funcionan.

Funciones opcionales que pueden no estar disponibles en este primer arranque:

- importación PDF mediante pypdf;
- informe PDF mediante reportlab;
- exportación XLSX mediante openpyxl;
- gráficos Plotly.

La exportación de datos cae automáticamente a CSV si XLSX no está disponible.
Después de confirmar que despliega, las dependencias opcionales pueden agregarse
de una en una para identificar cuál bloquea Community Cloud.
