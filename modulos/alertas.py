import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from utils.generador import LIMITES_IAEA

def mostrar(df_actual):

    st.markdown("## ⚠️ Sistema de Alertas — Normativa IAEA / OMS")
    st.markdown("Monitoreo automático contra límites internacionales de seguridad radiológica")
    st.divider()

    # Mapeo columnas → límites
    columnas_map = {
        "Cs137_Bq_m3":  "Cs-137 (Bq/m³)",
        "pH":           "pH",
        "Turbidez_NTU": "Turbidez (NTU)",
        "EDR_uSv_h":    "EDR (µSv/h)",
        "Sr90_Bq_L":    "Sr-90 (Bq/L)",
    }

    alertas_total = 0
    resumen = []

    for col, label in columnas_map.items():
        cfg = LIMITES_IAEA[col]
        violaciones = df_actual[df_actual[col] > cfg["limite"]]
        n_viol = len(violaciones)
        alertas_total += n_viol

        if n_viol > 0:
            with st.expander(f"🔴 {label} — {n_viol} nodo(s) fuera de norma | {cfg['norma']}", expanded=True):
                for _, r in violaciones.iterrows():
                    st.error(f"📍 **{r['nombre']}** ({r['zona']}): `{r[col]} {cfg['unidad']}` — Límite: `{cfg['limite']} {cfg['unidad']}`")
        else:
            st.success(f"✅ **{label}** — Todos los nodos dentro del límite ({cfg['limite']} {cfg['unidad']}) | {cfg['norma']}")

        resumen.append({"Parámetro": label, "Violaciones": n_viol,
                        "Límite": cfg["limite"], "Unidad": cfg["unidad"]})

    st.divider()

    c1, c2, c3 = st.columns(3)
    c1.metric("🚨 Total Alertas",    str(alertas_total), "revisar nodos")
    c2.metric("✅ Parámetros OK",    str(sum(1 for r in resumen if r["Violaciones"] == 0)), "de 5 monitoreados")
    c3.metric("📊 Nodos Evaluados",  "15", "todos los puntos")

    st.divider()

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("#### 📊 Violaciones por Parámetro")
        import pandas as pd
        df_res = pd.DataFrame(resumen)
        fig = px.bar(df_res, x="Parámetro", y="Violaciones",
                     color="Violaciones", color_continuous_scale="Reds",
                     height=300)
        fig.update_layout(**_layout())
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.markdown("#### 🏥 Distribución del Índice de Salud")
        fig2 = px.histogram(df_actual, x="Indice_Salud", nbins=12,
                            color_discrete_sequence=["#00d4ff"], height=300,
                            labels={"Indice_Salud":"Índice de Salud"})
        fig2.add_vline(x=40, line_dash="dash", line_color="#e74c3c", annotation_text="Crítico (<40)")
        fig2.add_vline(x=70, line_dash="dash", line_color="#f39c12", annotation_text="Precaución (<70)")
        fig2.update_layout(**_layout())
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()
    st.markdown("#### 📋 Tabla Completa de Cumplimiento Normativo")
    st.dataframe(
        df_actual[["nombre","zona","Cs137_Bq_m3","pH","Turbidez_NTU",
                   "EDR_uSv_h","Sr90_Bq_L","Indice_Salud","Estado"]].rename(columns={
            "nombre":"Punto","zona":"Zona","Cs137_Bq_m3":"Cs-137",
            "Turbidez_NTU":"Turbidez","EDR_uSv_h":"EDR","Sr90_Bq_L":"Sr-90","Indice_Salud":"Índice"
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