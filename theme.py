# theme.py
# EUROPHARMA · PitaSmart — Identidad visual "farma premium".
# Provee: paleta, logo SVG, inyección de CSS, hero, cabeceras de sección y tarjetas.
# IMPORTANTE: conserva las clases CSS que usan render_result_card / render_classification
# del core (result-card, result-good/warn/bad/info, kpi-label, kpi-value,
# green-card, yellow-card, red-card, gray-card, card, step-card, badge, big-title, small-muted).

from __future__ import annotations
import html
import streamlit as st

# ---- Paleta de marca -------------------------------------------------------
PALETTE = {
    "blue":   "#0E5AA7",   # azul Europharma
    "blue2":  "#1179C4",
    "deep":   "#0A2C52",   # azul profundo
    "teal":   "#12A594",   # verde salud
    "teal2":  "#0FBFA6",
    "cyan":   "#38BDF8",
    "ink":    "#0B2239",
    "slate":  "#41597A",
    "line":   "#DFEAF5",
    "bg":     "#F5F9FD",
    "white":  "#FFFFFF",
    "amber":  "#E08A00",
    "red":    "#DC2F3C",
    "green":  "#128A4E",
}


def brand_logo_svg(height: int = 34, on_dark: bool = False) -> str:
    """Wordmark Europharma: cápsula + pulso cardíaco + tipografía."""
    text_color = "#FFFFFF" if on_dark else PALETTE["deep"]
    accent = "#8FE3D6" if on_dark else PALETTE["teal"]
    mark = "#FFFFFF" if on_dark else PALETTE["blue"]
    return f"""
<svg width="{height*6.4}" height="{height}" viewBox="0 0 320 50" fill="none" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Europharma">
  <defs>
    <linearGradient id="epcap" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{mark}"/>
      <stop offset="1" stop-color="{accent}"/>
    </linearGradient>
  </defs>
  <rect x="2" y="6" width="38" height="38" rx="11" fill="url(#epcap)"/>
  <path d="M9 27 h6 l3 -9 l5 16 l3 -9 h6" fill="none" stroke="#FFFFFF" stroke-width="2.6"
        stroke-linecap="round" stroke-linejoin="round"/>
  <text x="52" y="26" font-family="Segoe UI, Helvetica, Arial, sans-serif" font-size="22"
        font-weight="800" letter-spacing="1.5" fill="{text_color}">EUROPHARMA</text>
  <text x="53" y="42" font-family="Segoe UI, Helvetica, Arial, sans-serif" font-size="10.5"
        font-weight="600" letter-spacing="3.4" fill="{accent}">LABORATORIO CLÍNICO</text>
</svg>
"""


def inject_theme() -> None:
    p = PALETTE
    st.markdown(
        f"""
<style>
:root {{
  --ep-blue:{p['blue']}; --ep-blue2:{p['blue2']}; --ep-deep:{p['deep']};
  --ep-teal:{p['teal']}; --ep-teal2:{p['teal2']}; --ep-cyan:{p['cyan']};
  --ep-ink:{p['ink']}; --ep-slate:{p['slate']}; --ep-line:{p['line']};
  --ep-bg:{p['bg']}; --ep-amber:{p['amber']}; --ep-red:{p['red']}; --ep-green:{p['green']};
}}

/* Lienzo general */
html, body, [data-testid="stAppViewContainer"] {{
  background:
    radial-gradient(1200px 480px at 8% -8%, #EAF3FC 0%, rgba(234,243,252,0) 60%),
    radial-gradient(1000px 420px at 100% 0%, #E7F6F2 0%, rgba(231,246,242,0) 55%),
    var(--ep-bg);
}}
.main .block-container {{ padding-top: 1.1rem; max-width: 1180px; }}
[data-testid="stAppViewContainer"] * {{ font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif; }}

/* Sidebar */
[data-testid="stSidebar"] {{
  background: linear-gradient(178deg, #0A2C52 0%, #0E4C86 62%, #0F6F8E 100%);
}}
[data-testid="stSidebar"] * {{ color: #E9F2FB !important; }}
[data-testid="stSidebar"] .ep-sb-brand {{
  padding: 6px 4px 14px 4px; border-bottom: 1px solid rgba(255,255,255,.14); margin-bottom: 12px;
}}
[data-testid="stSidebar"] .ep-sb-tag {{
  font-size:.74rem; letter-spacing:.14em; text-transform:uppercase; opacity:.75; margin-top:6px;
}}
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {{ color:#CFE2F5 !important; font-weight:600; }}
[data-testid="stSidebar"] input, [data-testid="stSidebar"] textarea,
[data-testid="stSidebar"] [data-baseweb="select"] > div {{
  background: rgba(255,255,255,.10) !important; color:#fff !important; border-radius:10px !important;
  border:1px solid rgba(255,255,255,.18) !important;
}}
/* Navegación de páginas */
[data-testid="stSidebarNav"] a {{ border-radius:10px; }}
[data-testid="stSidebarNav"] a:hover {{ background: rgba(255,255,255,.10); }}

/* HERO de cada página */
.ep-hero {{
  position:relative; overflow:hidden; border-radius:22px; padding:26px 30px;
  background: linear-gradient(120deg, #0A2C52 0%, #0E5AA7 52%, #12A594 116%);
  color:#EAF4FF; box-shadow: 0 18px 40px -22px rgba(10,44,82,.7); margin-bottom:18px;
}}
.ep-hero::after {{
  content:""; position:absolute; right:-60px; top:-70px; width:280px; height:280px; border-radius:50%;
  background: radial-gradient(circle at center, rgba(56,189,248,.35), rgba(56,189,248,0) 70%);
}}
.ep-hero .ep-eyebrow {{
  display:inline-block; font-size:.72rem; letter-spacing:.2em; text-transform:uppercase;
  background: rgba(255,255,255,.16); border:1px solid rgba(255,255,255,.25);
  padding:4px 12px; border-radius:999px; font-weight:700; margin-bottom:12px;
}}
.ep-hero h1 {{ margin:.1rem 0 .3rem 0; font-size:2.05rem; font-weight:850; line-height:1.06; color:#fff; }}
.ep-hero p {{ margin:0; max-width:820px; font-size:1.02rem; opacity:.92; }}
.ep-hero .ep-ico {{ font-size:1.9rem; }}

/* Título de sección */
.ep-section {{ display:flex; align-items:center; gap:10px; margin:.4rem 0 .1rem 0; }}
.ep-section .ep-bar {{ width:6px; height:24px; border-radius:6px; background:linear-gradient(180deg,var(--ep-blue),var(--ep-teal)); }}
.ep-section h3 {{ margin:0; font-size:1.24rem; font-weight:820; color:var(--ep-deep); }}
.ep-section-desc {{ color:var(--ep-slate); font-size:.94rem; margin:.15rem 0 .6rem 16px; }}

/* Tarjetas KPI de portada / dashboards */
.ep-stat {{
  border-radius:16px; padding:16px 18px; background:#fff; border:1px solid var(--ep-line);
  box-shadow: 0 10px 26px -20px rgba(14,90,167,.55); height:100%;
}}
.ep-stat .ep-stat-ico {{ font-size:1.35rem; }}
.ep-stat .ep-stat-val {{ font-size:1.7rem; font-weight:850; color:var(--ep-deep); line-height:1.1; margin-top:4px; }}
.ep-stat .ep-stat-lbl {{ font-size:.82rem; text-transform:uppercase; letter-spacing:.04em; color:var(--ep-slate); font-weight:700; }}
.ep-stat .ep-stat-note {{ font-size:.84rem; color:var(--ep-slate); margin-top:4px; }}

/* Tarjeta de navegación (portada) */
.ep-nav {{
  border-radius:18px; padding:18px; background:#fff; border:1px solid var(--ep-line);
  box-shadow: 0 12px 30px -22px rgba(10,44,82,.6); height:100%;
  border-top:5px solid var(--ep-blue);
}}
.ep-nav .ep-nav-ico {{ font-size:1.7rem; }}
.ep-nav h4 {{ margin:.4rem 0 .25rem 0; color:var(--ep-deep); font-size:1.08rem; font-weight:800; }}
.ep-nav p {{ margin:0; color:var(--ep-slate); font-size:.9rem; }}

/* Chips / badges (compat con .badge del core) */
.badge, .ep-chip {{
  display:inline-block; border-radius:999px; padding:5px 12px; font-size:.8rem; font-weight:650;
  background: rgba(14,90,167,.10); border:1px solid rgba(14,90,167,.22); color:var(--ep-blue);
  margin-right:6px; margin-bottom:6px;
}}
.ep-chip-teal {{ background: rgba(18,165,148,.12); border-color: rgba(18,165,148,.28); color:#0C7C6E; }}

.big-title {{ font-size:2.1rem; font-weight:850; line-height:1.05; color:var(--ep-deep); }}
.small-muted {{ font-size:.9rem; color:var(--ep-slate); }}

/* Tarjetas de contenido (compat .card del core) */
.card {{
  border-radius:16px; padding:18px; border:1px solid var(--ep-line);
  background:#fff; box-shadow:0 10px 26px -22px rgba(10,44,82,.5); margin-bottom:12px;
}}
.card h4 {{ margin-top:0; color:var(--ep-deep); }}
.card ul {{ margin:.3rem 0 0 0; padding-left:1.1rem; color:var(--ep-slate); }}
.card li {{ margin:.2rem 0; }}

/* Clasificación (render_classification) */
.green-card  {{ border-left:9px solid var(--ep-green); border-radius:14px; padding:18px; background:rgba(18,138,78,.09); }}
.yellow-card {{ border-left:9px solid var(--ep-amber); border-radius:14px; padding:18px; background:rgba(224,138,0,.10); }}
.red-card    {{ border-left:9px solid var(--ep-red);   border-radius:14px; padding:18px; background:rgba(220,47,60,.09); }}
.gray-card   {{ border-left:9px solid var(--ep-slate); border-radius:14px; padding:18px; background:rgba(65,86,122,.09); }}
.green-card h3,.yellow-card h3,.red-card h3,.gray-card h3 {{ color:var(--ep-deep); }}

/* Pasos (step-card) */
.step-card {{
  border-radius:16px; padding:15px 16px; border:1px solid var(--ep-line);
  background: linear-gradient(180deg,#FFFFFF, #F4F9FE); min-height:112px;
  box-shadow:0 10px 26px -22px rgba(10,44,82,.5);
}}
.step-num {{ font-size:.74rem; font-weight:800; color:var(--ep-teal); text-transform:uppercase; letter-spacing:.08em; }}
.step-title {{ font-size:1.05rem; font-weight:820; margin:.15rem 0 .25rem 0; color:var(--ep-deep); }}

/* Result cards (render_result_card) */
.result-card {{ border-radius:16px; padding:15px 16px; border:1px solid var(--ep-line); background:#fff; margin-bottom:10px; box-shadow:0 10px 24px -22px rgba(10,44,82,.5); }}
.result-good {{ border-left:7px solid var(--ep-green); }}
.result-warn {{ border-left:7px solid var(--ep-amber); }}
.result-bad  {{ border-left:7px solid var(--ep-red); }}
.result-info {{ border-left:7px solid var(--ep-blue); }}
.kpi-label {{ font-size:.8rem; color:var(--ep-slate); text-transform:uppercase; letter-spacing:.03em; font-weight:700; }}
.kpi-value {{ font-size:1.4rem; font-weight:850; line-height:1.15; color:var(--ep-deep); }}

/* Tabs internos */
.stTabs [data-baseweb="tab-list"] {{ gap:6px; }}
.stTabs [data-baseweb="tab"] {{ border-radius:10px 10px 0 0; font-weight:650; }}

/* Botones */
.stButton > button, .stDownloadButton > button {{ border-radius:11px; font-weight:700; }}
.stButton > button[kind="primary"] {{
  background: linear-gradient(120deg, var(--ep-blue), var(--ep-teal)); border:0;
}}

/* Métricas nativas */
[data-testid="stMetric"] {{
  background:#fff; border:1px solid var(--ep-line); border-radius:14px; padding:12px 14px;
  box-shadow:0 10px 24px -22px rgba(10,44,82,.5);
}}
[data-testid="stMetricValue"] {{ color:var(--ep-deep); }}

/* Pie institucional */
.ep-footer {{
  margin-top:26px; padding-top:14px; border-top:1px solid var(--ep-line);
  color:var(--ep-slate); font-size:.82rem; display:flex; justify-content:space-between; flex-wrap:wrap; gap:8px;
}}
</style>
""",
        unsafe_allow_html=True,
    )


def brand_sidebar() -> None:
    st.markdown(
        f'<div class="ep-sb-brand">{brand_logo_svg(30, on_dark=True)}'
        f'<div class="ep-sb-tag">· PitaSmart · Decisión clínica</div></div>',
        unsafe_allow_html=True,
    )


def page_hero(title: str, subtitle: str, eyebrow: str = "", icon: str = "") -> None:
    eyebrow_html = f'<div class="ep-eyebrow">{html.escape(eyebrow)}</div>' if eyebrow else ""
    icon_html = f'<span class="ep-ico">{icon}</span> ' if icon else ""
    st.markdown(
        f"""
<div class="ep-hero">
  {eyebrow_html}
  <h1>{icon_html}{html.escape(title)}</h1>
  <p>{html.escape(subtitle)}</p>
</div>
""",
        unsafe_allow_html=True,
    )


def section(title: str, desc: str = "") -> None:
    st.markdown(
        f'<div class="ep-section"><span class="ep-bar"></span><h3>{html.escape(title)}</h3></div>',
        unsafe_allow_html=True,
    )
    if desc:
        st.markdown(f'<div class="ep-section-desc">{html.escape(desc)}</div>', unsafe_allow_html=True)


def stat_card(label: str, value: str, note: str = "", icon: str = "") -> None:
    st.markdown(
        f"""
<div class="ep-stat">
  <div class="ep-stat-ico">{icon}</div>
  <div class="ep-stat-val">{html.escape(value)}</div>
  <div class="ep-stat-lbl">{html.escape(label)}</div>
  <div class="ep-stat-note">{html.escape(note)}</div>
</div>
""",
        unsafe_allow_html=True,
    )


def nav_card(icon: str, title: str, desc: str) -> None:
    st.markdown(
        f"""
<div class="ep-nav">
  <div class="ep-nav-ico">{icon}</div>
  <h4>{html.escape(title)}</h4>
  <p>{html.escape(desc)}</p>
</div>
""",
        unsafe_allow_html=True,
    )


def goal_meter(baseline: float, current: float, goal: float, projected: float | None = None) -> None:
    """Medidor visual de progreso LDL-C hacia la meta (SVG responsivo)."""
    baseline = float(baseline); current = float(current); goal = float(goal)
    span = max(baseline, current, goal) - min(goal, current, baseline)
    lo = min(goal, current, baseline) - max(8.0, span * 0.08)
    hi = max(baseline, current, goal) + max(8.0, span * 0.08)
    if hi - lo < 1:
        hi = lo + 1
    x0, x1, w = 60.0, 560.0, 500.0

    def px(v: float) -> float:
        return x0 + (float(v) - lo) / (hi - lo) * w

    need = baseline - goal
    done = baseline - current
    pct = 0 if need <= 0 else max(0.0, min(1.0, done / need))
    reached = current <= goal
    fill_col = PALETTE["teal"] if reached else PALETTE["blue"]
    gap = max(0.0, current - goal)
    status = "Meta alcanzada" if reached else f"Faltan {gap:.0f} mg/dL"
    status_col = PALETTE["green"] if reached else PALETTE["amber"]

    cur_x = px(current); goal_x = px(goal); base_x = px(baseline)
    proj_marker = ""
    if projected is not None:
        pj_x = px(projected)
        proj_marker = (
            f'<line x1="{pj_x:.1f}" y1="46" x2="{pj_x:.1f}" y2="88" stroke="{PALETTE["deep"]}" '
            f'stroke-width="2" stroke-dasharray="3 3"/>'
            f'<text x="{pj_x:.1f}" y="104" text-anchor="middle" font-size="12" fill="{PALETTE["slate"]}">'
            f'Proy. {float(projected):.0f}</text>'
        )
    st.markdown(
        f"""
<div style="background:#fff;border:1px solid {PALETTE['line']};border-radius:16px;padding:14px 18px 6px;
            box-shadow:0 10px 26px -20px rgba(14,90,167,.55);">
  <div style="display:flex;justify-content:space-between;align-items:baseline;">
    <div style="font-weight:800;color:{PALETTE['deep']};">Progreso a meta de LDL-C</div>
    <div style="font-weight:800;color:{status_col};">{status} · {pct*100:.0f}%</div>
  </div>
  <svg viewBox="0 0 620 118" width="100%" height="118" xmlns="http://www.w3.org/2000/svg">
    <rect x="{x0}" y="58" width="{w}" height="14" rx="7" fill="#E9F1FA"/>
    <rect x="{min(base_x,cur_x):.1f}" y="58" width="{abs(cur_x-base_x):.1f}" height="14" rx="7" fill="{fill_col}" opacity="0.9"/>
    <line x1="{goal_x:.1f}" y1="44" x2="{goal_x:.1f}" y2="86" stroke="{PALETTE['teal']}" stroke-width="3"/>
    <text x="{goal_x:.1f}" y="38" text-anchor="middle" font-size="12" font-weight="700" fill="{PALETTE['teal']}">Meta &lt;{goal:.0f}</text>
    <circle cx="{base_x:.1f}" cy="65" r="6" fill="#fff" stroke="{PALETTE['slate']}" stroke-width="2"/>
    <text x="{base_x:.1f}" y="104" text-anchor="middle" font-size="12" fill="{PALETTE['slate']}">Basal {baseline:.0f}</text>
    <circle cx="{cur_x:.1f}" cy="65" r="8" fill="{fill_col}" stroke="#fff" stroke-width="2"/>
    <text x="{cur_x:.1f}" y="24" text-anchor="middle" font-size="15" font-weight="850" fill="{PALETTE['deep']}">{current:.0f}</text>
    {proj_marker}
  </svg>
</div>
""",
        unsafe_allow_html=True,
    )


def footer(version: str, date: str, regulatory: str) -> None:
    st.markdown(
        f"""
<div class="ep-footer">
  <span>© EUROPHARMA · PitaSmart — apoyo educativo para profesionales. No reemplaza el juicio clínico.</span>
  <span>{html.escape(version)} · {html.escape(date)} · {html.escape(regulatory)}</span>
</div>
""",
        unsafe_allow_html=True,
    )
