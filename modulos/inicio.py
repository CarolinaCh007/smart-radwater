import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from utils.generador import LIMITES_IAEA

def mostrar(df, df_actual):

    st.markdown("## 🏠 Centro de Control")
    st.markdown("**Sistema de Tratamiento Radiolítico Molecular Avanzado, Bolivia**")
    st.divider()

    # ── KPIs ──────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    criticos   = len(df_actual[df_actual["Estado"] == "CRÍTICO"])
    precaucion = len(df_actual[df_actual["Estado"] == "PRECAUCIÓN"])
    normales   = len(df_actual[df_actual["Estado"] == "NORMAL"])

    c1.metric("📡 Nodos Activos",    "15 / 15",    "100% operativo")
    c2.metric("☢️ Cs-137 Promedio", f"{df_actual['Cs137_Bq_m3'].mean():.3f} Bq/m³", f"Límite: 10 Bq/m³")
    c3.metric("💧 pH Promedio",      f"{df_actual['pH'].mean():.2f}", "Óptimo: 6.5–8.5")
    c4.metric("💚 Salud Promedio",   f"{df_actual['Indice_Salud'].mean():.1f} / 100", "")
    c5.metric("🚨 Alertas Activas",  str(criticos + precaucion), f"{criticos} críticos")

    st.divider()

    # ── Gráficos fila 1 ───────────────────────────────
    col_a, col_b = st.columns([3, 2])

    with col_a:
        st.markdown("#### 📈 Cs-137 por Punto de Muestreo")
        fig = px.bar(
            df_actual.sort_values("Cs137_Bq_m3", ascending=False),
            x="nombre", y="Cs137_Bq_m3",
            color="Indice_Salud",
            color_continuous_scale="RdYlGn",
            labels={"nombre": "", "Cs137_Bq_m3": "Cs-137 (Bq/m³)"},
            height=320,
        )
        fig.add_hline(y=10, line_dash="dash", line_color="#ff4444",
                      annotation_text="Límite IAEA 10 Bq/m³")
        fig.update_layout(**_layout())
        fig.update_xaxes(tickangle=-40)
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.markdown("#### 🥧 Estado de la Red")
        fig2 = go.Figure(go.Pie(
            labels=["🟢 Normal", "🟡 Precaución", "🔴 Crítico"],
            values=[normales, precaucion, criticos],
            hole=0.55,
            marker_colors=["#2ecc71", "#f39c12", "#e74c3c"],
        ))
        fig2.update_layout(**_layout(), height=320,
                           annotations=[dict(text="Estado", x=0.5, y=0.5,
                                             font_size=14, showarrow=False,
                                             font_color="white")])
        st.plotly_chart(fig2, use_container_width=True)

    # ── Gráfico fila 2: tendencia histórica ───────────
    st.markdown("#### 📉 Tendencia Histórica — Índice de Salud (últimos 300 registros)")
    df_trend = df.groupby("timestamp")["Indice_Salud"].mean().reset_index()
    df_trend = df_trend.tail(50)
    fig3 = px.line(df_trend, x="timestamp", y="Indice_Salud",
                   labels={"timestamp": "Tiempo", "Indice_Salud": "Índice Salud"},
                   height=250, color_discrete_sequence=["#00d4ff"])
    fig3.add_hline(y=40, line_dash="dot", line_color="#e74c3c", annotation_text="Crítico")
    fig3.add_hline(y=70, line_dash="dot", line_color="#f39c12", annotation_text="Precaución")
    fig3.update_layout(**_layout())
    st.plotly_chart(fig3, use_container_width=True)

    # ── Tabla resumen ─────────────────────────────────
    st.markdown("#### 📋 Estado Actual — Todos los Nodos")
    cols_tabla = ["nombre","zona","Cs137_Bq_m3","pH","Turbidez_NTU","EDR_uSv_h","Indice_Salud","Estado"]
    st.dataframe(
        df_actual[cols_tabla].rename(columns={
            "nombre":"Punto","zona":"Zona",
            "Cs137_Bq_m3":"Cs-137 (Bq/m³)","Turbidez_NTU":"Turbidez (NTU)",
            "EDR_uSv_h":"EDR (µSv/h)","Indice_Salud":"Índice Salud"
        }),
        use_container_width=True, hide_index=True,
    )

# ── Helpers ───────────────────────────────────────────
def _layout():
    return dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#e0e0e0",
        margin=dict(l=10, r=10, t=30, b=10),
    )