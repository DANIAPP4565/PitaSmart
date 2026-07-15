# core.py
# EUROPHARMA · PitaSmart — Motor clínico (lógica intacta extraída del app original).
# NO contiene UI de página: solo constantes, funciones de negocio y helpers de estado.

from __future__ import annotations

import re
import json
import html
import unicodedata
from io import BytesIO
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional

import pandas as pd
import streamlit as st

try:
    import plotly.graph_objects as go
except Exception:
    go = None

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.units import cm
    REPORTLAB_OK = True
except Exception:
    REPORTLAB_OK = False


# ============================================================
# CONFIGURACIÓN
# ============================================================


APP_VERSION = "3.1 - Estrategia a meta y despliegue público"
APP_DATE = "2026-07-14"

DEFAULTS = {
    "age": 58,
    "sex": "Femenino",
    "ct": 240.0,
    "ldl": 160.0,
    "hdl": 48.0,
    "tg": 180.0,
    "egfr": 85.0,
    "creatinine": 0.9,
    "glucose": 95.0,
    "hba1c": 5.6,
    "ast": 25.0,
    "alt": 28.0,
    "ck": 90.0,
    "tsh": 2.0,
}

LDL_REDUCTION_BY_DOSE = {
    "1 mg": 0.31,
    "2 mg": 0.39,
    "4 mg": 0.45,
}

OBJETIVOS_LDL = {
    "Bajo / moderado": 100,
    "Alto riesgo": 70,
    "Muy alto riesgo / ASCVD": 55,
    "Hipercolesterolemia familiar sin ASCVD": 70,
    "Personalizado": 70,
}

FUENTES = [
    "Prospecto/ficha técnica vigente de pitavastatina: indicaciones, dosis, contraindicaciones, interacciones y seguridad; revalidar según producto y jurisdicción.",
    "DailyMed/FDA: etiquetado de pitavastatina para restricciones con ciclosporina, gemfibrozil, eritromicina, rifampicina, fibratos, niacina y colchicina.",
    "ANMAT Argentina: pitavastatina como tratamiento para reducción de colesterol total y LDL-C en adultos, según prospecto local aprobado.",
    "Girona Brumós L. (coord.). Introducción a las interacciones farmacológicas, 1ª ed.; capítulos 1 y 8, incluida la sección de estatinas y Tabla 21.",
    "NIH ClinicalInfo: interacciones entre estatinas y antirretrovirales; verificar el esquema ARV específico y la actualización vigente.",
    "Guías de manejo de dislipidemia: intensidad de estatinas, objetivos LDL-C/no-HDL-C/ApoB según riesgo.",
    "REPRIEVE: evidencia de resultados cardiovasculares con pitavastatina 4 mg en personas con VIH; interpretar población, beneficios y seguridad.",
    "REAL-CAD: comparación de pitavastatina 4 mg frente a 1 mg en enfermedad coronaria estable; considerar aplicabilidad poblacional.",
    "Ensayos de combinación pitavastatina + ezetimiba: mayor reducción de LDL-C que la monoterapia; verificar formulación y prospecto local.",
]

# Base de conocimiento estructurada. Las entradas distinguen:
# - Específica pitavastatina: respaldada por ficha técnica/label.
# - Riesgo de clase: señal farmacodinámica o farmacocinética descrita para estatinas.
# - Contextual: alerta para no extrapolar automáticamente interacciones de otras estatinas.
INTERACCIONES = {
    "ciclosporina": {
        "nivel": "ROJO",
        "alcance": "Específica pitavastatina",
        "evidencia": "Ficha técnica vigente + mecanismo de transportadores descrito en literatura",
        "mecanismo": "Aumento marcado de la exposición a pitavastatina; posible participación de transportadores hepáticos.",
        "mensaje": "Interacción mayor: aumenta la exposición a pitavastatina y el riesgo de miopatía/rabdomiólisis.",
        "accion": "No recomendar pitavastatina durante uso concomitante; considerar alternativa y verificar prospecto local.",
        "monitoreo": "No se resuelve solo con CK: priorizar evitar la combinación.",
        "riesgo_muscular": True,
        "regex": r"\bciclosporina\b|\bcyclosporine\b",
    },
    "gemfibrozil": {
        "nivel": "ROJO",
        "alcance": "Específica pitavastatina + riesgo de clase",
        "evidencia": "Ficha técnica vigente + capítulo 8 del libro",
        "mecanismo": "Toxicidad muscular aditiva; gemfibrozil también puede interferir con transportadores/metabolismo de estatinas.",
        "mensaje": "Combinación a evitar por incremento del riesgo de miopatía y rabdomiólisis.",
        "accion": "Evitar combinación; considerar estrategia alternativa para triglicéridos.",
        "monitoreo": "Si existiera exposición no planificada: síntomas musculares, CK y función renal según clínica.",
        "riesgo_muscular": True,
        "regex": r"\bgemfibrozil\b|\bgemfibrocilo\b",
    },
    "eritromicina": {
        "nivel": "AMARILLO",
        "alcance": "Específica pitavastatina",
        "evidencia": "Ficha técnica vigente",
        "mecanismo": "Aumento significativo de la exposición a pitavastatina.",
        "mensaje": "Aumenta la exposición a pitavastatina y el riesgo de toxicidad muscular.",
        "accion": "Si se usa concomitantemente, no superar 1 mg/día de pitavastatina.",
        "monitoreo": "Vigilar mialgias/debilidad; CK y función renal si hay síntomas.",
        "riesgo_muscular": True,
        "regex": r"\beritromicina\b|\berythromycin\b",
    },
    "rifampicina": {
        "nivel": "AMARILLO",
        "alcance": "Específica pitavastatina",
        "evidencia": "Ficha técnica vigente",
        "mecanismo": "Aumenta el pico de exposición a pitavastatina; interacción compleja con transportadores/inducción.",
        "mensaje": "Puede aumentar la exposición pico a pitavastatina y el riesgo de toxicidad muscular.",
        "accion": "Si se usa concomitantemente, no superar 2 mg/día de pitavastatina.",
        "monitoreo": "Vigilar tolerancia muscular y revisar cambios al iniciar o suspender rifampicina.",
        "riesgo_muscular": True,
        "regex": r"\brifampicina\b|\brifampin\b|\brifampicina\b",
    },
    "fibratos": {
        "nivel": "AMARILLO",
        "alcance": "Específica pitavastatina + riesgo de clase",
        "evidencia": "Ficha técnica vigente + capítulo 8 del libro",
        "mecanismo": "Suma de toxicidad muscular; el riesgo aumenta con insuficiencia renal e hipotiroidismo.",
        "mensaje": "Los fibratos pueden aumentar el riesgo de miopatía/rabdomiólisis con estatinas, incluida pitavastatina.",
        "accion": "Usar solo si el beneficio supera el riesgo; gemfibrozil se evalúa por separado como combinación a evitar.",
        "monitoreo": "Preguntar por mialgias/debilidad; CK si síntomas o alto riesgo; vigilar función renal.",
        "riesgo_muscular": True,
        "regex": r"\bfenofibrato\b|\bfenofibrate\b|\bbezafibrato\b|\bciprofibrato\b|\bclofibrato\b|\bfibrato(?:s)?\b|\bfibrate(?:s)?\b",
    },
    "niacina hipolipemiante": {
        "nivel": "AMARILLO",
        "alcance": "Específica pitavastatina",
        "evidencia": "Ficha técnica vigente",
        "mecanismo": "Toxicidad muscular aditiva, especialmente con dosis hipolipemiantes de niacina.",
        "mensaje": "Dosis hipolipemiantes de niacina (aprox. ≥1 g/día) pueden aumentar miopatía/rabdomiólisis.",
        "accion": "Confirmar dosis; mantener combinación solo si el beneficio supera el riesgo.",
        "monitoreo": "Síntomas musculares; CK si clínica; reevaluar si aparece debilidad o dolor no explicado.",
        "riesgo_muscular": True,
        "regex": r"\bniacina\b|\bniacin\b|\bacido\s+nicotinico\b",
    },
    "colchicina": {
        "nivel": "AMARILLO",
        "alcance": "Específica pitavastatina",
        "evidencia": "Ficha técnica vigente",
        "mecanismo": "Se han comunicado miopatía y rabdomiólisis con colchicina y estatinas.",
        "mensaje": "Puede aumentar el riesgo de toxicidad muscular con pitavastatina.",
        "accion": "Valorar riesgo/beneficio, dosis, función renal y duración de la combinación.",
        "monitoreo": "Mialgias, debilidad y CK si síntomas; especial atención en insuficiencia renal.",
        "riesgo_muscular": True,
        "regex": r"\bcolchicina\b|\bcolchicine\b",
    },
    "daptomicina": {
        "nivel": "AMARILLO",
        "alcance": "Riesgo de clase / interacción potencial",
        "evidencia": "Capítulo 1 del libro: suma de efectos musculares",
        "mecanismo": "Toxicidad muscular farmacodinámica aditiva.",
        "mensaje": "Señal potencial de mayor toxicidad muscular por asociación de daptomicina con una estatina.",
        "accion": "Revisar necesidad de combinación y protocolo del antibiótico; no asumir contraindicación específica de pitavastatina.",
        "monitoreo": "CK según protocolo de daptomicina y clínica muscular; revisar función renal.",
        "riesgo_muscular": True,
        "regex": r"\bdaptomicina\b|\bdaptomycin\b",
    },
    "ezetimiba": {
        "nivel": "AZUL",
        "alcance": "Riesgo de clase / señal potencial",
        "evidencia": "Capítulos 1 y 8 del libro; señal de toxicidad muscular descrita para estatinas",
        "mecanismo": "Posible suma de efectos musculares; la combinación también se usa terapéuticamente para mayor reducción de LDL-C.",
        "mensaje": "No es una contraindicación automática: existe una señal potencial de miopatía que debe contextualizarse.",
        "accion": "Puede ser una combinación válida; vigilar síntomas y evitar sobrerreaccionar a una señal de clase.",
        "monitoreo": "CK solo si síntomas o alto riesgo; documentar síntomas basales.",
        "riesgo_muscular": True,
        "regex": r"\bezetimiba\b|\bezetimibe\b",
    },
    "ácido fusídico sistémico": {
        "nivel": "AMARILLO",
        "alcance": "Riesgo de clase / no específica",
        "evidencia": "Capítulo 8 del libro: casos con otras estatinas",
        "mecanismo": "Interacción descrita con algunas estatinas, con aumento de exposición y rabdomiólisis; no extrapolar magnitud sin evidencia específica.",
        "mensaje": "Señal relevante de clase con ácido fusídico sistémico; la evidencia citada no es específica de pitavastatina.",
        "accion": "Verificar ficha técnica local y necesidad de suspender temporalmente la estatina durante tratamiento sistémico.",
        "monitoreo": "Síntomas musculares, CK y función renal si clínica.",
        "riesgo_muscular": True,
        "regex": r"\bacido\s+fusidico\b|\bfusidic\s+acid\b|\bfusidato\b",
    },
    "resinas de intercambio iónico": {
        "nivel": "AZUL",
        "alcance": "Contextual / potencial de absorción",
        "evidencia": "Capítulo 1 del libro: interacción de absorción descrita con algunas estatinas",
        "mecanismo": "Adsorción intestinal y reducción potencial de biodisponibilidad de fármacos orales.",
        "mensaje": "Posible reducción de absorción; la evidencia del libro no establece una regla específica para pitavastatina.",
        "accion": "Revisar prospecto del producto y considerar separación horaria si corresponde.",
        "monitoreo": "Respuesta LDL-C y adherencia; no requiere CK por este mecanismo.",
        "riesgo_muscular": False,
        "regex": r"\bcolestiramina\b|\bcholestyramine\b|\bcolestipol\b|\bcolesevelam\b",
    },
    "claritromicina / telitromicina": {
        "nivel": "AZUL",
        "alcance": "Contextual: interacción de clase no extrapolable",
        "evidencia": "Capítulos 6 y 8 del libro: macrólidos e inhibición CYP3A4 en estatinas susceptibles",
        "mecanismo": "Los macrólidos pueden elevar algunas estatinas dependientes de CYP3A4; pitavastatina tiene baja dependencia de CYP3A4.",
        "mensaje": "Alerta contextual: no asumir la misma magnitud de interacción que con simvastatina/lovastatina/atorvastatina.",
        "accion": "Revisar evidencia específica del antibiótico y pitavastatina; eritromicina tiene una regla propia en esta base.",
        "monitoreo": "Síntomas musculares si coexistencia y factores de riesgo.",
        "riesgo_muscular": False,
        "regex": r"\bclaritromicina\b|\bclarithromycin\b|\btelitromicina\b|\btelithromycin\b",
    },
    "azoles sistémicos": {
        "nivel": "AZUL",
        "alcance": "Contextual: interacción de clase no extrapolable",
        "evidencia": "Libro: inhibición CYP y riesgo con estatinas susceptibles",
        "mecanismo": "Inhibición enzimática relevante para estatinas dependientes de CYP; la pitavastatina posee un perfil metabólico diferente.",
        "mensaje": "Alerta contextual para revisión individual; no clasificar automáticamente como interacción mayor de pitavastatina.",
        "accion": "Confirmar compuesto, vía, duración y fuente específica actualizada.",
        "monitoreo": "Clínica muscular y hepática según contexto.",
        "riesgo_muscular": False,
        "regex": r"\bketoconazol\b|\bketoconazole\b|\bitraconazol\b|\bitraconazole\b|\bposaconazol\b|\bposaconazole\b|\bvoriconazol\b|\bvoriconazole\b|\bfluconazol\b|\bfluconazole\b",
    },
    "antirretrovirales potenciados": {
        "nivel": "AMARILLO",
        "alcance": "Requiere verificación por esquema ARV",
        "evidencia": "NIH ClinicalInfo + principio general de transportadores/interacciones",
        "mecanismo": "Ritonavir/cobicistat pueden modificar metabolismo y transportadores; el efecto depende del ARV y de la estatina.",
        "mensaje": "Posible interacción clínicamente relevante con esquemas potenciados; no usar una regla única para todos los ARV.",
        "accion": "Verificar la combinación exacta en tablas NIH/Liverpool y ajustar o monitorizar según esquema.",
        "monitoreo": "Toxicidad muscular y revisión de dosis al cambiar el esquema ARV.",
        "riesgo_muscular": True,
        "regex": r"\britonavir\b|\bcobicistat\b|\bdarunavir\b|\batazanavir\b|\blopinavir\b",
    },
    "bictegravir / dolutegravir": {
        "nivel": "AZUL",
        "alcance": "Contextual ARV",
        "evidencia": "NIH ClinicalInfo: la interacción debe verificarse por combinación exacta",
        "mecanismo": "No debe agruparse automáticamente con inhibidores de proteasa potenciados.",
        "mensaje": "Detección informativa: revisar esquema completo, pero no etiquetar por defecto como interacción mayor.",
        "accion": "Consultar tabla ARV-estatina vigente para la combinación exacta.",
        "monitoreo": "Según esquema completo y factores del paciente.",
        "riesgo_muscular": False,
        "regex": r"\bbictegravir\b|\bdolutegravir\b",
    },
    "otra estatina concomitante": {
        "nivel": "AMARILLO",
        "alcance": "Riesgo de clase / duplicación terapéutica",
        "evidencia": "Principio farmacodinámico de suma de toxicidad muscular",
        "mecanismo": "Duplicación de inhibición HMG-CoA reductasa y potencial incremento de toxicidad muscular/hepática.",
        "mensaje": "Se detecta otra estatina en la lista: revisar si se trata de sustitución, transición o duplicación no intencional.",
        "accion": "No mantener doble estatina de rutina; reconciliar medicación antes de indicar pitavastatina.",
        "monitoreo": "Síntomas musculares, CK si clínica y función hepática según contexto.",
        "riesgo_muscular": True,
        "regex": r"\batorvastatina\b|\batorvastatin\b|\bsimvastatina\b|\bsimvastatin\b|\brosuvastatina\b|\brosuvastatin\b|\bpravastatina\b|\bpravastatin\b|\bfluvastatina\b|\bfluvastatin\b|\blovastatina\b|\blovastatin\b",
    },
}


# Ezetimiba se maneja como combinación hipolipemiante reconocida y no como
# una interacción problemática por defecto. La vigilancia muscular se decide
# por síntomas, riesgo acumulado y contexto clínico.
INTERACCIONES.pop("ezetimiba", None)

THERAPEUTIC_COMBINATIONS = {
    "ezetimiba": {
        "regex": r"\bezetimiba\b|\bezetimibe\b",
        "tipo": "Combinación terapéutica reconocida",
        "mensaje": "Puede aumentar de manera relevante la reducción de LDL-C y la probabilidad de alcanzar la meta.",
        "accion": "Integrar como estrategia de intensificación; vigilar tolerancia según el perfil clínico, sin etiquetarla como interacción mayor automática.",
    }
}

# Reducciones promedio orientativas usadas solo para simulación clínica.
# La respuesta individual debe confirmarse con un nuevo perfil lipídico.
THERAPEUTIC_SCENARIOS = {
    "Pitavastatina 1 mg": {
        "reduction": 0.31, "type": "Monoterapia", "pitavastatin": True, "dose_mg": 1,
        "evidence": "Reducción promedio orientativa por dosis.",
    },
    "Pitavastatina 2 mg": {
        "reduction": 0.39, "type": "Monoterapia", "pitavastatin": True, "dose_mg": 2,
        "evidence": "Reducción promedio orientativa por dosis.",
    },
    "Pitavastatina 4 mg": {
        "reduction": 0.45, "type": "Monoterapia", "pitavastatin": True, "dose_mg": 4,
        "evidence": "Máxima monoterapia habitual cuando no existen restricciones.",
    },
    "Pitavastatina 1 mg + ezetimiba": {
        "reduction": 0.45, "type": "Combinación", "pitavastatin": True, "dose_mg": 1,
        "evidence": "Estimación conservadora de efecto combinado; confirmar respuesta real.",
    },
    "Pitavastatina 2 mg + ezetimiba": {
        "reduction": 0.51, "type": "Combinación", "pitavastatin": True, "dose_mg": 2,
        "evidence": "Reducción promedio aproximada informada en ensayos de combinación.",
    },
    "Pitavastatina 4 mg + ezetimiba": {
        "reduction": 0.58, "type": "Combinación", "pitavastatin": True, "dose_mg": 4,
        "evidence": "Reducción promedio aproximada informada en ensayos de combinación.",
    },
    "Estatina de alta intensidad (comparador)": {
        "reduction": 0.50, "type": "Comparador", "pitavastatin": False, "dose_mg": None,
        "evidence": "Umbral orientativo de alta intensidad; no representa una molécula o dosis específica.",
    },
    "Estatina máxima tolerada + ezetimiba (comparador)": {
        "reduction": 0.60, "type": "Comparador", "pitavastatin": False, "dose_mg": None,
        "evidence": "Escenario comparativo; el efecto depende de la estatina y la respuesta individual.",
    },
}

EVIDENCE_MATRIX = [
    {
        "Contexto": "VIH con riesgo cardiovascular bajo-moderado",
        "Evidencia": "REPRIEVE",
        "Mensaje útil": "Pitavastatina 4 mg cuenta con evidencia directa de reducción de eventos en esta población.",
        "Límite": "No extrapolar automáticamente a todas las poblaciones ni omitir seguridad e interacciones del esquema ARV.",
    },
    {
        "Contexto": "Enfermedad coronaria estable",
        "Evidencia": "REAL-CAD",
        "Mensaje útil": "La dosis de 4 mg mostró mejores resultados que 1 mg en la población estudiada.",
        "Límite": "Considerar población, diseño y aplicabilidad al paciente individual.",
    },
    {
        "Contexto": "Necesidad de mayor reducción de LDL-C",
        "Evidencia": "Pitavastatina + ezetimiba",
        "Mensaje útil": "La combinación puede superar el efecto de la monoterapia y acercarse o superar 50% de reducción.",
        "Límite": "Confirmar disponibilidad, formulación, prospecto y respuesta real.",
    },
    {
        "Contexto": "Polifarmacia",
        "Evidencia": "Perfil farmacocinético",
        "Mensaje útil": "La baja dependencia de CYP3A4 puede ser relevante frente a algunas estatinas susceptibles.",
        "Límite": "No significa ausencia de interacciones: importan transportadores y toxicidad acumulativa.",
    },
]

INTERACTION_LEVEL_ORDER = {"ROJO": 3, "AMARILLO": 2, "AZUL": 1}
INTERACTION_LEVEL_LABEL = {
    "ROJO": "Mayor / evitar o contraindicación",
    "AMARILLO": "Precaución / ajuste / verificación",
    "AZUL": "Informativa / señal potencial",
}


LAB_FIELDS = {
    "ct": {
        "label": "Colesterol total",
        "patterns": [
            r"colesterol\s+total", r"\bcol\s*total\b", r"\bct\b", r"cholesterol\s+total",
        ],
        "range": (50, 600),
        "unit": "mg/dL",
    },
    "ldl": {
        "label": "LDL-C",
        "patterns": [
            r"colesterol\s+ldl", r"\bldl\b", r"\bc-?\s*ldl\b", r"\bcldl\b", r"low\s+density",
        ],
        "range": (10, 500),
        "unit": "mg/dL",
    },
    "hdl": {
        "label": "HDL-C",
        "patterns": [
            r"colesterol\s+hdl", r"\bhdl\b", r"\bc-?\s*hdl\b", r"\bchdl\b", r"high\s+density",
        ],
        "range": (5, 150),
        "unit": "mg/dL",
    },
    "tg": {
        "label": "Triglicéridos",
        "patterns": [
            r"trigliceridos", r"triglicéridos", r"\btg\b", r"triglycerides",
        ],
        "range": (20, 2000),
        "unit": "mg/dL",
    },
    "egfr": {
        "label": "eGFR / filtrado glomerular",
        "patterns": [
            r"\begfr\b", r"\bifge\b", r"\btfge\b", r"\bfge\b", r"filtrado\s+glomerular", r"ckd-?epi", r"mdrd",
        ],
        "range": (1, 200),
        "unit": "ml/min/1,73 m²",
    },
    "creatinine": {
        "label": "Creatinina",
        "patterns": [
            r"creatinina", r"creatinine",
        ],
        "range": (0.2, 20),
        "unit": "mg/dL",
    },
    "glucose": {
        "label": "Glucemia",
        "patterns": [
            r"glucemia", r"glucosa", r"glucose", r"glycemia",
        ],
        "range": (30, 700),
        "unit": "mg/dL",
    },
    "hba1c": {
        "label": "HbA1c",
        "patterns": [
            r"hba1c", r"hemoglobina\s+glicosilada", r"hemoglobina\s+glucosilada", r"a1c",
        ],
        "range": (3, 18),
        "unit": "%",
    },
    "ast": {
        "label": "AST/GOT",
        "patterns": [
            r"\btgo\b", r"\bast\b", r"\bgot\b", r"aspartato", r"transaminasa\s+glutamico\s+oxalacetica", r"transaminasa\s+glutámico\s+oxalacética",
        ],
        "range": (1, 1000),
        "unit": "U/L",
    },
    "alt": {
        "label": "ALT/GPT",
        "patterns": [
            r"\btgp\b", r"\balt\b", r"\bgpt\b", r"alanina", r"transaminasa\s+glutamico\s+piruvica", r"transaminasa\s+glutámico\s+pirúvica",
        ],
        "range": (1, 1000),
        "unit": "U/L",
    },
    "ck": {
        "label": "CK/CPK",
        "patterns": [
            r"\bck\b", r"\bcpk\b", r"creatin\s+quinasa", r"creatinfosfoquinasa", r"creatine\s+kinase",
        ],
        "range": (1, 20000),
        "unit": "U/L",
    },
    "tsh": {
        "label": "TSH",
        "patterns": [
            r"\btsh\b", r"tirotrofina", r"thyroid\s+stimulating",
        ],
        "range": (0.01, 100),
        "unit": "µUI/mL",
    },
    "age": {
        "label": "Edad",
        "patterns": [
            r"\bedad\b", r"\bage\b",
        ],
        "range": (1, 110),
        "unit": "años",
    },
}
def strip_accents(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "")
    return "".join(ch for ch in text if not unicodedata.combining(ch))


def norm_text(text: str) -> str:
    return strip_accents(text).lower().replace(",", ".")


def parse_number(s: str) -> Optional[float]:
    if not s:
        return None
    s = s.strip().replace(",", ".")
    s = re.sub(r"(?<=\d)\.(?=\d{3}\b)", "", s)  # 1.234 -> 1234 si parece separador miles
    try:
        return float(s)
    except Exception:
        return None


def numbers_from_text(text: str) -> List[float]:
    """Devuelve números del texto, excluyendo fechas. Mantiene orden de aparición."""
    text = re.sub(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", " ", text or "")
    raw = re.findall(r"(?<![A-Za-z])[-+]?\d{1,4}(?:[.,]\d+)?(?![A-Za-z])", text)
    nums = []
    for x in raw:
        n = parse_number(x)
        if n is not None:
            nums.append(n)
    return nums


def choose_value(nums: List[float], low: float, high: float) -> Optional[float]:
    candidates = [n for n in nums if low <= n <= high]
    if not candidates:
        return None
    return candidates[0]


def line_matches_field(line: str, field_info: Dict[str, Any]) -> bool:
    nline = norm_text(line)
    return any(re.search(pat, nline, flags=re.IGNORECASE) for pat in field_info["patterns"])


REFERENCE_WORDS = [
    "valor de referencia", "valores de referencia", "referencia", "rango",
    "intervalo", "normal", "deseable", "limite", "límite", "riesgo",
    "metodo", "método", "unidad", "observaciones", "comentario"
]


def remove_reference_tail(text: str) -> str:
    """Corta la parte de rangos de referencia; evita tomar <100, 40-60, 0.5-5, etc. como resultado."""
    if not text:
        return ""
    n = norm_text(text)
    cut_positions = []
    for word in REFERENCE_WORDS:
        pos = n.find(norm_text(word))
        if pos >= 0:
            cut_positions.append(pos)
    if cut_positions:
        return text[:min(cut_positions)].strip()
    return text.strip()


def is_line_likely_reference_only(line: str) -> bool:
    n = norm_text(line)
    return any(w in n for w in [norm_text(x) for x in REFERENCE_WORDS])


def first_value_after_label(line: str, info: Dict[str, Any]) -> Optional[float]:
    """Busca el primer valor numérico después del nombre de la determinación en la misma línea."""
    nline = norm_text(line)
    best_pos = None
    for pat in info["patterns"]:
        m = re.search(pat, nline, flags=re.IGNORECASE)
        if m:
            best_pos = m.end()
            break
    if best_pos is None:
        return None

    after = line[best_pos:]
    after = remove_reference_tail(after)
    nums = numbers_from_text(after)
    low, high = info["range"]
    return choose_value(nums, low, high)


def value_from_pipe_or_table_line(line: str, info: Dict[str, Any]) -> Optional[float]:
    """Maneja filas tipo: 'Colesterol LDL | 148 | mg/dL | <100'."""
    if "|" not in line and "\t" not in line and ";" not in line:
        return None
    parts = re.split(r"\||\t|;", line)
    match_idx = None
    for idx, part in enumerate(parts):
        if line_matches_field(part, info):
            match_idx = idx
            break
    if match_idx is None:
        return None
    low, high = info["range"]
    # Buscar en las celdas posteriores. Evitar celdas claramente de referencia.
    for part in parts[match_idx + 1:]:
        if is_line_likely_reference_only(part):
            continue
        val = choose_value(numbers_from_text(part), low, high)
        if val is not None:
            return val
    return None


def value_from_next_lines(lines: List[str], idx: int, info: Dict[str, Any], max_next: int = 3) -> Optional[float]:
    """Si el PDF separa determinación y resultado en líneas distintas, toma el primer valor plausible cercano."""
    low, high = info["range"]
    for j in range(idx + 1, min(idx + 1 + max_next, len(lines))):
        nxt = lines[j]
        if any(line_matches_field(nxt, other) for k, other in LAB_FIELDS.items() if other is not info):
            # aparece otra determinación antes de un resultado claro
            break
        if is_line_likely_reference_only(nxt):
            continue
        cleaned = remove_reference_tail(nxt)
        val = choose_value(numbers_from_text(cleaned), low, high)
        if val is not None:
            return val
    return None


def suspicious_reason(key: str, value: float) -> str:
    """No invalida el dato; marca valores que suelen ser errores de extracción y requieren confirmación manual."""
    limits = {
        "ldl": (30, 300),
        "hdl": (25, 120),
        "tg": (40, 1000),
        "ct": (100, 400),
        "egfr": (20, 150),
        "creatinine": (0.3, 8),
        "glucose": (50, 400),
        "hba1c": (4.0, 14),
        "ast": (5, 500),
        "alt": (5, 500),
        "ck": (10, 10000),
        "tsh": (0.05, 20),
        "age": (18, 100),
    }
    lo_hi = limits.get(key)
    if not lo_hi:
        return ""
    lo, hi = lo_hi
    if value < lo or value > hi:
        return f"REVISAR: valor extremo para {LAB_FIELDS.get(key, {}).get('label', key)}; puede ser rango de referencia o lectura errónea."
    return ""


def extraction_status(key: str, value: float) -> str:
    reason = suspicious_reason(key, value)
    return reason if reason else "OK"


def extracted_table_rows(values: Dict[str, float]) -> List[Dict[str, Any]]:
    rows = []
    for k, v in values.items():
        rows.append({
            "Variable": LAB_FIELDS.get(k, {}).get("label", k),
            "Valor extraído": v,
            "Unidad": LAB_FIELDS.get(k, {}).get("unit", ""),
            "Estado": extraction_status(k, v),
            "Aplicación automática": "No aplicada; revisar manualmente" if suspicious_reason(k, v) else "Aplicada al formulario",
        })
    return rows



EXTRACTION_METHOD_CONFIDENCE = {
    "fila_tabla": 96,
    "misma_linea_despues_del_nombre": 92,
    "lineas_siguientes": 78,
    "contexto_cercano": 64,
    "misma_linea_unidad": 98,
    "linea_siguiente_unidad": 94,
    "unidad_y_valor_separados": 90,
    "misma_linea_egfr": 96,
    "consenso_multimotor": 99,
}


def evidence_method(evidence_text: str) -> str:
    m = re.match(r"\[([^\]]+)\]", evidence_text or "")
    return m.group(1) if m else ""


def extraction_confidence(key: str, value: float, evidence_text: str = "") -> Tuple[int, str]:
    method = evidence_method(evidence_text)
    if method.startswith("consenso_"):
        score = EXTRACTION_METHOD_CONFIDENCE["consenso_multimotor"]
    else:
        score = EXTRACTION_METHOD_CONFIDENCE.get(method, 60)
    if suspicious_reason(key, float(value)):
        score = min(score, 35)
    if score >= 85:
        return score, "🟢 Alta"
    if score >= 65:
        return score, "🟡 Media"
    return score, "🔴 Revisar"


def lab_value_interpretation(key: str, value: float) -> Tuple[str, str]:
    """Lectura orientativa. No reemplaza el rango del laboratorio ni el contexto clínico."""
    v = float(value)
    if key == "ct":
        return ("🟢 Deseable", "<200 mg/dL") if v < 200 else (("🟡 Elevado", "200–239 mg/dL") if v < 240 else ("🔴 Alto", "≥240 mg/dL"))
    if key == "ldl":
        if v < 100: return "🟢 Favorable", "La meta real depende del riesgo cardiovascular"
        if v < 130: return "🟡 Sobre óptimo", "Comparar con objetivo individual"
        if v < 160: return "🟠 Elevado", "Requiere contextualizar riesgo y meta"
        if v < 190: return "🔴 Alto", "Mayor necesidad de reducción"
        return "🔴 Muy alto", "≥190 mg/dL: evaluar hipercolesterolemia severa/HeFH"
    if key == "hdl":
        if v < 40: return "🔴 Bajo", "Interpretar también según sexo y contexto"
        if v >= 60: return "🟢 Favorable", "Valor alto habitualmente protector en la evaluación lipídica"
        return "🟡 Intermedio", "Interpretar según sexo y riesgo global"
    if key == "tg":
        if v < 150: return "🟢 Normal", "<150 mg/dL"
        if v < 500: return "🟡 Elevados", "150–499 mg/dL"
        return "🔴 Severos", "≥500 mg/dL: priorizar riesgo de pancreatitis y causas secundarias"
    if key == "egfr":
        if v >= 90: return "🟢 Preservado", "Categorizar junto con albuminuria y cronicidad"
        if v >= 60: return "🟡 Leve reducción", "No define ERC aislada sin persistencia/otros marcadores"
        if v >= 30: return "🟠 Reducido", "Influye en selección y dosis"
        return "🔴 Marcadamente reducido", "Requiere especial precaución y contexto nefrológico"
    if key == "creatinine":
        return "ℹ️ Contextual", "Usar rango del laboratorio, sexo, masa muscular y eGFR"
    if key == "glucose":
        if v < 100: return "🟢 Habitual si ayunas", "Confirmar condición de ayuno"
        if v < 126: return "🟡 Alterada si ayunas", "100–125 mg/dL"
        return "🔴 Elevada", "≥126 mg/dL puede ser compatible con diabetes si se confirma en contexto apropiado"
    if key == "hba1c":
        if v < 5.7: return "🟢 Habitual", "<5,7%"
        if v < 6.5: return "🟡 Prediabetes", "5,7–6,4%"
        return "🔴 Rango diabetes", "≥6,5% requiere confirmación/contexto clínico"
    if key in ("ast", "alt"):
        if v <= 40: return "🟢 Sin elevación evidente", "Comparar con LSN del laboratorio"
        if v <= 120: return "🟡 Elevada", "Interpretar respecto al LSN local y etiología"
        return "🔴 Elevación importante", "Revisar hepatopatía antes de intensificar tratamiento"
    if key == "ck":
        if v <= 200: return "🟢 Sin elevación evidente", "El rango depende de sexo, masa muscular y laboratorio"
        if v <= 500: return "🟡 Elevada", "Correlacionar con ejercicio, trauma y síntomas"
        return "🔴 Elevada", "Requiere correlación clínica antes de iniciar/intensificar estatina"
    if key == "tsh":
        if 0.4 <= v <= 4.5: return "🟢 Rango habitual", "Interpretar con rango local y T4L"
        if v > 10: return "🔴 Elevada", "Hipotiroidismo significativo aumenta riesgo muscular"
        return "🟡 Fuera de rango habitual", "Correlacionar con T4L y clínica"
    if key == "age":
        return "ℹ️ Dato clínico", "Se usa para contextualizar riesgo y seguridad"
    return "ℹ️ Revisar", "Interpretar según rango de referencia del laboratorio"


def build_lab_review_dataframe(values: Dict[str, float], evidence: Dict[str, str]) -> pd.DataFrame:
    """Tabla de revisión explícita con trazabilidad del motor y de las conversiones de unidad."""
    rows = []
    for key, value in values.items():
        ev = evidence.get(key, "")
        score, conf = extraction_confidence(key, float(value), ev)
        interp, note = lab_value_interpretation(key, float(value))
        method = evidence_method(ev) or "no informado"

        conversion = "Sin conversión"
        for token in ("g/L→mg/dL", "mmol/L→mg/dL", "µmol/L→mg/dL"):
            if token in ev:
                conversion = token
                break

        if method.startswith("consenso_"):
            trace = method.replace("_", " ")
        else:
            m_motor = re.search(r"motor=([^|]+)", ev)
            trace = m_motor.group(1).strip() if m_motor else method.replace("_", " ")

        rows.append({
            "Aplicar": not bool(suspicious_reason(key, float(value))),
            "Variable": LAB_FIELDS.get(key, {}).get("label", key),
            "Valor extraído": float(value),
            "Valor confirmado": float(value),
            "Unidad": LAB_FIELDS.get(key, {}).get("unit", ""),
            "Origen lectura": trace,
            "Conversión": conversion,
            "Confianza": conf,
            "Conf. %": score,
            "Lectura orientativa": interp,
            "Qué significa": note,
            "Estado extracción": "⚠️ Revisar" if suspicious_reason(key, float(value)) else "✅ Plausible",
        })
    return pd.DataFrame(rows)


def reviewed_lab_dataframe_to_values(review_df: pd.DataFrame, only_selected: bool = True) -> Dict[str, float]:
    """Convierte la tabla editada en valores corregidos/confirmados para coherencia y aplicación."""
    label_to_key = {info["label"]: key for key, info in LAB_FIELDS.items()}
    values: Dict[str, float] = {}
    for _, row in review_df.iterrows():
        try:
            if only_selected and not bool(row.get("Aplicar", False)):
                continue
            key = label_to_key.get(str(row.get("Variable", "")))
            if not key:
                continue
            value = float(row.get("Valor confirmado"))
            if pd.isna(value):
                continue
            values[key] = int(round(value)) if key == "age" else float(value)
        except Exception:
            continue
    return values


def apply_reviewed_lab_dataframe(review_df: pd.DataFrame) -> Tuple[List[str], List[str], Dict[str, float]]:
    """Aplica exclusivamente los valores de la columna 'Valor confirmado' y devuelve una instantánea auditable."""
    label_to_key = {info["label"]: key for key, info in LAB_FIELDS.items()}
    applied, errors = [], []
    applied_values: Dict[str, float] = {}
    for _, row in review_df.iterrows():
        try:
            if not bool(row.get("Aplicar", False)):
                continue
            key = label_to_key.get(str(row.get("Variable", "")))
            if not key:
                continue
            value = float(row.get("Valor confirmado"))
            low, high = LAB_FIELDS[key]["range"]
            if not (low <= value <= high):
                errors.append(f"{LAB_FIELDS[key]['label']}={value}: fuera del rango operativo {low}–{high}")
                continue
            if key == "age":
                final_value = int(round(value))
                st.session_state["manual_age"] = final_value
            elif key in DEFAULTS:
                final_value = float(value)
                st.session_state[f"manual_{key}"] = final_value
            else:
                continue
            applied_values[key] = final_value
            applied.append(f"{LAB_FIELDS[key]['label']}={final_value:g}")
        except Exception as exc:
            errors.append(f"Fila no aplicada: {type(exc).__name__}")
    return applied, errors, applied_values


def active_lab_values_from_session() -> Dict[str, float]:
    """Única fuente de verdad para los valores que consume la evaluación."""
    values: Dict[str, float] = {}
    for key in LAB_FIELDS:
        session_key = f"manual_{key}"
        if session_key in st.session_state:
            raw = st.session_state[session_key]
            values[key] = int(raw) if key == "age" else float(raw)
    return values


def active_lab_values_dataframe(values: Optional[Dict[str, float]] = None) -> pd.DataFrame:
    """Muestra valor activo y procedencia; permite constatar qué usa realmente el cálculo."""
    active = values or active_lab_values_from_session()
    confirmed = st.session_state.get("lab_confirmed_values", {}) or {}
    extracted = st.session_state.get("extracted_values", {}) or {}
    rows = []
    priority = ["ct", "ldl", "hdl", "tg", "egfr", "creatinine", "glucose", "hba1c", "ast", "alt", "ck", "tsh", "age"]
    for key in priority:
        if key not in active:
            continue
        value = float(active[key])
        if key in confirmed:
            conf = float(confirmed[key])
            same = abs(value - conf) < 1e-9
            origin = "✅ Corregido y confirmado en revisión" if same else "✍️ Modificado manualmente después de confirmar"
        elif key in extracted:
            origin = "⚠️ Valor activo no confirmado desde la extracción"
        else:
            origin = "✍️ Carga manual / valor activo"
        rows.append({
            "Variable": LAB_FIELDS[key]["label"],
            "Valor usado": int(round(value)) if key == "age" else value,
            "Unidad": LAB_FIELDS[key]["unit"],
            "Origen del valor usado": origin,
        })
    return pd.DataFrame(rows)


def missing_lab_fields(values: Dict[str, float]) -> List[str]:
    priority = ["ct", "ldl", "hdl", "tg", "egfr", "creatinine", "glucose", "hba1c", "ast", "alt", "ck", "tsh"]
    return [LAB_FIELDS[k]["label"] for k in priority if k not in values]


def lab_cross_consistency(values: Dict[str, float]) -> List[Tuple[str, str]]:
    """Controles relacionales para detectar lecturas numéricamente plausibles pero incoherentes entre sí."""
    findings: List[Tuple[str, str]] = []
    ct = values.get("ct")
    ldl = values.get("ldl")
    hdl = values.get("hdl")
    tg = values.get("tg")

    if ct is not None and ldl is not None and float(ldl) > float(ct):
        findings.append(("error", "LDL-C mayor que colesterol total: probable error de extracción o transcripción."))
    if ct is not None and hdl is not None and float(hdl) > float(ct):
        findings.append(("error", "HDL-C mayor que colesterol total: probable error de extracción o transcripción."))
    if ct is not None and hdl is not None and ldl is not None:
        nonhdl = float(ct) - float(hdl)
        if float(ldl) > nonhdl + 10:
            findings.append(("error", f"LDL-C ({float(ldl):.0f}) es incoherente con no-HDL-C calculado ({nonhdl:.0f}); revisar lectura."))
        if tg is not None and float(tg) < 400:
            friedewald = float(ct) - float(hdl) - float(tg) / 5.0
            if friedewald > 0 and abs(float(ldl) - friedewald) > max(40.0, 0.35 * friedewald):
                findings.append(("warn", f"LDL-C extraído difiere marcadamente del LDL-C calculado aproximado ({friedewald:.0f} mg/dL). Puede ser LDL directo, pero conviene confirmar el dato."))
    if ct is not None and hdl is not None and float(ct) - float(hdl) < 0:
        findings.append(("error", "No-HDL-C calculado negativo: revisar colesterol total y HDL-C."))
    return findings


def render_result_card(title: str, value: str, detail: str, level: str = "info") -> None:
    css = {"good": "result-good", "warn": "result-warn", "bad": "result-bad", "info": "result-info"}.get(level, "result-info")
    st.markdown(
        f'<div class="result-card {css}"><div class="kpi-label">{html.escape(title)}</div>'
        f'<div class="kpi-value">{html.escape(value)}</div><div>{html.escape(detail)}</div></div>',
        unsafe_allow_html=True,
    )


def best_lab_value_for_field(lines: List[str], idx: int, info: Dict[str, Any]) -> Tuple[Optional[float], str]:
    """Estrategia conservadora: resultado en tabla/same line/next line, evitando rangos de referencia."""
    line = lines[idx]
    strategies = [
        ("fila_tabla", value_from_pipe_or_table_line(line, info)),
        ("misma_linea_despues_del_nombre", first_value_after_label(line, info)),
        ("lineas_siguientes", value_from_next_lines(lines, idx, info)),
    ]
    for method, val in strategies:
        if val is not None:
            return val, method

    # Último recurso: contexto muy cercano sin cola de referencias.
    context = remove_reference_tail(" ".join(lines[idx:idx+2]))
    low, high = info["range"]
    val = choose_value(numbers_from_text(context), low, high)
    if val is not None:
        return val, "contexto_cercano"
    return None, ""


def extract_pdf_text_all_methods(file_bytes: bytes) -> Tuple[str, List[str]]:
    texts = []
    methods = []

    # 1) pypdf
    try:
        from pypdf import PdfReader
        reader = PdfReader(BytesIO(file_bytes))
        out = []
        for page in reader.pages:
            out.append(page.extract_text() or "")
        txt = "\n".join(out).strip()
        if txt:
            texts.append(txt)
            methods.append("pypdf")
    except Exception as e:
        methods.append(f"pypdf no disponible/error: {type(e).__name__}")

    # 2) pdfplumber texto + tablas
    try:
        import pdfplumber
        out = []
        tables_out = []
        with pdfplumber.open(BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                txt = page.extract_text() or ""
                if txt:
                    out.append(txt)
                try:
                    tables = page.extract_tables() or []
                    for table in tables:
                        for row in table:
                            if row:
                                tables_out.append(" | ".join([str(c) for c in row if c is not None]))
                except Exception:
                    pass
        txt = "\n".join(out + tables_out).strip()
        if txt:
            texts.append(txt)
            methods.append("pdfplumber texto/tablas")
    except Exception as e:
        methods.append(f"pdfplumber no disponible/error: {type(e).__name__}")

    # 3) PyMuPDF
    try:
        import fitz  # pymupdf
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        out = []
        for page in doc:
            out.append(page.get_text("text") or "")
        txt = "\n".join(out).strip()
        if txt:
            texts.append(txt)
            methods.append("PyMuPDF")
    except Exception as e:
        methods.append(f"PyMuPDF no disponible/error: {type(e).__name__}")

    # Unificar líneas únicas preservando orden
    seen = set()
    lines = []
    for txt in texts:
        for line in txt.splitlines():
            clean = re.sub(r"\s+", " ", line).strip()
            if clean and clean not in seen:
                seen.add(clean)
                lines.append(clean)

    return "\n".join(lines), methods


def anonymize_line(line: str) -> str:
    original = line
    lower = norm_text(line)

    # Eliminar líneas con identificadores probables.
    sensitive_keywords = [
        "paciente", "apellido", "nombre", "dni", "documento", "cuit", "cuil",
        "historia clinica", "hc ", "fecha de nacimiento", "nacimiento",
        "domicilio", "direccion", "dirección", "telefono", "teléfono",
        "mail", "email", "obra social", "afiliado", "orden", "protocolo",
    ]
    if any(k in lower for k in sensitive_keywords):
        # Mantener edad si aparece en esa línea
        if re.search(r"\bedad\b", lower):
            return re.sub(r"[A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ]+)+", "[NOMBRE]", original)
        return ""

    # Enmascarar documentos, mails, teléfonos.
    line = re.sub(r"\b\d{7,8}\b", "[DNI]", line)
    line = re.sub(r"\b\d{2}-?\d{8}-?\d\b", "[CUIT]", line)
    line = re.sub(r"[\w\.-]+@[\w\.-]+\.\w+", "[EMAIL]", line)
    line = re.sub(r"\+?\d[\d\s\-\(\)]{7,}\d", "[TEL]", line)
    return line


def lab_candidate_lines(text: str, max_lines: int = 120) -> List[str]:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    out = []
    for line in lines:
        if any(line_matches_field(line, info) for info in LAB_FIELDS.values()):
            anon = anonymize_line(line)
            if anon:
                out.append(anon)
    return out[:max_lines]


LAB_UNIT_PATTERN = (
    r"(?:mg\s*/?\s*d[lL]|g\s*/?\s*[lL]|mmol\s*/?\s*[lL]|"
    r"[µu]mol\s*/?\s*[lL]|U\s*/?\s*[lL]|UI\s*/?\s*[lL]|%|"
    r"m[lL]\s*/\s*min(?:\s*/\s*1[.,]73)?(?:\s*m2)?|"
    r"[µu]?lU\s*/?\s*m[lL]|[µu]?UI\s*/?\s*m[lL]|mIU\s*/?\s*[lL])"
)


def _normalize_lab_unit(unit: str) -> str:
    u = norm_text(unit or "")
    u = re.sub(r"\s+", "", u)
    return u.replace("μ", "µ")


def _canonicalize_lab_value(key: str, value: float, unit: str) -> Tuple[float, str]:
    """Convierte la unidad informada por el laboratorio a la unidad canónica usada por la app."""
    v = float(value)
    u = _normalize_lab_unit(unit)

    # La app usa mg/dL para glucemia y perfil lipídico.
    if key in {"ct", "ldl", "hdl", "tg", "glucose"}:
        if u.startswith("g/l"):
            return round(v * 100.0, 6), "g/L→mg/dL"
        if u.startswith("mmol/l"):
            if key == "glucose":
                return round(v * 18.018, 6), "mmol/L→mg/dL"
            if key == "tg":
                return round(v * 88.57, 6), "mmol/L→mg/dL"
            return round(v * 38.67, 6), "mmol/L→mg/dL"

    # La app usa mg/dL para creatinina.
    if key == "creatinine" and (u.startswith("µmol/l") or u.startswith("umol/l")):
        return round(v / 88.4, 6), "µmol/L→mg/dL"

    return round(v, 6), ""


def _field_match_end(line: str, info: Dict[str, Any]) -> Optional[int]:
    nline = norm_text(line)
    matches = []
    for pat in info["patterns"]:
        m = re.search(pat, nline, flags=re.IGNORECASE)
        if m:
            matches.append(m)
    if not matches:
        return None
    # Preferir la coincidencia más temprana; ante empate, la más larga.
    best = sorted(matches, key=lambda m: (m.start(), -(m.end() - m.start())))[0]
    return best.end()


def _number_unit_pairs(text: str) -> List[Tuple[int, float, str, str]]:
    """Detecta pares resultado-unidad tanto '2.80 g/L' como 'g/L2.80'."""
    pairs: List[Tuple[int, float, str, str]] = []
    num_pat = r"[-+]?\d{1,7}(?:[.,]\d+)?"
    p_num_unit = re.compile(
        rf"(?P<num>{num_pat})\s*(?P<unit>{LAB_UNIT_PATTERN})",
        flags=re.IGNORECASE,
    )
    p_unit_num = re.compile(
        rf"(?P<unit>{LAB_UNIT_PATTERN})\s*(?P<num>{num_pat})",
        flags=re.IGNORECASE,
    )

    for m in p_num_unit.finditer(text or ""):
        value = parse_number(m.group("num"))
        if value is not None:
            pairs.append((m.start(), float(value), m.group("unit"), "numero_unidad"))

    for m in p_unit_num.finditer(text or ""):
        value = parse_number(m.group("num"))
        if value is not None:
            pairs.append((m.start(), float(value), m.group("unit"), "unidad_numero"))

    # Evitar duplicados cuando ambas regex capturan el mismo fragmento.
    unique = {}
    for item in sorted(pairs, key=lambda x: x[0]):
        pos, value, unit, mode = item
        sig = (round(value, 8), _normalize_lab_unit(unit), pos)
        unique.setdefault(sig, item)
    return list(unique.values())


def _candidate_for_lab_occurrence(
    lines: List[str],
    idx: int,
    key: str,
    info: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """Extrae un candidato anclado a nombre + unidad, evitando rangos y valores anteriores."""
    line = lines[idx]
    candidates: List[Dict[str, Any]] = []
    match_end = _field_match_end(line, info)

    # 1) Mejor escenario: resultado y unidad en la misma línea que la determinación.
    after_label = line[match_end:] if match_end is not None else line
    for _, raw_value, unit, _ in _number_unit_pairs(after_label):
        value, conversion = _canonicalize_lab_value(key, raw_value, unit)
        candidates.append({
            "value": value,
            "score": 100,
            "method": "misma_linea_unidad",
            "unit_original": unit,
            "conversion": conversion,
            "context": line,
        })

    # 2) eGFR suele venir con la unidad quebrada por columnas: "... CKD-EPI 82 mL/ ..."
    if key == "egfr" and match_end is not None:
        m = re.search(r"[-+]?\d{1,3}(?:[.,]\d+)?", after_label)
        if m:
            value = parse_number(m.group(0))
            if value is not None:
                candidates.append({
                    "value": float(value),
                    "score": 98,
                    "method": "misma_linea_egfr",
                    "unit_original": "mL/min/1.73 m²",
                    "conversion": "",
                    "context": line,
                })

    # 3) PDFs que separan determinación / método / resultado.
    for j in range(idx + 1, min(len(lines), idx + 8)):
        nxt = lines[j]

        # No atravesar otra determinación distinta.
        if j > idx + 1 and any(
            line_matches_field(nxt, other)
            for other_key, other in LAB_FIELDS.items()
            if other_key != key
        ):
            break

        n_nxt = norm_text(nxt)
        if n_nxt.startswith("metodo:") or n_nxt.startswith("método:"):
            continue

        for _, raw_value, unit, _ in _number_unit_pairs(nxt):
            value, conversion = _canonicalize_lab_value(key, raw_value, unit)
            candidates.append({
                "value": value,
                "score": 95 - 2 * (j - idx - 1),
                "method": "linea_siguiente_unidad",
                "unit_original": unit,
                "conversion": conversion,
                "context": f"{line} | {nxt}",
            })

        # PyMuPDF puede devolver la unidad y el número en líneas consecutivas.
        if re.fullmatch(rf"\s*{LAB_UNIT_PATTERN}\s*", nxt, flags=re.IGNORECASE):
            if j + 1 < len(lines):
                m_num = re.fullmatch(r"\s*[-+]?\d{1,7}(?:[.,]\d+)?\s*", lines[j + 1])
                if m_num:
                    raw_value = parse_number(m_num.group(0))
                    if raw_value is not None:
                        value, conversion = _canonicalize_lab_value(key, float(raw_value), nxt)
                        candidates.append({
                            "value": value,
                            "score": 90 - 2 * (j - idx - 1),
                            "method": "unidad_y_valor_separados",
                            "unit_original": nxt,
                            "conversion": conversion,
                            "context": f"{line} | {nxt} | {lines[j + 1]}",
                        })

    # Filtrar después de convertir a la unidad canónica de la app.
    low, high = info["range"]
    valid: List[Dict[str, Any]] = []
    for cand in candidates:
        value = float(cand["value"])
        if not (low <= value <= high):
            continue

        score = int(cand["score"])

        # HbA1c: privilegiar inequívocamente la medición porcentual,
        # no la variante IFCC en mmol/mol.
        if key == "hba1c" and "%" in str(cand["unit_original"]):
            score += 5

        # Perfil lipídico y glucemia expresados en g/L: la conversión explícita
        # es una señal fuerte de que se tomó el RESULTADO y no el rango.
        if key in {"ct", "ldl", "hdl", "tg", "glucose"} and cand["conversion"]:
            score += 4

        cand = dict(cand)
        cand["score"] = score
        valid.append(cand)

    if not valid:
        return None

    return sorted(valid, key=lambda c: c["score"], reverse=True)[0]


def _extraction_score_from_evidence(evidence_text: str) -> int:
    method = evidence_method(evidence_text)
    if method.startswith("consenso_"):
        return 99
    return EXTRACTION_METHOD_CONFIDENCE.get(method, 60)


def _lab_values_agree(key: str, a: float, b: float) -> bool:
    a, b = float(a), float(b)
    tol_abs = {
        "creatinine": 0.03,
        "hba1c": 0.06,
        "tsh": 0.06,
    }.get(key, 1.0)
    tol_rel = 0.015 if key not in {"creatinine", "hba1c", "tsh"} else 0.0
    return abs(a - b) <= max(tol_abs, tol_rel * max(abs(a), abs(b), 1.0))


def extract_lab_values_from_text(text: str) -> Tuple[Dict[str, float], Dict[str, str], List[Dict[str, Any]]]:
    """
    Extracción conservadora y anclada a unidad:
    - no toma el primer número plausible del contexto;
    - busca RESULTADO + UNIDAD;
    - convierte g/L→mg/dL y otras unidades equivalentes;
    - evalúa todas las apariciones y elige el candidato de mayor calidad.
    """
    lines = [re.sub(r"\s+", " ", ln).strip() for ln in (text or "").splitlines() if ln.strip()]
    values: Dict[str, float] = {}
    evidence: Dict[str, str] = {}
    diagnostics: List[Dict[str, Any]] = []

    for key, info in LAB_FIELDS.items():
        field_candidates: List[Dict[str, Any]] = []

        for i, line in enumerate(lines):
            if not line_matches_field(line, info):
                continue

            candidate = _candidate_for_lab_occurrence(lines, i, key, info)
            if candidate is None:
                diagnostics.append({
                    "variable": info["label"],
                    "linea": anonymize_line(line),
                    "contexto": anonymize_line(" | ".join(lines[i:i + 5])),
                    "metodo": "sin_valor_anclado_a_unidad",
                    "unidad_original": "",
                    "conversion": "",
                    "puntaje": 0,
                    "valor_elegido": None,
                    "estado": "Sin resultado confiable",
                })
                continue

            field_candidates.append(candidate)
            diagnostics.append({
                "variable": info["label"],
                "linea": anonymize_line(line),
                "contexto": anonymize_line(candidate["context"]),
                "metodo": candidate["method"],
                "unidad_original": candidate["unit_original"],
                "conversion": candidate["conversion"] or "Sin conversión",
                "puntaje": candidate["score"],
                "valor_elegido": candidate["value"],
                "estado": extraction_status(key, candidate["value"]),
            })

        if not field_candidates:
            continue

        best = sorted(field_candidates, key=lambda c: c["score"], reverse=True)[0]
        found = float(best["value"])
        if key == "age":
            found = int(round(found))

        values[key] = found
        conversion_note = f" {best['conversion']}" if best["conversion"] else ""
        evidence[key] = (
            f"[{best['method']}] "
            f"unidad={best['unit_original']}{conversion_note} | {best['context']}"
        )

    return values, evidence, diagnostics


def _extract_pdf_text_sources(file_bytes: bytes) -> Tuple[Dict[str, str], List[str]]:
    """Extrae cada motor por separado. No mezcla líneas: mezclar motores rompe columnas y asociaciones."""
    sources: Dict[str, str] = {}
    methods: List[str] = []

    try:
        from pypdf import PdfReader
        reader = PdfReader(BytesIO(file_bytes))
        txt = "\n".join((page.extract_text() or "") for page in reader.pages).strip()
        if txt:
            sources["pypdf"] = txt
            methods.append("pypdf")
    except Exception as exc:
        methods.append(f"pypdf error: {type(exc).__name__}")

    try:
        import pdfplumber
        out = []
        with pdfplumber.open(BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                if page_text:
                    out.append(page_text)
        txt = "\n".join(out).strip()
        if txt:
            sources["pdfplumber"] = txt
            methods.append("pdfplumber")
    except Exception as exc:
        methods.append(f"pdfplumber error: {type(exc).__name__}")

    try:
        import fitz
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        txt = "\n".join((page.get_text("text") or "") for page in doc).strip()
        if txt:
            sources["PyMuPDF"] = txt
            methods.append("PyMuPDF")
    except Exception as exc:
        methods.append(f"PyMuPDF error: {type(exc).__name__}")

    return sources, methods


def extract_lab_values_from_pdf_bytes(
    file_bytes: bytes,
) -> Tuple[str, List[str], Dict[str, float], Dict[str, str], List[Dict[str, Any]]]:
    """
    Extracción PDF multimotor con consenso por variable.
    Cada motor conserva su estructura; luego se comparan valores ya convertidos
    a las unidades canónicas de la app.
    """
    sources, methods = _extract_pdf_text_sources(file_bytes)
    if not sources:
        return "", methods, {}, {}, []

    per_source: Dict[str, Dict[str, Any]] = {}
    all_diagnostics: List[Dict[str, Any]] = []

    for source_name, source_text in sources.items():
        values, evidence, diagnostics = extract_lab_values_from_text(source_text)
        per_source[source_name] = {
            "values": values,
            "evidence": evidence,
        }
        for row in diagnostics:
            row = dict(row)
            row["motor_pdf"] = source_name
            all_diagnostics.append(row)

    merged_values: Dict[str, float] = {}
    merged_evidence: Dict[str, str] = {}
    source_priority = {"pdfplumber": 3, "PyMuPDF": 2, "pypdf": 1}

    for key in LAB_FIELDS:
        candidates = []
        for source_name, payload in per_source.items():
            if key not in payload["values"]:
                continue
            value = float(payload["values"][key])
            ev = payload["evidence"].get(key, "")
            candidates.append({
                "source": source_name,
                "value": value,
                "evidence": ev,
                "score": _extraction_score_from_evidence(ev),
                "priority": source_priority.get(source_name, 0),
            })

        if not candidates:
            continue

        # Construir el grupo de acuerdo más grande.
        best_group: List[Dict[str, Any]] = []
        for seed in candidates:
            group = [c for c in candidates if _lab_values_agree(key, seed["value"], c["value"])]
            if len(group) > len(best_group):
                best_group = group
            elif len(group) == len(best_group) and group:
                group_rank = sum(c["score"] + c["priority"] for c in group)
                best_rank = sum(c["score"] + c["priority"] for c in best_group)
                if group_rank > best_rank:
                    best_group = group

        if len(best_group) >= 2:
            chosen_value = float(pd.Series([c["value"] for c in best_group]).median())
            chosen_value = round(chosen_value, 6)
            sources_agree = ", ".join(c["source"] for c in best_group)
            representative = sorted(
                best_group,
                key=lambda c: (c["score"], c["priority"]),
                reverse=True,
            )[0]
            merged_values[key] = int(round(chosen_value)) if key == "age" else chosen_value
            merged_evidence[key] = (
                f"[consenso_{len(best_group)}_motores] "
                f"{sources_agree} | {representative['evidence']}"
            )
        else:
            chosen = sorted(
                candidates,
                key=lambda c: (c["score"], c["priority"]),
                reverse=True,
            )[0]
            merged_values[key] = int(round(chosen["value"])) if key == "age" else chosen["value"]
            merged_evidence[key] = (
                f"[{evidence_method(chosen['evidence'])}] "
                f"motor={chosen['source']} | {chosen['evidence']}"
            )

        # Auditoría de discrepancia entre motores.
        if len(candidates) >= 2:
            vals = [c["value"] for c in candidates]
            if not all(_lab_values_agree(key, vals[0], v) for v in vals[1:]):
                all_diagnostics.append({
                    "variable": LAB_FIELDS[key]["label"],
                    "linea": "",
                    "contexto": " | ".join(
                        f"{c['source']}={c['value']}" for c in candidates
                    ),
                    "metodo": "comparacion_multimotor",
                    "unidad_original": LAB_FIELDS[key]["unit"],
                    "conversion": "Valores ya normalizados",
                    "puntaje": 0,
                    "valor_elegido": merged_values[key],
                    "estado": "⚠️ Discrepancia entre motores; se eligió el candidato de mayor calidad",
                    "motor_pdf": "consenso",
                })

    # Para la vista anonimizada usar el motor con mayor cobertura, no una mezcla.
    def source_quality(item: Tuple[str, str]) -> Tuple[int, int, int]:
        source_name, _ = item
        payload = per_source.get(source_name, {})
        n_values = len(payload.get("values", {}))
        total_score = sum(
            _extraction_score_from_evidence(ev)
            for ev in payload.get("evidence", {}).values()
        )
        return n_values, total_score, source_priority.get(source_name, 0)

    primary_source = max(sources.items(), key=source_quality)[0]
    raw_text = sources[primary_source]
    methods = methods + [
        f"motor principal para vista: {primary_source}",
        f"consenso por variable: {'sí' if len(sources) >= 2 else 'no'}",
    ]

    return raw_text, methods, merged_values, merged_evidence, all_diagnostics
def update_session_with_extracted(values: Dict[str, float], only_safe: bool = True) -> Tuple[List[str], List[str]]:
    """Aplica valores al formulario. Por defecto no aplica valores extremos sospechosos."""
    applied: List[str] = []
    skipped: List[str] = []
    for key, val in values.items():
        reason = suspicious_reason(key, float(val))
        if only_safe and reason:
            skipped.append(f"{LAB_FIELDS.get(key, {}).get('label', key)}={val} ({reason})")
            continue
        if key in DEFAULTS:
            st.session_state[f"manual_{key}"] = float(val)
            applied.append(f"{LAB_FIELDS.get(key, {}).get('label', key)}={val}")
        elif key == "age":
            st.session_state["manual_age"] = int(val)
            applied.append(f"{LAB_FIELDS.get(key, {}).get('label', key)}={val}")
    return applied, skipped


def get_session_default(key: str) -> Any:
    return st.session_state.get(f"manual_{key}", DEFAULTS[key])


# ============================================================
# CÁLCULOS CLÍNICOS
# ============================================================

def non_hdl(ct: float, hdl: float) -> float:
    return max(float(ct) - float(hdl), 0.0)


def estimate_ldl_after(ldl: float, dose: str) -> float:
    return max(float(ldl) * (1 - LDL_REDUCTION_BY_DOSE.get(dose, 0.39)), 0.0)


def detect_interactions(meds_text: str) -> List[Dict[str, Any]]:
    """Detecta señales de la base y agrega una alerta de carga miotóxica acumulativa."""
    found: List[Dict[str, Any]] = []
    text = norm_text(meds_text or "")
    for name, item in INTERACCIONES.items():
        if re.search(item["regex"], text, flags=re.IGNORECASE):
            found.append({"farmaco": name, **item})

    muscle_hits = [x for x in found if x.get("riesgo_muscular")]
    if len(muscle_hits) >= 2:
        names = ", ".join(x["farmaco"] for x in muscle_hits[:5])
        found.append({
            "farmaco": "carga miotóxica acumulativa",
            "nivel": "AMARILLO",
            "alcance": "Integración automática de múltiples señales",
            "evidencia": "Regla clínica de suma farmacodinámica basada en la base integrada",
            "mecanismo": "Concurrencia de dos o más medicamentos/señales con potencial de toxicidad muscular.",
            "mensaje": f"Se detectaron múltiples señales miotóxicas simultáneas ({names}).",
            "accion": "Reconciliar medicación, reducir combinaciones evitables y contextualizar con edad, función renal, TSH y CK.",
            "monitoreo": "Interrogar síntomas basales y durante seguimiento; CK y función renal si clínica o alto riesgo.",
            "riesgo_muscular": True,
            "regex": "",
        })

    return sorted(found, key=lambda x: INTERACTION_LEVEL_ORDER.get(x.get("nivel", "AZUL"), 0), reverse=True)


def interaction_max_level(interactions: List[Dict[str, Any]]) -> str:
    if not interactions:
        return "SIN SEÑALES"
    return max(
        (x.get("nivel", "AZUL") for x in interactions),
        key=lambda lvl: INTERACTION_LEVEL_ORDER.get(lvl, 0),
    )


def interactions_dataframe(interactions: List[Dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for item in interactions:
        rows.append({
            "Fármaco / grupo": item.get("farmaco", ""),
            "Nivel": item.get("nivel", ""),
            "Interpretación": INTERACTION_LEVEL_LABEL.get(item.get("nivel", ""), item.get("nivel", "")),
            "Alcance de evidencia": item.get("alcance", ""),
            "Mecanismo": item.get("mecanismo", ""),
            "Hallazgo": item.get("mensaje", ""),
            "Acción sugerida": item.get("accion", ""),
            "Monitoreo": item.get("monitoreo", ""),
            "Fuente/evidencia": item.get("evidencia", ""),
        })
    return pd.DataFrame(rows)


def knowledge_base_dataframe() -> pd.DataFrame:
    return interactions_dataframe([{"farmaco": name, **item} for name, item in INTERACCIONES.items()])


def recommend_goal(risk_category: str, custom_goal: int) -> int:
    if risk_category == "Personalizado":
        return int(custom_goal)
    return int(OBJETIVOS_LDL.get(risk_category, custom_goal))


def tg_class(tg: float) -> str:
    if tg < 150:
        return "Normal"
    if tg < 500:
        return "Hipertrigliceridemia leve-moderada"
    return "Hipertrigliceridemia severa"


def assess_indication(data: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    indications, reasons = [], []

    if data["ldl"] >= 130 or data["ct"] >= 200:
        indications.append("Hipercolesterolemia primaria / LDL-C elevado")
        reasons.append("Colesterol total o LDL-C por encima del rango deseable.")
    if data["hefh"]:
        indications.append("Hipercolesterolemia familiar heterocigota probable/conocida")
        reasons.append("HeFH requiere reducción intensiva y seguimiento longitudinal.")
    if data["tg"] >= 150 and data["tg"] < 500 and (data["ldl"] >= 100 or data["non_hdl"] >= 130):
        indications.append("Dislipidemia mixta")
        reasons.append("TG elevado con LDL-C/no-HDL-C por encima de objetivo.")
    if data["ascvd"]:
        indications.append("Prevención secundaria por ASCVD")
        reasons.append("ASCVD establecida implica alto/muy alto riesgo.")
    if data["diabetes"] and 40 <= data["age"] <= 75:
        indications.append("Diabetes 40–75 años: considerar estatina según riesgo")
        reasons.append("La diabetes aumenta el riesgo cardiovascular global.")
    if data["risk_category"] in ["Alto riesgo", "Muy alto riesgo / ASCVD"] and data["ldl"] >= 70:
        indications.append("Prevención cardiovascular por riesgo elevado")
        reasons.append("Riesgo cardiovascular elevado con LDL-C por encima del objetivo usado.")

    if not indications:
        indications.append("Indicación no concluyente con los datos cargados")
        reasons.append("No se identificó indicación clara; completar estratificación de riesgo y confirmar laboratorio.")

    return indications, reasons


def assess_warnings(data: Dict[str, Any], interactions: List[Dict[str, str]]) -> Tuple[List[str], List[str]]:
    red_flags, yellow_flags = [], []

    if data["acute_liver_failure"]:
        red_flags.append("Falla hepática aguda o cirrosis descompensada.")
    if data["hypersensitivity"]:
        red_flags.append("Hipersensibilidad conocida a pitavastatina/excipientes.")
    if data["pregnancy_lactation"]:
        red_flags.append("Embarazo o lactancia: evitar uso rutinario; requiere criterio especializado y prospecto local.")

    for item in interactions:
        if item["nivel"] == "ROJO":
            red_flags.append(f"Interacción mayor: {item['farmaco']}. {item['accion']}")
        elif item["nivel"] == "AMARILLO":
            yellow_flags.append(f"Interacción/precaución: {item['farmaco']}. {item['accion']}")
        elif item["nivel"] == "AZUL":
            # Señal informativa: se muestra en el chequeador, sin convertir por sí sola al paciente en precaución clínica.
            pass

    if data["age"] >= 65:
        yellow_flags.append("Edad ≥65 años: mayor riesgo de miopatía; titular con vigilancia clínica.")
    if data["egfr"] < 60:
        yellow_flags.append("eGFR <60 ml/min/1,73 m²: iniciar 1 mg/día y no superar 2 mg/día.")
    if data["hypothyroidism"]:
        yellow_flags.append("Hipotiroidismo no controlado: corregir antes de intensificar estatina.")
    if data["alcohol_liver_history"]:
        yellow_flags.append("Antecedente hepático/alcohol relevante: controlar enzimas hepáticas según criterio clínico.")
    if data["polypharmacy"]:
        yellow_flags.append("Polifarmacia: revisar interacciones, adherencia y tolerancia muscular.")
    if data["hiv_arv"]:
        yellow_flags.append("VIH/antirretrovirales: verificar interacción específica del esquema ARV.")

    if data.get("alt", 0) > 120 or data.get("ast", 0) > 120:
        yellow_flags.append("Transaminasas elevadas en laboratorio cargado: revisar hepatopatía antes de indicar.")
    if data.get("ck", 0) > 500:
        yellow_flags.append("CK/CPK elevada: correlacionar con síntomas, ejercicio, trauma o miopatía antes de iniciar.")
    if data.get("tsh", 0) > 10:
        yellow_flags.append("TSH elevada compatible con hipotiroidismo significativo: corregir por riesgo muscular.")
    if data.get("hba1c", 0) >= 6.5 or data.get("glucose", 0) >= 126:
        yellow_flags.append("Perfil glucémico compatible con diabetes o alto riesgo metabólico: controlar HbA1c/glucemia durante seguimiento.")

    return red_flags, yellow_flags


def detect_therapeutic_combinations(meds_text: str) -> List[Dict[str, str]]:
    text_norm = norm_text(meds_text or "")
    found: List[Dict[str, str]] = []
    for name, item in THERAPEUTIC_COMBINATIONS.items():
        if re.search(item["regex"], text_norm, flags=re.IGNORECASE):
            found.append({"farmaco": name, **item})
    return found


def required_ldl_reduction(baseline_ldl: float, goal_ldl: float) -> Dict[str, float]:
    baseline = max(float(baseline_ldl), 0.1)
    goal = max(float(goal_ldl), 0.0)
    absolute = max(baseline - goal, 0.0)
    percentage = max(absolute / baseline * 100.0, 0.0)
    return {"absolute": absolute, "percentage": percentage}


def _pitavastatin_dose_limits(data: Dict[str, Any], interactions: List[Dict[str, Any]]) -> Tuple[int, int, List[str]]:
    start_mg, max_mg = 2, 4
    notes: List[str] = []
    if float(data.get("egfr", 90)) < 60:
        start_mg, max_mg = 1, 2
        notes.append("Por eGFR <60: inicio orientativo 1 mg/día y máximo 2 mg/día según la regla incorporada.")
    for item in interactions:
        if item.get("farmaco") == "eritromicina":
            start_mg, max_mg = 1, 1
            notes.append("Con eritromicina: la base limita pitavastatina a 1 mg/día.")
        elif item.get("farmaco") == "rifampicina" and max_mg > 1:
            max_mg = min(max_mg, 2)
            start_mg = min(start_mg, max_mg)
            notes.append("Con rifampicina: la base limita pitavastatina a 2 mg/día.")
    return start_mg, max_mg, notes


def strategy_comparison(data: Dict[str, Any], interactions: List[Dict[str, Any]], goal_ldl: int) -> pd.DataFrame:
    baseline = float(data.get("baseline_ldl") or data.get("ldl", 0))
    start_mg, max_mg, _ = _pitavastatin_dose_limits(data, interactions)
    major_block = any(i.get("nivel") == "ROJO" for i in interactions) or bool(
        data.get("acute_liver_failure") or data.get("hypersensitivity") or data.get("pregnancy_lactation")
    )
    rows: List[Dict[str, Any]] = []
    for name, item in THERAPEUTIC_SCENARIOS.items():
        available = True
        reason = "Disponible para comparar"
        if item.get("pitavastatin"):
            dose_mg = int(item.get("dose_mg") or 0)
            if major_block:
                available = False
                reason = "No disponible mientras exista una alerta mayor para pitavastatina"
            elif dose_mg > max_mg:
                available = False
                reason = f"Supera el máximo calculado de {max_mg} mg/día"
        projected = max(baseline * (1.0 - float(item["reduction"])), 0.0)
        rows.append({
            "Estrategia": name,
            "Tipo": item["type"],
            "Reducción estimada %": round(float(item["reduction"]) * 100.0, 1),
            "LDL-C proyectado": round(projected, 1),
            "Meta": f"<{goal_ldl} mg/dL",
            "Alcanza meta": "Sí" if projected <= goal_ldl else "No",
            "Distancia residual": round(max(projected - goal_ldl, 0.0), 1),
            "Disponibilidad": "Disponible" if available else "No disponible",
            "Motivo / evidencia": reason if not available else item["evidence"],
            "_available": available,
            "_pitavastatin": bool(item.get("pitavastatin")),
            "_dose_mg": item.get("dose_mg"),
            "_reduction": float(item["reduction"]),
        })
    return pd.DataFrame(rows)


def pitavastatin_clinical_fit(data: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    reasons: List[str] = []
    limits: List[str] = []
    if data.get("polypharmacy"):
        reasons.append("Polifarmacia: la baja dependencia de CYP3A4 puede ser una ventaja frente a estatinas más susceptibles, sin asumir ausencia de interacciones.")
    if data.get("hiv_arv"):
        reasons.append("VIH/ARV: existe evidencia de resultados cardiovasculares con pitavastatina 4 mg y debe verificarse el esquema antirretroviral exacto.")
    if data.get("prior_statin_intolerance"):
        reasons.append("Intolerancia previa: puede considerarse como estrategia de reintento con dosis tolerada, titulación y seguimiento estructurado.")
    if data.get("ascvd"):
        reasons.append("ASCVD/enfermedad coronaria: existe evidencia clínica con intensificación de pitavastatina, pero la llegada a meta sigue siendo prioritaria.")
    if float(data.get("required_reduction_pct", 0)) <= 45:
        reasons.append("La magnitud de reducción requerida es compatible con el rango promedio de la monoterapia máxima, si está permitida y es tolerada.")
    if float(data.get("required_reduction_pct", 0)) > 58:
        limits.append("La reducción requerida supera el efecto promedio modelado de pitavastatina 4 mg + ezetimiba; probablemente se necesite una estrategia más intensiva o un tercer agente.")
    if float(data.get("egfr", 90)) < 60:
        limits.append("La función renal limita la dosis máxima modelada de pitavastatina y puede reducir su capacidad de alcanzar la meta como monoterapia.")
    if not reasons:
        reasons.append("No se identificó un fenotipo diferencial fuerte; la selección debe basarse en reducción necesaria, seguridad, preferencia y disponibilidad.")
    return reasons, limits


def dose_recommendation(data: Dict[str, Any], interactions: List[Dict[str, Any]], goal_ldl: int) -> Dict[str, Any]:
    baseline = float(data.get("baseline_ldl") or data.get("ldl", 0))
    gap = required_ldl_reduction(baseline, goal_ldl)
    data["required_reduction_pct"] = gap["percentage"]
    start_mg, max_mg, notes = _pitavastatin_dose_limits(data, interactions)
    scenarios = strategy_comparison(data, interactions, goal_ldl)

    available_pitava = scenarios[(scenarios["_available"] == True) & (scenarios["_pitavastatin"] == True)].copy()
    available_pitava = available_pitava.sort_values(["_reduction", "_dose_mg"], ascending=[True, True])
    reaching = available_pitava[available_pitava["LDL-C proyectado"] <= goal_ldl]

    if not reaching.empty:
        chosen = reaching.iloc[0]
    elif not available_pitava.empty:
        chosen = available_pitava.sort_values("_reduction", ascending=False).iloc[0]
    else:
        chosen = None

    if chosen is not None:
        chosen_name = str(chosen["Estrategia"])
        estimated = float(chosen["LDL-C proyectado"])
        reaches_goal = estimated <= goal_ldl
        requires_combination = str(chosen["Tipo"]) == "Combinación"
    else:
        chosen_name = "Pitavastatina no disponible por alertas/restricciones"
        estimated = baseline
        reaches_goal = False
        requires_combination = False

    comparator_reaching = scenarios[
        (scenarios["_available"] == True) &
        (scenarios["_pitavastatin"] == False) &
        (scenarios["LDL-C proyectado"] <= goal_ldl)
    ]

    if chosen is None:
        recommendation = "Resolver la alerta mayor y seleccionar una alternativa segura."
    elif reaches_goal and not requires_combination:
        recommendation = f"{chosen_name}: primera estrategia pitavastatina modelada que podría alcanzar la meta."
    elif reaches_goal and requires_combination:
        recommendation = f"{chosen_name}: utilizar pitavastatina como base de combinación para aumentar la probabilidad de llegar a meta."
    elif not comparator_reaching.empty:
        recommendation = "La mejor estrategia pitavastatina modelada no alcanza la meta; un esquema de mayor intensidad ofrece mayor probabilidad de lograrla."
    else:
        recommendation = "Ningún escenario estándar modelado alcanza la meta; considerar escalamiento combinado individualizado y reevaluación temprana."

    suitability = (
        f"Brecha requerida desde LDL-C basal/de referencia {baseline:.0f} mg/dL: "
        f"{gap['absolute']:.0f} mg/dL ({gap['percentage']:.1f}%). "
        f"Mejor escenario pitavastatina seleccionado: {chosen_name}, LDL-C proyectado {estimated:.0f} mg/dL."
    )

    return {
        "inicio": f"{start_mg} mg",
        "maxima": f"{max_mg} mg",
        "mejor_estimacion": chosen_name,
        "ldl_estimado": estimated,
        "notas": notes,
        "suitability": suitability,
        "recommended_strategy": recommendation,
        "reaches_goal": reaches_goal,
        "requires_combination": requires_combination,
        "required_reduction_pct": gap["percentage"],
        "required_reduction_abs": gap["absolute"],
        "baseline_ldl": baseline,
        "scenarios": scenarios.drop(columns=[c for c in scenarios.columns if c.startswith("_")]).to_dict("records"),
        "comparator_reaches": not comparator_reaching.empty,
    }


def final_classification(indications: List[str], red_flags: List[str], yellow_flags: List[str], data: Dict[str, Any], dose_info: Dict[str, Any], goal_ldl: int) -> Tuple[str, str, str]:
    if red_flags:
        return (
            "PITAVASTATINA NO RECOMENDADA / ALERTA MAYOR",
            "red-card",
            "Existe una contraindicación o interacción mayor cargada. La prioridad es resolver seguridad y seleccionar una alternativa apropiada.",
        )
    if "Indicación no concluyente con los datos cargados" in indications:
        return (
            "INDICACIÓN HIPOLIPEMIANTE NO CONCLUYENTE",
            "gray-card",
            "Completar estratificación de riesgo, situación terapéutica actual y objetivo antes de elegir la estrategia.",
        )

    fit_reasons, _ = pitavastatin_clinical_fit(data)
    differential_fit = any(data.get(k) for k in ("polypharmacy", "hiv_arv", "prior_statin_intolerance", "ascvd"))
    caution_suffix = " Requiere además resolver las precauciones señaladas." if yellow_flags else ""

    if dose_info.get("reaches_goal") and not dose_info.get("requires_combination"):
        return (
            "PITAVASTATINA APROPIADA Y SUFICIENTE COMO MONOTERAPIA",
            "green-card",
            f"La primera estrategia pitavastatina seleccionada podría alcanzar la meta modelada. {dose_info['recommended_strategy']}{caution_suffix}",
        )
    if dose_info.get("reaches_goal") and dose_info.get("requires_combination") and differential_fit:
        return (
            "PITAVASTATINA PREFERIBLE POR PERFIL CLÍNICO, CON INTENSIFICACIÓN",
            "yellow-card",
            f"El perfil aporta razones específicas para elegir pitavastatina, pero la brecha terapéutica requiere combinación. {dose_info['recommended_strategy']}{caution_suffix}",
        )
    if dose_info.get("reaches_goal") and dose_info.get("requires_combination"):
        return (
            "PITAVASTATINA APROPIADA COMO BASE DE COMBINACIÓN",
            "yellow-card",
            f"La monoterapia no sería suficiente, pero una combinación basada en pitavastatina podría alcanzar la meta. {dose_info['recommended_strategy']}{caution_suffix}",
        )
    return (
        "OTRA ESTRATEGIA OFRECE MAYOR PROBABILIDAD DE ALCANZAR LA META",
        "yellow-card",
        f"La mejor estrategia pitavastatina estándar modelada deja una brecha residual. {dose_info['recommended_strategy']} La selección final debe priorizar eficacia necesaria, tolerabilidad y seguridad.{caution_suffix}",
    )


def personalized_advantages(data: Dict[str, Any], dose_info: Dict[str, Any]) -> List[str]:
    reasons, limits = pitavastatin_clinical_fit(data)
    output = list(reasons)
    if dose_info.get("requires_combination"):
        output.append("La app no interpreta la monoterapia insuficiente como fracaso: propone pitavastatina como base de combinación cuando el escenario combinado alcanza la meta.")
    if dose_info.get("reaches_goal"):
        output.append(f"El escenario seleccionado proyecta LDL-C ≈{dose_info['ldl_estimado']:.0f} mg/dL frente a meta <{data['goal_ldl']} mg/dL.")
    output.extend(limits)
    return output


def followup_response_analysis(
    baseline_ldl: float,
    followup_ldl: float,
    expected_reduction: float,
    goal_ldl: float,
    weeks: int,
    adherence: str,
    muscle_symptoms: str,
    ck_value: float,
    alt_value: float,
) -> Dict[str, Any]:
    baseline = max(float(baseline_ldl), 0.1)
    followup = max(float(followup_ldl), 0.0)
    observed_pct = max((baseline - followup) / baseline * 100.0, -100.0)
    expected_pct = float(expected_reduction) * 100.0
    expected_ldl = baseline * (1.0 - float(expected_reduction))
    difference = observed_pct - expected_pct
    actions: List[str] = []

    if followup <= goal_ldl:
        status = "META ALCANZADA"
        interpretation = "La respuesta observada alcanza la meta cargada. Mantener tolerabilidad, adherencia y seguimiento clínico."
        level = "good"
    elif weeks < 4:
        status = "CONTROL TEMPRANO"
        interpretation = "El control puede ser demasiado precoz para juzgar la respuesta definitiva."
        level = "warn"
        actions.append("Repetir perfil lipídico cuando exista tiempo suficiente desde el inicio o ajuste.")
    elif difference >= -10:
        status = "RESPUESTA ACORDE O CERCANA A LA ESPERADA"
        interpretation = "La reducción observada es compatible con la respuesta modelada, aunque la meta aún no se alcanza."
        level = "warn"
        actions.append("Intensificar según la brecha residual y la estrategia máxima tolerada.")
    else:
        status = "RESPUESTA MENOR A LA ESPERADA"
        interpretation = "La reducción observada es sustancialmente menor que la estimada para la estrategia seleccionada."
        level = "bad"
        actions.extend([
            "Verificar adherencia, interrupciones y forma de administración.",
            "Revisar causas secundarias, interacciones, cambios de peso/dieta y variabilidad biológica.",
            "Confirmar que el LDL-C basal y el control sean comparables.",
        ])

    if adherence in {"Baja (<50%)", "Intermedia (50–79%)"}:
        actions.insert(0, "Priorizar intervención sobre adherencia antes de declarar fracaso farmacológico.")
    if muscle_symptoms != "No":
        actions.append("Caracterizar síntomas musculares, relación temporal, dechallenge/rechallenge y diagnósticos alternativos.")
    if ck_value > 500:
        actions.append("CK elevada: correlacionar con síntomas, ejercicio, trauma y función renal antes de continuar o intensificar.")
    if alt_value > 120:
        actions.append("ALT elevada: aclarar hepatopatía y relación temporal antes de intensificar.")
    if not actions:
        actions.append("Mantener control periódico, adherencia y manejo integral del riesgo cardiovascular.")

    return {
        "status": status,
        "interpretation": interpretation,
        "level": level,
        "baseline_ldl": baseline,
        "followup_ldl": followup,
        "observed_reduction_pct": observed_pct,
        "expected_reduction_pct": expected_pct,
        "expected_ldl": expected_ldl,
        "goal_ldl": float(goal_ldl),
        "gap_to_goal": max(followup - float(goal_ldl), 0.0),
        "weeks": int(weeks),
        "adherence": adherence,
        "muscle_symptoms": muscle_symptoms,
        "ck": float(ck_value),
        "alt": float(alt_value),
        "actions": actions,
    }


def patient_text() -> str:
    return (
        "La pitavastatina es una medicación del grupo de las estatinas. Su objetivo principal es reducir el colesterol LDL, "
        "conocido como colesterol malo. El tratamiento debe acompañarse de alimentación saludable, actividad física, control "
        "del peso y abandono del tabaco si corresponde.\n\n"
        "Consulte de inmediato si presenta dolor muscular intenso, debilidad marcada, fiebre, orina oscura, coloración amarilla "
        "de piel u ojos, o cansancio inusual. No suspenda ni modifique la medicación sin indicación médica."
    )



def evaluation_domains(data: Dict[str, Any], interactions: List[Dict[str, Any]], red_flags: List[str], yellow_flags: List[str], dose_info: Dict[str, Any], goal_ldl: int) -> pd.DataFrame:
    rows: List[Dict[str, str]] = []
    has_indication = bool(data.get("ldl", 0) >= 130 or data.get("ct", 0) >= 200 or data.get("ascvd") or data.get("diabetes") or data.get("hefh"))
    rows.append({
        "Dominio": "Indicación hipolipemiante",
        "Estado": "🟢 Favorable" if has_indication else "🟡 Incompleta",
        "Interpretación": "Hay elementos que apoyan tratamiento hipolipemiante." if has_indication else "Completar riesgo global e indicación antes de decidir.",
        "Acción": "Definir intensidad según riesgo, brecha y objetivo." if has_indication else "Completar estratificación de riesgo.",
    })
    rows.append({
        "Dominio": "Seguridad mayor",
        "Estado": "🔴 Bloqueada" if red_flags else "🟢 Sin alerta mayor",
        "Interpretación": "Existe al menos una alerta mayor cargada." if red_flags else "No se detectaron contraindicaciones/alertas mayores en los datos ingresados.",
        "Acción": "No avanzar con pitavastatina sin resolver la alerta." if red_flags else "Continuar revisión de precauciones.",
    })

    egfr = float(data.get("egfr", 0))
    if egfr < 30:
        renal_state, renal_text, renal_action = "🔴 Alto impacto", "Función renal marcadamente reducida.", "Revisar indicación y dosificación especializada."
    elif egfr < 60:
        renal_state, renal_text, renal_action = "🟡 Ajuste", "La función renal limita la dosis máxima modelada.", "Usar la estrategia permitida y valorar combinación."
    else:
        renal_state, renal_text, renal_action = "🟢 Favorable", "Sin restricción renal automática detectada.", "Seguimiento habitual según contexto."
    rows.append({"Dominio": "Función renal", "Estado": renal_state, "Interpretación": renal_text, "Acción": renal_action})

    muscular_risk = bool(data.get("prior_statin_intolerance") or data.get("hypothyroidism") or float(data.get("ck", 0)) > 500 or any(i.get("riesgo_muscular") for i in interactions))
    rows.append({
        "Dominio": "Riesgo muscular",
        "Estado": "🟡 Vigilancia" if muscular_risk else "🟢 Bajo según carga",
        "Interpretación": "Hay antecedentes, laboratorio o fármacos que aumentan la necesidad de vigilancia." if muscular_risk else "No se detectaron señales musculares relevantes con lo cargado.",
        "Acción": "Documentar síntomas basales y seguimiento; CK según clínica/riesgo." if muscular_risk else "Educar sobre síntomas y controlar según clínica.",
    })

    liver_signal = bool(data.get("acute_liver_failure") or float(data.get("alt", 0)) > 120 or float(data.get("ast", 0)) > 120)
    rows.append({
        "Dominio": "Seguridad hepática",
        "Estado": "🔴/🟡 Revisar" if liver_signal else "🟢 Sin señal relevante",
        "Interpretación": "Hay señal hepática que requiere aclaración antes de avanzar." if liver_signal else "No se detectó señal hepática mayor con los datos cargados.",
        "Acción": "Aclarar etiología y actividad hepática." if liver_signal else "Seguimiento según clínica y práctica habitual.",
    })

    max_level = interaction_max_level(interactions)
    state_map = {
        "ROJO": ("🔴 Mayor", "Se detectó interacción mayor.", "Evitar o resolver combinación antes de indicar."),
        "AMARILLO": ("🟡 Precaución", "Hay ajuste, vigilancia o verificación requerida.", "Revisar fármaco por fármaco."),
        "AZUL": ("🔵 Informativa", "Hay señales contextuales sin contraindicación automática.", "Verificar evidencia específica."),
        "SIN SEÑALES": ("🟢 Sin señal", "No hay coincidencias en la base actual.", "Mantener reconciliación farmacológica."),
    }
    istate, itext, iaction = state_map.get(max_level, state_map["SIN SEÑALES"])
    rows.append({"Dominio": "Interacciones", "Estado": istate, "Interpretación": itext, "Acción": iaction})

    required = float(dose_info.get("required_reduction_pct", 0))
    rows.append({
        "Dominio": "Brecha terapéutica",
        "Estado": "🟢 Moderada" if required <= 45 else ("🟡 Alta" if required <= 58 else "🔴 Muy alta"),
        "Interpretación": f"Se requiere una reducción aproximada de {required:.1f}% desde el LDL-C basal/de referencia.",
        "Acción": "Seleccionar la estrategia mínima eficaz, no solo una dosis aislada.",
    })

    projected = float(dose_info.get("ldl_estimado", data.get("ldl", 0)))
    if dose_info.get("reaches_goal"):
        estate, etext, eaction = "🟢 Meta estimada", f"{dose_info.get('mejor_estimacion')}: LDL-C proyectado ≈{projected:.0f} mg/dL.", "Confirmar respuesta real en seguimiento."
    else:
        gap = max(projected - goal_ldl, 0.0)
        estate, etext, eaction = "🟡 Meta no estimada", f"La mejor estrategia pitavastatina modelada deja ≈{gap:.0f} mg/dL de brecha.", "Comparar mayor intensidad, combinación ampliada o tercer agente."
    rows.append({"Dominio": "Capacidad de alcanzar meta", "Estado": estate, "Interpretación": etext, "Acción": eaction})
    return pd.DataFrame(rows)


def evaluation_key_messages(data: Dict[str, Any], interactions: List[Dict[str, Any]], red_flags: List[str], yellow_flags: List[str], dose_info: Dict[str, Any], goal_ldl: int) -> Tuple[List[str], List[str], List[str]]:
    favor, cautions, actions = [], [], []
    fit_reasons, fit_limits = pitavastatin_clinical_fit(data)
    favor.extend(fit_reasons[:4])
    cautions.extend(red_flags[:3] if red_flags else yellow_flags[:4])
    cautions.extend(fit_limits[:2])
    if not cautions:
        cautions.append("No se detectaron precauciones relevantes con los datos ingresados; esto no excluye información clínica no cargada.")
    actions.append(dose_info.get("recommended_strategy", "Definir estrategia según brecha terapéutica."))
    actions.append(f"Reevaluar LDL-C y tolerabilidad luego del inicio/ajuste; meta cargada <{goal_ldl} mg/dL.")
    if data.get("prior_statin_intolerance"):
        actions.append("Documentar número de estatinas intentadas, dosis mínima, dechallenge/rechallenge y causas secundarias.")
    if interactions:
        actions.append("Reconciliar medicación y resolver primero las interacciones de mayor nivel.")
    return favor, cautions, actions


def build_report(data: Dict[str, Any], indications: List[str], reasons: List[str], red_flags: List[str], yellow_flags: List[str], interactions: List[Dict[str, str]], dose_info: Dict[str, Any], classification: str, summary: str, advantages: List[str]) -> str:
    meds = data.get("meds_text", "").strip() or "No declarada"
    scenarios = dose_info.get("scenarios", [])
    scenario_lines = []
    for row in scenarios:
        scenario_lines.append(
            f"- {row.get('Estrategia')}: reducción {row.get('Reducción estimada %')}%; "
            f"LDL-C proyectado {row.get('LDL-C proyectado')} mg/dL; "
            f"meta: {row.get('Alcanza meta')}; disponibilidad: {row.get('Disponibilidad')}."
        )
    followup = st.session_state.get("last_followup_analysis", {}) or {}
    if followup:
        followup_text = "\n".join([
            f"- Estado: {followup.get('status')}",
            f"- LDL-C basal: {followup.get('baseline_ldl', 0):.0f} mg/dL",
            f"- LDL-C de control: {followup.get('followup_ldl', 0):.0f} mg/dL",
            f"- Reducción observada: {followup.get('observed_reduction_pct', 0):.1f}%",
            f"- Reducción esperada: {followup.get('expected_reduction_pct', 0):.1f}%",
            f"- Interpretación: {followup.get('interpretation', '')}",
            *("- " + x for x in followup.get("actions", [])),
        ])
    else:
        followup_text = "- Sin seguimiento analizado en esta sesión."

    intolerance_detail = ""
    if data.get("prior_statin_intolerance"):
        intolerance_detail = f"""
## Evaluación de intolerancia previa

- Estatinas intentadas informadas: {data.get('statin_attempts', 0)}
- Estatina/dosis asociada: {data.get('intolerance_agent', 'No informada')}
- Síntomas: {data.get('intolerance_symptoms', 'No informados')}
- Mejoría al suspender: {data.get('dechallenge', 'No informado')}
- Reaparición al reexponer: {data.get('rechallenge', 'No informado')}
- Interpretación: pitavastatina puede considerarse una alternativa de reintento; la app no afirma superioridad universal de tolerabilidad.
"""

    return f"""
# Informe clínico-educativo: PitaSmart

Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}
Paciente/código: {data.get('patient_id') or 'Código anónimo/no informado'}
Fuente de datos: {data.get('data_source', 'No informada')}
Autor/Desarrollador: {data.get('author', '')}
Versión app: {APP_VERSION}

## Datos lipídicos y metabólicos

- Edad: {data['age']} años
- Sexo: {data['sex']}
- Colesterol total: {data['ct']:.0f} mg/dL
- LDL-C actual: {data['ldl']:.0f} mg/dL
- LDL-C basal/de referencia: {dose_info.get('baseline_ldl', data['ldl']):.0f} mg/dL
- HDL-C: {data['hdl']:.0f} mg/dL
- Triglicéridos: {data['tg']:.0f} mg/dL
- No-HDL-C: {data['non_hdl']:.0f} mg/dL
- ApoB: {data.get('apob', 0):.0f} mg/dL {'(no informado)' if not data.get('apob') else ''}
- Lp(a): {data.get('lpa', 0):.0f} mg/dL {'(no informada)' if not data.get('lpa') else ''}
- CAC: {data.get('cac', 0):.0f} {'(no informado)' if not data.get('cac') else ''}
- PREVENT 10 años informado: {data.get('prevent_risk', 0):.1f}% {'(no informado)' if not data.get('prevent_risk') else ''}
- eGFR: {data['egfr']:.0f} ml/min/1,73 m²
- Creatinina: {data['creatinine']:.2f} mg/dL
- Glucemia: {data['glucose']:.0f} mg/dL
- HbA1c: {data['hba1c']:.1f} %
- AST/GOT: {data['ast']:.0f} U/L
- ALT/GPT: {data['alt']:.0f} U/L
- CK/CPK: {data['ck']:.0f} U/L
- TSH: {data['tsh']:.2f} µUI/mL
- Categoría de riesgo: {data['risk_category']}
- Objetivo LDL-C usado: <{data['goal_ldl']} mg/dL
- Tratamiento hipolipemiante actual: {data.get('current_therapy', 'No informado')}
- Adherencia declarada: {data.get('adherence', 'No informada')}
- Medicación concomitante: {meds}

## Brecha terapéutica

- Reducción absoluta requerida: {dose_info.get('required_reduction_abs', 0):.0f} mg/dL.
- Reducción porcentual requerida: {dose_info.get('required_reduction_pct', 0):.1f}%.
- Estrategia seleccionada por el motor: {dose_info.get('mejor_estimacion')}.
- LDL-C proyectado: {dose_info.get('ldl_estimado', 0):.0f} mg/dL.

## Resultado final

{classification}

{summary}

## Recomendación estratégica

- {dose_info.get('recommended_strategy', '')}
- Inicio orientativo: {dose_info.get('inicio')} una vez al día.
- Dosis máxima según datos cargados: {dose_info.get('maxima')} una vez al día.
- {dose_info.get('suitability', '')}
{chr(10).join('- ' + x for x in dose_info.get('notas', [])) if dose_info.get('notas') else '- Sin restricciones adicionales de dosis detectadas.'}

## Comparación de estrategias

{chr(10).join(scenario_lines)}

## ¿Por qué pitavastatina en este paciente?

{chr(10).join('- ' + x for x in advantages)}

## Indicaciones y fundamentos

{chr(10).join('- ' + x for x in indications)}
{chr(10).join('- ' + x for x in reasons)}
{intolerance_detail}
## Alertas e interacciones

Alertas mayores:
{chr(10).join('- ' + x for x in red_flags) if red_flags else '- No se detectaron alertas mayores con los datos cargados.'}

Precauciones:
{chr(10).join('- ' + x for x in yellow_flags) if yellow_flags else '- No se detectaron precauciones relevantes con los datos cargados.'}

Interacciones detectadas:
{chr(10).join('- [' + i.get('nivel', '') + '] ' + i['farmaco'].title() + ': ' + i['mensaje'] + ' Acción: ' + i['accion'] for i in interactions) if interactions else '- No se detectaron señales incluidas en la base para la medicación declarada.'}

## Seguimiento de respuesta

{followup_text}

## Seguimiento sugerido

- Repetir perfil lipídico luego del inicio o ajuste y comparar respuesta observada con la esperada.
- Antes de declarar fracaso, verificar adherencia, tiempo de exposición, causas secundarias y comparabilidad de los laboratorios.
- Considerar ALT/AST basal y control según clínica.
- CK no rutinaria; solicitar si hay síntomas musculares o alto riesgo.
- Reforzar estilo de vida y manejo integral del riesgo cardiovascular.

## Texto educativo para paciente

{patient_text()}

## Fuentes utilizadas por la app

{chr(10).join('- ' + x for x in FUENTES)}

Aviso: PitaSmart es una herramienta educativa y de apoyo. No reemplaza juicio médico, historia clínica completa, prospecto aprobado local ni guías vigentes.
""".strip()


def report_to_pdf(report_text: str) -> bytes:
    if not REPORTLAB_OK:
        return b""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=1.4 * cm, leftMargin=1.4 * cm,
        topMargin=1.3 * cm, bottomMargin=1.3 * cm
    )
    styles = getSampleStyleSheet()
    small = ParagraphStyle("SmallClean", parent=styles["BodyText"], fontSize=8.4, leading=11)
    h2 = ParagraphStyle("HeadingClean", parent=styles["Heading2"], fontSize=12.5, leading=14, textColor=colors.HexColor("#1d4ed8"))
    title = ParagraphStyle("TitleClean", parent=styles["Title"], fontSize=16, leading=18, textColor=colors.HexColor("#1d4ed8"))

    story = []
    for raw in report_text.splitlines():
        line = raw.strip()
        if not line:
            story.append(Spacer(1, 5))
            continue
        safe = html.escape(line)
        if line.startswith("# "):
            story.append(Paragraph(html.escape(line[2:]), title))
        elif line.startswith("## "):
            story.append(Spacer(1, 4))
            story.append(Paragraph(html.escape(line[3:]), h2))
        elif line.startswith("- "):
            story.append(Paragraph("• " + html.escape(line[2:]), small))
        else:
            story.append(Paragraph(safe, small))
    doc.build(story)
    buffer.seek(0)
    return buffer.read()


def make_export_table(data: Dict[str, Any], classification: str, dose_info: Dict[str, Any], red_flags: List[str], yellow_flags: List[str], advantages: List[str], interactions: List[Dict[str, Any]]) -> Tuple[bytes, str, str]:
    row = {
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "fuente_datos": data.get("data_source"),
        "paciente_codigo": data.get("patient_id"),
        "edad": data.get("age"),
        "sexo": data.get("sex"),
        "ct": data.get("ct"),
        "ldl_actual": data.get("ldl"),
        "ldl_basal_referencia": dose_info.get("baseline_ldl"),
        "hdl": data.get("hdl"),
        "tg": data.get("tg"),
        "no_hdl": data.get("non_hdl"),
        "apob": data.get("apob"),
        "lpa": data.get("lpa"),
        "cac": data.get("cac"),
        "prevent_10a": data.get("prevent_risk"),
        "egfr": data.get("egfr"),
        "creatinina": data.get("creatinine"),
        "glucemia": data.get("glucose"),
        "hba1c": data.get("hba1c"),
        "ast": data.get("ast"),
        "alt": data.get("alt"),
        "ck": data.get("ck"),
        "tsh": data.get("tsh"),
        "riesgo": data.get("risk_category"),
        "objetivo_ldl": data.get("goal_ldl"),
        "tratamiento_actual": data.get("current_therapy"),
        "adherencia": data.get("adherence"),
        "reduccion_requerida_pct": round(float(dose_info.get("required_reduction_pct", 0)), 1),
        "clasificacion": classification,
        "estrategia_recomendada": dose_info.get("recommended_strategy"),
        "estrategia_seleccionada": dose_info.get("mejor_estimacion"),
        "dosis_inicio": dose_info.get("inicio"),
        "dosis_maxima": dose_info.get("maxima"),
        "ldl_estimado": round(float(dose_info.get("ldl_estimado", 0)), 1),
        "alertas_mayores": " | ".join(red_flags),
        "precauciones": " | ".join(yellow_flags),
        "ajuste_clinico": " | ".join(advantages),
        "nivel_max_interaccion": interaction_max_level(interactions),
        "interacciones_detectadas": " | ".join(f"[{i.get('nivel', '')}] {i.get('farmaco', '')}: {i.get('accion', '')}" for i in interactions),
    }
    eval_df = pd.DataFrame([row])
    scenarios_df = pd.DataFrame(dose_info.get("scenarios", []))
    interactions_df = interactions_dataframe(interactions) if interactions else pd.DataFrame(columns=["Fármaco / grupo", "Nivel", "Acción sugerida"])
    followup = st.session_state.get("last_followup_analysis", {}) or {}
    followup_df = pd.DataFrame([followup]) if followup else pd.DataFrame()
    if not followup_df.empty and "actions" in followup_df.columns:
        followup_df["actions"] = followup_df["actions"].apply(lambda x: " | ".join(x) if isinstance(x, list) else x)
    try:
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            eval_df.to_excel(writer, index=False, sheet_name="evaluacion")
            scenarios_df.to_excel(writer, index=False, sheet_name="estrategias")
            interactions_df.to_excel(writer, index=False, sheet_name="interacciones")
            if not followup_df.empty:
                followup_df.to_excel(writer, index=False, sheet_name="seguimiento")
        output.seek(0)
        return output.read(), "evaluacion_PitaSmart.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    except Exception:
        csv = eval_df.to_csv(index=False).encode("utf-8-sig")
        return csv, "evaluacion_PitaSmart.csv", "text/csv"


def render_classification(classification: str, card_class: str, summary: str) -> None:
    st.markdown(
        f"""
<div class="{card_class}">
<h3 style="margin-top:0">{html.escape(classification)}</h3>
<p>{html.escape(summary)}</p>
</div>
""",
        unsafe_allow_html=True,
    )


# ============================================================
# ESTADO INICIAL
# ============================================================

for k, v in DEFAULTS.items():
    st.session_state.setdefault(f"manual_{k}", v)

st.session_state.setdefault("data_source", "Carga manual")
st.session_state.setdefault("extracted_values", {})
st.session_state.setdefault("extraction_evidence", {})
st.session_state.setdefault("extraction_diagnostics", [])
st.session_state.setdefault("pdf_methods", [])
st.session_state.setdefault("raw_text_len", 0)
st.session_state.setdefault("anon_preview", [])
st.session_state.setdefault("lab_review_version", 0)
st.session_state.setdefault("lab_review_applied", False)
st.session_state.setdefault("lab_confirmed_values", {})
st.session_state.setdefault("lab_confirmed_at", "")
st.session_state.setdefault("followup_extracted_values", {})
st.session_state.setdefault("followup_pdf_methods", [])
st.session_state.setdefault("last_followup_analysis", {})


# ============================================================
# SIDEBAR
# ============================================================


# ============================================================
# HELPERS MULTIPÁGINA (nuevos, no alteran la lógica clínica)
# ============================================================

BRAND_NAME = "EUROPHARMA"
PLATFORM_NAME = "PitaSmart"
PLATFORM_TAGLINE = "Plataforma de decisión clínica en pitavastatina"

DEFAULT_AUTHOR = "Dr. Olano Ricardo Daniel - Cardiólogo Hipertensólogo"
REGULATORY_OPTIONS = [
    "Argentina / ANMAT + guías clínicas",
    "Internacional / FDA + guías clínicas",
    "Educativo general",
]


def init_state() -> None:
    """Estado inicial: idéntico al bloque ESTADO INICIAL del app original."""
    for k, v in DEFAULTS.items():
        st.session_state.setdefault(f"manual_{k}", v)
    st.session_state.setdefault("data_source", "Carga manual")
    st.session_state.setdefault("extracted_values", {})
    st.session_state.setdefault("extraction_evidence", {})
    st.session_state.setdefault("extraction_diagnostics", [])
    st.session_state.setdefault("pdf_methods", [])
    st.session_state.setdefault("raw_text_len", 0)
    st.session_state.setdefault("anon_preview", [])
    st.session_state.setdefault("lab_review_version", 0)
    st.session_state.setdefault("lab_review_applied", False)
    st.session_state.setdefault("lab_confirmed_values", {})
    st.session_state.setdefault("lab_confirmed_at", "")
    st.session_state.setdefault("followup_extracted_values", {})
    st.session_state.setdefault("followup_pdf_methods", [])
    st.session_state.setdefault("last_followup_analysis", {})
    # Config global (antes en el sidebar del app monolítico)
    st.session_state.setdefault("cfg_author", DEFAULT_AUTHOR)
    st.session_state.setdefault("cfg_regulatory", REGULATORY_OPTIONS[0])
    st.session_state.setdefault("cfg_risk_category", list(OBJETIVOS_LDL.keys())[1])
    st.session_state.setdefault("patient_id", "")
    st.session_state.setdefault("sex", "Femenino")


def current_goal() -> Tuple[str, int, int]:
    """Devuelve (categoria_riesgo, objetivo_personalizado, goal_ldl)."""
    risk_category = st.session_state.get("cfg_risk_category", list(OBJETIVOS_LDL.keys())[1])
    custom_goal = int(st.session_state.get("cfg_custom_goal", OBJETIVOS_LDL.get(risk_category, 70)))
    goal_ldl = recommend_goal(risk_category, custom_goal)
    return risk_category, custom_goal, int(goal_ldl)


def build_base_data() -> Tuple[Dict[str, Any], int]:
    """Construye el dict `data` base leyendo session_state.

    Reproduce exactamente el dict `data` del app original (demografía + labs +
    riesgo + objetivo). Las páginas de decisión/seguimiento/informe agregan sus
    propios campos tal como lo hacía el app monolítico.
    """
    ss = st.session_state
    risk_category, _custom_goal, goal_ldl = current_goal()
    no_hdl_value = non_hdl(ss["manual_ct"], ss["manual_hdl"])
    data = {
        "patient_id": ss.get("patient_id", ""),
        "author": ss.get("cfg_author", DEFAULT_AUTHOR),
        "data_source": ss.get("data_source", "Carga manual"),
        "age": int(ss["manual_age"]),
        "sex": ss.get("sex", "Femenino"),
        "ct": float(ss["manual_ct"]),
        "ldl": float(ss["manual_ldl"]),
        "hdl": float(ss["manual_hdl"]),
        "tg": float(ss["manual_tg"]),
        "non_hdl": float(no_hdl_value),
        "egfr": float(ss["manual_egfr"]),
        "creatinine": float(ss["manual_creatinine"]),
        "glucose": float(ss["manual_glucose"]),
        "hba1c": float(ss["manual_hba1c"]),
        "ast": float(ss["manual_ast"]),
        "alt": float(ss["manual_alt"]),
        "ck": float(ss["manual_ck"]),
        "tsh": float(ss["manual_tsh"]),
        "risk_category": risk_category,
        "goal_ldl": int(goal_ldl),
        "apob": 0.0,
        "lpa": 0.0,
        "cac": 0.0,
        "prevent_risk": 0.0,
    }
    return data, int(goal_ldl)


def apply_clinical_defaults(data: Dict[str, Any]) -> Dict[str, Any]:
    """Rellena los campos clínicos ausentes (idéntico al bloque de setdefault del app original)."""
    data.setdefault("ascvd", False)
    data.setdefault("diabetes", False)
    data.setdefault("hta", True)
    data.setdefault("smoking", False)
    data.setdefault("hefh", False)
    data.setdefault("prior_statin_intolerance", False)
    data.setdefault("hiv_arv", False)
    data.setdefault("polypharmacy", False)
    data.setdefault("hypothyroidism", False)
    data.setdefault("acute_liver_failure", False)
    data.setdefault("alcohol_liver_history", False)
    data.setdefault("pregnancy_lactation", False)
    data.setdefault("hypersensitivity", False)
    data.setdefault("meds_text", "")
    data.setdefault("baseline_ldl", float(data.get("ldl", 0)))
    data.setdefault("current_therapy", "Sin tratamiento")
    data.setdefault("adherence", "No evaluada")
    data.setdefault("weeks_on_therapy", 0)
    data.setdefault("apob", 0.0)
    data.setdefault("lpa", 0.0)
    data.setdefault("cac", 0.0)
    data.setdefault("prevent_risk", 0.0)
    data.setdefault("statin_attempts", 0)
    data.setdefault("intolerance_agent", "No informado")
    data.setdefault("intolerance_symptoms", "No informados")
    data.setdefault("dechallenge", "No informado")
    data.setdefault("rechallenge", "No informado")
    return data
