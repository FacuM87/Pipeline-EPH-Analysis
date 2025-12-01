import os
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd


def versionar_archivo(path):
    if not os.path.exists(path):
        return path

    base, ext = os.path.splitext(path)
    version = 2

    while True:
        new_path = f"{base}_v{version}{ext}"
        if not os.path.exists(new_path):
            return new_path
        version += 1


def limpiar_boxplot(df):
    """
    Limpieza específica para boxplot:
    - Confirmar columna INGRESO_REAL
    - Eliminar ingresos <= 0
    - Eliminar pondera <= 0
    - Quitar outliers extremos (percentil 99.5)
    - Filtrar edad >= 18 (si existe columna CH06)
    """

    df = df.copy()

    # 1) Detectar columna de ingreso real
    posibles = [c for c in df.columns if "ingreso" in c.lower() and "real" in c.lower()]
    if not posibles:
        raise ValueError("No se encontró la columna de ingreso real.")
    df = df.rename(columns={posibles[0]: "INGRESO_REAL"})

    # 2) Eliminar no válidos
    df = df[df["INGRESO_REAL"] > 0]
    df = df[df["PONDERA"] > 0]

    # 3) Excluir outliers extremos
    q995 = df["INGRESO_REAL"].quantile(0.995)
    df = df[df["INGRESO_REAL"] <= q995]

    # 4) Filtrar mayores de 18 si existe CH06
    if "CH06" in df.columns:
        df = df[df["CH06"] >= 18]

    return df


def generar_boxplot_ingresos(df_ocup, carpeta_salida="output/graficos"):

    df = limpiar_boxplot(df_ocup)

    nombres = {
        31: "Ushuaia – Río Grande",
        34: "Mar del Plata – Batán"
    }

    df["AGLOMERADO_DESC"] = df["AGLOMERADO"].map(nombres)

    plt.figure(figsize=(18, 8))
    sns.set_style("whitegrid")

    sns.boxplot(
        data=df,
        x="ANO4",
        y="INGRESO_REAL",
        hue="AGLOMERADO_DESC",
        palette="pastel",
        width=0.7,
        fliersize=3
    )

    plt.ylim(0, 6_000_000)

    # eje Y en millones
    plt.gca().yaxis.set_major_formatter(lambda x, pos: f"{x/1_000_000:.1f} M")

    plt.title("Distribución Anual de Ingresos Reales (Aglomerados 31 y 34)", fontsize=16)
    plt.xlabel("Año")
    plt.ylabel("Ingreso Real (en millones de pesos)")
    plt.xticks(rotation=45, ha="right")
    plt.grid(axis="y", linestyle="--", alpha=0.4)

    os.makedirs(carpeta_salida, exist_ok=True)
    filename = os.path.join(carpeta_salida, "boxplot_ingresos.png")
    final_path = versionar_archivo(filename)

    plt.tight_layout()
    plt.savefig(final_path, dpi=300)
    plt.close()

    return final_path
