import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

def mostrar(df_actual):

    st.markdown("## 🔋 Estado de Sensores IoT — Energía y Batería")
    st.markdown("Monitoreo de potencia acumulada | Alertas automáticas de batería crítica")
    st.divider()

    # ── Alertas críticas primero ──────────────────────
    criticos  = df_actual[df_actual["Bateria_pct"] < 20]
    bajos     = df_actual[(df_actual["Bateria_pct"] >= 20) & (df_actual["Bateria_pct"] < 40)]

    if not criticos.empty:
        st.error(f"🚨 **{len(criticos)} sensor(es) con batería CRÍTICA (<20%) — requieren reemplazo inmediato**")
        for _, r in criticos.iterrows():
            st.markdown(f"&nbsp;&nbsp;&nbsp;→ **{r['nombre']}** ({r['zona']}): `{r['Bateria_pct']}%` | `{r['Voltaje_V']}V`")

    if not bajos.empty:
        st.warning(f"⚠️ **{len(bajos)} sensor(es) con batería BAJA (20-40%) — programar mantenimiento**")

    st.divider()

    # ── KPIs ──────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("🔋 Promedio Batería", f"{df_actual['Bateria_pct'].mean():.1f}%")
    c2.metric("⚡ Voltaje Promedio", f"{df_actual['Voltaje_V'].mean():.2f}V")
    c3.metric("🔴 Críticos (<20%)", str(len(criticos)),    "reemplazar ya")
    c4.metric("🟡 Bajos (20-40%)",  str(len(bajos)),       "programar mant.")
    c5.metric("🟢 OK (>40%)",       str(len(df_actual) - len(criticos) - len(bajos)))

    st.divider()

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("#### 🔋 Nivel de Batería por Sensor")
        df_sorted = df_actual.sort_values("Bateria_pct")
        colores   = ["#e74c3c" if v < 20 else ("#f39c12" if v < 40 else "#2ecc71")
                     for v in df_sorted["Bateria_pct"]]

        fig = go.Figure(go.Bar(
            x=df_sorted["Bateria_pct"],
            y=df_sorted["nombre"],
            orientation="h",
            marker_color=colores,
            hovertemplate="<b>%{y}</b><br>Batería: %{x}%<extra></extra>"
        ))
        fig.add_vline(x=20, line_dash="dash", line_color="#e74c3c",
                      annotation_text="Crítico 20%")
        fig.add_vline(x=40, line_dash="dash", line_color="#f39c12",
                      annotation_text="Bajo 40%")
        fig.update_layout(**_layout(), height=500, xaxis_range=[0, 105])
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.markdown("#### ⚡ Voltaje por Sensor (LiPo 3.3V-4.2V)")
        fig2 = go.Figure(go.Bar(
            x=df_actual.sort_values("Voltaje_V")["Voltaje_V"],
            y=df_actual.sort_values("Voltaje_V")["nombre"],
            orientation="h",
            marker_color="#00d4ff",
            hovertemplate="<b>%{y}</b><br>Voltaje: %{x}V<extra></extra>"
        ))
        fig2.add_vline(x=3.5, line_dash="dash", line_color="#ff4444",
                       annotation_text="Mínimo 3.5V")
        fig2.update_layout(**_layout(), height=500, xaxis_range=[3.0, 4.5])
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()

    # ── Gauge por zona ────────────────────────────────
    st.markdown("#### 🗺️ Batería Promedio por Zona")
    df_zona = df_actual.groupby("zona")["Bateria_pct"].mean().reset_index()

    cols_gauge = st.columns(len(df_zona))
    for i, (_, row) in enumerate(df_zona.iterrows()):
        with cols_gauge[i]:
            color = "#e74c3c" if row["Bateria_pct"] < 20 else (
                    "#f39c12" if row["Bateria_pct"] < 40 else "#2ecc71")
            fig_g = go.Figure(go.Indicator(
                mode="gauge+number",
                value=row["Bateria_pct"],
                title={"text": row["zona"], "font": {"color": "#e0e0e0", "size": 11}},
                number={"suffix": "%", "font": {"color": "#e0e0e0"}},
                gauge={
                    "axis": {"range": [0, 100], "tickcolor": "#e0e0e0"},
                    "bar":  {"color": color},
                    "bgcolor": "#0d2137",
                    "steps": [
                        {"range": [0,  20], "color": "#3d0000"},
                        {"range": [20, 40], "color": "#3d2000"},
                        {"range": [40, 100],"color": "#003d00"},
                    ],
                    "threshold": {"line": {"color": "white", "width": 2}, "value": 20}
                }
            ))
            fig_g.update_layout(**_layout(), height=220)
            st.plotly_chart(fig_g, use_container_width=True)

    st.divider()

    # ── Tabla completa ────────────────────────────────
    st.markdown("#### 📋 Estado Completo de Sensores")
    st.dataframe(
        df_actual[["nombre","zona","tipo","Bateria_pct","Voltaje_V","Estado_Bateria","Indice_Salud","Estado"]]
        .sort_values("Bateria_pct")
        .rename(columns={
            "nombre":"Sensor","zona":"Zona","tipo":"Tipo",
            "Bateria_pct":"Batería (%)","Voltaje_V":"Voltaje (V)",
            "Estado_Bateria":"Est. Batería","Indice_Salud":"Índice Salud"
        }),
        use_container_width=True, hide_index=True
    )

def _layout():
    return dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#e0e0e0",
        margin=dict(l=10, r=10, t=30, b=10),
    )