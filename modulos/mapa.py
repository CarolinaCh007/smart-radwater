import streamlit as st
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import plotly.express as px

def mostrar(df, df_actual):

    st.markdown("## 🗺️ Red de Monitoreo — Río Katari & Bahía de Cohana")
    st.markdown("Cuenca crítica minera · El Alto · Viacha · Desembocadura en Bahía de Cohana")
    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        capa = st.selectbox("🗂️ Capa:", ["Heatmap Cs-137", "Heatmap Arsénico", "Heatmap Índice Salud", "Solo marcadores"])
    with col2:
        zona_filtro = st.multiselect("📍 Zonas:", ["Río Katari", "Bahía Cohana", "Zona Minera"],
                                     default=["Río Katari", "Bahía Cohana", "Zona Minera"])

    df_f = df_actual[df_actual["zona"].isin(zona_filtro)]

    mapa = folium.Map(location=[-16.52, -68.58], zoom_start=10,
                      tiles="CartoDB dark_matter")

    if capa == "Heatmap Cs-137":
        heat = [[r["lat"], r["lon"], r["Cs137_Bq_m3"]] for _, r in df_f.iterrows()]
        HeatMap(heat, radius=45, blur=30,
                gradient={"0.2": "#0000ff", "0.5": "#ffff00", "1.0": "#ff0000"}).add_to(mapa)
    elif capa == "Heatmap Arsénico":
        heat = [[r["lat"], r["lon"], r["As_mg_kg"] / 41.0] for _, r in df_f.iterrows()]
        HeatMap(heat, radius=45, blur=30,
                gradient={"0.2": "#00ff00", "0.6": "#ffaa00", "1.0": "#ff0000"}).add_to(mapa)
    elif capa == "Heatmap Índice Salud":
        heat = [[r["lat"], r["lon"], (100 - r["Indice_Salud"]) / 100] for _, r in df_f.iterrows()]
        HeatMap(heat, radius=45, blur=30,
                gradient={"0.0": "#00ff00", "0.5": "#ffff00", "1.0": "#ff0000"}).add_to(mapa)

    ICONOS = {
        "descarga":    ("red",    "exclamation-sign"),
        "mina":        ("darkred","warning-sign"),
        "riego":       ("green",  "tint"),
        "bahia":       ("orange", "eye-open"),
        "confluencia": ("blue",   "transfer"),
        "origen":      ("cadetblue","home"),
        "monitoreo":   ("blue",   "stats"),
    }

    for _, row in df_f.iterrows():
        color_circulo = "red" if row["Indice_Salud"] < 40 else (
                        "orange" if row["Indice_Salud"] < 70 else "blue")
        ico_color, ico_icon = ICONOS.get(row["tipo"], ("blue", "info-sign"))

        popup_html = f"""
        <div style='font-family:monospace;min-width:230px;
                    background:#0d2137;color:#e0e0e0;
                    padding:12px;border-radius:8px'>
            <b style='color:#00d4ff'>📍 {row['nombre']}</b><br>
            <span style='color:#aaa'>{row['id']} | {row['zona']} | {row['tipo']}</span>
            <hr style='border-color:#1a3a5c'>
            🪨 As: <b>{row['As_mg_kg']} mg/kg</b>
            {'🔴' if row['As_mg_kg'] > 41 else '✅'}<br>
            ⚫ Hg: <b>{row['Hg_mg_kg']} mg/kg</b>
            {'🔴' if row['Hg_mg_kg'] > 5  else '✅'}<br>
            🔩 Pb: <b>{row['Pb_mg_kg']} mg/kg</b>
            {'🔴' if row['Pb_mg_kg'] > 50 else '✅'}<br>
            ☢️ Cs-137: <b>{row['Cs137_Bq_m3']} Bq/m³</b><br>
            💧 pH: <b>{row['pH']}</b><br>
            🌫️ Turb: <b>{row['Turbidez_NTU']} NTU</b><br>
            🔋 Batería: <b>{row['Bateria_pct']}%</b> {row['Estado_Bateria']}
            <hr style='border-color:#1a3a5c'>
            <b>Índice Salud: <span style='color:#00d4ff'>{row['Indice_Salud']}/100</span></b><br>
            Estado: <b>{row['Estado']}</b>
        </div>"""

        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=12, color=color_circulo, fill=True, fill_opacity=0.85,
            popup=folium.Popup(popup_html, max_width=260),
            tooltip=f"📍 {row['nombre']} | {row['Estado']} | Salud: {row['Indice_Salud']}"
        ).add_to(mapa)

        folium.Marker(
            location=[row["lat"], row["lon"]],
            icon=folium.Icon(color=ico_color, icon=ico_icon, prefix="glyphicon"),
            tooltip=row["nombre"]
        ).add_to(mapa)

    st_folium(mapa, width=None, height=520, returned_objects=[])

    st.divider()
    st.markdown("#### 📊 Comparativa por Zona — Índice de Salud")
    fig = px.box(df_f, x="zona", y="Indice_Salud", color="zona",
                 color_discrete_map={
                     "Río Katari":  "#00d4ff",
                     "Bahía Cohana":"#ff6b6b",
                     "Zona Minera": "#888888"
                 },
                 labels={"zona": "Zona", "Indice_Salud": "Índice de Salud"},
                 height=300)
    fig.add_hline(y=40, line_dash="dash", line_color="#e74c3c", annotation_text="Crítico")
    fig.add_hline(y=70, line_dash="dash", line_color="#f39c12", annotation_text="Precaución")
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font_color="#e0e0e0", showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.markdown("#### 📋 Tabla de Nodos")
    st.dataframe(
        df_f[["id","nombre","zona","tipo","As_mg_kg","Hg_mg_kg","Cs137_Bq_m3",
              "pH","Turbidez_NTU","Bateria_pct","Indice_Salud","Estado"]]
        .rename(columns={
            "nombre":"Punto","zona":"Zona","tipo":"Tipo",
            "As_mg_kg":"As (mg/kg)","Hg_mg_kg":"Hg (mg/kg)",
            "Cs137_Bq_m3":"Cs-137","Turbidez_NTU":"Turbidez",
            "Bateria_pct":"Batería (%)","Indice_Salud":"Índice"
        }),
        use_container_width=True, hide_index=True
    )