import streamlit as st
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

def mostrar(df_actual):

    st.markdown("## 📊 Análisis de Espectros Gamma — INAA")
    st.markdown("Simulación de Análisis por Activación Neutrónica | Detector HPGe | FWHM < 2 keV")
    st.divider()

    col1, col2 = st.columns([2, 1])

    with col1:
        punto_sel = st.selectbox("📍 Seleccionar punto de muestreo:", df_actual["nombre"].tolist())
    with col2:
        modo = st.radio("Modo:", ["Individual", "Comparar zonas"], horizontal=True)

    fila = df_actual[df_actual["nombre"] == punto_sel].iloc[0]
    energias = np.linspace(0, 1600, 3200)

    def pico(centro, intensidad, sigma=2.5):
        return intensidad * np.exp(-0.5 * ((energias - centro) / sigma) ** 2)

    espectro = (
        np.random.exponential(0.3, len(energias)) * 0.4 +
        pico(661.7,  fila["Cs137_Bq_m3"] * 180, 2.8) +   # Cs-137 — 661.7 keV
        pico(1460.8, fila["K40_Bq_L"] * 0.8,    3.2) +   # K-40   — 1460.8 keV
        pico(514.0,  fila["Sr90_Bq_L"] * 90,    2.5) +   # Sr-90  — 514.0 keV
        pico(1173.2, 14, 2.8) +                           # Co-60  — 1173.2 keV (fondo)
        pico(1332.5, 11, 2.8)                             # Co-60  — 1332.5 keV (fondo)
    )

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=energias, y=espectro, mode="lines",
        line=dict(color="#00d4ff", width=1.2), name="Espectro",
        fill="tozeroy", fillcolor="rgba(0,212,255,0.08)"
    ))

    picos_ref = [
        (661.7,  "Cs-137\n661.7 keV",  "#ff4444"),
        (1460.8, "K-40\n1460.8 keV",   "#ffaa00"),
        (514.0,  "Sr-90\n514 keV",     "#cc44ff"),
        (1173.2, "Co-60\n1173.2 keV",  "#44ff88"),
        (1332.5, "Co-60\n1332.5 keV",  "#44ff88"),
    ]
    for en, label, color in picos_ref:
        fig.add_vline(x=en, line_dash="dash", line_color=color, opacity=0.6)
        fig.add_annotation(x=en, y=max(espectro) * 0.82, text=label,
                           showarrow=False, font=dict(color=color, size=9),
                           textangle=-90)

    fig.update_layout(
        title=f"Espectro Gamma — {punto_sel}",
        xaxis_title="Energía (keV)",
        yaxis_title="Cuentas / segundo",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#e0e0e0",
        height=420,
    )
    st.plotly_chart(fig, use_container_width=True)

    st.divider()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("☢️ Cs-137", f"{fila['Cs137_Bq_m3']} Bq/m³",  "Pico: 661.7 keV")
    c2.metric("🔬 K-40",   f"{fila['K40_Bq_L']} Bq/L",      "Pico: 1460.8 keV")
    c3.metric("⚗️ Sr-90",  f"{fila['Sr90_Bq_L']} Bq/L",     "Pico: 514.0 keV")
    c4.metric("🌡️ EDR",   f"{fila['EDR_uSv_h']} µSv/h",    "Fondo gamma")

    st.divider()
    st.markdown("#### 📊 Distribución de Cs-137 en todos los nodos")
    fig2 = px.violin(df_actual, y="Cs137_Bq_m3", x="zona", color="zona", box=True,
                     color_discrete_map={"Norte":"#00d4ff","Central":"#ffd700","Sur":"#ff6b6b"},
                     labels={"Cs137_Bq_m3":"Cs-137 (Bq/m³)","zona":"Zona"},
                     height=300)
    fig2.add_hline(y=10, line_dash="dash", line_color="red", annotation_text="Límite IAEA")
    fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                       font_color="#e0e0e0", showlegend=False)
    st.plotly_chart(fig2, use_container_width=True)