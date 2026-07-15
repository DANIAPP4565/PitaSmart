# EUROPHARMA · PitaSmart — Web multipágina

Rediseño gráfico de la aplicación de decisión clínica en pitavastatina, con identidad visual
"farma premium" de Europharma y arquitectura multipágina en Streamlit. **La lógica clínica es
idéntica** a la app original (motor de indicación, dosis, interacciones, extracción de PDF,
seguimiento e informes); sólo se reescribió la capa visual y la navegación.

## Cómo ejecutar

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Estructura

```
europharma_pitasmart/
├── app.py                 # Entrada: tema + sidebar de marca/config + st.navigation
├── core.py                # Motor clínico (lógica intacta) + helpers de estado multipágina
├── theme.py               # Identidad Europharma: paleta, logo SVG, hero, tarjetas, CSS
├── requirements.txt
├── .streamlit/config.toml # Tema base de Streamlit (colores de marca)
└── pages/
    ├── 1_Inicio.py        # Portada: hero, KPIs del caso y accesos a cada módulo
    ├── 2_Importar.py      # Importación guiada (PDF/texto), revisión y confirmación
    ├── 3_Decision.py      # Brecha a meta, comparador de estrategias, interacciones
    ├── 4_Seguimiento.py   # Respuesta observada vs. esperada y tolerabilidad
    ├── 5_Informe.py       # Informe editable + descargas MD/PDF/Excel/JSON
    ├── 6_Evidencia.py     # Base clínica, escenarios y matriz de evidencia
    ├── 7_Paciente.py      # Texto educativo para paciente
    └── 8_Fuentes.py       # Fuentes, instalación y notas institucionales
```

## Qué cambió respecto del original

- **Multipágina real** con `st.navigation`: cada sección es una página con su propio hero.
- **Identidad Europharma**: azul profundo + verde salud, logo SVG, tarjetas KPI, gradientes,
  sidebar de marca y pie institucional.
- **Configuración global** (autor, marco regulatorio, riesgo, objetivo) en el sidebar,
  compartida por todas las páginas vía `session_state`.
- **Realce de funcionalidades**: portada con panorama del caso, tarjetas de navegación,
  semáforos y métricas destacadas.

## Qué NO cambió

Todo el motor clínico: extracción multimotor de laboratorio, control de plausibilidad y
coherencia, cálculo de brecha a meta, recomendación de dosis, base de interacciones, análisis
de seguimiento e informes. Las funciones se movieron sin modificar a `core.py`.

> Herramienta de apoyo educativo para profesionales. No reemplaza el juicio clínico, la historia
> clínica completa, las guías vigentes ni el prospecto aprobado local.
