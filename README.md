# PitaSmart

Plataforma Streamlit de apoyo a la decisión clínica para pitavastatina, brecha hasta la meta de LDL-C, comparación de estrategias y seguimiento de respuesta.

## Archivos que deben quedar en la raíz

```text
app.py
requirements.txt
README.md
.gitignore
```

No suba el ZIP al repositorio: descomprímalo y cargue estos archivos directamente.

## Despliegue en repositorio público

1. Cree en GitHub un repositorio **Public** vacío.
2. Suba únicamente los archivos de este paquete a la rama `main`.
3. En Streamlit Community Cloud seleccione **Create app**.
4. Configure:

```text
Repository: SU_USUARIO/SU_REPOSITORIO
Branch: main
Main file path: app.py
Python: 3.12
```

5. No hace falta agregar Secrets para iniciar la aplicación.

## Instalación local

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```

## Privacidad

El repositorio es público, por lo que no deben subirse PDFs de pacientes, bases de datos, exportaciones, credenciales, claves API ni `secrets.toml`. La aplicación procesa el PDF cargado en memoria durante la sesión y no incluye persistencia clínica en el repositorio.

## Nota clínica

Herramienta educativa y de apoyo para profesionales. No reemplaza juicio clínico, historia clínica completa, guías vigentes ni prospecto aprobado local.
