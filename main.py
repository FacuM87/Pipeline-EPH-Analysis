# main.py

import os
import pandas as pd

from src.cleaning import generar_eph_limpia
from src.recortar_aglomerados import generar_archivo_recortado
from src.ingresos import calcular_ingresos
from src.tasas import tasas_trimestrales
from src.geoespacial import generar_mapas


# ======================================================
#   Versionado automático para outputs
# ======================================================

def versionar_archivo(path):
    """
    Si path existe:
        archivo.csv -> archivo_v2.csv -> archivo_v3.csv ...
    Devuelve el nombre final donde debe guardarse.
    """
    if not os.path.exists(path):
        return path

    base, ext = os.path.splitext(path)
    version = 2

    while True:
        candidate = f"{base}_v{version}{ext}"
        if not os.path.exists(candidate):
            return candidate
        version += 1


# ======================================================
#   Paths del proyecto
# ======================================================

AGLOS_TARGET = [31, 34]

DATA_LIMPIA = "data/EPH_datos_limpios.csv"
DATA_LIMPIA_RECORTADA = "data/EPH_datos_limpios_31_34.csv"
DATA_CRUDA = "data/data_cruda"
IPC_PATH = "data/deflator_ipc_proxy_nacional.csv"

OUTPUT_DIR = "output"
MAPAS_DIR = os.path.join(OUTPUT_DIR, "mapas")
TASAS_DIR = os.path.join(OUTPUT_DIR, "tasas")
INGRESOS_DIR = os.path.join(OUTPUT_DIR, "ingresos")

os.makedirs(MAPAS_DIR, exist_ok=True)
os.makedirs(TASAS_DIR, exist_ok=True)
os.makedirs(INGRESOS_DIR, exist_ok=True)


print("\n==============================")
print("🚀 INICIANDO PIPELINE EPH ")
print("==============================\n")


# ======================================================
#   1) Generar EPH limpia si NO existe
# ======================================================

if os.path.exists(DATA_LIMPIA):
    print("✔ Usando EPH limpia existente (no se regenera).")
else:
    print("🔧 Generando EPH limpia...")
    generar_eph_limpia(DATA_CRUDA, DATA_LIMPIA)


# ======================================================
#   2) Generar archivo recortado SOLO si no existe
# ======================================================

generar_archivo_recortado(
    path_limpio=DATA_LIMPIA,
    path_recortado=DATA_LIMPIA_RECORTADA,
    aglos=AGLOS_TARGET
)


# ======================================================
#   3) Cargar archivo recortado
# ======================================================

print("\n📥 Cargando dataset limpio (solo aglos 31 y 34)...")
df = pd.read_csv(DATA_LIMPIA_RECORTADA, low_memory=False)
print(f"✔ Filas cargadas: {len(df)}")


# ======================================================
#   4) Calcular ingresos reales
# ======================================================

print("\n💰 Calculando ingresos (deflactado + ocupados + promedios)...")

df_defl, df_ocup, tabla_aglo, tabla_aglo_trim = calcular_ingresos(
    df_eph=df,
    ipc_path=IPC_PATH,
    ano_base=2025,
    trimestre_base=2,
    aglos=AGLOS_TARGET
)

# --- df_defl SOLO CSV ---
csv_defl = versionar_archivo(os.path.join(INGRESOS_DIR, "ingresos_deflactados.csv"))
df_defl.to_csv(csv_defl, index=False)
print(f"✔ Deflactado exportado SOLO CSV:\n   {csv_defl}")

# --- df_ocup SOLO CSV ---
csv_ocup = versionar_archivo(os.path.join(INGRESOS_DIR, "ingresos_ocupados.csv"))
df_ocup.to_csv(csv_ocup, index=False)
print(f"✔ Ocupados exportados SOLO CSV:\n   {csv_ocup}")

# --- ingreso promedio general por aglomerado ---
csv_aglo = versionar_archivo(os.path.join(INGRESOS_DIR, "ingreso_prom_aglomerado.csv"))
xlsx_aglo = versionar_archivo(os.path.join(INGRESOS_DIR, "ingreso_prom_aglomerado.xlsx"))
tabla_aglo.to_csv(csv_aglo, index=False)
tabla_aglo.to_excel(xlsx_aglo, index=False)
print(f"✔ Ingreso promedio general exportado:\n   {csv_aglo}\n   {xlsx_aglo}")

# --- ingreso promedio trimestral 2016–2025 ---
csv_aglo_trim = versionar_archivo(os.path.join(INGRESOS_DIR, "ingreso_prom_trimestral_aglomerado.csv"))
xlsx_aglo_trim = versionar_archivo(os.path.join(INGRESOS_DIR, "ingreso_prom_trimestral_aglomerado.xlsx"))
tabla_aglo_trim.to_csv(csv_aglo_trim, index=False)
tabla_aglo_trim.to_excel(xlsx_aglo_trim, index=False)
print(f"✔ Ingreso promedio trimestral exportado:\n   {csv_aglo_trim}\n   {xlsx_aglo_trim}")


# ======================================================
#   5) Calcular tasas trimestrales
# ======================================================

print("\n📊 Calculando tasas trimestrales...")

df_tasas = tasas_trimestrales(df)

csv_tasas = versionar_archivo(os.path.join(TASAS_DIR, "tasas_trimestrales.csv"))
xlsx_tasas = versionar_archivo(os.path.join(TASAS_DIR, "tasas_trimestrales.xlsx"))

df_tasas.to_csv(csv_tasas, index=False)
df_tasas.to_excel(xlsx_tasas, index=False)

print(f"✔ Tasas exportadas:\n   {csv_tasas}\n   {xlsx_tasas}")


# ======================================================
#   6) Generar mapas geoespaciales
# ======================================================

print("\n🗺 Generando mapas geoespaciales 2025 para 31 y 34...")

from src.geoespacial import generar_mapas

generar_mapas(
    df_ingresos=tabla_aglo,
    carpeta_salida=MAPAS_DIR
)

print(f"✔ Mapas generados en: {MAPAS_DIR}")


# ======================================================
#   7) Generar gráficos (tasas + ingreso trimestral)
# ======================================================

print("\n📈 Generando gráficos...")

from src.graficos import generar_graficos

graficos_paths = generar_graficos(
    df_tasas=df_tasas,
    df_ing_trimestral=tabla_aglo_trim,
    carpeta_salida=os.path.join(OUTPUT_DIR, "graficos")
)

print("✔ Gráficos generados:")
for p in graficos_paths:
    print("   →", p)


# ======================================================
#   8) Boxplot de ingresos
# ======================================================

print("\n📦 Generando boxplot de ingresos...")

from src.boxplots import generar_boxplot_ingresos

boxplot_path = generar_boxplot_ingresos(
    df_ocup=df_ocup,
    carpeta_salida=os.path.join(OUTPUT_DIR, "graficos")
)

print("✔ Boxplot generado en:")
print("   →", boxplot_path)



print("\n📘 Generando gráficos univariados de ingreso (media/mediana + Q25/Q75)...")



from src.graficos_ingresos import generar_graficos_ingresos_univariados

paths_uni = generar_graficos_ingresos_univariados(
    df_ocup=df_ocup,
    carpeta_salida=os.path.join(OUTPUT_DIR, "graficos")
)

print("✔ Gráficos univariados:")
for p in paths_uni:
    print("   →", p)


# ======================================================
#   9) Tasas de Empleo por rama
# ======================================================

from src.te_ramas import tasas_empleo_por_rama, exportar_tasas_rama, graficar_tasas_rama

print("\n📊 Calculando tasa de empleo por rama (Industria vs Turismo)...")

df_t_ramas = tasas_empleo_por_rama(df)  

csv_ramas, xlsx_ramas = exportar_tasas_rama(df_t_ramas, carpeta_salida=os.path.join(OUTPUT_DIR, "tasas"))
print("✔ Tasas por rama exportadas:")
print("   ", csv_ramas)
print("   ", xlsx_ramas)

paths_ramas = graficar_tasas_rama(df_t_ramas, carpeta_salida=os.path.join(OUTPUT_DIR, "graficos"))
print("✔ Gráficos de tasas por rama generados:")
for p in paths_ramas:
    print("   →", p)


# ======================================================
#   10) Participación de un sector en empleo total
# ======================================================

from src.te_ramas_participacion import (
    participacion_empleo_por_rama,
    exportar_participacion_rama,
    graficar_participacion_rama,
)

print("\n📊 Calculando participación del empleo por rama (Industria vs Turismo)...")

df_part_ramas = participacion_empleo_por_rama(df, aglos_target=[31, 34])

csv_part, xlsx_part = exportar_participacion_rama(
    df_part_ramas,
    carpeta_salida=os.path.join(OUTPUT_DIR, "tasas")
)
print("✔ Participación por rama exportada:")
print("   ", csv_part)
print("   ", xlsx_part)

paths_part = graficar_participacion_rama(
    df_part_ramas,
    carpeta_salida=os.path.join(OUTPUT_DIR, "graficos")
)
print("✔ Gráficos de participación por rama generados:")
for p in paths_part:
    print("   →", p)


print("\n=======================================")
print("🎉 PIPELINE COMPLETO ")
print("=======================================\n")
