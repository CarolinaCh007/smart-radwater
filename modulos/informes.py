import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from utils.generador import LIMITES_IAEA
import io

def mostrar(df, df_actual):

    st.markdown("## 📄 Informes — Análisis por Localidad")
    st.markdown("Generación de informes diarios descargables | Por zona y variable")
    st.divider()

    col1, col2, col3 = st.columns(3)
    with col1:
        zona_inf = st.selectbox("📍 Zona:", ["Todas"] + list(df["zona"].unique()))
    with col2:
        tipo_inf = st.selectbox("📋 Tipo de informe:", [
            "Resumen General",
            "Metales Pesados",
            "Variables Radiológicas",
            "Estado de Sensores",
        ])
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        generar = st.button("📊 Generar Informe", use_container_width=True)

    st.divider()

    # Filtrar datos
    df_inf = df_actual if zona_inf == "Todas" else df_actual[df_actual["zona"] == zona_inf]

    # ── Resumen siempre visible ───────────────────────
    st.markdown(f"### 📊 {tipo_inf} — {zona_inf}")
    st.markdown(f"*Generado: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Nodos analizados: {len(df_inf)}*")

    if tipo_inf == "Resumen General":
        _informe_general(df_inf, df)

    elif tipo_inf == "Metales Pesados":
        _informe_metales(df_inf)

    elif tipo_inf == "Variables Radiológicas":
        _informe_radiologico(df_inf)

    elif tipo_inf == "Estado de Sensores":
        _informe_sensores(df_inf)

    st.divider()

    # ── Descarga CSV ──────────────────────────────────
    st.markdown("#### 💾 Descargar Datos")
    col_d1, col_d2 = st.columns(2)

    with col_d1:
        csv_data = df_inf.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Descargar CSV completo",
            data=csv_data,
            file_name=f"SMART_RADWATER_{zona_inf}_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )

    with col_d2:
        # Resumen ejecutivo en texto
        resumen_txt = _generar_resumen_texto(df_inf, zona_inf, tipo_inf)
        st.download_button(
            label="📄 Descargar Resumen Ejecutivo (.txt)",
            data=resumen_txt.encode("utf-8"),
            file_name=f"Informe_{zona_inf}_{datetime.now().strftime('%Y%m%d')}.txt",
            mime="text/plain",
            use_container_width=True
        )


def _informe_general(df_inf, df):
    c1, c2, c3, c4 = st.columns(4)
    criticos   = len(df_inf[df_inf["Estado"] == "CRÍTICO"])
    precaucion = len(df_inf[df_inf["Estado"] == "PRECAUCIÓN"])
    c1.metric("🟢 Normales",   str(len(df_inf[df_inf["Estado"] == "NORMAL"])))
    c2.metric("🟡 Precaución", str(precaucion))
    c3.metric("🔴 Críticos",   str(criticos))
    c4.metric("💚 Salud Prom.", f"{df_inf['Indice_Salud'].mean():.1f}/100")

    col_a, col_b = st.columns(2)
    with col_a:
        fig = px.bar(df_inf.sort_values("Indice_Salud"),
                     x="nombre", y="Indice_Salud",
                     color="Indice_Salud", color_continuous_scale="RdYlGn",
                     labels={"nombre": "", "Indice_Salud": "Índice Salud"},
                     height=300)
        fig.add_hline(y=40, line_dash="dash", line_color="#e74c3c")
        fig.add_hline(y=70, line_dash="dash", line_color="#f39c12")
        fig.update_layout(**_layout(), xaxis_tickangle=-40)
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        fig2 = px.pie(
            values=[len(df_inf[df_inf["Estado"]=="NORMAL"]),
                    len(df_inf[df_inf["Estado"]=="PRECAUCIÓN"]),
                    len(df_inf[df_inf["Estado"]=="CRÍTICO"])],
            names=["Normal","Precaución","Crítico"],
            color_discrete_sequence=["#2ecc71","#f39c12","#e74c3c"],
            height=300, hole=0.5
        )
        fig2.update_layout(**_layout())
        st.plotly_chart(fig2, use_container_width=True)


def _informe_metales(df_inf):
    metales = {
        "As_mg_kg": ("Arsénico", 41.0,  "🪨"),
        "Hg_mg_kg": ("Mercurio",  5.0,  "⚫"),
        "Pb_mg_kg": ("Plomo",    50.0,  "🔩"),
        "Cd_mg_kg": ("Cadmio",   10.0,  "🔋"),
        "Zn_mg_kg": ("Zinc",    100.0,  "🔧"),
        "Cu_mg_kg": ("Cobre",    50.0,  "🟤"),
    }
    cols = st.columns(3)
    for i, (col, (nombre, limite, emoji)) in enumerate(metales.items()):
        with cols[i % 3]:
            sobre = len(df_inf[df_inf[col] > limite])
            color = "🔴" if sobre > 0 else "🟢"
            st.metric(f"{emoji} {nombre}",
                      f"{df_inf[col].mean():.2f} mg/kg",
                      f"{color} {sobre} sobre límite ({limite})")

    st.divider()
    df_melt = df_inf[["nombre"] + list(metales.keys())].melt(
        id_vars="nombre", var_name="Metal", value_name="Concentración"
    )
    df_melt["Metal"] = df_melt["Metal"].map({k: v[0] for k, v in metales.items()})

    fig = px.bar(df_melt, x="nombre", y="Concentración", color="Metal",
                 barmode="group",
                 color_discrete_sequence=px.colors.qualitative.Set2,
                 labels={"nombre": "", "Concentración": "mg/kg"},
                 height=380)
    fig.update_layout(**_layout(), xaxis_tickangle=-40)
    st.plotly_chart(fig, use_container_width=True)


def _informe_radiologico(df_inf):
    rad_vars = {
        "Cs137_Bq_m3": ("Cs-137", 10.0,  "Bq/m³", "☢️"),
        "Sr90_Bq_L":   ("Sr-90",   0.10, "Bq/L",  "⚗️"),
        "K40_Bq_L":    ("K-40",  125.0,  "Bq/L",  "🔬"),
        "EDR_uSv_h":   ("EDR",    0.30,  "µSv/h", "🌡️"),
    }
    cols = st.columns(4)
    for i, (col, (nombre, limite, unidad, emoji)) in enumerate(rad_vars.items()):
        sobre = len(df_inf[df_inf[col] > limite])
        color = "🔴" if sobre > 0 else "🟢"
        cols[i].metric(f"{emoji} {nombre}",
                       f"{df_inf[col].mean():.3f} {unidad}",
                       f"{color} {sobre} sobre límite")

    st.divider()
    col_a, col_b = st.columns(2)
    with col_a:
        fig = px.bar(df_inf.sort_values("Cs137_Bq_m3", ascending=False),
                     x="nombre", y="Cs137_Bq_m3",
                     color="zona", labels={"nombre":"","Cs137_Bq_m3":"Cs-137 (Bq/m³)"},
                     height=300)
        fig.add_hline(y=10, line_dash="dash", line_color="#ff4444",
                      annotation_text="Límite IAEA")
        fig.update_layout(**_layout(), xaxis_tickangle=-40)
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        fig2 = px.bar(df_inf.sort_values("Sr90_Bq_L", ascending=False),
                      x="nombre", y="Sr90_Bq_L",
                      color="zona", labels={"nombre":"","Sr90_Bq_L":"Sr-90 (Bq/L)"},
                      height=300)
        fig2.add_hline(y=0.10, line_dash="dash", line_color="#ff4444",
                       annotation_text="Límite OMS")
        fig2.update_layout(**_layout(), xaxis_tickangle=-40)
        st.plotly_chart(fig2, use_container_width=True)


def _informe_sensores(df_inf):
    c1, c2, c3 = st.columns(3)
    c1.metric("🔋 Batería Prom.", f"{df_inf['Bateria_pct'].mean():.1f}%")
    c2.metric("🔴 Críticos",     str(len(df_inf[df_inf["Bateria_pct"] < 20])))
    c3.metric("🟡 Bajos",        str(len(df_inf[(df_inf["Bateria_pct"]>=20)&(df_inf["Bateria_pct"]<40)])))

    fig = px.bar(df_inf.sort_values("Bateria_pct"),
                 x="nombre", y="Bateria_pct",
                 color="Estado_Bateria",
                 color_discrete_map={"🟢 OK":"#2ecc71","🟡 BAJO":"#f39c12","🔴 CRÍTICO":"#e74c3c"},
                 labels={"nombre":"","Bateria_pct":"Batería (%)"},
                 height=320)
    fig.add_hline(y=20, line_dash="dash", line_color="#e74c3c")
    fig.add_hline(y=40, line_dash="dash", line_color="#f39c12")
    fig.update_layout(**_layout(), xaxis_tickangle=-40)
    st.plotly_chart(fig, use_container_width=True)


def _generar_resumen_texto(df_inf, zona, tipo):
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M")
    criticos = df_inf[df_inf["Estado"]=="CRÍTICO"]["nombre"].tolist()
    txt = f"""
=====================================================================
INFORME SMART-RADWATER — {tipo.upper()}
Zona: {zona} | Generado: {ahora}
Proyecto: Sistema de Tratamiento Radiolítico Molecular Avanzado
UMSA Bolivia — HackAtom 2026
=====================================================================

RESUMEN EJECUTIVO
-----------------
Nodos analizados    : {len(df_inf)}
Índice salud prom.  : {df_inf['Indice_Salud'].mean():.1f}/100
Nodos NORMALES      : {len(df_inf[df_inf['Estado']=='NORMAL'])}
Nodos PRECAUCIÓN    : {len(df_inf[df_inf['Estado']=='PRECAUCIÓN'])}
Nodos CRÍTICOS      : {len(df_inf[df_inf['Estado']=='CRÍTICO'])}

VARIABLES RADIOLÓGICAS
----------------------
Cs-137 promedio     : {df_inf['Cs137_Bq_m3'].mean():.3f} Bq/m³  (Límite IAEA: 10.0)
Sr-90 promedio      : {df_inf['Sr90_Bq_L'].mean():.4f} Bq/L    (Límite OMS: 0.10)
EDR promedio        : {df_inf['EDR_uSv_h'].mean():.3f} µSv/h   (Límite: 0.30)

METALES PESADOS
---------------
Arsénico (As)       : {df_inf['As_mg_kg'].mean():.2f} mg/kg (Límite: 41.0)
Mercurio (Hg)       : {df_inf['Hg_mg_kg'].mean():.2f} mg/kg (Límite: 5.0)
Plomo (Pb)          : {df_inf['Pb_mg_kg'].mean():.2f} mg/kg (Límite: 50.0)
Cadmio (Cd)         : {df_inf['Cd_mg_kg'].mean():.2f} mg/kg (Límite: 10.0)

ESTADO DE SENSORES
------------------
Batería promedio    : {df_inf['Bateria_pct'].mean():.1f}%
Sensores críticos   : {len(df_inf[df_inf['Bateria_pct']<20])}

NODOS EN ESTADO CRÍTICO
------------------------
{chr(10).join(f'  - {n}' for n in criticos) if criticos else '  Ninguno'}

REFERENCIAS NORMATIVAS
----------------------
- IAEA-TECDOC-1250 (Cs-137, EDR)
- OMS Guías Calidad Agua 2017 (Sr-90, pH, Turbidez)
- DS 24176 Bolivia (Metales pesados)
- SERGEOTECMIN Bolivia (Metales en cuencas mineras)

=====================================================================
Fin del informe
=====================================================================
"""
    return txt


def _layout():
    return dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#e0e0e0",
        margin=dict(l=10, r=10, t=30, b=10),
    )