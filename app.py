import streamlit as st
import pandas as pd
from utils.generador import generar_dataset_completo, get_datos_actuales
from modulos import inicio, mapa, espectros, prediccion, alertas, variables, baterias, informes

st.set_page_config(
    page_title="SMART-RADWATER",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ══════════════════════════════════════════════════════
# ESTILOS
# ══════════════════════════════════════════════════════
st.markdown("""
<style>
    .stApp { background-color: #0a1628; }
    [data-testid="stSidebar"] {
        background-color: #0d1f35;
        border-right: 1px solid #1a3a5c;
    }
    [data-testid="stMetric"] {
        background-color: #0d2137;
        border: 1px solid #1a3a5c;
        border-radius: 10px;
        padding: 12px 16px;
    }
    [data-testid="stExpander"] {
        background-color: #0d2137;
        border: 1px solid #1a3a5c;
        border-radius: 8px;
    }
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: #0a1628; }
    ::-webkit-scrollbar-thumb { background: #1a3a5c; border-radius: 3px; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
# DATOS
# ══════════════════════════════════════════════════════
@st.cache_data
def cargar_datos():
    try:
        df = pd.read_csv("data/datos_titicaca.csv")
    except FileNotFoundError:
        df = generar_dataset_completo(400)
        df.to_csv("data/datos_titicaca.csv", index=False)
    return df

df        = cargar_datos()
df_actual = get_datos_actuales(df)

# ══════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════
with st.sidebar:
    st.image(
        "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6a/Flag_of_Bolivia.svg/320px-Flag_of_Bolivia.svg.png",
        width=100
    )
    st.markdown("## 🌊 SMART-RADWATER")
    st.markdown("**Monitoreo Nuclear Hídrico**")
    st.markdown("*Titicaca · Katari · Cohana*")
    st.divider()

    seccion = st.radio("📌 Módulos", [
        "🏠 Centro de Control",
        "🗺️ Mapa de Muestreo",
        "📊 Dashboard por Variable",
        "📡 Espectros Gamma",
        "🤖 Predicción IA",
        "🔋 Estado de Sensores",
        "⚠️ Alertas IAEA",
        "📄 Informes y Descarga",
    ])

    st.divider()
    from datetime import datetime
    st.caption(f"🕐 `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`")
    st.caption(f"📡 Nodos: **{len(df_actual)}/{len(df_actual)}** activos")

    # Alertas de batería en sidebar
    criticos_bat = df_actual[df_actual["Bateria_pct"] < 20]
    if not criticos_bat.empty:
        st.divider()
        st.error(f"🔴 {len(criticos_bat)} sensor(es) batería crítica")

    st.divider()
    st.caption("HackAtom 2026 | UMSA Bolivia")

# ══════════════════════════════════════════════════════
# NAVEGACIÓN
# ══════════════════════════════════════════════════════
if   seccion == "🏠 Centro de Control":     inicio.mostrar(df, df_actual)
elif seccion == "🗺️ Mapa de Muestreo":      mapa.mostrar(df, df_actual)
elif seccion == "📊 Dashboard por Variable": variables.mostrar(df, df_actual)
elif seccion == "📡 Espectros Gamma":        espectros.mostrar(df_actual)
elif seccion == "🤖 Predicción IA":          prediccion.mostrar(df, df_actual)
elif seccion == "🔋 Estado de Sensores":     baterias.mostrar(df_actual)
elif seccion == "⚠️ Alertas IAEA":           alertas.mostrar(df_actual)
elif seccion == "📄 Informes y Descarga":    informes.mostrar(df, df_actual)