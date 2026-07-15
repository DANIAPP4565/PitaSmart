# app.py  ·  EUROPHARMA — PitaSmart
# Punto de entrada de la web multipágina en Streamlit.
# Ejecutar:  streamlit run app.py
#
# Arquitectura:
#   core.py    -> motor clínico (lógica intacta del app original) + helpers de estado
#   theme.py   -> identidad visual Europharma (paleta, hero, tarjetas, CSS)
#   pages/*.py -> una página por sección, navegadas con st.navigation

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

# ------------------------------------------------------------------
# Sidebar: marca + configuración global (compartida por todas las páginas)
# ------------------------------------------------------------------
with st.sidebar:
    theme.brand_sidebar()

pages = {
    "Plataforma": [
        st.Page("pages/1_Inicio.py", title="Inicio", icon="🏠", default=True),
    ],
    "Flujo clínico": [
        st.Page("pages/2_Importar.py", title="Importar laboratorio", icon="📥"),
        st.Page("pages/3_Decision.py", title="Decisión y meta", icon="🧭"),
        st.Page("pages/4_Seguimiento.py", title="Seguimiento", icon="📈"),
        st.Page("pages/5_Informe.py", title="Informe y descargas", icon="📄"),
    ],
    "Conocimiento": [
        st.Page("pages/6_Evidencia.py", title="Base clínica y evidencia", icon="📚"),
        st.Page("pages/7_Paciente.py", title="Texto para paciente", icon="👤"),
        st.Page("pages/8_Fuentes.py", title="Fuentes y uso", icon="ℹ️"),
    ],
}

pg = st.navigation(pages, position="sidebar")

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
