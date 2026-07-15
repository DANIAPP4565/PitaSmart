# app.py  ·  EUROPHARMA — PitaSmart
# Punto de entrada de la web multipágina en Streamlit.
# Ejecutar:  streamlit run app.py
#
# Arquitectura:
#   core.py    -> motor clínico (lógica intacta del app original) + helpers de estado
#   theme.py   -> identidad visual Europharma (paleta, hero, tarjetas, CSS)
#   pages/*.py -> una página por sección, navegadas con st.navigation

from pathlib import Path
import streamlit as st

st.set_page_config(
    page_title="Europharma · PitaSmart",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded",
)

import core
import theme

theme.inject_theme()
core.init_state()

# Rutas absolutas basadas en la ubicación real de app.py.
# Esto evita el error "The file `1_Inicio.py` could not be found" en Streamlit Cloud,
# donde el directorio de trabajo puede no coincidir con la carpeta del proyecto.
BASE = Path(__file__).resolve().parent
PDIR = BASE / "pages"

# ------------------------------------------------------------------
# Sidebar: marca + configuración global (compartida por todas las páginas)
# ------------------------------------------------------------------
with st.sidebar:
    theme.brand_sidebar()

p_inicio = st.Page(PDIR / "1_Inicio.py", title="Inicio", icon="🏠", default=True)
p_importar = st.Page(PDIR / "2_Importar.py", title="Importar laboratorio", icon="📥")
p_decision = st.Page(PDIR / "3_Decision.py", title="Decisión y meta", icon="🧭")
p_seguimiento = st.Page(PDIR / "4_Seguimiento.py", title="Seguimiento", icon="📈")
p_informe = st.Page(PDIR / "5_Informe.py", title="Informe y descargas", icon="📄")
p_evidencia = st.Page(PDIR / "6_Evidencia.py", title="Base clínica y evidencia", icon="📚")
p_paciente = st.Page(PDIR / "7_Paciente.py", title="Texto para paciente", icon="👤")
p_fuentes = st.Page(PDIR / "8_Fuentes.py", title="Fuentes y uso", icon="ℹ️")

# Objetos de página disponibles para st.page_link dentro de cada página
# (evita cualquier ambigüedad de rutas relativas al navegar).
st.session_state["_nav"] = {
    "inicio": p_inicio, "importar": p_importar, "decision": p_decision,
    "seguimiento": p_seguimiento, "informe": p_informe, "evidencia": p_evidencia,
    "paciente": p_paciente, "fuentes": p_fuentes,
}

pg = st.navigation(
    {
        "Plataforma": [p_inicio],
        "Flujo clínico": [p_importar, p_decision, p_seguimiento, p_informe],
        "Conocimiento": [p_evidencia, p_paciente, p_fuentes],
    },
    position="sidebar",
)

with st.sidebar:
    st.divider()
    st.markdown("### ⚙️ Configuración")
    st.text_input("Autor / firma", key="cfg_author")
    st.selectbox("Marco de referencia", core.REGULATORY_OPTIONS, key="cfg_regulatory")
    st.selectbox("Categoría de riesgo", list(core.OBJETIVOS_LDL.keys()), key="cfg_risk_category")
    st.number_input(
        "Objetivo LDL-C personalizado, mg/dL", 20, 200,
        int(core.OBJETIVOS_LDL.get(st.session_state.get("cfg_risk_category", "Alto riesgo"), 70)),
        5, key="cfg_custom_goal",
        help="Sólo se aplica cuando la categoría de riesgo es 'Personalizado'.",
    )
    st.divider()
    st.caption("🔐 El PDF se lee en memoria y no se guarda. Se exportan sólo datos anonimizados/análisis.")

pg.run()
