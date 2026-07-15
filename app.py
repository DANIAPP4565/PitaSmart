# app.py  ·  EUROPHARMA — PitaSmart
# Entrada multipágina en Streamlit basada en FUNCIONES (no requiere carpeta pages/).
# Ejecutar:  streamlit run app.py
#
# Solo se necesitan 3 archivos en el repositorio/carpeta:
#   app.py    -> este archivo (navegación + páginas como funciones)
#   core.py   -> motor clínico (lógica intacta del app original)
#   theme.py  -> identidad visual Europharma
# No hace falta ninguna subcarpeta pages/.

import json
from datetime import datetime

import pandas as pd
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


def _nav():
    return st.session_state.get("_nav", {})


# ======================================================================
# PÁGINA · INICIO
# ======================================================================
def page_inicio():
    NAV = _nav()
    data, goal = core.build_base_data()
    gap = core.required_ldl_reduction(data["ldl"], goal)

    theme.page_hero(
        title="PitaSmart",
        subtitle="Plataforma de decisión clínica de EUROPHARMA para seleccionar la estrategia con pitavastatina, "
                 "cuantificar la brecha a meta de LDL-C y seguir la respuesta del paciente.",
        eyebrow="Laboratorio clínico · Cardiometabolismo",
        icon="💊",
    )

    st.markdown(
        f'<span class="badge">{core.APP_VERSION}</span>'
        f'<span class="ep-chip ep-chip-teal">Actualización {core.APP_DATE}</span>'
        f'<span class="badge">{st.session_state.get("cfg_regulatory","")}</span>',
        unsafe_allow_html=True,
    )

    st.write("")
    theme.section("Panorama del caso activo", "Valores vigentes que la plataforma usará en la evaluación.")
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        theme.stat_card("LDL-C actual", f"{data['ldl']:.0f} mg/dL", f"Colesterol total {data['ct']:.0f}", "🩸")
    with k2:
        theme.stat_card("Meta LDL-C", f"< {goal} mg/dL", data["risk_category"], "🎯")
    with k3:
        theme.stat_card("No-HDL-C", f"{data['non_hdl']:.0f} mg/dL", "Marcador complementario", "📊")
    with k4:
        theme.stat_card("Reducción a meta", f"{gap['percentage']:.0f}%", f"{gap['absolute']:.0f} mg/dL a recortar", "📉")

    st.caption(f"Fuente de datos actual: {data.get('data_source','Carga manual')}")

    st.write("")
    theme.goal_meter(data["ldl"], data["ldl"], goal)

    st.write("")
    theme.section("Recorrido de la plataforma", "Cada módulo es una página; el flujo recomendado va de izquierda a derecha.")

    r1 = st.columns(4)
    items1 = [
        ("📥", "Importar laboratorio", "Leé un PDF o texto, corregí y confirmá los valores.", "importar"),
        ("🧭", "Decisión y meta", "Brecha a meta, comparador de estrategias e interacciones.", "decision"),
        ("📈", "Seguimiento", "Compará respuesta observada vs. esperada y tolerabilidad.", "seguimiento"),
        ("📄", "Informe", "Generá y descargá el informe en MD, PDF, Excel o JSON.", "informe"),
    ]
    for col, (ico, ttl, desc, key) in zip(r1, items1):
        with col:
            theme.nav_card(ico, ttl, desc)
            if NAV.get(key) is not None:
                st.page_link(NAV[key], label=f"Abrir {ttl}", icon="➡️")

    st.write("")
    r2 = st.columns(4)
    items2 = [
        ("📚", "Base y evidencia", "Interacciones, escenarios y matriz de evidencia.", "evidencia"),
        ("👤", "Texto paciente", "Material educativo editable y descargable.", "paciente"),
        ("ℹ️", "Fuentes y uso", "Referencias, instalación y notas institucionales.", "fuentes"),
        ("🧪", "Metodología", "Extracción multimotor con confianza y plausibilidad.", "importar"),
    ]
    for col, (ico, ttl, desc, key) in zip(r2, items2):
        with col:
            theme.nav_card(ico, ttl, desc)
            if NAV.get(key) is not None:
                st.page_link(NAV[key], label=f"Abrir {ttl}", icon="➡️")

    st.write("")
    st.warning(
        "Herramienta de apoyo educativo para profesionales. No reemplaza el juicio clínico, la historia clínica "
        "completa, las guías vigentes ni el prospecto aprobado local.",
        icon="⚠️",
    )
    theme.footer(core.APP_VERSION, core.APP_DATE, st.session_state.get("cfg_regulatory", ""))


# ======================================================================
# PÁGINA · IMPORTAR LABORATORIO
# ======================================================================
def page_importar():
    NAV = _nav()
    theme.page_hero(
        title="Importar laboratorio",
        subtitle="Leé el PDF o el texto del laboratorio, revisá cada valor con su confianza y plausibilidad, "
                 "corregí lo dudoso y confirmá qué usará la evaluación.",
        eyebrow="Paso 1 del flujo clínico",
        icon="📥",
    )
    st.info(
        "La app no convierte una lectura dudosa en un dato clínico. Cada valor extraído muestra confianza, "
        "plausibilidad y una lectura orientativa antes de aplicarse al formulario."
    )

    theme.section("Flujo en 4 pasos")
    s1, s2, s3, s4 = st.columns(4)
    for col, num, title, detail in [
        (s1, "Paso 1", "Subir", "PDF o texto copiado"),
        (s2, "Paso 2", "Extraer", "Lectura multimétodo"),
        (s3, "Paso 3", "Revisar", "Corregir y elegir qué aplicar"),
        (s4, "Paso 4", "Interpretar", "Resultado clínico integrado"),
    ]:
        with col:
            st.markdown(
                f'<div class="step-card"><div class="step-num">{num}</div>'
                f'<div class="step-title">{title}</div><div>{detail}</div></div>',
                unsafe_allow_html=True,
            )

    st.write("")
    theme.section("Paso 1-2 · Origen y extracción")
    source_tab_pdf, source_tab_text = st.tabs(["📄 PDF", "📋 Texto copiado"])

    with source_tab_pdf:
        uploaded_pdf = st.file_uploader("Seleccionar PDF de laboratorio", type=["pdf"], key="lab_pdf_uploader")
        c1, c2 = st.columns([2, 1])
        with c1:
            process_pdf = st.button("🔎 Extraer resultados del PDF", width="stretch", disabled=uploaded_pdf is None)
        with c2:
            clear_pdf = st.button("🧹 Reiniciar importación", width="stretch")

        if clear_pdf:
            st.session_state["extracted_values"] = {}
            st.session_state["extraction_evidence"] = {}
            st.session_state["extraction_diagnostics"] = []
            st.session_state["pdf_methods"] = []
            st.session_state["raw_text_len"] = 0
            st.session_state["anon_preview"] = []
            st.session_state["data_source"] = "Carga manual"
            st.session_state["lab_review_version"] += 1
            st.session_state["lab_review_applied"] = False
            st.session_state["lab_confirmed_values"] = {}
            st.session_state["lab_confirmed_at"] = ""
            st.success("Importación reiniciada. Los campos manuales permanecen editables.")

        if process_pdf and uploaded_pdf is not None:
            file_bytes = uploaded_pdf.getvalue()
            raw_text, methods, values, evidence, diagnostics = core.extract_lab_values_from_pdf_bytes(file_bytes)
            st.session_state["extracted_values"] = values
            st.session_state["extraction_evidence"] = evidence
            st.session_state["extraction_diagnostics"] = diagnostics
            st.session_state["pdf_methods"] = methods
            st.session_state["raw_text_len"] = len(raw_text or "")
            st.session_state["anon_preview"] = core.lab_candidate_lines(raw_text)
            st.session_state["data_source"] = "PDF de laboratorio anonimizado"
            st.session_state["lab_review_version"] += 1
            st.session_state["lab_review_applied"] = False
            st.session_state["lab_confirmed_values"] = {}
            st.session_state["lab_confirmed_at"] = ""
            if values:
                st.success(f"Extracción completada: {len(values)} variables candidatas. Revise la tabla antes de aplicarlas.")
            else:
                st.error("No se reconocieron variables. El PDF puede ser una imagen escaneada o tener una estructura no "
                         "recuperable como texto. Use la pestaña Texto copiado o carga manual.")

    with source_tab_text:
        pasted_lab = st.text_area(
            "Pegue aquí el texto del laboratorio",
            height=170,
            placeholder="Ej.: Colesterol total 245 mg/dL\nLDL 162 mg/dL\nHDL 45 mg/dL\nTriglicéridos 210 mg/dL...",
            key="pasted_lab_text",
        )
        if st.button("🔎 Extraer resultados del texto", width="stretch"):
            values, evidence, diagnostics = core.extract_lab_values_from_text(pasted_lab)
            st.session_state["extracted_values"] = values
            st.session_state["extraction_evidence"] = evidence
            st.session_state["extraction_diagnostics"] = diagnostics
            st.session_state["anon_preview"] = core.lab_candidate_lines(pasted_lab)
            st.session_state["pdf_methods"] = ["texto pegado"]
            st.session_state["raw_text_len"] = len(pasted_lab or "")
            st.session_state["data_source"] = "Texto de laboratorio pegado / anonimizado"
            st.session_state["lab_review_version"] += 1
            st.session_state["lab_review_applied"] = False
            st.session_state["lab_confirmed_values"] = {}
            st.session_state["lab_confirmed_at"] = ""
            if values:
                st.success(f"Se detectaron {len(values)} variables candidatas. Revise y corrija antes de aplicar.")
            else:
                st.warning("No se reconocieron variables. Revise el texto o complete manualmente.")

    extracted = st.session_state.get("extracted_values", {})
    evidence = st.session_state.get("extraction_evidence", {})

    st.divider()
    theme.section("Paso 3 · Corregí y confirmá qué valores usar")
    if extracted:
        review_df = core.build_lab_review_dataframe(extracted, evidence)
        n_ok = sum(not bool(core.suspicious_reason(k, float(v))) for k, v in extracted.items())
        n_review = len(extracted) - n_ok
        missing = core.missing_lab_fields(extracted)
        q1, q2, q3, q4 = st.columns(4)
        q1.metric("Detectadas", len(extracted))
        q2.metric("Plausibles", n_ok)
        q3.metric("A revisar", n_review)
        q4.metric("Prioritarias faltantes", len(missing))

        if st.session_state.get("pdf_methods"):
            st.caption("Lectores utilizados: " + " | ".join(st.session_state["pdf_methods"]) +
                       f" · Texto recuperado: {st.session_state['raw_text_len']} caracteres")

        st.warning(
            "**Lugar exacto de corrección:** modifique la columna **✏️ Valor confirmado**. "
            "La columna **Valor extraído** queda bloqueada como constancia. "
            "Revise además **Origen lectura** y **Conversión**: por ejemplo, 2,80 g/L se normaliza a 280 mg/dL. "
            "Desmarque **Usar** para excluir una variable dudosa."
        )
        edited_review = st.data_editor(
            review_df,
            width="stretch",
            hide_index=True,
            disabled=["Variable", "Valor extraído", "Unidad", "Origen lectura", "Conversión", "Confianza",
                      "Conf. %", "Lectura orientativa", "Qué significa", "Estado extracción"],
            column_config={
                "Aplicar": st.column_config.CheckboxColumn("Usar", help="Solo los valores marcados pasarán a la evaluación"),
                "Valor extraído": st.column_config.NumberColumn("Valor extraído", format="%.2f", help="Lectura original del PDF; no editable"),
                "Valor confirmado": st.column_config.NumberColumn("✏️ Valor confirmado", format="%.2f", help="CORRIJA AQUÍ antes de confirmar"),
                "Conf. %": st.column_config.ProgressColumn("Conf. %", min_value=0, max_value=100, format="%d%%"),
            },
            key=f"lab_review_editor_{st.session_state['lab_review_version']}",
        )

        corrected_selected_values = core.reviewed_lab_dataframe_to_values(edited_review, only_selected=True)
        consistency_findings = core.lab_cross_consistency(corrected_selected_values)
        if consistency_findings:
            st.markdown("#### Control de coherencia de los valores CORREGIDOS/SELECCIONADOS")
            for level, message in consistency_findings:
                if level == "error":
                    st.error(message)
                else:
                    st.warning(message)
        else:
            st.success("Control de coherencia de la selección corregida: no se detectaron contradicciones mayores.")

        a1, a2 = st.columns([2, 1])
        with a1:
            if st.button("✅ CONFIRMAR correcciones y USAR estos valores en la evaluación", type="primary", width="stretch"):
                applied, errors, applied_values = core.apply_reviewed_lab_dataframe(edited_review)
                if applied:
                    st.session_state["lab_review_applied"] = True
                    st.session_state["lab_confirmed_values"] = dict(applied_values)
                    st.session_state["lab_confirmed_at"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                    st.session_state["data_source"] = "Laboratorio revisado y confirmado"
                if errors:
                    st.warning("No aplicados: " + " | ".join(errors))
                st.rerun()
        with a2:
            st.download_button(
                "⬇️ JSON anonimizado",
                data=json.dumps(extracted, ensure_ascii=False, indent=2).encode("utf-8"),
                file_name="laboratorio_anonimizado_extraido.json",
                mime="application/json",
                width="stretch",
            )

        if missing:
            st.warning("Variables prioritarias no detectadas: " + ", ".join(missing) + ". Complételas manualmente si están disponibles.")
        if st.session_state.get("lab_review_applied"):
            stamp = st.session_state.get("lab_confirmed_at", "")
            st.success(
                f"✅ Valores corregidos CONFIRMADOS{f' el {stamp}' if stamp else ''}. "
                "La evaluación toma ahora los valores activos mostrados en el Paso 4."
            )
    else:
        st.caption("Aún no hay resultados extraídos. Puede usar PDF, texto copiado o completar directamente el formulario manual.")

    with st.expander("🔐 Vista anonimizada del texto detectado", expanded=False):
        preview = st.session_state.get("anon_preview", [])
        if preview:
            st.text("\n".join(preview[:120]))
        else:
            st.caption("Sin líneas candidatas para mostrar.")

    with st.expander("🛠️ Diagnóstico técnico de extracción", expanded=False):
        diag = st.session_state.get("extraction_diagnostics", [])
        if diag:
            st.dataframe(pd.DataFrame(diag), width="stretch", hide_index=True)
        else:
            st.caption("Sin diagnóstico disponible.")

    st.divider()
    theme.section("Paso 4 · Valores finales ACTIVOS que usará la evaluación")
    st.info("Estos campos son la última instancia de edición. Todo cambio realizado aquí reemplaza el valor confirmado "
            "y se usa inmediatamente en la evaluación, el informe y las simulaciones.")

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.text_input("Paciente / código anónimo", key="patient_id")
        st.number_input("Edad", min_value=1, max_value=110, step=1, key="manual_age")
    with m2:
        st.selectbox("Sexo", ["Femenino", "Masculino", "Otro / no especificado"], key="sex")
        st.number_input("eGFR ml/min/1,73 m²", min_value=1.0, max_value=200.0, step=1.0, key="manual_egfr")
    with m3:
        st.number_input("Colesterol total mg/dL", min_value=50.0, max_value=600.0, step=1.0, key="manual_ct")
        st.number_input("HDL-C mg/dL", min_value=5.0, max_value=150.0, step=1.0, key="manual_hdl")
    with m4:
        st.number_input("LDL-C mg/dL", min_value=10.0, max_value=500.0, step=1.0, key="manual_ldl")
        st.number_input("Triglicéridos mg/dL", min_value=20.0, max_value=2000.0, step=1.0, key="manual_tg")

    a1, a2, a3, a4 = st.columns(4)
    with a1:
        st.number_input("Creatinina mg/dL", min_value=0.2, max_value=20.0, step=0.1, key="manual_creatinine")
    with a2:
        st.number_input("Glucemia mg/dL", min_value=30.0, max_value=700.0, step=1.0, key="manual_glucose")
    with a3:
        st.number_input("HbA1c %", min_value=3.0, max_value=18.0, step=0.1, key="manual_hba1c")
    with a4:
        st.number_input("TSH µUI/mL", min_value=0.01, max_value=100.0, step=0.1, key="manual_tsh")

    b1, b2, b3 = st.columns(3)
    with b1:
        st.number_input("AST/GOT U/L", min_value=1.0, max_value=1000.0, step=1.0, key="manual_ast")
    with b2:
        st.number_input("ALT/GPT U/L", min_value=1.0, max_value=1000.0, step=1.0, key="manual_alt")
    with b3:
        st.number_input("CK/CPK U/L", min_value=1.0, max_value=20000.0, step=1.0, key="manual_ck")

    st.markdown("#### 🔎 Constancia de valores realmente usados")
    st.dataframe(core.active_lab_values_dataframe(), width="stretch", hide_index=True)
    st.success("La página **Decisión y meta** toma directamente la columna **Valor usado** de esta tabla. "
               "No utiliza los valores extraídos originales si fueron corregidos.")

    if NAV.get("decision") is not None:
        st.page_link(NAV["decision"], label="Continuar a Decisión y meta", icon="🧭")
    theme.footer(core.APP_VERSION, core.APP_DATE, st.session_state.get("cfg_regulatory", ""))


# ======================================================================
# PÁGINA · DECISIÓN Y META
# ======================================================================
def page_decision():
    NAV = _nav()
    data, goal_ldl = core.build_base_data()

    theme.page_hero(
        title="Decisión y llegada a meta",
        subtitle="Calcula la reducción necesaria, compara monoterapia y combinaciones, explica por qué elegir "
                 "pitavastatina y define el plan de control.",
        eyebrow="Paso 2 del flujo clínico",
        icon="🧭",
    )

    theme.section("Valores activos utilizados")
    eval_active_values = {
        "ct": data["ct"], "ldl": data["ldl"], "hdl": data["hdl"], "tg": data["tg"],
        "egfr": data["egfr"], "creatinine": data["creatinine"], "glucose": data["glucose"],
        "hba1c": data["hba1c"], "ast": data["ast"], "alt": data["alt"],
        "ck": data["ck"], "tsh": data["tsh"], "age": data["age"],
    }
    st.dataframe(core.active_lab_values_dataframe(eval_active_values), width="stretch", hide_index=True)
    st.caption(f"Fuente: {data.get('data_source', 'No informada')} · no-HDL-C: {data['non_hdl']:.0f} mg/dL")

    theme.section("1) Situación terapéutica y brecha")
    t1, t2, t3 = st.columns(3)
    with t1:
        current_therapy = st.selectbox(
            "Tratamiento hipolipemiante actual",
            ["Sin tratamiento", "Pitavastatina 1 mg", "Pitavastatina 2 mg", "Pitavastatina 4 mg",
             "Pitavastatina + ezetimiba", "Otra estatina", "Otra estatina + ezetimiba", "Otro / no precisado"],
            key="current_lipid_therapy",
        )
        baseline_ldl = st.number_input(
            "LDL-C basal o previo al tratamiento, mg/dL",
            min_value=10.0, max_value=500.0, value=float(st.session_state.get("baseline_ldl_input", data["ldl"])), step=1.0,
            key="baseline_ldl_input",
            help="Si el paciente no recibe tratamiento, use el LDL-C actual. Si ya está tratado, ingrese el valor previo más confiable.",
        )
    with t2:
        adherence = st.selectbox("Adherencia declarada", ["No evaluada", "Alta (≥80%)", "Intermedia (50–79%)", "Baja (<50%)"], key="adherence_input")
        weeks_on_therapy = st.number_input("Semanas con el esquema actual", 0, 520, int(st.session_state.get("weeks_current_therapy", 0)), 1, key="weeks_current_therapy")
    with t3:
        apob = st.number_input("ApoB, mg/dL (0 = no informado)", 0.0, 300.0, float(st.session_state.get("apob_input", 0.0)), 1.0, key="apob_input")
        lpa = st.number_input("Lp(a), mg/dL (0 = no informada)", 0.0, 500.0, float(st.session_state.get("lpa_input", 0.0)), 1.0, key="lpa_input")

    with st.expander("Refinamiento del riesgo y modificadores", expanded=False):
        r1, r2 = st.columns(2)
        with r1:
            cac = st.number_input("Calcio coronario CAC (0 = no informado)", 0.0, 5000.0, float(st.session_state.get("cac_input", 0.0)), 1.0, key="cac_input")
        with r2:
            prevent_risk = st.number_input("Riesgo PREVENT a 10 años, % (0 = no informado)", 0.0, 100.0, float(st.session_state.get("prevent_input", 0.0)), 0.1, key="prevent_input")
        st.caption("PitaSmart registra el valor PREVENT calculado externamente; esta versión no reemplaza el calculador oficial.")

    theme.section("2) Condiciones clínicas y seguridad")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        ascvd = st.checkbox("ASCVD previa", value=bool(st.session_state.get("ascvd_input", False)), key="ascvd_input")
        diabetes = st.checkbox("Diabetes", value=bool(st.session_state.get("diabetes_input", False)), key="diabetes_input")
        hta = st.checkbox("Hipertensión arterial", value=bool(st.session_state.get("hta_input", True)), key="hta_input")
    with c2:
        smoking = st.checkbox("Tabaquismo actual", value=bool(st.session_state.get("smoking_input", False)), key="smoking_input")
        hefh = st.checkbox("HeFH probable/conocida", value=bool(st.session_state.get("hefh_input", False)), key="hefh_input")
        prior_statin_intolerance = st.checkbox("Intolerancia previa a estatina", value=bool(st.session_state.get("intolerance_input", False)), key="intolerance_input")
    with c3:
        hiv_arv = st.checkbox("VIH o antirretrovirales", value=bool(st.session_state.get("hiv_input", False)), key="hiv_input")
        polypharmacy = st.checkbox("Polifarmacia relevante", value=bool(st.session_state.get("polypharmacy_input", False)), key="polypharmacy_input")
        hypothyroidism = st.checkbox("Hipotiroidismo no controlado", value=bool(st.session_state.get("hypothyroidism_input", False)), key="hypothyroidism_input")
    with c4:
        acute_liver_failure = st.checkbox("Falla hepática aguda/cirrosis descompensada", value=bool(st.session_state.get("acute_liver_input", False)), key="acute_liver_input")
        alcohol_liver_history = st.checkbox("Antecedente hepático/alcohol relevante", value=bool(st.session_state.get("liver_history_input", False)), key="liver_history_input")
        pregnancy_lactation = st.checkbox("Embarazo o lactancia", value=bool(st.session_state.get("pregnancy_input", False)), key="pregnancy_input")
        hypersensitivity = st.checkbox("Hipersensibilidad a pitavastatina", value=bool(st.session_state.get("hypersensitivity_input", False)), key="hypersensitivity_input")

    statin_attempts = 0
    intolerance_agent = "No informado"
    intolerance_symptoms = "No informados"
    dechallenge = "No informado"
    rechallenge = "No informado"
    if prior_statin_intolerance:
        with st.expander("Caracterización estructurada de intolerancia", expanded=True):
            i1, i2, i3 = st.columns(3)
            with i1:
                statin_attempts = st.number_input("Número de estatinas intentadas", 0, 10, int(st.session_state.get("statin_attempts_input", 1)), 1, key="statin_attempts_input")
                intolerance_agent = st.text_input("Estatina y dosis asociada", value=st.session_state.get("intolerance_agent_input", ""), key="intolerance_agent_input") or "No informado"
            with i2:
                intolerance_symptoms = st.text_area("Síntomas y localización", value=st.session_state.get("intolerance_symptoms_input", ""), height=80, key="intolerance_symptoms_input") or "No informados"
            with i3:
                dechallenge = st.selectbox("¿Mejoró al suspender?", ["No informado", "Sí", "No", "Parcial"], key="dechallenge_input")
                rechallenge = st.selectbox("¿Reapareció al reexponer?", ["No informado", "Sí", "No", "No se reexpuso"], key="rechallenge_input")
            if statin_attempts < 2:
                st.info("Con menos de dos estatinas intentadas, la información es compatible con posible intolerancia, pero no confirma por sí sola intolerancia completa.")

    meds_text = st.text_area(
        "Medicación concomitante",
        placeholder="Ej.: enalapril, amlodipina, metformina, ezetimiba, ciclosporina, gemfibrozil, eritromicina, rifampicina, colchicina, ritonavir...",
        height=100,
        key="meds_text_input",
    )

    data.update({
        "baseline_ldl": float(baseline_ldl),
        "current_therapy": current_therapy,
        "adherence": adherence,
        "weeks_on_therapy": int(weeks_on_therapy),
        "apob": float(apob), "lpa": float(lpa), "cac": float(cac), "prevent_risk": float(prevent_risk),
        "ascvd": bool(ascvd), "diabetes": bool(diabetes), "hta": bool(hta), "smoking": bool(smoking),
        "hefh": bool(hefh), "prior_statin_intolerance": bool(prior_statin_intolerance),
        "hiv_arv": bool(hiv_arv), "polypharmacy": bool(polypharmacy), "hypothyroidism": bool(hypothyroidism),
        "acute_liver_failure": bool(acute_liver_failure), "alcohol_liver_history": bool(alcohol_liver_history),
        "pregnancy_lactation": bool(pregnancy_lactation), "hypersensitivity": bool(hypersensitivity),
        "statin_attempts": int(statin_attempts), "intolerance_agent": intolerance_agent,
        "intolerance_symptoms": intolerance_symptoms, "dechallenge": dechallenge, "rechallenge": rechallenge,
        "meds_text": meds_text,
    })

    interactions = core.detect_interactions(meds_text)
    therapeutic_combinations = core.detect_therapeutic_combinations(meds_text)
    indications, reasons = core.assess_indication(data)
    red_flags, yellow_flags = core.assess_warnings(data, interactions)
    dose_info = core.dose_recommendation(data, interactions, goal_ldl)
    classification, card_class, summary = core.final_classification(indications, red_flags, yellow_flags, data, dose_info, goal_ldl)
    advantages = core.personalized_advantages(data, dose_info)
    scenarios_df = pd.DataFrame(dose_info.get("scenarios", []))

    st.divider()
    theme.section("Resultado integrado")
    core.render_classification(classification, card_class, summary)

    gap = core.required_ldl_reduction(float(baseline_ldl), goal_ldl)
    e1, e2, e3, e4 = st.columns(4)
    with e1:
        core.render_result_card("LDL-C basal/de referencia", f"{baseline_ldl:.0f} mg/dL", f"Actual: {data['ldl']:.0f} mg/dL", "info")
    with e2:
        core.render_result_card("Reducción requerida", f"{gap['percentage']:.1f}%", f"{gap['absolute']:.0f} mg/dL para meta <{goal_ldl}", "warn" if gap['percentage'] > 45 else "good")
    with e3:
        core.render_result_card("Estrategia seleccionada", dose_info["mejor_estimacion"], f"LDL-C proyectado {dose_info['ldl_estimado']:.0f} mg/dL", "good" if dose_info.get("reaches_goal") else "warn")
    with e4:
        max_int = core.interaction_max_level(interactions)
        core.render_result_card("Interacciones", max_int, f"{len(interactions)} señal(es)", "bad" if max_int == "ROJO" else ("warn" if max_int == "AMARILLO" else "good"))

    st.write("")
    theme.goal_meter(float(baseline_ldl), data["ldl"], goal_ldl, projected=dose_info.get("ldl_estimado"))

    theme.section("Recomendación operativa")
    st.info(dose_info["recommended_strategy"])
    if dose_info.get("notas"):
        for note in dose_info["notas"]:
            st.warning(note)

    theme.section("3) Comparador de estrategias")
    display_cols = ["Estrategia", "Tipo", "Reducción estimada %", "LDL-C proyectado", "Meta", "Alcanza meta", "Distancia residual", "Disponibilidad", "Motivo / evidencia"]
    st.dataframe(scenarios_df[display_cols], width="stretch", hide_index=True)
    if core.go and not scenarios_df.empty:
        available_plot = scenarios_df[scenarios_df["Disponibilidad"] == "Disponible"].copy()
        fig = core.go.Figure()
        fig.add_trace(core.go.Bar(
            x=available_plot["Estrategia"],
            y=available_plot["LDL-C proyectado"],
            text=[f"{x:.0f}" for x in available_plot["LDL-C proyectado"]],
            textposition="outside",
            marker_color="#0E5AA7",
            name="LDL-C proyectado",
        ))
        fig.add_hline(y=goal_ldl, line_dash="dash", line_color="#12A594", annotation_text=f"Meta <{goal_ldl}")
        fig.update_layout(title="LDL-C proyectado por estrategia", yaxis_title="LDL-C (mg/dL)", xaxis_title="",
                          height=470, showlegend=False, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, width="stretch", key="strategy_comparison_chart")
    st.caption("Las reducciones son promedios orientativos. El comparador de alta intensidad no prescribe una molécula; "
               "sirve para evidenciar cuándo otra intensidad ofrece mayor probabilidad de alcanzar la meta.")

    theme.section("4) ¿Por qué pitavastatina en este paciente?")
    for x in advantages:
        st.write("• " + x)
    if therapeutic_combinations:
        st.success("Ezetimiba detectada como combinación terapéutica: se integra para aumentar la probabilidad de alcanzar la meta y no como interacción mayor automática.")

    theme.section("5) Semáforo por dominios clínicos")
    st.dataframe(core.evaluation_domains(data, interactions, red_flags, yellow_flags, dose_info, goal_ldl), width="stretch", hide_index=True)

    favor, cautions, actions = core.evaluation_key_messages(data, interactions, red_flags, yellow_flags, dose_info, goal_ldl)
    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown("#### ✅ Qué favorece")
        for item in favor:
            st.write("• " + item)
    with m2:
        st.markdown("#### ⚠️ Qué limita")
        for item in cautions:
            st.write("• " + item)
    with m3:
        st.markdown("#### 🎯 Próximos pasos")
        for item in actions:
            st.write("• " + item)

    theme.section("6) Alertas e interacciones")
    if red_flags:
        for x in red_flags:
            st.error(x)
    elif yellow_flags:
        for x in yellow_flags:
            st.warning(x)
    else:
        st.success("No se detectaron alertas mayores ni precauciones relevantes con los datos cargados.")
    if interactions:
        st.dataframe(core.interactions_dataframe(interactions), width="stretch", hide_index=True)
    else:
        st.caption("No se detectaron señales incluidas en la base para la medicación declarada.")

    theme.section("7) Evidencia contextual activada")
    evidence_df = pd.DataFrame(core.EVIDENCE_MATRIX)
    if hiv_arv:
        st.dataframe(evidence_df[evidence_df["Evidencia"] == "REPRIEVE"], width="stretch", hide_index=True)
    if ascvd:
        st.dataframe(evidence_df[evidence_df["Evidencia"] == "REAL-CAD"], width="stretch", hide_index=True)
    if dose_info.get("requires_combination"):
        st.dataframe(evidence_df[evidence_df["Evidencia"] == "Pitavastatina + ezetimiba"], width="stretch", hide_index=True)
    if not (hiv_arv or ascvd or dose_info.get("requires_combination")):
        st.info("No se activó una población de evidencia específica; la decisión depende de brecha, seguridad y preferencia clínica.")

    st.session_state["last_data"] = dict(data)
    st.session_state["last_interactions"] = interactions
    st.session_state["last_therapeutic_combinations"] = therapeutic_combinations
    st.session_state["last_indications"] = indications
    st.session_state["last_reasons"] = reasons
    st.session_state["last_red_flags"] = red_flags
    st.session_state["last_yellow_flags"] = yellow_flags
    st.session_state["last_dose_info"] = dose_info
    st.session_state["last_classification"] = classification
    st.session_state["last_card_class"] = card_class
    st.session_state["last_summary"] = summary
    st.session_state["last_advantages"] = advantages

    if NAV.get("informe") is not None:
        st.page_link(NAV["informe"], label="Ir al Informe y descargas", icon="📄")
    theme.footer(core.APP_VERSION, core.APP_DATE, st.session_state.get("cfg_regulatory", ""))


# ======================================================================
# PÁGINA · SEGUIMIENTO
# ======================================================================
def page_seguimiento():
    data, goal_ldl = core.build_base_data()
    data = core.apply_clinical_defaults(data)

    theme.page_hero(
        title="Seguimiento de respuesta",
        subtitle="Compará la respuesta observada con la esperada y evitá declarar fracaso sin revisar adherencia y "
                 "tiempo de exposición.",
        eyebrow="Paso 3 del flujo clínico",
        icon="📈",
    )
    st.info("Importe un segundo laboratorio o cargue el LDL-C de control. La app compara la respuesta observada con la "
            "esperada y evita declarar fracaso sin revisar adherencia y tiempo de exposición.")

    theme.section("Laboratorio de control")
    fup_pdf = st.file_uploader("PDF de laboratorio de seguimiento (opcional)", type=["pdf"], key="followup_pdf_uploader")
    if st.button("🔎 Extraer laboratorio de seguimiento", disabled=fup_pdf is None, width="stretch"):
        raw, methods, values, evidence, diagnostics = core.extract_lab_values_from_pdf_bytes(fup_pdf.getvalue())
        st.session_state["followup_extracted_values"] = values
        st.session_state["followup_pdf_methods"] = methods
        if "ldl" in values:
            st.session_state["followup_ldl_input"] = float(values["ldl"])
        if "ck" in values:
            st.session_state["followup_ck_input"] = float(values["ck"])
        if "alt" in values:
            st.session_state["followup_alt_input"] = float(values["alt"])
        st.success(f"Se extrajeron {len(values)} variables. Revise y confirme los valores de control.")

    if st.session_state.get("followup_extracted_values"):
        st.dataframe(pd.DataFrame(core.extracted_table_rows(st.session_state["followup_extracted_values"])), width="stretch", hide_index=True)

    latest_dose_info = st.session_state.get("last_dose_info") or core.dose_recommendation(data, core.detect_interactions(data.get("meds_text", "")), goal_ldl)
    scenario_options = [r["Estrategia"] for r in latest_dose_info.get("scenarios", []) if r.get("Disponibilidad") == "Disponible"]
    if not scenario_options:
        scenario_options = list(core.THERAPEUTIC_SCENARIOS.keys())
    default_strategy = latest_dose_info.get("mejor_estimacion")
    default_idx = scenario_options.index(default_strategy) if default_strategy in scenario_options else 0

    theme.section("Datos del control")
    f1, f2, f3 = st.columns(3)
    with f1:
        followup_baseline = st.number_input("LDL-C basal para seguimiento", 10.0, 500.0, float(latest_dose_info.get("baseline_ldl", data["ldl"])), 1.0, key="followup_baseline_input")
        followup_strategy = st.selectbox("Estrategia indicada", scenario_options, index=default_idx, key="followup_strategy_input")
    with f2:
        followup_ldl = st.number_input("LDL-C de control", 1.0, 500.0, float(st.session_state.get("followup_ldl_input", data["ldl"])), 1.0, key="followup_ldl_input")
        followup_weeks = st.number_input("Semanas desde inicio/ajuste", 0, 104, int(st.session_state.get("followup_weeks_input", 6)), 1, key="followup_weeks_input")
    with f3:
        followup_adherence = st.selectbox("Adherencia en seguimiento", ["Alta (≥80%)", "Intermedia (50–79%)", "Baja (<50%)", "No evaluada"], key="followup_adherence_input")
        muscle_symptoms = st.selectbox("Síntomas musculares", ["No", "Leves", "Moderados", "Intensos"], key="followup_muscle_input")

    f4, f5 = st.columns(2)
    with f4:
        followup_ck = st.number_input("CK de control, U/L", 0.0, 20000.0, float(st.session_state.get("followup_ck_input", data.get("ck", 0))), 1.0, key="followup_ck_input")
    with f5:
        followup_alt = st.number_input("ALT de control, U/L", 0.0, 5000.0, float(st.session_state.get("followup_alt_input", data.get("alt", 0))), 1.0, key="followup_alt_input")

    scenario_reduction = core.THERAPEUTIC_SCENARIOS.get(followup_strategy, {}).get("reduction", 0.0)
    followup_analysis = core.followup_response_analysis(
        followup_baseline, followup_ldl, scenario_reduction, goal_ldl, int(followup_weeks),
        followup_adherence, muscle_symptoms, followup_ck, followup_alt,
    )
    st.session_state["last_followup_analysis"] = followup_analysis

    st.divider()
    theme.section("Resultado del seguimiento")
    core.render_classification(
        followup_analysis["status"],
        {"good": "green-card", "warn": "yellow-card", "bad": "red-card"}.get(followup_analysis["level"], "gray-card"),
        followup_analysis["interpretation"],
    )
    q1, q2, q3, q4 = st.columns(4)
    q1.metric("Reducción observada", f"{followup_analysis['observed_reduction_pct']:.1f}%")
    q2.metric("Reducción esperada", f"{followup_analysis['expected_reduction_pct']:.1f}%")
    q3.metric("LDL-C esperado", f"{followup_analysis['expected_ldl']:.0f} mg/dL")
    q4.metric("Brecha residual", f"{followup_analysis['gap_to_goal']:.0f} mg/dL" if followup_analysis['gap_to_goal'] else "Meta alcanzada")
    st.markdown("#### Conducta sugerida")
    for action in followup_analysis["actions"]:
        st.write("• " + action)

    theme.footer(core.APP_VERSION, core.APP_DATE, st.session_state.get("cfg_regulatory", ""))


# ======================================================================
# PÁGINA · INFORME
# ======================================================================
def page_informe():
    if st.session_state.get("last_data"):
        data = dict(st.session_state["last_data"])
    else:
        data, _goal = core.build_base_data()
    data = core.apply_clinical_defaults(data)

    _risk, _custom, goal_ldl = core.current_goal()

    _interactions = st.session_state.get("last_interactions", core.detect_interactions(data["meds_text"]))
    _indications = st.session_state.get("last_indications", core.assess_indication(data)[0])
    _reasons = st.session_state.get("last_reasons", core.assess_indication(data)[1])
    _red_flags = st.session_state.get("last_red_flags", core.assess_warnings(data, _interactions)[0])
    _yellow_flags = st.session_state.get("last_yellow_flags", core.assess_warnings(data, _interactions)[1])
    _dose_info = st.session_state.get("last_dose_info", core.dose_recommendation(data, _interactions, goal_ldl))
    _classification = st.session_state.get("last_classification", "")
    _card_class = st.session_state.get("last_card_class", "")
    _summary = st.session_state.get("last_summary", "")
    if not _classification:
        _classification, _card_class, _summary = core.final_classification(_indications, _red_flags, _yellow_flags, data, _dose_info, goal_ldl)
    _advantages = st.session_state.get("last_advantages", core.personalized_advantages(data, _dose_info))

    theme.page_hero(
        title="Informe y descargas",
        subtitle="Generá el informe clínico integrado y exportalo en los formatos que necesites: Markdown, PDF, "
                 "Excel/CSV o JSON anonimizado.",
        eyebrow="Paso 4 del flujo clínico",
        icon="📄",
    )

    theme.section("Clasificación final")
    core.render_classification(_classification, _card_class, _summary)

    theme.section("Informe editable")
    report_md = core.build_report(
        data, _indications, _reasons, _red_flags, _yellow_flags,
        _interactions, _dose_info, _classification, _summary, _advantages
    )
    edited_report = st.text_area("Informe editable", value=report_md, height=520, label_visibility="collapsed")

    theme.section("Descargas")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.download_button("⬇️ Informe Markdown", edited_report.encode("utf-8"), "informe_PitaSmart.md", "text/markdown", width="stretch")
    with c2:
        bytes_export, fname, mime = core.make_export_table(data, _classification, _dose_info, _red_flags, _yellow_flags, _advantages, _interactions)
        st.download_button("⬇️ Datos Excel/CSV", bytes_export, fname, mime, width="stretch")
    with c3:
        if core.REPORTLAB_OK:
            pdf = core.report_to_pdf(edited_report)
            st.download_button("⬇️ Informe PDF", pdf, "informe_PitaSmart.pdf", "application/pdf", width="stretch")
        else:
            st.info("Para PDF instale reportlab.")
    with c4:
        st.download_button(
            "⬇️ Lab extraído JSON",
            json.dumps(st.session_state.get("extracted_values", {}), ensure_ascii=False, indent=2).encode("utf-8"),
            "laboratorio_extraido_anonimizado.json",
            "application/json",
            width="stretch",
        )

    theme.footer(core.APP_VERSION, core.APP_DATE, st.session_state.get("cfg_regulatory", ""))


# ======================================================================
# PÁGINA · BASE Y EVIDENCIA
# ======================================================================
def page_evidencia():
    theme.page_hero(
        title="Base clínica y evidencia",
        subtitle="Indicaciones, escenarios terapéuticos comparados, matriz de evidencia y base de conocimiento de "
                 "interacciones con reglas específicas de pitavastatina.",
        eyebrow="Conocimiento",
        icon="📚",
    )

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            """
<div class="card">
<h4>Indicaciones evaluadas</h4>
<ul>
<li>Hipercolesterolemia primaria / LDL-C elevado.</li>
<li>Dislipidemia mixta.</li>
<li>Hipercolesterolemia familiar heterocigota.</li>
<li>Prevención cardiovascular según riesgo global.</li>
<li>Situaciones donde se busca estatina de intensidad moderada.</li>
</ul>
</div>
""",
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            """
<div class="card">
<h4>Ajuste clínico diferencial</h4>
<ul>
<li>Monoterapia de intensidad moderada con titulación individual.</li>
<li>Base de combinación con ezetimiba cuando la monoterapia no alcanza la meta.</li>
<li>Baja dependencia CYP3A4 útil en polifarmacia seleccionada.</li>
<li>Evidencia contextual en VIH y enfermedad coronaria estable.</li>
<li>La app muestra también límites y alternativas de mayor intensidad.</li>
</ul>
</div>
""",
            unsafe_allow_html=True,
        )

    theme.section("Escenarios terapéuticos comparados")
    st.dataframe(pd.DataFrame([
        {"Estrategia": name, "Tipo": item["type"], "Reducción LDL-C orientativa": f"{item['reduction']*100:.0f}%", "Uso": item["evidence"]}
        for name, item in core.THERAPEUTIC_SCENARIOS.items()
    ]), width="stretch", hide_index=True)

    theme.section("Combinaciones terapéuticas reconocidas")
    st.success("Ezetimiba se clasifica como herramienta de intensificación y no como interacción problemática automática. "
               "La vigilancia se individualiza.")
    st.dataframe(pd.DataFrame([
        {"Combinación": "Pitavastatina + ezetimiba", "Objetivo": "Aumentar reducción de LDL-C y llegada a meta", "Precaución": "Confirmar tolerabilidad, prospecto y respuesta real"}
    ]), width="stretch", hide_index=True)

    theme.section("Matriz de evidencia y aplicabilidad")
    st.dataframe(pd.DataFrame(core.EVIDENCE_MATRIX), width="stretch", hide_index=True)

    theme.section("Base de conocimiento de interacciones")
    st.info(
        "Integración estructurada del material aportado sobre interacciones farmacológicas con reglas específicas de "
        "pitavastatina. El libro aporta mecanismos y señales de clase; las decisiones de dosis/contraindicación se "
        "separan de esas extrapolaciones."
    )
    kb_search = st.text_input(
        "Buscar en la base por fármaco, mecanismo o evidencia",
        placeholder="Ej.: miopatía, OATP, fibrato, CYP3A4, daptomicina, ARV...",
        key="kb_interaction_search",
    )
    kb_df = core.knowledge_base_dataframe()
    if kb_search.strip():
        needle = core.norm_text(kb_search)
        mask = kb_df.astype(str).apply(lambda row: needle in core.norm_text(" | ".join(row.tolist())), axis=1)
        kb_df = kb_df.loc[mask].reset_index(drop=True)
    st.dataframe(kb_df, width="stretch", hide_index=True)

    with st.expander("🧬 Fundamento farmacológico integrado", expanded=False):
        st.markdown(
            """
- **Pitavastatina no debe tratarse como una estatina CYP3A4 clásica.** La base del libro describe para pitavastatina vías UGT1A3/UGT2B7 y participación CYP2C9/CYP2C8, con fármaco sin alterar predominante en plasma.
- **La toxicidad muscular puede ser farmacodinámica y acumulativa.** Fibratos, colchicina, daptomicina y otras exposiciones pueden aumentar la vigilancia. Ezetimiba se muestra por separado como combinación terapéutica reconocida.
- **Los transportadores importan.** El material señala OATP1B1 y describe ciclosporina/gemfibrozil como inhibidores de transportadores relevantes para estatinas.
- **No extrapolar automáticamente.** Una interacción fuerte con simvastatina, lovastatina o atorvastatina por CYP3A4 no implica la misma magnitud con pitavastatina.
"""
        )

    theme.section("Otras reglas de seguridad no farmacológicas")
    st.dataframe(pd.DataFrame([
        {"Situación": "eGFR 15–59 o hemodiálisis", "Nivel": "Ajuste", "Acción": "Inicio 1 mg/día; máximo 2 mg/día"},
        {"Situación": "Falla hepática aguda/cirrosis descompensada", "Nivel": "Contraindicación", "Acción": "No usar"},
        {"Situación": "Edad ≥65 años", "Nivel": "Factor de riesgo", "Acción": "Mayor vigilancia de miopatía"},
        {"Situación": "Hipotiroidismo no controlado", "Nivel": "Factor de riesgo", "Acción": "Corregir y reevaluar riesgo muscular"},
        {"Situación": "Embarazo", "Nivel": "Situación especial", "Acción": "Revisar necesidad terapéutica individual y prospecto local"},
    ]), width="stretch", hide_index=True)

    theme.footer(core.APP_VERSION, core.APP_DATE, st.session_state.get("cfg_regulatory", ""))


# ======================================================================
# PÁGINA · TEXTO PARA PACIENTE
# ======================================================================
def page_paciente():
    theme.page_hero(
        title="Texto para paciente",
        subtitle="Material educativo editable y descargable, con los mensajes clave de seguridad y adherencia.",
        eyebrow="Conocimiento",
        icon="👤",
    )
    theme.section("Texto editable")
    txt = st.text_area("Texto editable", value=core.patient_text(), height=260, label_visibility="collapsed")
    st.download_button("⬇️ Descargar texto paciente", txt.encode("utf-8"), "educacion_paciente_pitavastatina.txt", "text/plain")

    theme.section("Mensajes clave")
    st.write("• Mantener cambios de estilo de vida.")
    st.write("• No suspender ni modificar dosis sin consultar.")
    st.write("• Avisar por dolor muscular intenso, debilidad marcada, fiebre, orina oscura o ictericia.")
    st.write("• Llevar lista actualizada de medicamentos para revisar interacciones.")

    theme.footer(core.APP_VERSION, core.APP_DATE, st.session_state.get("cfg_regulatory", ""))


# ======================================================================
# PÁGINA · FUENTES Y USO
# ======================================================================
def page_fuentes():
    theme.page_hero(
        title="Fuentes y uso",
        subtitle="Referencias que respaldan la base de conocimiento, instalación local y notas para una versión "
                 "institucional.",
        eyebrow="Conocimiento",
        icon="ℹ️",
    )
    theme.section("Fuentes")
    for src in core.FUENTES:
        st.write(f"• {src}")

    st.success("La base de interacciones integra el PDF aportado 'Introducción a las interacciones farmacológicas', "
               "especialmente los capítulos 1 y 8, y separa evidencia de clase de reglas específicas de pitavastatina.")

    theme.section("Instalación local")
    st.code("pip install -r requirements.txt\nstreamlit run app.py", language="bash")

    theme.section("Verificación de que la importación está activa")
    st.success("El módulo 📥 Importar laboratorio precede a 🧭 Decisión y meta. Los valores extremos quedan marcados como "
               "REVISAR y no se aplican automáticamente.")

    theme.section("Recomendaciones para versión institucional")
    st.write("• Agregar prospecto ANMAT completo como base JSON editable.")
    st.write("• Mantener versionada la base de interacciones y revalidarla contra prospectos/guías vigentes.")
    st.write("• Agregar login, historial por usuario, firma digital e informe institucional.")
    st.write("• Integrar el calculador PREVENT oficial solo con coeficientes y validación documentados; actualmente se "
             "registra un valor calculado externamente.")

    theme.footer(core.APP_VERSION, core.APP_DATE, st.session_state.get("cfg_regulatory", ""))


# ======================================================================
# NAVEGACIÓN
# ======================================================================
with st.sidebar:
    theme.brand_sidebar()

p_inicio = st.Page(page_inicio, title="Inicio", icon="🏠", default=True, url_path="inicio")
p_importar = st.Page(page_importar, title="Importar laboratorio", icon="📥", url_path="importar")
p_decision = st.Page(page_decision, title="Decisión y meta", icon="🧭", url_path="decision")
p_seguimiento = st.Page(page_seguimiento, title="Seguimiento", icon="📈", url_path="seguimiento")
p_informe = st.Page(page_informe, title="Informe y descargas", icon="📄", url_path="informe")
p_evidencia = st.Page(page_evidencia, title="Base clínica y evidencia", icon="📚", url_path="evidencia")
p_paciente = st.Page(page_paciente, title="Texto para paciente", icon="👤", url_path="paciente")
p_fuentes = st.Page(page_fuentes, title="Fuentes y uso", icon="ℹ️", url_path="fuentes")

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
