import numpy as np
import pandas as pd
from datetime import datetime, timedelta

np.random.seed(42)

# ── Puntos de muestreo ampliados con ríos y zonas mineras ─────────────
PUNTOS_MUESTREO = [
    # Lago Titicaca original
    {"id": "TIT-01", "nombre": "Bahía de Puno",       "lat": -15.8402, "lon": -70.0219, "zona": "Lago Titicaca", "tipo": "lago"},
    {"id": "TIT-02", "nombre": "Isla del Sol",         "lat": -16.0225, "lon": -69.0753, "zona": "Lago Titicaca", "tipo": "lago"},
    {"id": "TIT-03", "nombre": "Desaguadero",          "lat": -16.5653, "lon": -69.0428, "zona": "Lago Titicaca", "tipo": "lago"},
    {"id": "TIT-04", "nombre": "Bahía Copacabana",     "lat": -16.1669, "lon": -69.0854, "zona": "Lago Titicaca", "tipo": "lago"},
    {"id": "TIT-05", "nombre": "Lago Huiñaimarca",     "lat": -16.5000, "lon": -68.8000, "zona": "Lago Titicaca", "tipo": "lago"},
    {"id": "TIT-06", "nombre": "Puerto Acosta",        "lat": -15.5167, "lon": -69.2500, "zona": "Lago Titicaca", "tipo": "lago"},
    {"id": "TIT-07", "nombre": "Moho",                 "lat": -15.3500, "lon": -69.4833, "zona": "Lago Titicaca", "tipo": "lago"},
    {"id": "TIT-08", "nombre": "Conima",               "lat": -15.4000, "lon": -69.3167, "zona": "Lago Titicaca", "tipo": "lago"},
    {"id": "TIT-09", "nombre": "Isla Taquile",         "lat": -15.7667, "lon": -69.7000, "zona": "Lago Titicaca", "tipo": "lago"},
    {"id": "TIT-10", "nombre": "Isla Amantaní",        "lat": -15.6000, "lon": -69.6167, "zona": "Lago Titicaca", "tipo": "lago"},
    {"id": "TIT-11", "nombre": "Juli",                 "lat": -16.2167, "lon": -69.4500, "zona": "Lago Titicaca", "tipo": "lago"},
    {"id": "TIT-12", "nombre": "Pomata",               "lat": -16.2667, "lon": -69.2833, "zona": "Lago Titicaca", "tipo": "lago"},
    {"id": "TIT-13", "nombre": "Zepita",               "lat": -16.4000, "lon": -69.1500, "zona": "Lago Titicaca", "tipo": "lago"},
    {"id": "TIT-14", "nombre": "Huancané",             "lat": -15.2000, "lon": -69.7667, "zona": "Lago Titicaca", "tipo": "lago"},
    {"id": "TIT-15", "nombre": "Puerto Yunguyo",       "lat": -16.2333, "lon": -69.1000, "zona": "Lago Titicaca", "tipo": "lago"},
    # Río Katari — zona crítica minera El Alto/Viacha
    {"id": "KAT-01", "nombre": "Katari — Nacimiento",  "lat": -16.6500, "lon": -68.4500, "zona": "Río Katari",    "tipo": "rio"},
    {"id": "KAT-02", "nombre": "Katari — El Alto",     "lat": -16.5800, "lon": -68.3800, "zona": "Río Katari",    "tipo": "rio"},
    {"id": "KAT-03", "nombre": "Katari — Viacha",      "lat": -16.6500, "lon": -68.3000, "zona": "Río Katari",    "tipo": "rio"},
    {"id": "KAT-04", "nombre": "Katari — Medio",       "lat": -16.5200, "lon": -68.5500, "zona": "Río Katari",    "tipo": "rio"},
    {"id": "KAT-05", "nombre": "Katari — Desembocadura","lat": -16.3800, "lon": -68.7500, "zona": "Río Katari",   "tipo": "rio"},
    # Bahía de Cohana — receptor final contaminación
    {"id": "COH-01", "nombre": "Cohana — Entrada",     "lat": -16.3200, "lon": -68.7800, "zona": "Bahía Cohana",  "tipo": "bahia"},
    {"id": "COH-02", "nombre": "Cohana — Centro",      "lat": -16.3500, "lon": -68.8200, "zona": "Bahía Cohana",  "tipo": "bahia"},
    {"id": "COH-03", "nombre": "Cohana — Sur",         "lat": -16.3800, "lon": -68.8500, "zona": "Bahía Cohana",  "tipo": "bahia"},
    # Zona Minera Referencia
    {"id": "MIN-01", "nombre": "Mina Colquiri",        "lat": -17.3833, "lon": -67.1167, "zona": "Zona Minera",   "tipo": "mina"},
    {"id": "MIN-02", "nombre": "Mina Huanuni",         "lat": -18.2833, "lon": -66.8333, "zona": "Zona Minera",   "tipo": "mina"},
]

# ── Límites IAEA/OMS/Norma Boliviana ──────────────────────────────────
# Fuentes: IAEA-TECDOC-1250, OMS 2017, DS 24176 Bolivia
LIMITES_IAEA = {
    "Cs137_Bq_m3":   {"limite": 10.0,  "unidad": "Bq/m³",  "norma": "IAEA-TECDOC-1250"},
    "pH":            {"limite": 8.5,   "unidad": "",        "norma": "OMS 2017"},
    "Turbidez_NTU":  {"limite": 25.0,  "unidad": "NTU",     "norma": "OMS 2017"},
    "EDR_uSv_h":     {"limite": 0.30,  "unidad": "µSv/h",   "norma": "IAEA Safety Reports"},
    "Sr90_Bq_L":     {"limite": 0.10,  "unidad": "Bq/L",    "norma": "OMS 2017"},
    "As_mg_kg":      {"limite": 41.0,  "unidad": "mg/kg",   "norma": "DS 24176 Bolivia"},
    "Hg_mg_kg":      {"limite": 5.0,   "unidad": "mg/kg",   "norma": "DS 24176 Bolivia"},
    "Pb_mg_kg":      {"limite": 50.0,  "unidad": "mg/kg",   "norma": "DS 24176 Bolivia"},
    "Cd_mg_kg":      {"limite": 10.0,  "unidad": "mg/kg",   "norma": "DS 24176 Bolivia"},
    "Zn_mg_kg":      {"limite": 100.0, "unidad": "mg/kg",   "norma": "DS 24176 Bolivia"},
    "Cu_mg_kg":      {"limite": 50.0,  "unidad": "mg/kg",   "norma": "DS 24176 Bolivia"},
}

def _nivel_contaminacion_zona(zona):
    """Multiplica los metales pesados según zona — zonas mineras más contaminadas"""
    factores = {
        "Lago Titicaca": 1.0,
        "Río Katari":    3.5,   # contaminación minera alta
        "Bahía Cohana":  4.5,   # receptor final, más contaminado
        "Zona Minera":   6.0,   # zona de origen
    }
    return factores.get(zona, 1.0)

def calcular_indice_salud(cs137, ph, turbidez, sr90, As, Hg, Pb):
    """Índice ponderado 0-100 incluyendo metales pesados"""
    idx_cs   = max(0, 100 - (cs137 / 3.0)   * 100)
    idx_ph   = 100 if 6.5 <= ph <= 8.5 else max(0, 100 - abs(ph - 7.5) * 30)
    idx_turb = max(0, 100 - (turbidez / 45)  * 100)
    idx_sr   = max(0, 100 - (sr90 / 0.15)    * 100)
    idx_as   = max(0, 100 - (As / 41.0)      * 100)
    idx_hg   = max(0, 100 - (Hg / 5.0)       * 100)
    idx_pb   = max(0, 100 - (Pb / 50.0)      * 100)
    return round(
        idx_cs   * 0.25 +
        idx_ph   * 0.20 +
        idx_turb * 0.10 +
        idx_sr   * 0.10 +
        idx_as   * 0.15 +
        idx_hg   * 0.10 +
        idx_pb   * 0.10, 1
    )

def generar_dataset_completo(n_historico=400):
    """
    Dataset ampliado con metales pesados y nuevas zonas
    Rangos: IAEA-TECDOC-1508, estudios UMSA Titicaca 2019,
            SERGEOTECMIN Bolivia, OPS/OMS Cuenca Katari 2018
    """
    registros = []
    n_puntos = len(PUNTOS_MUESTREO)

    for i in range(n_historico):
        punto = PUNTOS_MUESTREO[i % n_puntos]
        fecha = datetime.now() - timedelta(hours=i * 1.2)
        f     = _nivel_contaminacion_zona(punto["zona"])

        cs137 = round(np.random.uniform(0.08, 2.8)   * min(f, 2),    3)
        k40   = round(np.random.uniform(75, 125),                      2)
        sr90  = round(np.random.uniform(0.005, 0.18) * min(f, 1.5),   4)
        ph    = round(np.random.uniform(6.2, 9.1),                     2)
        cond  = round(np.random.uniform(900, 1900)   * min(f, 1.8),   1)
        turb  = round(np.random.uniform(1.5, 45.0)  * min(f, 2),      2)
        edr   = round(np.random.uniform(0.05, 0.35) * min(f, 1.5),    3)

        # Metales pesados — del simulador core_engine
        As_v  = round(np.random.uniform(5.0,  45.0) * f * 0.4,  2)
        Hg_v  = round(np.random.uniform(0.5,  6.0)  * f * 0.3,  2)
        Pb_v  = round(np.random.uniform(5.0,  55.0) * f * 0.35, 2)
        Cd_v  = round(np.random.uniform(0.5,  12.0) * f * 0.3,  2)
        Zn_v  = round(np.random.uniform(10.0, 110.0)* f * 0.35, 2)
        Cu_v  = round(np.random.uniform(5.0,  55.0) * f * 0.3,  2)

        # Batería del sensor (%) — degradación simulada realista
        bateria = round(np.random.uniform(15, 100) - (i % 15) * 2, 1)
        bateria = max(5.0, min(100.0, bateria))
        voltaje = round(3.3 + (bateria / 100) * 0.9, 2)  # 3.3V-4.2V LiPo
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
            # Variables radiológicas
            "Cs137_Bq_m3":      cs137,
            "K40_Bq_L":         k40,
            "Sr90_Bq_L":        sr90,
            "EDR_uSv_h":        edr,
            # Variables fisicoquímicas
            "pH":               ph,
            "Conductividad_uS": cond,
            "Turbidez_NTU":     turb,
            # Metales pesados (del simulador)
            "As_mg_kg":         As_v,
            "Hg_mg_kg":         Hg_v,
            "Pb_mg_kg":         Pb_v,
            "Cd_mg_kg":         Cd_v,
            "Zn_mg_kg":         Zn_v,
            "Cu_mg_kg":         Cu_v,
            # Batería del sensor IoT
            "Bateria_pct":      bateria,
            "Voltaje_V":        voltaje,
            "Estado_Bateria":   estado_bat,
            # Índices
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
    print(f"✅ Dataset generado: {len(df)} registros, {len(df.columns)} variables")
    print(f"Zonas: {df['zona'].unique()}")
    print(df.head(3))