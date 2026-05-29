import numpy as np
import pandas as pd
from datetime import datetime, timedelta

np.random.seed(42)

PUNTOS_MUESTREO = [
    # Río Katari — cuenca completa
    {"id": "KAT-01", "nombre": "Nacimiento Katari",    "lat": -16.650, "lon": -68.450, "zona": "Río Katari",   "tipo": "origen"},
    {"id": "KAT-02", "nombre": "El Alto — Zona Ind.",  "lat": -16.580, "lon": -68.380, "zona": "Río Katari",   "tipo": "descarga"},
    {"id": "KAT-03", "nombre": "Viacha — Minería",     "lat": -16.650, "lon": -68.300, "zona": "Río Katari",   "tipo": "descarga"},
    {"id": "KAT-04", "nombre": "Toma Riego Norte",     "lat": -16.520, "lon": -68.380, "zona": "Río Katari",   "tipo": "riego"},
    {"id": "KAT-05", "nombre": "Confluencia Pallina",  "lat": -16.540, "lon": -68.520, "zona": "Río Katari",   "tipo": "confluencia"},
    {"id": "KAT-06", "nombre": "Toma Riego Central",   "lat": -16.510, "lon": -68.550, "zona": "Río Katari",   "tipo": "riego"},
    {"id": "KAT-07", "nombre": "Descarga Media",       "lat": -16.500, "lon": -68.620, "zona": "Río Katari",   "tipo": "descarga"},
    {"id": "KAT-08", "nombre": "Zona Sedimentación",   "lat": -16.495, "lon": -68.640, "zona": "Río Katari",   "tipo": "monitoreo"},
    {"id": "KAT-09", "nombre": "Toma Riego Sur",       "lat": -16.490, "lon": -68.650, "zona": "Río Katari",   "tipo": "riego"},
    {"id": "KAT-10", "nombre": "Tramo Bajo Katari",    "lat": -16.480, "lon": -68.680, "zona": "Río Katari",   "tipo": "monitoreo"},
    {"id": "KAT-11", "nombre": "Toma Riego Final",     "lat": -16.470, "lon": -68.720, "zona": "Río Katari",   "tipo": "riego"},
    {"id": "KAT-12", "nombre": "Descarga Pre-Cohana",  "lat": -16.460, "lon": -68.750, "zona": "Río Katari",   "tipo": "descarga"},
    # Bahía de Cohana — receptor final
    {"id": "COH-01", "nombre": "Cohana — Entrada",     "lat": -16.320, "lon": -68.780, "zona": "Bahía Cohana", "tipo": "bahia"},
    {"id": "COH-02", "nombre": "Cohana — Centro",      "lat": -16.350, "lon": -68.820, "zona": "Bahía Cohana", "tipo": "bahia"},
    {"id": "COH-03", "nombre": "Cohana — Sur",         "lat": -16.380, "lon": -68.850, "zona": "Bahía Cohana", "tipo": "bahia"},
    # Zona Minera — referencia
    {"id": "MIN-01", "nombre": "Zona Minera El Alto",  "lat": -16.600, "lon": -68.350, "zona": "Zona Minera",  "tipo": "mina"},
    {"id": "MIN-02", "nombre": "Vertedero Viacha",     "lat": -16.670, "lon": -68.290, "zona": "Zona Minera",  "tipo": "mina"},
]

LIMITES_IAEA = {
    "Cs137_Bq_m3":      {"limite": 10.0,  "unidad": "Bq/m³",  "norma": "IAEA-TECDOC-1250"},
    "pH":               {"limite": 8.5,   "unidad": "",        "norma": "OMS 2017"},
    "Turbidez_NTU":     {"limite": 25.0,  "unidad": "NTU",     "norma": "OMS 2017"},
    "EDR_uSv_h":        {"limite": 0.30,  "unidad": "µSv/h",   "norma": "IAEA Safety Reports"},
    "Sr90_Bq_L":        {"limite": 0.10,  "unidad": "Bq/L",    "norma": "OMS 2017"},
    "As_mg_kg":         {"limite": 41.0,  "unidad": "mg/kg",   "norma": "DS 24176 Bolivia"},
    "Hg_mg_kg":         {"limite": 5.0,   "unidad": "mg/kg",   "norma": "DS 24176 Bolivia"},
    "Pb_mg_kg":         {"limite": 50.0,  "unidad": "mg/kg",   "norma": "DS 24176 Bolivia"},
    "Cd_mg_kg":         {"limite": 10.0,  "unidad": "mg/kg",   "norma": "DS 24176 Bolivia"},
    "Zn_mg_kg":         {"limite": 100.0, "unidad": "mg/kg",   "norma": "DS 24176 Bolivia"},
    "Cu_mg_kg":         {"limite": 50.0,  "unidad": "mg/kg",   "norma": "DS 24176 Bolivia"},
}

def _factor_zona(zona, tipo):
    factores = {
        "Zona Minera":   6.0,
        "Río Katari":    3.0,
        "Bahía Cohana":  4.5,
    }
    f = factores.get(zona, 1.0)
    if tipo == "descarga": f *= 1.4
    return f

def calcular_indice_salud(cs137, ph, turbidez, sr90, As, Hg, Pb):
    idx_cs   = max(0, 100 - (cs137 / 3.0)   * 100)
    idx_ph   = 100 if 6.5 <= ph <= 8.5 else max(0, 100 - abs(ph - 7.5) * 30)
    idx_turb = max(0, 100 - (turbidez / 45)  * 100)
    idx_sr   = max(0, 100 - (sr90 / 0.15)    * 100)
    idx_as   = max(0, 100 - (As / 41.0)      * 100)
    idx_hg   = max(0, 100 - (Hg / 5.0)       * 100)
    idx_pb   = max(0, 100 - (Pb / 50.0)      * 100)
    return round(
        idx_cs   * 0.20 +
        idx_ph   * 0.15 +
        idx_turb * 0.10 +
        idx_sr   * 0.10 +
        idx_as   * 0.20 +
        idx_hg   * 0.15 +
        idx_pb   * 0.10, 1
    )

def generar_dataset_completo(n_historico=400):
    registros = []
    n_puntos  = len(PUNTOS_MUESTREO)

    for i in range(n_historico):
        punto = PUNTOS_MUESTREO[i % n_puntos]
        fecha = datetime.now() - timedelta(hours=i * 1.2)
        f     = _factor_zona(punto["zona"], punto["tipo"])

        cs137 = round(np.random.uniform(0.1,  2.8)   * min(f * 0.4, 3),   3)
        k40   = round(np.random.uniform(75,   125),                         2)
        sr90  = round(np.random.uniform(0.01, 0.18)  * min(f * 0.4, 1.8), 4)
        ph    = round(np.random.uniform(6.0,  9.1),                         2)
        cond  = round(np.random.uniform(800,  2200)  * min(f * 0.4, 2.0), 1)
        turb  = round(np.random.uniform(5.0,  80.0)  * min(f * 0.35, 2.5),2)
        edr   = round(np.random.uniform(0.05, 0.35)  * min(f * 0.3, 1.8), 3)

        As_v  = round(np.random.uniform(5,    45)  * f * 0.35, 2)
        Hg_v  = round(np.random.uniform(0.5,  6.5) * f * 0.28, 2)
        Pb_v  = round(np.random.uniform(5,    55)  * f * 0.30, 2)
        Cd_v  = round(np.random.uniform(0.5,  12)  * f * 0.28, 2)
        Zn_v  = round(np.random.uniform(10,  115)  * f * 0.30, 2)
        Cu_v  = round(np.random.uniform(5,    55)  * f * 0.28, 2)

        bateria = round(max(5.0, min(100.0, np.random.uniform(15, 100) - (i % n_puntos) * 2)), 1)
        voltaje = round(3.3 + (bateria / 100) * 0.9, 2)
        estado_bat = "🔴 CRÍTICO" if bateria < 20 else ("🟡 BAJO" if bateria < 40 else "🟢 OK")

        salud  = calcular_indice_salud(cs137, ph, turb, sr90, As_v, Hg_v, Pb_v)
        estado = "CRÍTICO" if salud < 40 else ("PRECAUCIÓN" if salud < 70 else "NORMAL")

        registros.append({
            "timestamp":        fecha.strftime("%Y-%m-%d %H:%M"),
            "id":               punto["id"],
            "nombre":           punto["nombre"],
            "zona":             punto["zona"],
            "tipo":             punto["tipo"],
            "lat":              punto["lat"],
            "lon":              punto["lon"],
            "Cs137_Bq_m3":      cs137,
            "K40_Bq_L":         k40,
            "Sr90_Bq_L":        sr90,
            "EDR_uSv_h":        edr,
            "pH":               ph,
            "Conductividad_uS": cond,
            "Turbidez_NTU":     turb,
            "As_mg_kg":         As_v,
            "Hg_mg_kg":         Hg_v,
            "Pb_mg_kg":         Pb_v,
            "Cd_mg_kg":         Cd_v,
            "Zn_mg_kg":         Zn_v,
            "Cu_mg_kg":         Cu_v,
            "Bateria_pct":      bateria,
            "Voltaje_V":        voltaje,
            "Estado_Bateria":   estado_bat,
            "Indice_Salud":     salud,
            "Estado":           estado,
        })

    return pd.DataFrame(registros)

def get_datos_actuales(df):
    return df.groupby("id").first().reset_index()

def generar_serie_tiempo_nodo(df, nombre_punto):
    return df[df["nombre"] == nombre_punto].sort_values("timestamp").tail(24)

if __name__ == "__main__":
    df = generar_dataset_completo(400)
    df.to_csv("data/datos_titicaca.csv", index=False)
    print(f"✅ {len(df)} registros | {df['zona'].unique()}")