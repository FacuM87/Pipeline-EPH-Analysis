import os
import pandas as pd
import matplotlib.pyplot as plt


# ==========================================================
#   Función de versionado (igual que en main.py)
# ==========================================================

def versionar_archivo(path):
    """Genera versiones archivo.png → archivo_v2.png → archivo_v3.png ..."""
    if not os.path.exists(path):
        return path

    base, ext = os.path.splitext(path)
    version = 2

    while True:
        candidate = f"{base}_v{version}{ext}"
        if not os.path.exists(candidate):
            return candidate
        version += 1


# ==========================================================
#   Formateo del eje X (AAAAT)
# ==========================================================

def crear_periodo(df):
    """Crea columna PERIODO con formato AAAA-Tn."""
    return df["ANO4"].astype(str) + "-T" + df["TRIMESTRE"].astype(str)


# ==========================================================
#   Gráfico de tasas (TA, TE, TD)
# ==========================================================

def graficar_tasas(df_tasas, aglo, carpeta_salida):
    """
    df_tasas debe contener:
    AGLOMERADO, ANO4, TRIMESTRE, TA, TE, TD
    Genera gráfico de líneas TA/TE/TD vs período.
    """

    df = df_tasas[df_tasas["AGLOMERADO"] == aglo].copy()
    df = df.sort_values(["ANO4", "TRIMESTRE"])

    df["PERIODO"] = crear_periodo(df)

    plt.figure(figsize=(12, 6))
    plt.plot(df["PERIODO"], df["TA"] * 100, label="Tasa de Actividad (TA)", marker="o")
    plt.plot(df["PERIODO"], df["TE"] * 100, label="Tasa de Empleo (TE)", marker="o")
    plt.plot(df["PERIODO"], df["TD"] * 100, label="Tasa de Desocupación (TD)", marker="o")

    plt.xticks(rotation=90)
    plt.ylabel("Porcentaje (%)")
    plt.xlabel("Período (AAAA-Tn)")
    plt.title(f"Tasas Trimestrales - Aglomerado {aglo}")
    plt.grid(alpha=0.3)
    plt.legend()

    os.makedirs(carpeta_salida, exist_ok=True)
    path = os.path.join(carpeta_salida, f"tasas_{aglo}.png")
    path_final = versionar_archivo(path)

    plt.tight_layout()
    plt.savefig(path_final)
    plt.close()

    return path_final


# ==========================================================
#   Gráfico de ingreso real promedio trimestral
# ==========================================================

def graficar_ingreso_trimestral(df_ing, aglo, carpeta_salida):
    """
    df_ing debe contener:
    AGLOMERADO, ANO4, TRIMESTRE, INGRESO_REAL_PROM
    """

    df = df_ing[df_ing["AGLOMERADO"] == aglo].copy()
    df = df.sort_values(["ANO4", "TRIMESTRE"])

    df["PERIODO"] = crear_periodo(df)

    plt.figure(figsize=(12, 6))
    plt.plot(df["PERIODO"], df["INGRESO_REAL_PROM"], marker="o", color="green")

    plt.xticks(rotation=90)
    plt.ylabel("Ingreso real promedio (pesos constantes)")
    plt.xlabel("Período (AAAA-Tn)")
    plt.title(f"Ingreso real promedio trimestral - Aglomerado {aglo}")
    plt.grid(alpha=0.3)

    os.makedirs(carpeta_salida, exist_ok=True)
    path = os.path.join(carpeta_salida, f"ingreso_trimestral_{aglo}.png")
    path_final = versionar_archivo(path)

    plt.tight_layout()
    plt.savefig(path_final)
    plt.close()

    return path_final


# ==========================================================
#   Función principal: genera todos los gráficos
# ==========================================================

def generar_graficos(df_tasas, df_ing_trimestral, carpeta_salida="output/graficos"):
    """
    Genera:
    - gráfico de tasas para 31 y 34
    - gráfico de ingreso trimestral para 31 y 34
    """

    os.makedirs(carpeta_salida, exist_ok=True)

    aglos = [31, 34]
    paths = []

    for aglo in aglos:
        p1 = graficar_tasas(df_tasas, aglo, carpeta_salida)
        p2 = graficar_ingreso_trimestral(df_ing_trimestral, aglo, carpeta_salida)
        paths.extend([p1, p2])

    return paths
