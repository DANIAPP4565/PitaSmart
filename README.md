# EUROPHARMA · PitaSmart — Web multipágina (Streamlit)

Plataforma de decisión clínica en pitavastatina con identidad "farma premium" de Europharma.
El motor clínico original está intacto; se agregó la capa visual, la navegación y un módulo de
**evidencia comparada y lipidología de precisión**.

## Estructura (4 archivos de código)

```
app.py           # Navegación + páginas del flujo clínico (definidas como FUNCIONES)
core.py          # Motor clínico intacto (extracción PDF, dosis, interacciones, informe...)
theme.py         # Identidad visual Europharma (paleta, hero, tarjetas, medidor de meta)
evidence.py      # Comparador de estatinas, estudios de respaldo y lipidología de precisión
requirements.txt
.streamlit/config.toml
assets/logo.svg
```

> **No hace falta ninguna carpeta `pages/`.** Las páginas son funciones registradas con
> `st.Page(funcion, ...)`, por lo que Streamlit Cloud no necesita encontrar archivos sueltos.

## Ejecutar

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Secciones

**Plataforma:** Inicio
**Flujo clínico:** Importar laboratorio · Decisión y meta · Seguimiento · Informe y descargas
**Evidencia comparada:** Comparador de estatinas · Lipidología de precisión
**Conocimiento:** Base clínica y evidencia · Texto para paciente · Fuentes y uso

### Comparador de estatinas
16 esquemas (pitavastatina, rosuvastatina, atorvastatina, simvastatina, pravastatina,
fluvastatina, lovastatina), con reducción esperada de LDL-C, LDL-C proyectado, si alcanzan la
meta del paciente y la **reducción relativa de eventos estimada** aplicando la relación del
metaanálisis CTT (22% por cada 1 mmol/L ≈ 38,7 mg/dL de descenso de LDL-C). Opción de sumar
ezetimiba a todos los esquemas.

### Lipidología de precisión
ApoB, Lp(a), no-HDL-C y colesterol remanente con sus metas; detección de **discordancias**
(LDL-C "en meta" con riesgo residual) y una matriz de por qué la elección de molécula no es
intercambiable: metabolismo glucídico, farmacogenómica SLCO1B1, polifarmacia/CYP3A4, VIH e
intensidad necesaria.

## Evidencia citada

| Estudio | Aporte |
|---|---|
| REAL-CAD (Circulation 2018;137:1997-2009) | Pitavastatina 4 mg vs 1 mg: 4,3% vs 5,4%; HR 0,81 (0,69–0,95) |
| REPRIEVE (NEJM 2023;389:687-699) | Pitavastatina 4 mg vs placebo en VIH: MACE 4,81 vs 7,32/1.000 personas-año |
| PATROL (Circ J 2011) | Pitavastatina 2 mg no inferior a atorvastatina 10 mg y rosuvastatina 2,5 mg |
| PREVAIL-US (J Clin Lipidol 2012) | Pitavastatina 4 mg superior a pravastatina 40 mg |
| J-PREDICT | Menor incidencia de diabetes de novo en IGT |
| CTT (Lancet 2010;376:1670-1681) | 22% menos eventos vasculares por mmol/L de LDL-C |
| CPIC 2022 (SLCO1B1/ABCG2/CYP2C9) | Impacto mínimo de rs4149056 sobre pitavastatina |
| VOYAGER | Potencia comparada rosuvastatina/atorvastatina/simvastatina |

Las magnitudes de reducción son **promedios orientativos**; la respuesta individual se confirma
con un perfil lipídico de control.

> Herramienta de apoyo educativo para profesionales. No reemplaza el juicio clínico, la historia
> clínica completa, las guías vigentes ni el prospecto aprobado local.
