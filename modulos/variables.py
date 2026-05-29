import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from utils.generador import LIMITES_IAEA

def mostrar(df, df_actual):

    st.markdown("## 📊 Dashboard por Variable")
    st.markdown("Análisis completo por variable | Zonas: Río Katari · Bahía Cohana · Zona Minera")
    st.divider()

    # ── Selector de variable ──────────────────────────
    VARIABLES = {
        "☢️ Cs-137 (Bq/m³)":    ("Cs137_Bq_m3",  10.0,  "Bq/m³",  "reds"),
        "⚗️ Sr-90 (Bq/L)":      ("Sr90_Bq_L",    0.10,  "Bq/L",   "purples"),
        "🔬 K-40 (Bq/L)":       ("K40_Bq_L",     125.0, "Bq/L",   "blues"),
        "🌡️ EDR (µSv/h)":       ("EDR_uSv_h",    0.30,  "µSv/h",  "oranges"),
        "💧 pH":                 ("pH",            8.5,   "",       "teal"),
        "⚡ Conductividad":      ("Conductividad_uS", 1800, "µS/cm","blues"),
        "🌫️ Turbidez (NTU)":   ("Turbidez_NTU", 25.0,  "NTU",    "earth"),
        "🪨 Arsénico As":        ("As_mg_kg",     41.0,  "mg/kg",  "reds"),
        "⚫ Mercurio Hg":        ("Hg_mg_kg",      5.0,  "mg/kg",  "greys"),
        "🔩 Plomo Pb":           ("Pb_mg_kg",     50.0,  "mg/kg",  "reds"),
        "🔋 Cadmio Cd":          ("Cd_mg_kg",     10.0,  "mg/kg",  "purples"),
        "🔧 Zinc Zn":            ("Zn_mg_kg",    100.0,  "mg/kg",  "greens"),
        "🟤 Cobre Cu":           ("Cu_mg_kg",     50.0,  "mg/kg",  "oranges"),
    }

    col_sel1, col_sel2 = st.columns(2)
    with col_sel1:
        var_label = st.selectbox("📌 Variable a analizar:", list(VARIABLES.keys()))
    with col_sel2:
        zona_filtro = st.multiselect(
            "🗺️ Zonas:",
            [ "Río Katari", "Bahía Cohana", "Zona Minera"],
            default=[ "Río Katari", "Bahía Cohana"]
        )

    col, limite, unidad, escala = VARIABLES[var_label]
    df_f = df_actual[df_actual["zona"].isin(zona_filtro)].copy()

    if df_f.empty:
        st.warning("No hay datos para las zonas seleccionadas.")
        return

    st.divider()

    # ── Fila 1: KPIs de la variable ───────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    val_max  = df_f[col].max()
    val_min  = df_f[col].min()
    val_mean = df_f[col].mean()
    n_sobre  = len(df_f[df_f[col] > limite])
    pct_ok   = round((1 - n_sobre / len(df_f)) * 100, 1)

    c1.metric("📈 Máximo",      f"{val_max:.3f} {unidad}")
    c2.metric("📉 Mínimo",      f"{val_min:.3f} {unidad}")
    c3.metric("📊 Promedio",    f"{val_mean:.3f} {unidad}")
    c4.metric("🚨 Sobre límite",f"{n_sobre} nodos",   f"Límite: {limite} {unidad}")
    c5.metric("✅ En norma",    f"{pct_ok}%",          "de nodos")

    st.divider()

    # ── Fila 2: Barras por nodo + Pie por zona ────────
    col_a, col_b = st.columns([3, 2])

    with col_a:
        st.markdown(f"#### 📊 {var_label} por Nodo — Click para ver detalle")

        df_sorted = df_f.sort_values(col, ascending=False)

        # Colores según supera límite
        colores = ["#e74c3c" if v > limite else "#00d4ff" for v in df_sorted[col]]

        fig = go.Figure(go.Bar(
            x=df_sorted["nombre"],
            y=df_sorted[col],
            marker_color=colores,
            customdata=df_sorted[["zona","tipo","Indice_Salud","Estado","Bateria_pct"]].values,
            hovertemplate=(
                "<b>%{x}</b><br>"
                f"{var_label}: <b>%{{y:.3f}} {unidad}</b><br>"
                "Zona: %{customdata[0]}<br>"
                "Tipo: %{customdata[1]}<br>"
                "Índice Salud: %{customdata[2]}<br>"
                "Estado: %{customdata[3]}<br>"
                "Batería: %{customdata[4]}%<br>"
                "<extra></extra>"
            ),
        ))
        fig.add_hline(y=limite, line_dash="dash", line_color="#ff4444",
                      annotation_text=f"Límite {limite} {unidad}")
        fig.update_layout(**_layout(), height=350, xaxis_tickangle=-40)
        
        evento = st.plotly_chart(fig, use_container_width=True, on_select="rerun", key=f"bar_{col}")

        # Mostrar info del nodo clickeado
        if evento and evento.get("selection") and evento["selection"].get("points"):
            punto_click = evento["selection"]["points"][0]
            nombre_click = df_sorted.iloc[punto_click["point_index"]]["nombre"]
            _mostrar_ficha_nodo(df_actual, df, nombre_click, col, unidad, limite)

    with col_b:
        st.markdown("#### 🥧 Promedio por Zona")
        df_zona = df_f.groupby("zona")[col].mean().reset_index()
        colores_zona = {
    
            "Río Katari":    "#ff6b6b",
            "Bahía Cohana":  "#ff4444",
            "Zona Minera":   "#888888"
        }
        fig2 = go.Figure(go.Pie(
            labels=df_zona["zona"],
            values=df_zona[col].round(3),
            hole=0.5,
            marker_colors=[colores_zona.get(z, "#aaaaaa") for z in df_zona["zona"]],
            hovertemplate="<b>%{label}</b><br>Promedio: %{value:.3f} " + unidad + "<extra></extra>"
        ))
        fig2.update_layout(**_layout(), height=350)
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()

    # ── Fila 3: Histórico + Boxplot ───────────────────
    col_c, col_d = st.columns(2)

    with col_c:
        st.markdown(f"#### 📈 Histórico — {var_label}")
        zona_hist = st.selectbox("Zona para histórico:", zona_filtro, key=f"hist_{col}")
        df_hist = df[df["zona"] == zona_hist].groupby("timestamp")[col].mean().reset_index().tail(48)
        
        fig3 = px.line(df_hist, x="timestamp", y=col,
                       color_discrete_sequence=["#00d4ff"],
                       labels={"timestamp": "Tiempo", col: f"{var_label}"},
                       height=280)
        fig3.add_hline(y=limite, line_dash="dash", line_color="#ff4444",
                       annotation_text=f"Límite {limite}")
        fig3.update_layout(**_layout())
        st.plotly_chart(fig3, use_container_width=True)

    with col_d:
        st.markdown("#### 📦 Distribución por Zona")
        fig4 = px.box(df_f, x="zona", y=col, color="zona",
                      color_discrete_map=colores_zona,
                      labels={"zona": "", col: f"{var_label}"},
                      height=280)
        fig4.add_hline(y=limite, line_dash="dash", line_color="#ff4444")
        fig4.update_layout(**_layout(), showlegend=False)
        st.plotly_chart(fig4, use_container_width=True)

    st.divider()

    # ── Tabla completa ────────────────────────────────
    st.markdown("#### 📋 Tabla Completa")
    cols_show = ["nombre", "zona", "tipo", col, "Indice_Salud", "Estado", "Bateria_pct", "Estado_Bateria"]
    df_tabla = df_f[cols_show].copy()
    df_tabla[col] = df_tabla[col].apply(
        lambda v: f"🔴 {v}" if v > limite else f"✅ {v}"
    )
    st.dataframe(df_tabla.rename(columns={
        "nombre": "Punto", "zona": "Zona", "tipo": "Tipo",
        col: f"{var_label}", "Indice_Salud": "Índice",
        "Bateria_pct": "Batería (%)", "Estado_Bateria": "Est. Batería"
    }), use_container_width=True, hide_index=True)


def _mostrar_ficha_nodo(df_actual, df, nombre, col, unidad, limite):
    """Ficha completa del nodo cuando se hace click"""
    fila = df_actual[df_actual["nombre"] == nombre]
    if fila.empty:
        return
    fila = fila.iloc[0]

    st.divider()
    st.markdown(f"### 📍 Ficha Detallada — {nombre}")

    color_estado = {"NORMAL": "🟢", "PRECAUCIÓN": "🟡", "CRÍTICO": "🔴"}.get(fila["Estado"], "⚪")
    st.markdown(f"**Zona:** {fila['zona']} | **Tipo:** {fila['tipo']} | **Estado:** {color_estado} {fila['Estado']}")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("☢️ Cs-137",    f"{fila['Cs137_Bq_m3']} Bq/m³")
    c2.metric("⚗️ Sr-90",     f"{fila['Sr90_Bq_L']} Bq/L")
    c3.metric("🪨 Arsénico",  f"{fila['As_mg_kg']} mg/kg")
    c4.metric("⚫ Mercurio",  f"{fila['Hg_mg_kg']} mg/kg")

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("🔩 Plomo",     f"{fila['Pb_mg_kg']} mg/kg")
    c6.metric("💧 pH",        f"{fila['pH']}")
    c7.metric("🌫️ Turbidez", f"{fila['Turbidez_NTU']} NTU")
    c8.metric("🔋 Batería",   f"{fila['Bateria_pct']}%", fila["Estado_Bateria"])

    # Histórico del nodo
    df_nodo = df[df["nombre"] == nombre].sort_values("timestamp").tail(20)
    if not df_nodo.empty:
        fig = px.line(df_nodo, x="timestamp", y=col,
                      color_discrete_sequence=["#ffd700"],
                      title=f"Histórico {nombre} — últimas 24h",
                      height=220)
        fig.add_hline(y=limite, line_dash="dash", line_color="#ff4444")
        fig.update_layout(**_layout())
        st.plotly_chart(fig, use_container_width=True)


def _layout():
    return dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#e0e0e0",
        margin=dict(l=10, r=10, t=30, b=10),
    )