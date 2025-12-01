import os
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import pandas as pd
import numpy as np


def versionar_archivo(path):
    if not os.path.exists(path):
        return path

    base, ext = os.path.splitext(path)
    version = 2

    while True:
        newpath = f"{base}_v{version}{ext}"
        if not os.path.exists(newpath):
            return newpath
        version += 1


def calcular_univariado(df_ocup):
    """
    Calcula MEDIA, MEDIANA, Q25 y Q75 del ingreso real por aglomerado y período.
    """

    resultados = []

    df_ocup = df_ocup.copy()
    df_ocup["PERIODO"] = df_ocup["ANO4"].astype(str) + "-T" + df_ocup["TRIMESTRE"].astype(str)

    for (aglo, periodo), grupo in df_ocup.groupby(["AGLOMERADO", "PERIODO"]):
        x = grupo["INGRESO_REAL"].values
        w = grupo["PONDERA"].values

        # media ponderada
        mask = ~np.isnan(x) & (w > 0)
        if mask.sum() == 0:
            media = np.nan
        else:
            media = np.sum(x[mask] * w[mask]) / np.sum(w[mask])

        # percentiles ponderados (simple aproximado con repetición)
        dfp = pd.DataFrame({"x": x, "w": w}).dropna()
        dfp = dfp.loc[dfp["w"] > 0]

        if not dfp.empty:
            dfp_rep = dfp.loc[dfp.index.repeat(dfp["w"].astype(int))]
            mediana = dfp_rep["x"].median()
            q25 = dfp_rep["x"].quantile(0.25)
            q75 = dfp_rep["x"].quantile(0.75)
        else:
            mediana, q25, q75 = np.nan, np.nan, np.nan

        resultados.append({
            "AGLOMERADO": aglo,
            "PERIODO": periodo,
            "MEDIA": media,
            "MEDIANA": mediana,
            "Q25": q25,
            "Q75": q75
        })

    return pd.DataFrame(resultados)


def graficar_univariado(tabla_uni, aglo, nombre_aglo, carpeta_salida):
    """
    Genera un PNG con dos subplots:
    1) Media vs Mediana
    2) Q25 vs Q75
    """

    df = tabla_uni[tabla_uni["AGLOMERADO"] == aglo].copy()
    df = df.sort_values("PERIODO")

    fig, axes = plt.subplots(2, 1, figsize=(14, 8), sharex=True)
    fig.suptitle(f"Evolución del Ingreso Real en {nombre_aglo}", fontsize=16)

    # --- SUBPLOT 1: MEDIA vs MEDIANA ---
    axes[0].plot(df["PERIODO"], df["MEDIA"], label="Media", marker="o")
    axes[0].plot(df["PERIODO"], df["MEDIANA"], label="Mediana", marker="x")
    axes[0].set_title("Medidas de Tendencia Central")
    axes[0].set_ylabel("Ingreso Real (miles de pesos)")
    axes[0].grid(True, linestyle="--", alpha=0.4)
    axes[0].yaxis.set_major_formatter(lambda x, pos: f"{x/1000:,.0f}K")
    axes[0].legend()

    # --- SUBPLOT 2: Q25 vs Q75 ---
    axes[1].plot(df["PERIODO"], df["Q25"], label="Q25", marker="o")
    axes[1].plot(df["PERIODO"], df["Q75"], label="Q75", marker="x")
    axes[1].set_title("Medidas de Posición (Cuartiles)")
    axes[1].set_ylabel("Ingreso Real (miles de pesos)")
    axes[1].grid(True, linestyle="--", alpha=0.4)
    axes[1].yaxis.set_major_formatter(lambda x, pos: f"{x/1000:,.0f}K")
    axes[1].set_xticks(range(0, len(df["PERIODO"]), 4))
    axes[1].set_xticklabels(df["PERIODO"][::4], rotation=45, ha="right")
    axes[1].legend()

    outname = f"ingresos_univariado_aglo_{aglo}.png"
    outpath = os.path.join(carpeta_salida, outname)
    outpath = versionar_archivo(outpath)

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig(outpath, dpi=300)
    plt.close()

    return outpath


def generar_graficos_ingresos_univariados(df_ocup, carpeta_salida="output/graficos"):
    """
    Pipeline completo:
    1. calcular tabla univariada
    2. graficar dos subplots por aglomerado
    """

    os.makedirs(carpeta_salida, exist_ok=True)

    nombres = {
        31: "Ushuaia – Río Grande",
        34: "Mar del Plata – Batán"
    }

    tabla_uni = calcular_univariado(df_ocup)

    paths = []

    for aglo, nombre in nombres.items():
        p = graficar_univariado(tabla_uni, aglo, nombre, carpeta_salida)
        paths.append(p)

    return paths
