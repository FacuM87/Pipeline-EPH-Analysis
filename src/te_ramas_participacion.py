"""
te_ramas_participacion.py

Participación del empleo por rama (Industria vs Turismo)
sobre el empleo total, por año y aglomerado.

Métrica:
    PART_RAMA(aglo, año, rama) =
        ocupados_en_rama(aglo, año) / ocupados_totales(aglo, año)

Usa:
- PP04B_COD: rama de actividad económica (CAES)
- PONDERA: factor de expansión
- ESTADO: condición de actividad (1 = ocupado)
- CH06: edad
- AGLOMERADO, ANO4

Definiciones de sector (CAES):

Industria:
    - Códigos CAES entre 1500 y 3999

Turismo:
    - Transporte / hoteles / restaurantes: 5000–5999
    - Actividades artísticas / culturales / recreativas: 9100–9499
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter


# ---------------------------------------------------------
# Utilidad general: versionado de archivos
# ---------------------------------------------------------

def versionar_archivo(path: str) -> str:
    """
    Si path existe:
        archivo.ext -> archivo_v2.ext -> archivo_v3.ext, etc.
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


# ---------------------------------------------------------
# Clasificación de ramas: Industria / Turismo
# ---------------------------------------------------------

def _clasificar_rama(pp04b_cod) -> str | None:
    """
    Recibe un código CAES (PP04B_COD) y devuelve:

        "Industria" | "Turismo" | None

    Industria:
        1500 <= código < 4000

    Turismo:
        5000 <= código < 6000   (transporte + hotelería/restaurantes)
        9100 <= código < 9500   (actividades artísticas / culturales / recreativas)
    """
    if pd.isna(pp04b_cod):
        return None

    try:
        c = int(pp04b_cod)
    except (TypeError, ValueError):
        return None

    # Industria manufacturera
    if 1500 <= c < 4000:
        return "Industria"

    # Transporte / almacenamiento / hoteles / restaurantes
    if 5000 <= c < 6000:
        return "Turismo"

    # Arte / cultura / entretenimiento / recreación
    if 9100 <= c < 9500:
        return "Turismo"

    return None


def agregar_columna_rama(df: pd.DataFrame) -> pd.DataFrame:
    """
    Agrega columna RAMA_TUR a partir de PP04B_COD,
    con valores: "Industria", "Turismo" o NaN.
    """
    df2 = df.copy()

    if "PP04B_COD" not in df2.columns:
        raise KeyError("No se encontró la columna 'PP04B_COD' en el DataFrame.")

    df2["RAMA_TUR"] = df2["PP04B_COD"].apply(_clasificar_rama)
    return df2


# ---------------------------------------------------------
# Participación del empleo por rama
# ---------------------------------------------------------

def participacion_empleo_por_rama(df: pd.DataFrame,
                                  aglos_target=None,
                                  edad_min: int = 18) -> pd.DataFrame:
    """
    Calcula la PARTICIPACIÓN del empleo por rama (Industria / Turismo)
    sobre el empleo total (ocupados), para cada aglomerado y año.

    Parámetros:
        df : DataFrame EPH limpia (NO solo ocupados),
             con columnas:
                - AGLOMERADO, ANO4, ESTADO, PONDERA, CH06, PP04B_COD
        aglos_target : lista de aglomerados (e.g. [31, 34])
        edad_min : edad mínima para considerar (default 18)

    Retorna:
        DataFrame con columnas:
            AGLOMERADO, ANO4, RAMA, OCUPADOS_RAMA, OCUPADOS_TOTALES, PART_RAMA
    """
    if aglos_target is not None:
        df = df[df["AGLOMERADO"].isin(aglos_target)].copy()
    else:
        df = df.copy()

    # Asegurar tipos
    df["ANO4"] = pd.to_numeric(df["ANO4"], errors="coerce")
    df["CH06"] = pd.to_numeric(df["CH06"], errors="coerce")
    df["PONDERA"] = pd.to_numeric(df["PONDERA"], errors="coerce")
    df["ESTADO"] = pd.to_numeric(df["ESTADO"], errors="coerce")

    # Población en edad de trabajar (18+)
    df = df[df["CH06"] >= edad_min]

    # Solo ocupados
    df_ocup = df[df["ESTADO"] == 1].copy()

    # Agregar columna de rama
    df_ocup = agregar_columna_rama(df_ocup)

    # -------------------------------------------------
    # Denominador: ocupados totales por aglo y año
    # -------------------------------------------------
    ocup_total = (
        df_ocup.groupby(["AGLOMERADO", "ANO4"], as_index=False)["PONDERA"]
               .sum()
               .rename(columns={"PONDERA": "OCUPADOS_TOTALES"})
    )

    # -------------------------------------------------
    # Numerador: ocupados por rama, aglo y año
    # -------------------------------------------------
    df_ocup_rama = df_ocup[df_ocup["RAMA_TUR"].notna()].copy()

    num = (
        df_ocup_rama.groupby(["AGLOMERADO", "ANO4", "RAMA_TUR"], as_index=False)["PONDERA"]
                    .sum()
                    .rename(columns={"PONDERA": "OCUPADOS_RAMA"})
    )

    # Merge numerador + denominador
    merged = num.merge(
        ocup_total,
        on=["AGLOMERADO", "ANO4"],
        how="left"
    )

    # Participación del empleo
    merged["PART_RAMA"] = merged["OCUPADOS_RAMA"] / merged["OCUPADOS_TOTALES"]

    merged = merged.rename(columns={"RAMA_TUR": "RAMA"})

    # Orden prolijo
    merged = merged[
        ["AGLOMERADO", "ANO4", "RAMA",
         "OCUPADOS_RAMA", "OCUPADOS_TOTALES", "PART_RAMA"]
    ]

    return merged


# ---------------------------------------------------------
# Exportar tabla de participación por rama
# ---------------------------------------------------------

def exportar_participacion_rama(df_part: pd.DataFrame,
                                carpeta_salida: str = "output/tasas") -> tuple[str, str]:
    """
    Exporta la tabla de participación por rama a CSV + XLSX con versionado.

    Retorna:
        (ruta_csv, ruta_xlsx)
    """
    os.makedirs(carpeta_salida, exist_ok=True)

    csv_path = os.path.join(carpeta_salida, "participacion_empleo_ramas.csv")
    xlsx_path = os.path.join(carpeta_salida, "participacion_empleo_ramas.xlsx")

    csv_path = versionar_archivo(csv_path)
    xlsx_path = versionar_archivo(xlsx_path)

    df_part.to_csv(csv_path, index=False)
    df_part.to_excel(xlsx_path, index=False)

    return csv_path, xlsx_path


# ---------------------------------------------------------
# Gráficos: barras anuales (Industria vs Turismo) por aglo
# ---------------------------------------------------------

def graficar_participacion_rama(df_part: pd.DataFrame,
                                carpeta_salida: str = "output/graficos") -> list[str]:
    """
    Genera, para cada aglomerado, un gráfico de barras por año:

    - Eje X: año (ANO4)
    - Eje Y: % del empleo total en cada rama
    - En cada año: dos barras → Industria y Turismo

    PART_RAMA se muestra en porcentaje (0–100).

    Retorna lista de paths de los PNG generados.
    """
    os.makedirs(carpeta_salida, exist_ok=True)
    paths = []

    for aglo, df_aglo in df_part.groupby("AGLOMERADO"):
        df_plot = df_aglo.pivot_table(
            index="ANO4",
            columns="RAMA",
            values="PART_RAMA"
        )

        # Aseguramos columnas en orden consistente
        for col in ["Industria", "Turismo"]:
            if col not in df_plot.columns:
                df_plot[col] = np.nan

        df_plot = df_plot[["Industria", "Turismo"]].sort_index()

        # Gráfico
        fig, ax = plt.subplots(figsize=(10, 6))

        anios = df_plot.index.values
        x = np.arange(len(anios))
        width = 0.35

        ax.bar(x - width/2, df_plot["Industria"], width, label="Industria")
        ax.bar(x + width/2, df_plot["Turismo"], width, label="Turismo")

        ax.set_title(f"Participación del empleo por rama - Aglomerado {aglo}")
        ax.set_xlabel("Año")
        ax.set_ylabel("Participación del empleo (%)")

        # Mostrar eje Y en porcentaje
        ax.yaxis.set_major_formatter(PercentFormatter(xmax=1))

        ax.set_xticks(x)
        ax.set_xticklabels(anios, rotation=45, ha="right")
        ax.grid(axis="y", linestyle="--", alpha=0.4)
        ax.legend()

        plt.tight_layout()

        fname = os.path.join(carpeta_salida, f"part_ramas_aglo_{aglo}.png")
        fname = versionar_archivo(fname)
        plt.savefig(fname, dpi=300)
        plt.close()

        paths.append(fname)

    return paths



# ---------------------------------------------------------
# Ejecución manual de prueba (opcional)
# ---------------------------------------------------------

if __name__ == "__main__":
    # Ejemplo mínimo de uso manual:
    # (asumiendo que ejecutás ESTE archivo parado en la carpeta TP/)
    eph_path = "data/EPH_datos_limpios_recortada.csv"  # o el archivo que estés usando

    if os.path.exists(eph_path):
        df_eph = pd.read_csv(eph_path, low_memory=False)

        # Solo aglos 31 y 34
        df_part = participacion_empleo_por_rama(df_eph, aglos_target=[31, 34])

        csv, xlsx = exportar_participacion_rama(df_part)
        print("Participación del empleo por rama exportada en:")
        print("  CSV :", csv)
        print("  XLSX:", xlsx)

        paths_png = graficar_participacion_rama(df_part)
        print("Gráficos generados:")
        for p in paths_png:
            print("  →", p)
    else:
        print(f"No se encontró {eph_path}. Ejecutar desde main.py o ajustar la ruta.")
