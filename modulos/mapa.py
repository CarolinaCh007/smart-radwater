import streamlit as st
import folium
from folium.plugins import HeatMap, MarkerCluster
from streamlit_folium import st_folium

def mostrar(df, df_actual):

    st.markdown("## 🗺️ Red de Monitoreo — Lago Titicaca")
    st.markdown("15 nodos IoT sumergibles | Sensores: pH · Conductividad · Turbidez · EDR gamma")
    st.divider()

    col_ctrl1, col_ctrl2 = st.columns(2)
    with col_ctrl1:
        capa = st.selectbox("🗂️ Capa de datos:", ["Heatmap Cs-137", "Heatmap Índice Salud", "Solo marcadores"])
    with col_ctrl2:
        zona_filtro = st.multiselect("📍 Filtrar por zona:", ["Norte", "Central", "Sur"],
                                     default=["Norte", "Central", "Sur"])

    df_filtrado = df_actual[df_actual["zona"].isin(zona_filtro)]

    mapa = folium.Map(
        location=[-15.9, -69.3], zoom_start=9,
        tiles="CartoDB dark_matter",
    )

    if capa == "Heatmap Cs-137":
        heat = [[r["lat"], r["lon"], r["Cs137_Bq_m3"]] for _, r in df_filtrado.iterrows()]
        HeatMap(heat, radius=45, blur=30,
                gradient={"0.2": "#0000ff", "0.5": "#ffff00", "1.0": "#ff0000"}).add_to(mapa)

    elif capa == "Heatmap Índice Salud":
        heat = [[r["lat"], r["lon"], r["Indice_Salud"] / 100] for _, r in df_filtrado.iterrows()]
        HeatMap(heat, radius=45, blur=30,
                gradient={"0.0": "#ff0000", "0.5": "#ffff00", "1.0": "#00ff00"}).add_to(mapa)

    for _, row in df_filtrado.iterrows():
        color = {"CRÍTICO": "red", "PRECAUCIÓN": "orange", "NORMAL": "green"}.get(row["Estado"], "blue")
        popup_html = f"""
        <div style='font-family:monospace;min-width:220px;background:#0d2137;
                    color:#e0e0e0;padding:10px;border-radius:8px'>
            <b style='color:#00d4ff'>📍 {row['nombre']}</b><br>
            <span style='color:#aaa'>ID: {row['id']} | Zona: {row['zona']}</span><hr style='border-color:#333'>
            ☢️ Cs-137: <b>{row['Cs137_Bq_m3']} Bq/m³</b><br>
            🔬 K-40:   <b>{row['K40_Bq_L']} Bq/L</b><br>
            ⚗️ Sr-90:  <b>{row['Sr90_Bq_L']} Bq/L</b><br>
            💧 pH:     <b>{row['pH']}</b><br>
            ⚡ Cond:   <b>{row['Conductividad_uS']} µS/cm</b><br>
            🌫️ Turb:  <b>{row['Turbidez_NTU']} NTU</b><br>
            🌡️ EDR:   <b>{row['EDR_uSv_h']} µSv/h</b><br><hr style='border-color:#333'>
            <b>Índice Salud: <span style='color:#00d4ff'>{row['Indice_Salud']}/100</span></b><br>
            Estado: <b>{row['Estado']}</b>
        </div>"""
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=14, color=color, fill=True, fill_opacity=0.85,
            popup=folium.Popup(popup_html, max_width=260),
            tooltip=f"📍 {row['nombre']} — {row['Estado']} | Salud: {row['Indice_Salud']}"
        ).add_to(mapa)

    st_folium(mapa, width=None, height=520, returned_objects=[])

    st.divider()
    st.markdown("#### 📊 Comparativa por Zona")
    import plotly.express as px
    fig = px.box(df_actual, x="zona", y="Indice_Salud",
                 color="zona", color_discrete_map={"Norte":"#00d4ff","Central":"#ffd700","Sur":"#ff6b6b"},
                 labels={"zona":"Zona","Indice_Salud":"Índice de Salud"},
                 height=300)
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font_color="#e0e0e0", showlegend=False)
    st.plotly_chart(fig, use_container_width=True)