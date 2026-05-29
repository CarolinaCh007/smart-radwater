import streamlit as st
import numpy as np
import plotly.graph_objects as go
from scipy.spatial import distance_matrix

# ── Zonas reales del Río Katari ────────────────────────────────────────
ZONAS_KATARI = [
    {"nombre": "Nacimiento Katari",   "km": 0,  "lat": -16.65, "lon": -68.45, "tipo": "origen",   "descripcion": "Inicio cuenca, zona alta"},
    {"nombre": "El Alto — Zona Ind.", "km": 10, "lat": -16.58, "lon": -68.38, "tipo": "descarga",  "descripcion": "Descargas industriales El Alto"},
    {"nombre": "Viacha — Minería",    "km": 20, "lat": -16.65, "lon": -68.30, "tipo": "descarga",  "descripcion": "Efluentes mineros Viacha"},
    {"nombre": "Toma Riego Norte",    "km": 20, "lat": -16.52, "lon": -68.38, "tipo": "riego",     "descripcion": "Irrigación agrícola norte"},
    {"nombre": "Confluencia Pallina", "km": 28, "lat": -16.54, "lon": -68.52, "tipo": "confluencia","descripcion": "Unión Río Pallina"},
    {"nombre": "Toma Riego Central",  "km": 35, "lat": -16.51, "lon": -68.55, "tipo": "riego",     "descripcion": "Irrigación zona central"},
    {"nombre": "Descarga Media",      "km": 45, "lat": -16.50, "lon": -68.62, "tipo": "descarga",  "descripcion": "Vertidos agroindustriales"},
    {"nombre": "Toma Riego Sur",      "km": 50, "lat": -16.49, "lon": -68.65, "tipo": "riego",     "descripcion": "Irrigación zona sur"},
    {"nombre": "Toma Riego Final",    "km": 65, "lat": -16.47, "lon": -68.72, "tipo": "riego",     "descripcion": "Última toma antes del lago"},
    {"nombre": "Descarga Final",      "km": 70, "lat": -16.46, "lon": -68.75, "tipo": "descarga",  "descripcion": "Descarga pre-Cohana"},
    {"nombre": "Bahía de Cohana",     "km": 80, "lat": -16.38, "lon": -68.82, "tipo": "receptor",  "descripcion": "Receptor final — zona crítica"},
]

def crear_mapa_riesgo_katari(longitud_rio_km=80, n_tributarios=5, res_km=0.5):
    np.random.seed(42)
    rio_principal = np.column_stack([
        np.linspace(0, longitud_rio_km, int(longitud_rio_km/res_km)+1),
        np.zeros(int(longitud_rio_km/res_km)+1)
    ])
    tributarios = []
    for i in range(n_tributarios):
        origen_x = np.random.uniform(10, 70)
        longitud  = np.random.uniform(5, 15)
        angulo    = np.random.choice([-1, 1]) * np.random.uniform(30, 60)
        n_puntos  = int(longitud/res_km)
        t = np.linspace(0, longitud, n_puntos)
        x = origen_x + t * np.cos(np.radians(angulo))
        y = t * np.sin(np.radians(angulo))
        tributarios.append(np.column_stack([x, y]))

    grid  = np.vstack([rio_principal] + tributarios)
    pesos = np.ones(len(grid))

    dist_lago = np.abs(grid[:,0] - 80)
    pesos += 3.5 * np.exp(-dist_lago / 8)

    tomas_riego = np.array([20, 35, 50, 65])
    for toma in tomas_riego:
        dist_toma = np.abs(grid[:,0] - toma) * (grid[:,1]==0)
        pesos += 3.0 * np.exp(-dist_toma / 3)

    descargas = np.array([[10, 0], [20, 0], [45, 2], [70, -1]])
    for desc in descargas:
        dist_desc = np.linalg.norm(grid - desc, axis=1)
        pesos += 2.5 * np.exp(-dist_desc / 2)

    for trib in tributarios:
        dist_union = np.linalg.norm(grid - trib[0], axis=1)
        pesos += 2.0 * (dist_union < 1)

    zonas_lentas = (grid[:,0] > 25) & (grid[:,0] < 30) & (np.abs(grid[:,1]) < 0.5)
    pesos[zonas_lentas] += 2.0

    for toma in tomas_riego:
        aguas_abajo = grid[:,0] > toma
        dist_abajo  = grid[aguas_abajo, 0] - toma
        pesos[aguas_abajo] += 1.8 * np.exp(-dist_abajo / 10)

    pesos = pesos / np.max(pesos) * 100
    return grid, pesos, rio_principal, tributarios, tomas_riego, descargas

@st.cache_data
def greedy_muestreo_fluvial(k=15, alcance_sensor_km=3, res_km=0.5):
    grid, pesos, rio, tributarios, tomas, descargas = crear_mapa_riesgo_katari(res_km=res_km)
    n         = len(grid)
    cubierto  = np.zeros(n, dtype=bool)
    seleccionados = []
    dist_mat  = distance_matrix(grid, grid)
    umbral    = dist_mat <= alcance_sensor_km

    for paso in range(k):
        ya    = np.tile(cubierto, (n, 1))
        nueva = umbral & ~ya
        gan   = nueva @ pesos
        gan[cubierto] = -np.inf
        idx = np.argmax(gan)
        if gan[idx] <= 0: break
        seleccionados.append(grid[idx])
        cubierto[umbral[idx]] = True

    sel = np.array(seleccionados)
    cov = np.sum(pesos[cubierto]) / np.sum(pesos) * 100
    return sel, cubierto, grid, pesos, rio, tributarios, tomas, descargas, cov

def generar_datos_punto(idx, x):
    np.random.seed(idx * 7)
    # Más contaminación cerca de descargas El Alto(10), Viacha(20), media(45), final(70)
    factor = 1.0
    for dx in [10, 20, 45, 70]:
        factor += 2.0 * np.exp(-abs(x - dx) / 5)

    return {
        "As_mg_kg":    round(np.random.uniform(5,  40) * factor * 0.3,  2),
        "Hg_mg_kg":    round(np.random.uniform(0.5, 5) * factor * 0.3,  2),
        "Pb_mg_kg":    round(np.random.uniform(5,  45) * factor * 0.3,  2),
        "Cd_mg_kg":    round(np.random.uniform(0.5, 9) * factor * 0.3,  2),
        "Zn_mg_kg":    round(np.random.uniform(10,100) * factor * 0.25, 2),
        "Cu_mg_kg":    round(np.random.uniform(5,  45) * factor * 0.25, 2),
        "Cs137":       round(np.random.uniform(0.1, 2.5) * min(factor,2), 3),
        "pH":          round(np.random.uniform(6.2, 8.8), 2),
        "Turbidez":    round(np.random.uniform(5,  80) * min(factor,2),  1),
        "Bateria_pct": round(np.random.uniform(20, 100), 1),
        "factor_riesgo": round(factor, 2),
    }

def mostrar(df_actual=None):

    st.markdown("## 🌊 Río Katari — Muestreo Óptimo y Análisis de Riesgo")
    st.markdown("""
    **Zona crítica:** El Río Katari recibe descargas mineras de **El Alto** y **Viacha**,
    desembocando en la **Bahía de Cohana** con altos niveles de contaminación. Este módulo presenta un análisis de riesgo fluvial y un algoritmo greedy para identificar los puntos óptimos de muestreo a lo largo del rio
    *Algoritmo Greedy | 15 puntos óptimos de muestreo*
    """)
    st.divider()

    with st.spinner("Calculando puntos óptimos..."):
        sel, mascara, grid, pesos, rio, tributarios, tomas, descargas, cov = greedy_muestreo_fluvial()

    datos_puntos = [generar_datos_punto(i, p[0]) for i, p in enumerate(sel)]

    # ── KPIs ──────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📍 Puntos Óptimos",   f"{len(sel)}",    "Algoritmo Greedy")
    c2.metric("📊 Cobertura Riesgo", f"{cov:.1f}%",    "área crítica Katari")
    c3.metric("⚠️ Descargas",        "4 fuentes",      "El Alto · Viacha · x2")
    c4.metric("🚿 Tomas de Riego",   f"{len(tomas)}",  "aguas abajo en riesgo")

    st.divider()

    # ══════════════════════════════════════════════════
    # MAPA 1: ESQUEMÁTICO DEL RÍO (algoritmo greedy)
    # ══════════════════════════════════════════════════
    st.markdown("#### 🗺️ Mapa Esquemático — Algoritmo de Muestreo Greedy")
    st.caption("Click en un punto ✕ azul para ver su ficha completa")

    fig = go.Figure()

    # Heatmap riesgo
    fig.add_trace(go.Scatter(
        x=grid[:,0], y=grid[:,1],
        mode="markers",
        marker=dict(size=5, color=pesos, colorscale="YlOrRd", opacity=0.4,
                    colorbar=dict(title="Riesgo", tickfont=dict(color="#e0e0e0"))),
        name="Índice de Riesgo",
        hoverinfo="skip"
    ))

    # Río principal
    fig.add_trace(go.Scatter(
        x=rio[:,0], y=rio[:,1],
        mode="lines", line=dict(color="#4488ff", width=3),
        name="Río Katari", hoverinfo="skip"
    ))

    # Tributarios
    for i, trib in enumerate(tributarios):
        fig.add_trace(go.Scatter(
            x=trib[:,0], y=trib[:,1], mode="lines",
            line=dict(color="#6699ff", width=1.5, dash="dot"),
            name="Tributarios" if i==0 else None,
            showlegend=(i==0), hoverinfo="skip"
        ))

    # Tomas de riego — verde
    fig.add_trace(go.Scatter(
        x=tomas, y=np.zeros_like(tomas), mode="markers",
        marker=dict(size=14, color="#2ecc71", symbol="circle",
                    line=dict(color="darkgreen", width=2)),
        name="🚿 Tomas de Riego",
        hovertemplate="🚿 <b>Toma de Riego</b><br>km %{x}<extra></extra>"
    ))

    # Descargas mineras — rojo
    fig.add_trace(go.Scatter(
        x=descargas[:,0], y=descargas[:,1], mode="markers",
        marker=dict(size=16, color="#e74c3c", symbol="triangle-up",
                    line=dict(color="darkred", width=2)),
        name="⚠️ Descargas Mineras",
        hovertemplate="⚠️ <b>Descarga Minera</b><br>km %{x}<extra></extra>"
    ))

    # Puntos óptimos greedy — azul cyan clickeables
    fig.add_trace(go.Scatter(
        x=sel[:,0], y=sel[:,1], mode="markers",
        marker=dict(size=16, color="#00d4ff", symbol="x",
                    line=dict(color="white", width=2)),
        name="✅ Sensores Óptimos",
        customdata=[[
            f"KAT-{i+1:02d}", d["As_mg_kg"], d["Hg_mg_kg"],
            d["Pb_mg_kg"], d["Cs137"], d["pH"],
            d["Turbidez"], d["Bateria_pct"], d["factor_riesgo"]
        ] for i, d in enumerate(datos_puntos)],
        hovertemplate=(
            "<b>Sensor %{customdata[0]}</b> — km %{x:.1f}<br>"
            "🪨 As: %{customdata[1]} mg/kg | "
            "⚫ Hg: %{customdata[2]} mg/kg<br>"
            "🔩 Pb: %{customdata[3]} mg/kg | "
            "☢️ Cs-137: %{customdata[4]} Bq/m³<br>"
            "💧 pH: %{customdata[5]} | "
            "🌫️ Turb: %{customdata[6]} NTU<br>"
            "🔋 Batería: %{customdata[7]}% | "
            "⚡ Riesgo: %{customdata[8]}x<br>"
            "<i>Click para ficha completa</i>"
            "<extra></extra>"
        )
    ))

    # Bahía de Cohana — marcador especial
    fig.add_trace(go.Scatter(
        x=[80], y=[0], mode="markers+text",
        marker=dict(size=20, color="#ff6b6b", symbol="star",
                    line=dict(color="white", width=2)),
        text=["Bahía Cohana"], textposition="top center",
        textfont=dict(color="#ff6b6b", size=10),
        name="🔴 Bahía de Cohana",
        hovertemplate="🔴 <b>Bahía de Cohana</b><br>Receptor final contaminación<extra></extra>"
    ))

    fig.update_layout(
        **_layout(), height=460,
        xaxis_title="Distancia a lo largo del río (km)",
        yaxis_title="Desviación transversal (km)",
        title=f"Río Katari — {len(sel)} Sensores | Cobertura: {cov:.1f}%",
        legend=dict(orientation="h", y=1.15, font=dict(color="#e0e0e0")),
    )

    evento = st.plotly_chart(fig, use_container_width=True,
                              on_select="rerun", key="katari_greedy")

    # ── Ficha completa al hacer click ──────────────────
    if evento and evento.get("selection") and evento["selection"].get("points"):
        pts = [p for p in evento["selection"]["points"] if p.get("curveNumber") == 6]
        if pts:
            idx_c = pts[0]["pointIndex"]
            d     = datos_puntos[idx_c]
            km    = sel[idx_c][0]
            _mostrar_ficha(idx_c, d, km)

    st.divider()

    # ══════════════════════════════════════════════════
    # MAPA 2: GEOGRÁFICO REAL con Folium
    # ══════════════════════════════════════════════════
    st.markdown("#### 🌍 Mapa Geográfico Real — Cuenca del Río Katari")
    st.caption("Ubicación real de zonas críticas, descargas y sensores en Bolivia")

    try:
        import folium
        from streamlit_folium import st_folium

        mapa_geo = folium.Map(
            location=[-16.55, -68.60], zoom_start=10,
            tiles="CartoDB dark_matter"
        )

        # Sensores óptimos sobre el río
        coords_rio = [
            (-16.65, -68.45), (-16.63, -68.40), (-16.61, -68.37),
            (-16.60, -68.33), (-16.58, -68.30), (-16.56, -68.40),
            (-16.54, -68.48), (-16.52, -68.55), (-16.51, -68.60),
            (-16.50, -68.65), (-16.49, -68.68), (-16.48, -68.72),
            (-16.47, -68.75), (-16.43, -68.79), (-16.38, -68.82),
        ]

        for i, (lat, lon) in enumerate(coords_rio):
            d   = datos_puntos[i] if i < len(datos_puntos) else {}
            bat = d.get("Bateria_pct", 80)
            As  = d.get("As_mg_kg", 0)
            color_pin = "red" if As > 41 or bat < 20 else ("orange" if As > 25 else "blue")

            popup_html = f"""
            <div style='font-family:monospace;min-width:200px;
                        background:#0d2137;color:#e0e0e0;
                        padding:10px;border-radius:8px'>
                <b style='color:#00d4ff'>📍 Sensor KAT-{i+1:02d}</b><br>
                <span style='color:#aaa'>km {i*5:.0f} del nacimiento</span><hr
                style='border-color:#333'>
                🪨 As: <b>{d.get('As_mg_kg','—')} mg/kg</b><br>
                ⚫ Hg: <b>{d.get('Hg_mg_kg','—')} mg/kg</b><br>
                🔩 Pb: <b>{d.get('Pb_mg_kg','—')} mg/kg</b><br>
                ☢️ Cs-137: <b>{d.get('Cs137','—')} Bq/m³</b><br>
                💧 pH: <b>{d.get('pH','—')}</b><br>
                🔋 Batería: <b>{bat}%</b>
            </div>"""

            folium.CircleMarker(
                location=[lat, lon], radius=10,
                color=color_pin, fill=True, fill_opacity=0.85,
                popup=folium.Popup(popup_html, max_width=240),
                tooltip=f"KAT-{i+1:02d} | As:{d.get('As_mg_kg','—')} | Bat:{bat}%"
            ).add_to(mapa_geo)

        # Zonas críticas
        for zona in ZONAS_KATARI:
            if zona["tipo"] == "descarga":
                folium.Marker(
                    location=[zona["lat"], zona["lon"]],
                    popup=folium.Popup(
                        f"<b>⚠️ {zona['nombre']}</b><br>{zona['descripcion']}", max_width=200),
                    tooltip=f"⚠️ {zona['nombre']}",
                    icon=folium.Icon(color="red", icon="warning-sign", prefix="glyphicon")
                ).add_to(mapa_geo)

            elif zona["tipo"] == "riego":
                folium.Marker(
                    location=[zona["lat"], zona["lon"]],
                    popup=folium.Popup(
                        f"<b>🚿 {zona['nombre']}</b><br>{zona['descripcion']}", max_width=200),
                    tooltip=f"🚿 {zona['nombre']}",
                    icon=folium.Icon(color="green", icon="tint", prefix="glyphicon")
                ).add_to(mapa_geo)

            elif zona["tipo"] == "receptor":
                folium.Marker(
                    location=[zona["lat"], zona["lon"]],
                    popup=folium.Popup(
                        f"<b>🔴 {zona['nombre']}</b><br>{zona['descripcion']}", max_width=200),
                    tooltip=f"🔴 {zona['nombre']}",
                    icon=folium.Icon(color="darkred", icon="exclamation-sign", prefix="glyphicon")
                ).add_to(mapa_geo)

        # Línea del río
        folium.PolyLine(
            locations=coords_rio,
            color="#4488ff", weight=3, opacity=0.8,
            tooltip="Río Katari"
        ).add_to(mapa_geo)

        st_folium(mapa_geo, width=None, height=450, returned_objects=[])

    except Exception as e:
        st.error(f"Error cargando mapa geográfico: {e}")

    st.divider()

    # ══════════════════════════════════════════════════
    # GRÁFICO DE BARRAS — metales por sensor
    # ══════════════════════════════════════════════════
    st.markdown("#### 📊 Concentración de Metales — Todos los Sensores")
    st.caption("Barras rojas = sobre límite normativo | DS 24176 Bolivia")

    METALES = {
        "As_mg_kg": ("Arsénico As",  41.0),
        "Hg_mg_kg": ("Mercurio Hg",   5.0),
        "Pb_mg_kg": ("Plomo Pb",     50.0),
        "Cd_mg_kg": ("Cadmio Cd",    10.0),
        "Zn_mg_kg": ("Zinc Zn",     100.0),
        "Cu_mg_kg": ("Cobre Cu",     50.0),
    }

    col_sel = st.selectbox(
        "Metal:", list(METALES.keys()),
        format_func=lambda k: METALES[k][0]
    )
    nombre_metal, limite_metal = METALES[col_sel]

    vals    = [d[col_sel] for d in datos_puntos]
    names   = [f"KAT-{i+1:02d}" for i in range(len(sel))]
    colores = ["#e74c3c" if v > limite_metal else "#00d4ff" for v in vals]

    fig2 = go.Figure(go.Bar(
        x=names, y=vals, marker_color=colores,
        customdata=[[sel[i][0], datos_puntos[i]["factor_riesgo"]] for i in range(len(sel))],
        hovertemplate=(
            "<b>%{x}</b> — km %{customdata[0]:.1f}<br>"
            f"{nombre_metal}: <b>%{{y}} mg/kg</b><br>"
            "Factor riesgo: %{customdata[1]}x"
            "<extra></extra>"
        )
    ))
    fig2.add_hline(y=limite_metal, line_dash="dash", line_color="#ff4444",
                   annotation_text=f"Límite {limite_metal} mg/kg — DS 24176")
    fig2.update_layout(
        **_layout(), height=300,
        xaxis_title="Sensor", yaxis_title=f"{nombre_metal} (mg/kg)",
        title=f"Distribución de {nombre_metal} — Río Katari"
    )

    evento2 = st.plotly_chart(fig2, use_container_width=True,
                               on_select="rerun", key="katari_barras")

    # Ficha al hacer click en barras
    if evento2 and evento2.get("selection") and evento2["selection"].get("points"):
        idx_b = evento2["selection"]["points"][0]["pointIndex"]
        _mostrar_ficha(idx_b, datos_puntos[idx_b], sel[idx_b][0])


def _mostrar_ficha(idx, d, km):
    """Ficha completa del sensor al hacer click"""
    st.divider()
    st.markdown(f"### 📍 Ficha Completa — Sensor KAT-{idx+1:02d} | km {km:.1f}")

    # Estado general
    alertas = []
    if d["As_mg_kg"] > 41:  alertas.append(("Arsénico",  d["As_mg_kg"],  41.0,  "mg/kg"))
    if d["Hg_mg_kg"] > 5:   alertas.append(("Mercurio",  d["Hg_mg_kg"],   5.0,  "mg/kg"))
    if d["Pb_mg_kg"] > 50:  alertas.append(("Plomo",     d["Pb_mg_kg"],  50.0,  "mg/kg"))
    if d["Cd_mg_kg"] > 10:  alertas.append(("Cadmio",    d["Cd_mg_kg"],  10.0,  "mg/kg"))
    if d["Cs137"]    > 10:  alertas.append(("Cs-137",    d["Cs137"],     10.0,  "Bq/m³"))
    if d["pH"]       > 8.5: alertas.append(("pH",        d["pH"],         8.5,  ""))

    if alertas:
        st.error(f"🚨 **{len(alertas)} parámetro(s) sobre límite normativo**")
        for nombre, val, lim, unidad in alertas:
            st.markdown(f"&nbsp;&nbsp;&nbsp;→ **{nombre}**: `{val} {unidad}` > límite `{lim} {unidad}`")
    else:
        st.success("✅ Todos los parámetros dentro de norma")

    # Métricas
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🪨 Arsénico",  f"{d['As_mg_kg']} mg/kg",
              "🔴 CRÍTICO" if d["As_mg_kg"] > 41  else "✅ OK")
    c2.metric("⚫ Mercurio",  f"{d['Hg_mg_kg']} mg/kg",
              "🔴 CRÍTICO" if d["Hg_mg_kg"] > 5   else "✅ OK")
    c3.metric("🔩 Plomo",     f"{d['Pb_mg_kg']} mg/kg",
              "🔴 CRÍTICO" if d["Pb_mg_kg"] > 50  else "✅ OK")
    c4.metric("🔋 Cadmio",    f"{d['Cd_mg_kg']} mg/kg",
              "🔴 CRÍTICO" if d["Cd_mg_kg"] > 10  else "✅ OK")

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("🔧 Zinc",      f"{d['Zn_mg_kg']} mg/kg",
              "🔴 CRÍTICO" if d["Zn_mg_kg"] > 100 else "✅ OK")
    c6.metric("🟤 Cobre",     f"{d['Cu_mg_kg']} mg/kg",
              "🔴 CRÍTICO" if d["Cu_mg_kg"] > 50  else "✅ OK")
    c7.metric("☢️ Cs-137",   f"{d['Cs137']} Bq/m³",
              "🔴 CRÍTICO" if d["Cs137"] > 10     else "✅ OK")
    c8.metric("🔋 Batería",   f"{d['Bateria_pct']}%",
              "🔴 CRÍTICO" if d["Bateria_pct"] < 20 else "✅ OK")

    c9, c10 = st.columns(2)
    c9.metric("💧 pH",        f"{d['pH']}")
    c10.metric("🌫️ Turbidez",f"{d['Turbidez']} NTU",
               "🔴 CRÍTICO" if d["Turbidez"] > 25 else "✅ OK")

    # Mini radar de contaminación
    categorias = ["Arsénico", "Mercurio", "Plomo", "Cadmio", "Zinc", "Cobre"]
    valores_norm = [
        min(d["As_mg_kg"] / 41.0,  2.0),
        min(d["Hg_mg_kg"] / 5.0,   2.0),
        min(d["Pb_mg_kg"] / 50.0,  2.0),
        min(d["Cd_mg_kg"] / 10.0,  2.0),
        min(d["Zn_mg_kg"] / 100.0, 2.0),
        min(d["Cu_mg_kg"] / 50.0,  2.0),
    ]
    valores_norm += [valores_norm[0]]
    categorias   += [categorias[0]]

    fig_radar = go.Figure(go.Scatterpolar(
        r=valores_norm, theta=categorias,
        fill="toself",
        fillcolor="rgba(231,76,60,0.3)",
        line=dict(color="#e74c3c", width=2),
        name="Nivel (normalizado)"
    ))
    fig_radar.add_trace(go.Scatterpolar(
        r=[1]*len(categorias), theta=categorias,
        mode="lines", line=dict(color="#ffd700", dash="dash", width=1.5),
        name="Límite normativo"
    ))
    fig_radar.update_layout(
        **_layout(), height=320,
        polar=dict(
            bgcolor="#0d2137",
            radialaxis=dict(visible=True, range=[0, 2],
                            tickfont=dict(color="#e0e0e0"),
                            gridcolor="#1a3a5c"),
            angularaxis=dict(tickfont=dict(color="#e0e0e0"),
                             gridcolor="#1a3a5c")
        ),
        title=f"Radar de Contaminación — KAT-{idx+1:02d}",
        showlegend=True,
        legend=dict(font=dict(color="#e0e0e0"))
    )
    st.plotly_chart(fig_radar, use_container_width=True)


def _layout():
    return dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#e0e0e0",
        margin=dict(l=10, r=10, t=40, b=10),
    )