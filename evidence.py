# evidence.py · EUROPHARMA — PitaSmart
# Comparador de estatinas con respaldo bibliográfico + módulo de lipidología de precisión.
#
# Todas las reducciones de LDL-C son PROMEDIOS ORIENTATIVOS de la literatura; la respuesta
# individual debe confirmarse con un perfil lipídico de control.

from __future__ import annotations
from typing import Any, Dict, List

import pandas as pd
import streamlit as st

import core
import theme

# ============================================================
# 1) BIBLIOTECA DE ESTATINAS (potencia comparada)
# ============================================================
# Intensidad según ACC/AHA 2018: alta ≥50%, moderada 30–49%, baja <30%.
# Magnitudes de referencia: metaanálisis VOYAGER (rosuvastatina 5/10/20/40 = 39/44/50/55%)
# y equivalencias VOYAGER (1 dosis de rosuvastatina ≈ 3–3,5× atorvastatina ≈ 7–8× simvastatina).

STATIN_LIBRARY: List[Dict[str, Any]] = [
    # --- Pitavastatina (fármaco de la plataforma) ---
    {"molecula": "Pitavastatina", "dosis": "1 mg", "dosis_mg": 1, "reduccion": 0.31, "pitava": True,
     "fuente": "Ficha técnica / ensayos de dosis-respuesta"},
    {"molecula": "Pitavastatina", "dosis": "2 mg", "dosis_mg": 2, "reduccion": 0.39, "pitava": True,
     "fuente": "Ficha técnica; PATROL (no inferior a atorvastatina 10 mg)"},
    {"molecula": "Pitavastatina", "dosis": "4 mg", "dosis_mg": 4, "reduccion": 0.45, "pitava": True,
     "fuente": "Ficha técnica; REAL-CAD y REPRIEVE usaron 4 mg"},
    # --- Rosuvastatina (VOYAGER) ---
    {"molecula": "Rosuvastatina", "dosis": "5 mg", "dosis_mg": 5, "reduccion": 0.39, "pitava": False,
     "fuente": "VOYAGER (39%)"},
    {"molecula": "Rosuvastatina", "dosis": "10 mg", "dosis_mg": 10, "reduccion": 0.44, "pitava": False,
     "fuente": "VOYAGER (44%)"},
    {"molecula": "Rosuvastatina", "dosis": "20 mg", "dosis_mg": 20, "reduccion": 0.50, "pitava": False,
     "fuente": "VOYAGER (50%)"},
    {"molecula": "Rosuvastatina", "dosis": "40 mg", "dosis_mg": 40, "reduccion": 0.55, "pitava": False,
     "fuente": "VOYAGER (55%)"},
    # --- Atorvastatina ---
    {"molecula": "Atorvastatina", "dosis": "10 mg", "dosis_mg": 10, "reduccion": 0.37, "pitava": False,
     "fuente": "VOYAGER / etiquetado"},
    {"molecula": "Atorvastatina", "dosis": "20 mg", "dosis_mg": 20, "reduccion": 0.43, "pitava": False,
     "fuente": "VOYAGER / etiquetado"},
    {"molecula": "Atorvastatina", "dosis": "40 mg", "dosis_mg": 40, "reduccion": 0.49, "pitava": False,
     "fuente": "VOYAGER / etiquetado"},
    {"molecula": "Atorvastatina", "dosis": "80 mg", "dosis_mg": 80, "reduccion": 0.55, "pitava": False,
     "fuente": "VOYAGER / etiquetado"},
    # --- Simvastatina ---
    {"molecula": "Simvastatina", "dosis": "20 mg", "dosis_mg": 20, "reduccion": 0.35, "pitava": False,
     "fuente": "VOYAGER / etiquetado"},
    {"molecula": "Simvastatina", "dosis": "40 mg", "dosis_mg": 40, "reduccion": 0.41, "pitava": False,
     "fuente": "VOYAGER / etiquetado"},
    # --- Pravastatina ---
    {"molecula": "Pravastatina", "dosis": "40 mg", "dosis_mg": 40, "reduccion": 0.30, "pitava": False,
     "fuente": "Etiquetado; PREVAIL-US: pitavastatina 4 mg superior a pravastatina 40 mg"},
    # --- Fluvastatina / Lovastatina ---
    {"molecula": "Fluvastatina XL", "dosis": "80 mg", "dosis_mg": 80, "reduccion": 0.35, "pitava": False,
     "fuente": "Etiquetado"},
    {"molecula": "Lovastatina", "dosis": "40 mg", "dosis_mg": 40, "reduccion": 0.31, "pitava": False,
     "fuente": "Etiquetado"},
]

# Combinación con ezetimiba: suma aproximada de ~18–20 puntos porcentuales de reducción adicional.
EZETIMIBE_EXTRA = 0.19

MMOL_TO_MGDL = 38.67  # 1 mmol/L de LDL-C ≈ 38,7 mg/dL
CTT_RRR_PER_MMOL = 0.22  # 22% de reducción de eventos vasculares mayores por mmol/L (CTT, Lancet 2010)


def statin_intensity(reduction: float) -> str:
    if reduction >= 0.50:
        return "Alta"
    if reduction >= 0.30:
        return "Moderada"
    return "Baja"


def ldl_event_reduction(absolute_ldl_drop_mgdl: float, years: str = "por año-tratamiento") -> float:
    """Traduce una reducción absoluta de LDL-C a reducción relativa esperable de eventos (CTT).

    Usa la forma multiplicativa: RRR = 1 - (1 - 0,22)^(ΔLDL en mmol/L).
    Es una estimación poblacional orientativa, no una promesa individual.
    """
    if absolute_ldl_drop_mgdl <= 0:
        return 0.0
    mmol = float(absolute_ldl_drop_mgdl) / MMOL_TO_MGDL
    return 1.0 - (1.0 - CTT_RRR_PER_MMOL) ** mmol


def statin_comparison_table(baseline_ldl: float, goal_ldl: float, with_ezetimibe: bool = False) -> pd.DataFrame:
    """Compara todas las estatinas frente a la meta del paciente."""
    rows = []
    for item in STATIN_LIBRARY:
        red = float(item["reduccion"]) + (EZETIMIBE_EXTRA if with_ezetimibe else 0.0)
        red = min(red, 0.85)
        projected = float(baseline_ldl) * (1.0 - red)
        drop = float(baseline_ldl) - projected
        reaches = projected <= float(goal_ldl)
        rows.append({
            "Estatina": f"{item['molecula']} {item['dosis']}",
            "Molécula": item["molecula"],
            "Intensidad": statin_intensity(float(item["reduccion"])),
            "Reducción LDL-C %": round(red * 100, 1),
            "LDL-C proyectado": round(projected, 0),
            "Alcanza meta": "✅ Sí" if reaches else "❌ No",
            "Distancia a meta": 0 if reaches else round(projected - float(goal_ldl), 0),
            "Δ LDL-C absoluto": round(drop, 0),
            "RRR eventos estimada %": round(ldl_event_reduction(drop) * 100, 1),
            "Es pitavastatina": bool(item["pitava"]),
            "Fuente de la magnitud": item["fuente"],
        })
    df = pd.DataFrame(rows)
    return df.sort_values("Reducción LDL-C %", ascending=False).reset_index(drop=True)


# ============================================================
# 2) ESTUDIOS QUE RESPALDAN EL USO DE PITAVASTATINA
# ============================================================

PIVOTAL_STUDIES: List[Dict[str, str]] = [
    {
        "Estudio": "REAL-CAD (Circulation 2018;137:1997-2009)",
        "Diseño": "Aleatorizado, 13.054 pacientes japoneses con enfermedad coronaria estable",
        "Comparación": "Pitavastatina 4 mg/día vs 1 mg/día",
        "Resultado": "Endpoint primario 4,3% vs 5,4%; HR 0,81 (IC95% 0,69–0,95); p=0,01",
        "Qué demuestra": "Con la misma molécula, la dosis alta reduce eventos cardiovasculares: la titulación de pitavastatina tiene impacto en desenlaces duros.",
        "Límite": "Población japonesa; extrapolar con cautela a otras etnias y perfiles de riesgo.",
    },
    {
        "Estudio": "REPRIEVE (NEJM 2023;389:687-699)",
        "Diseño": "Aleatorizado, doble ciego, 7.769 personas con VIH y riesgo CV bajo-moderado; mediana 5,1 años",
        "Comparación": "Pitavastatina 4 mg/día vs placebo",
        "Resultado": "MACE 4,81 vs 7,32 por 1.000 personas-año; ~35% de reducción relativa (p=0,002); detenido precozmente por eficacia",
        "Qué demuestra": "Evidencia de prevención primaria con pitavastatina en una población donde las interacciones con antirretrovirales condicionan la elección de estatina.",
        "Límite": "Población específica con VIH; el beneficio absoluto depende del riesgo basal.",
    },
    {
        "Estudio": "PATROL (Circ J 2011;75:1380-1387)",
        "Diseño": "Head-to-head aleatorizado, 302 pacientes",
        "Comparación": "Pitavastatina 2 mg vs atorvastatina 10 mg vs rosuvastatina 2,5 mg",
        "Resultado": "Las tres redujeron LDL-C de forma similar (~40–45%), con perfiles de seguridad comparables",
        "Qué demuestra": "A dosis equipotentes, pitavastatina no es inferior a atorvastatina ni rosuvastatina en reducción de LDL-C.",
        "Límite": "Dosis bajas-medias; no evalúa desenlaces cardiovasculares.",
    },
    {
        "Estudio": "PREVAIL-US (J Clin Lipidol 2012)",
        "Diseño": "Aleatorizado en hiperlipidemia primaria / dislipidemia mixta",
        "Comparación": "Pitavastatina 4 mg vs pravastatina 40 mg",
        "Resultado": "Pitavastatina 4 mg superior a pravastatina 40 mg en reducción de LDL-C",
        "Qué demuestra": "Dentro de la intensidad moderada, la elección de molécula y dosis cambia la probabilidad de llegar a meta.",
        "Límite": "Desenlace subrogado (LDL-C), no eventos.",
    },
    {
        "Estudio": "J-PREDICT",
        "Diseño": "Aleatorizado, 1.269 participantes con intolerancia a la glucosa (IGT)",
        "Comparación": "Pitavastatina + estilo de vida vs estilo de vida solo",
        "Resultado": "Menor incidencia de diabetes de novo en el grupo con pitavastatina",
        "Qué demuestra": "A diferencia del efecto diabetogénico de clase descrito para otras estatinas, pitavastatina se comporta como neutra o favorable sobre el metabolismo glucídico.",
        "Límite": "Población con IGT; requiere confirmación en otras poblaciones y no autoriza a indicarla como prevención de diabetes.",
    },
    {
        "Estudio": "CTT Collaboration (Lancet 2010;376:1670-1681)",
        "Diseño": "Metaanálisis de datos individuales, 170.000 participantes en 26 ensayos",
        "Comparación": "Descenso de LDL-C con estatinas vs control / terapia más intensiva",
        "Resultado": "22% de reducción de eventos vasculares mayores por cada 1 mmol/L (≈38,7 mg/dL) de descenso de LDL-C",
        "Qué demuestra": "El beneficio depende de la MAGNITUD del descenso de LDL-C, no de la marca: permite traducir la brecha a meta en reducción esperable de eventos.",
        "Límite": "Estimación poblacional promedio; no reemplaza el riesgo absoluto individual.",
    },
    {
        "Estudio": "CPIC 2022 — SLCO1B1, ABCG2 y CYP2C9 (Clin Pharmacol Ther)",
        "Diseño": "Guía de farmacogenómica sobre síntomas musculares asociados a estatinas (SAMS)",
        "Comparación": "Variante rs4149056 (SLCO1B1 c.521T>C) entre distintas estatinas",
        "Resultado": "La variante aumenta la exposición sistémica; su impacto sobre eficacia es mínimo para pravastatina, rosuvastatina y pitavastatina, y máximo para simvastatina",
        "Qué demuestra": "La farmacogenómica permite elegir la estatina según el riesgo muscular individual: base concreta de lipidología de precisión.",
        "Límite": "El genotipo no sustituye la evaluación clínica ni excluye toxicidad muscular por otras causas.",
    },
]


# ============================================================
# 3) LIPIDOLOGÍA DE PRECISIÓN
# ============================================================
# Objetivos orientativos por categoría de riesgo (mg/dL).
APOB_GOALS = {
    "Muy alto riesgo / ASCVD": 65,
    "Alto riesgo": 80,
    "Hipercolesterolemia familiar sin ASCVD": 80,
    "Bajo / moderado": 100,
    "Personalizado": 80,
}


def non_hdl_goal(goal_ldl: float) -> float:
    """Meta de no-HDL-C = meta de LDL-C + 30 mg/dL."""
    return float(goal_ldl) + 30.0


def apob_goal(risk_category: str) -> int:
    return int(APOB_GOALS.get(risk_category, 80))


def remnant_cholesterol(ct: float, hdl: float, ldl: float) -> float:
    """Colesterol remanente = CT − HDL-C − LDL-C."""
    return max(0.0, float(ct) - float(hdl) - float(ldl))


def precision_panel(data: Dict[str, Any], goal_ldl: int) -> List[Dict[str, str]]:
    """Evalúa discordancias y riesgo residual más allá del LDL-C."""
    findings: List[Dict[str, str]] = []
    ldl = float(data.get("ldl", 0))
    ct = float(data.get("ct", 0))
    hdl = float(data.get("hdl", 0))
    tg = float(data.get("tg", 0))
    apob = float(data.get("apob", 0) or 0)
    lpa = float(data.get("lpa", 0) or 0)
    risk = str(data.get("risk_category", "Alto riesgo"))

    nhdl = core.non_hdl(ct, hdl)
    nhdl_target = non_hdl_goal(goal_ldl)
    remnant = remnant_cholesterol(ct, hdl, ldl)
    ab_target = apob_goal(risk)

    ldl_at_goal = ldl <= goal_ldl

    # 1) LDL-C
    findings.append({
        "Marcador": "LDL-C",
        "Valor": f"{ldl:.0f} mg/dL",
        "Meta": f"< {goal_ldl} mg/dL",
        "Estado": "✅ En meta" if ldl_at_goal else "❌ Fuera de meta",
        "Lectura de precisión": "Mide masa de colesterol, no número de partículas aterogénicas.",
    })

    # 2) no-HDL-C
    findings.append({
        "Marcador": "No-HDL-C",
        "Valor": f"{nhdl:.0f} mg/dL",
        "Meta": f"< {nhdl_target:.0f} mg/dL",
        "Estado": "✅ En meta" if nhdl <= nhdl_target else "❌ Fuera de meta",
        "Lectura de precisión": "Captura todas las lipoproteínas aterogénicas, incluidas remanentes. Útil con TG elevados.",
    })

    # 3) ApoB
    if apob > 0:
        findings.append({
            "Marcador": "ApoB",
            "Valor": f"{apob:.0f} mg/dL",
            "Meta": f"< {ab_target} mg/dL",
            "Estado": "✅ En meta" if apob <= ab_target else "❌ Fuera de meta",
            "Lectura de precisión": "Una molécula de ApoB por partícula aterogénica: es el marcador más directo de carga de partículas.",
        })
    else:
        findings.append({
            "Marcador": "ApoB",
            "Valor": "No informada",
            "Meta": f"< {ab_target} mg/dL",
            "Estado": "⚠️ No disponible",
            "Lectura de precisión": "Solicitarla cambia la decisión cuando hay TG altos, diabetes, obesidad o síndrome metabólico.",
        })

    # 4) Lp(a)
    if lpa > 0:
        findings.append({
            "Marcador": "Lp(a)",
            "Valor": f"{lpa:.0f} mg/dL",
            "Meta": "< 50 mg/dL (umbral de riesgo)",
            "Estado": "✅ Bajo umbral" if lpa < 50 else "❌ Elevada",
            "Lectura de precisión": "Determinada genéticamente y no modificable con estatinas: si está elevada, exige metas de LDL-C/ApoB más estrictas.",
        })
    else:
        findings.append({
            "Marcador": "Lp(a)",
            "Valor": "No informada",
            "Meta": "< 50 mg/dL",
            "Estado": "⚠️ No disponible",
            "Lectura de precisión": "Se recomienda medirla al menos una vez en la vida: reclasifica el riesgo y no se ve en un perfil lipídico estándar.",
        })

    # 5) Colesterol remanente
    findings.append({
        "Marcador": "Colesterol remanente",
        "Valor": f"{remnant:.0f} mg/dL",
        "Meta": "< 30 mg/dL (orientativo)",
        "Estado": "✅ Aceptable" if remnant < 30 else "❌ Elevado",
        "Lectura de precisión": "CT − HDL-C − LDL-C. Riesgo residual asociado a triglicéridos y partículas remanentes.",
    })

    return findings


def discordance_alerts(data: Dict[str, Any], goal_ldl: int) -> List[str]:
    """Detecta el patrón clave de la lipidología de precisión: LDL-C 'en meta' con riesgo residual."""
    alerts: List[str] = []
    ldl = float(data.get("ldl", 0))
    ct = float(data.get("ct", 0))
    hdl = float(data.get("hdl", 0))
    tg = float(data.get("tg", 0))
    apob = float(data.get("apob", 0) or 0)
    lpa = float(data.get("lpa", 0) or 0)
    risk = str(data.get("risk_category", "Alto riesgo"))

    nhdl = core.non_hdl(ct, hdl)
    remnant = remnant_cholesterol(ct, hdl, ldl)
    ldl_at_goal = ldl <= goal_ldl

    if ldl_at_goal and nhdl > non_hdl_goal(goal_ldl):
        alerts.append(
            f"**Discordancia LDL-C / no-HDL-C:** el LDL-C está en meta ({ldl:.0f}) pero el no-HDL-C ({nhdl:.0f}) "
            f"supera su objetivo ({non_hdl_goal(goal_ldl):.0f}). Persiste carga aterogénica no capturada por el LDL-C."
        )
    if ldl_at_goal and apob > 0 and apob > apob_goal(risk):
        alerts.append(
            f"**Discordancia LDL-C / ApoB:** LDL-C en meta pero ApoB {apob:.0f} mg/dL por encima de "
            f"{apob_goal(risk)} mg/dL. Indica exceso de partículas aterogénicas pequeñas y densas: el riesgo real es mayor que el sugerido por el LDL-C."
        )
    if tg >= 150 and remnant >= 30:
        alerts.append(
            f"**Riesgo residual por remanentes:** triglicéridos {tg:.0f} mg/dL con colesterol remanente {remnant:.0f} mg/dL. "
            "En este escenario el LDL-C subestima el riesgo y conviene guiar por no-HDL-C o ApoB."
        )
    if tg >= 400:
        alerts.append(
            "**LDL-C calculado no confiable:** con triglicéridos ≥400 mg/dL la fórmula de Friedewald pierde validez. "
            "Usar LDL directo, no-HDL-C o ApoB."
        )
    if lpa >= 50:
        alerts.append(
            f"**Lp(a) elevada ({lpa:.0f} mg/dL):** riesgo genéticamente determinado que las estatinas no reducen. "
            "Justifica metas de LDL-C/ApoB más estrictas y control agresivo del resto de los factores."
        )
    if not alerts:
        alerts.append("No se detectaron discordancias mayores con los datos disponibles. Considerar ApoB y Lp(a) si aún no fueron medidas.")
    return alerts


# Diferenciales de pitavastatina relevantes para decidir "qué estatina, en qué paciente".
PRECISION_DIFFERENTIALS = [
    {
        "Eje de precisión": "Metabolismo glucídico",
        "Problema clínico": "Las estatinas tienen un efecto diabetogénico de clase, relevante en prediabetes y síndrome metabólico.",
        "Qué aporta pitavastatina": "Perfil neutro o favorable sobre la glucemia; J-PREDICT mostró menor incidencia de diabetes de novo en pacientes con IGT.",
        "Cómo se usa": "Priorizarla cuando el paciente tiene IGT/prediabetes y se busca evitar empeorar el control glucémico.",
    },
    {
        "Eje de precisión": "Farmacogenómica (SLCO1B1)",
        "Problema clínico": "La variante rs4149056 aumenta la exposición sistémica y el riesgo de síntomas musculares (SAMS), sobre todo con simvastatina.",
        "Qué aporta pitavastatina": "CPIC 2022 señala impacto mínimo de esa variante sobre pravastatina, rosuvastatina y pitavastatina.",
        "Cómo se usa": "Alternativa razonable ante SAMS previos o genotipo de riesgo, evitando la estatina más dependiente del transportador.",
    },
    {
        "Eje de precisión": "Polifarmacia y vía metabólica",
        "Problema clínico": "Las estatinas dependientes de CYP3A4 (simva, lova, atorva) se elevan con inhibidores frecuentes (macrólidos, azoles, ARV potenciados).",
        "Qué aporta pitavastatina": "Escasa dependencia de CYP3A4; metabolismo principalmente por glucuronidación (UGT1A3/2B7).",
        "Cómo se usa": "Útil en polifarmacia seleccionada, sin asumir ausencia de interacciones: siguen importando transportadores (ciclosporina, gemfibrozil).",
    },
    {
        "Eje de precisión": "Población con VIH",
        "Problema clínico": "El riesgo CV está aumentado y las interacciones con antirretrovirales limitan la elección de estatina.",
        "Qué aporta pitavastatina": "REPRIEVE aporta evidencia directa de reducción de eventos con 4 mg en esta población.",
        "Cómo se usa": "Es la estatina con evidencia de desenlaces específica en VIH; igual verificar el esquema ARV exacto.",
    },
    {
        "Eje de precisión": "Intensidad necesaria",
        "Problema clínico": "Si la brecha a meta exige >50% de reducción, una estatina de intensidad moderada no alcanza en monoterapia.",
        "Qué aporta pitavastatina": "Techo de ~45% con 4 mg (intensidad moderada alta); combinada con ezetimiba supera el 50%.",
        "Cómo se usa": "La app lo muestra explícitamente: cuando la brecha es grande, propone combinación o reconoce que otra intensidad es preferible.",
    },
]


# ============================================================
# 4) PÁGINA · COMPARADOR DE ESTATINAS
# ============================================================
def page_comparador():
    data, goal_ldl = core.build_base_data()
    data = core.apply_clinical_defaults(data)

    theme.page_hero(
        title="Comparador de estatinas",
        subtitle="Cuánto reduce el LDL-C cada estatina y dosis, cuáles alcanzan la meta de este paciente y qué "
                 "reducción de eventos cabe esperar según la evidencia.",
        eyebrow="Evidencia comparada",
        icon="⚖️",
    )

    theme.section("Escenario del paciente")
    c1, c2, c3 = st.columns(3)
    with c1:
        baseline = st.number_input("LDL-C basal, mg/dL", 40.0, 500.0,
                                   float(st.session_state.get("cmp_baseline", data.get("baseline_ldl", data["ldl"]))),
                                   1.0, key="cmp_baseline")
    with c2:
        st.metric("Meta de LDL-C", f"< {goal_ldl} mg/dL", data.get("risk_category", ""))
    with c3:
        with_eze = st.checkbox("Sumar ezetimiba a todas", value=False, key="cmp_eze",
                               help="Agrega ~19 puntos porcentuales de reducción adicional (estimación conservadora).")

    df = statin_comparison_table(float(baseline), float(goal_ldl), with_ezetimibe=bool(with_eze))
    need_pct = 0.0 if baseline <= 0 else max(0.0, (float(baseline) - float(goal_ldl)) / float(baseline) * 100.0)

    k1, k2, k3 = st.columns(3)
    with k1:
        theme.stat_card("Reducción necesaria", f"{need_pct:.0f}%", f"De {baseline:.0f} a <{goal_ldl} mg/dL", "🎯")
    with k2:
        n_ok = int((df["Alcanza meta"] == "✅ Sí").sum())
        theme.stat_card("Opciones que llegan", f"{n_ok} de {len(df)}", "Esquemas que alcanzan la meta", "✅")
    with k3:
        pit = df[df["Es pitavastatina"]]
        pit_ok = int((pit["Alcanza meta"] == "✅ Sí").sum())
        theme.stat_card("Pitavastatina", f"{pit_ok} de {len(pit)}", "Dosis que alcanzan la meta", "💊")

    theme.section("Tabla comparativa", "Ordenada por potencia. La columna de eventos aplica la relación del metaanálisis CTT.")
    show_cols = ["Estatina", "Intensidad", "Reducción LDL-C %", "LDL-C proyectado", "Alcanza meta",
                 "Distancia a meta", "Δ LDL-C absoluto", "RRR eventos estimada %", "Fuente de la magnitud"]
    st.dataframe(df[show_cols], width="stretch", hide_index=True)

    # Gráfico comparativo
    if core.go is not None and not df.empty:
        colors = ["#12A594" if p else "#9DB6CE" for p in df["Es pitavastatina"]]
        fig = core.go.Figure()
        fig.add_trace(core.go.Bar(
            x=df["Estatina"], y=df["LDL-C proyectado"],
            marker_color=colors,
            text=[f"{v:.0f}" for v in df["LDL-C proyectado"]],
            textposition="outside", name="LDL-C proyectado",
        ))
        fig.add_hline(y=float(goal_ldl), line_dash="dash", line_color="#DC2F3C",
                      annotation_text=f"Meta <{goal_ldl} mg/dL")
        fig.update_layout(
            title="LDL-C proyectado por estatina (verde = pitavastatina)",
            yaxis_title="LDL-C (mg/dL)", xaxis_title="", height=520, showlegend=False,
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        )
        fig.update_xaxes(tickangle=-45)
        st.plotly_chart(fig, width="stretch", key="statin_comparison_chart")

    theme.section("Traducción a eventos (CTT)")
    st.info(
        "El metaanálisis CTT (170.000 participantes, 26 ensayos) mostró **22% de reducción de eventos vasculares "
        "mayores por cada 1 mmol/L (≈38,7 mg/dL) de descenso de LDL-C**. Por eso lo que importa es la MAGNITUD del "
        "descenso alcanzado y sostenido, más que la marca de la estatina."
    )
    pit_rows = df[df["Es pitavastatina"]].sort_values("Reducción LDL-C %", ascending=False)
    if not pit_rows.empty:
        best = pit_rows.iloc[0]
        st.success(
            f"Con **{best['Estatina']}** el LDL-C proyectado es **{best['LDL-C proyectado']:.0f} mg/dL** "
            f"(descenso de {best['Δ LDL-C absoluto']:.0f} mg/dL), lo que equivale a una reducción relativa estimada "
            f"de eventos de **{best['RRR eventos estimada %']:.0f}%** según la relación del CTT. "
            f"{'Alcanza la meta.' if best['Alcanza meta'] == '✅ Sí' else 'No alcanza la meta: considerar combinación con ezetimiba o mayor intensidad.'}"
        )

    theme.section("Cómo leer esta comparación")
    st.markdown(
        """
- **La potencia no es el único criterio.** Si la brecha exige >50% de reducción, la intensidad moderada no alcanza en
  monoterapia y hay que combinar o cambiar de intensidad. La app lo muestra en lugar de ocultarlo.
- **A dosis equipotentes las diferencias se achican.** PATROL mostró reducciones similares (~40–45%) entre
  pitavastatina 2 mg, atorvastatina 10 mg y rosuvastatina 2,5 mg.
- **La elección se decide por el paciente, no por el ranking.** Metabolismo glucídico, genotipo SLCO1B1, polifarmacia
  y población (p. ej. VIH) son los que inclinan la balanza — eso es lo que desarrolla la página de
  **Lipidología de precisión**.
"""
    )

    theme.footer(core.APP_VERSION, core.APP_DATE, st.session_state.get("cfg_regulatory", ""))


# ============================================================
# 5) PÁGINA · LIPIDOLOGÍA DE PRECISIÓN
# ============================================================
def page_precision():
    data, goal_ldl = core.build_base_data()
    data = core.apply_clinical_defaults(data)

    theme.page_hero(
        title="Lipidología de precisión",
        subtitle="Más allá del LDL-C: carga de partículas (ApoB), Lp(a), colesterol remanente y farmacogenómica "
                 "para decidir qué estatina conviene a este paciente en particular.",
        eyebrow="Decisión individualizada",
        icon="🧬",
    )

    st.info(
        "El LDL-C mide **masa de colesterol**, no el **número de partículas aterogénicas**. Cuando ambos no coinciden "
        "(discordancia), el LDL-C puede subestimar el riesgo — algo frecuente en diabetes, obesidad, síndrome "
        "metabólico e hipertrigliceridemia."
    )

    theme.section("Marcadores avanzados del paciente")
    c1, c2 = st.columns(2)
    with c1:
        apob_in = st.number_input("ApoB, mg/dL (0 = no informada)", 0.0, 300.0,
                                  float(st.session_state.get("apob_input", 0.0)), 1.0, key="prec_apob")
    with c2:
        lpa_in = st.number_input("Lp(a), mg/dL (0 = no informada)", 0.0, 500.0,
                                 float(st.session_state.get("lpa_input", 0.0)), 1.0, key="prec_lpa")
    data["apob"] = float(apob_in)
    data["lpa"] = float(lpa_in)

    panel = precision_panel(data, int(goal_ldl))
    st.dataframe(pd.DataFrame(panel), width="stretch", hide_index=True)

    theme.section("Discordancias y riesgo residual")
    alerts = discordance_alerts(data, int(goal_ldl))
    for a in alerts:
        if a.startswith("No se detectaron"):
            st.success(a)
        else:
            st.warning(a)

    theme.section("Qué aporta pitavastatina en cada eje de precisión",
                  "Aquí se ve por qué la elección de molécula no es intercambiable.")
    st.dataframe(pd.DataFrame(PRECISION_DIFFERENTIALS), width="stretch", hide_index=True)

    theme.section("Evidencia que respalda el uso de pitavastatina")
    st.dataframe(pd.DataFrame(PIVOTAL_STUDIES), width="stretch", hide_index=True)

    with st.expander("📌 Conceptos clave de lipidología de precisión", expanded=False):
        st.markdown(
            """
- **ApoB:** hay una molécula de ApoB por cada partícula aterogénica (LDL, VLDL, IDL, remanentes, Lp(a)). Por eso
  estima la *carga de partículas*, que es lo que impacta en la pared arterial.
- **Discordancia ApoB / LDL-C:** frecuente en resistencia a la insulina. Con LDL-C "en meta" puede persistir un
  número alto de partículas pequeñas y densas y, con ello, riesgo residual.
- **No-HDL-C:** disponible en cualquier perfil lipídico (CT − HDL-C). Meta = meta de LDL-C + 30 mg/dL. Es el
  sustituto práctico de ApoB cuando no se dispone de ella.
- **Colesterol remanente (CT − HDL-C − LDL-C):** captura el riesgo asociado a triglicéridos y partículas remanentes.
- **Lp(a):** determinada genéticamente, no baja con estatinas; se mide al menos una vez en la vida y, si está
  elevada, obliga a metas más estrictas del resto de los lípidos.
- **Farmacogenómica (SLCO1B1):** la variante rs4149056 aumenta la exposición sistémica y el riesgo de síntomas
  musculares; su impacto es máximo con simvastatina y mínimo con pitavastatina, rosuvastatina y pravastatina
  (CPIC 2022).
"""
        )

    st.caption(
        "Los umbrales de ApoB (<65/<80/<100 mg/dL según riesgo), no-HDL-C (meta LDL + 30) y Lp(a) (≥50 mg/dL) son "
        "orientativos y deben contrastarse con la guía vigente y el laboratorio local."
    )

    theme.footer(core.APP_VERSION, core.APP_DATE, st.session_state.get("cfg_regulatory", ""))
