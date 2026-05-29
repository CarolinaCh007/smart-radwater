import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error

def mostrar(df, df_actual):

    st.markdown("## 🤖 Motor de Predicción IA — Random Forest")
    st.markdown("Modelo entrenado con 300 registros históricos | Predice el Índice de Salud Hídrica")
    st.divider()

    # ── Entrenamiento ─────────────────────────────────
    features = ["Cs137_Bq_m3","K40_Bq_L","Sr90_Bq_L","pH","Conductividad_uS","Turbidez_NTU","EDR_uSv_h"]
    X = df[features]
    y = df["Indice_Salud"]

    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42)
    modelo = RandomForestRegressor(n_estimators=150, max_depth=10, random_state=42)
    modelo.fit(X_tr, y_tr)
    y_pred = modelo.predict(X_te)

    r2  = r2_score(y_te, y_pred)
    mae = mean_absolute_error(y_te, y_pred)

    # ── Métricas del modelo ───────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🎯 R² Score",      f"{r2:.4f}",    "Precisión del modelo")
    c2.metric("📉 MAE",           f"{mae:.3f}",   "Error medio absoluto")
    c3.metric("🌳 Estimadores",   "150 árboles",  "Random Forest")
    c4.metric("📊 Datos entreno", f"{len(X_tr)}",  "registros históricos")

    st.divider()

    col_a, col_b = st.columns(2)

    with col_a:
        # Real vs predicho
        st.markdown("#### 📈 Real vs Predicción — Conjunto de Prueba")
        df_pred = pd.DataFrame({"Real": y_te.values, "Predicho": y_pred})
        fig = px.scatter(df_pred, x="Real", y="Predicho",
                         opacity=0.7, color_discrete_sequence=["#00d4ff"],
                         height=320,
                         labels={"Real":"Valor Real","Predicho":"Predicción IA"})
        fig.add_shape(type="line", x0=0, y0=0, x1=100, y1=100,
                      line=dict(dash="dash", color="#ffd700", width=1.5))
        fig.update_layout(**_layout())
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        # Importancia de variables
        st.markdown("#### 🔍 Importancia de Variables")
        imp = pd.DataFrame({
            "Variable":    ["Cs-137","K-40","Sr-90","pH","Conductividad","Turbidez","EDR"],
            "Importancia": modelo.feature_importances_
        }).sort_values("Importancia")
        fig2 = px.bar(imp, x="Importancia", y="Variable", orientation="h",
                      color="Importancia", color_continuous_scale="Blues",
                      height=320)
        fig2.update_layout(**_layout(), coloraxis_showscale=False)
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()

    # ── Predicción en nodos actuales ──────────────────
    st.markdown("#### 🌊 Predicción en Tiempo Real — 15 Nodos")
    df_actual = df_actual.copy()
    df_actual["Salud_Predicha"] = modelo.predict(df_actual[features]).round(1)
    df_actual["Diferencia"]     = (df_actual["Salud_Predicha"] - df_actual["Indice_Salud"]).round(2)

    fig3 = go.Figure()
    fig3.add_trace(go.Bar(name="Índice Real", x=df_actual["nombre"],
                          y=df_actual["Indice_Salud"], marker_color="#ffd700"))
    fig3.add_trace(go.Bar(name="Predicción IA", x=df_actual["nombre"],
                          y=df_actual["Salud_Predicha"], marker_color="#00d4ff", opacity=0.8))
    fig3.update_layout(**_layout(), barmode="group", height=350,
                       xaxis_tickangle=-40,
                       legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig3, use_container_width=True)

    # ── Simulador interactivo ─────────────────────────
    st.divider()
    st.markdown("#### 🧪 Simulador — ¿Qué pasaría si...?")
    st.markdown("Ajusta los parámetros y el modelo predice el índice de salud en tiempo real")

    s1, s2, s3 = st.columns(3)
    s4, s5, s6, s7 = st.columns(4)

    cs_sim   = s1.slider("☢️ Cs-137 (Bq/m³)", 0.0, 5.0, 1.0, 0.01)
    ph_sim   = s2.slider("💧 pH",              5.0, 10.0, 7.5, 0.1)
    turb_sim = s3.slider("🌫️ Turbidez (NTU)", 0.0, 50.0, 15.0, 0.5)
    k40_sim  = s4.slider("🔬 K-40 (Bq/L)",   60.0, 140.0, 100.0, 1.0)
    sr90_sim = s5.slider("⚗️ Sr-90 (Bq/L)",  0.0, 0.2, 0.05, 0.001)
    cond_sim = s6.slider("⚡ Cond (µS/cm)",  800.0, 2000.0, 1200.0, 10.0)
    edr_sim  = s7.slider("🌡️ EDR (µSv/h)",  0.0, 0.5, 0.15, 0.01)

    entrada = np.array([[cs_sim, k40_sim, sr90_sim, ph_sim, cond_sim, turb_sim, edr_sim]])
    pred_val = modelo.predict(entrada)[0]
    estado_pred = "🔴 CRÍTICO" if pred_val < 40 else ("🟡 PRECAUCIÓN" if pred_val < 70 else "🟢 NORMAL")

    st.markdown(f"### Índice de Salud Predicho: `{pred_val:.1f} / 100` — {estado_pred}")

def _layout():
    return dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#e0e0e0",
        margin=dict(l=10, r=10, t=30, b=10),
    )