"""
Módulo de limpieza de datos EPH.
Genera EPH_datos_limpios.csv a partir de los archivos crudos.

Responsabilidades:
- Cargar datos crudos usando loader.load_raw_eph()
- Estandarizar nombres y tipos
- Convertir valores de no respuesta (9 / 99 / -1) a NaN
- Corregir ingresos negativos
- Crear columna PERIODO (ANO4-Tn)
- Exportar CSV limpio solo si no existe
"""

import numpy as np
import pandas as pd
from pathlib import Path
from src.loader import load_raw_eph

# Variables para reemplazar valores de no respuesta
NO_RESPUESTA = {9, 99, -1}

# Algunas columnas donde 9 y 99 significan NA
COLS_CON_NA = [
    "CH04", "CH05", "CH06", "CH07", "CH08",
    "CAT_OCUP", "CAT_INAC",
    "PP04A", "PP04B_COD", "P47T"
]

NUMERIC_COLS = [
    "ANO4", "TRIMESTRE", "AGLOMERADO", "PONDERA",
    "ESTADO", "CH06", "P47T"
]


def _convert_numeric(df):
    """Convierte columnas numéricas usando coerces y corrige negativos en ingresos."""
    for col in NUMERIC_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Ingresos negativos → NaN
    if "P47T" in df.columns:
        df.loc[df["P47T"] < 0, "P47T"] = np.nan

    return df


def _replace_no_respuesta(df):
    """Convierte códigos de no respuesta (9 / 99 / -1) a NaN en columnas relevantes."""
    for col in COLS_CON_NA:
        if col in df.columns:
            df[col] = df[col].replace(list(NO_RESPUESTA), np.nan)
    return df


def _create_period_column(df):
    """Crea PERIODO en formato 'AAAA-Tn'."""
    if "ANO4" in df.columns and "TRIMESTRE" in df.columns:
        df["PERIODO"] = df["ANO4"].astype(int).astype(str) + "-T" + df["TRIMESTRE"].astype(int).astype(str)
    else:
        df["PERIODO"] = np.nan
    return df


def generar_eph_limpia(input_folder, output_file, force=False):
    """
    Genera EPH_datos_limpios.csv si no existe o si force=True.

    Pasos:
    1. Cargar data cruda
    2. Normalizar columnas
    3. Limpiar NA
    4. Convertir numéricos
    5. Crear columna PERIODO
    6. Exportar CSV
    """

    output_file = Path(output_file)

    # Si ya existe y force=False → no se regenera
    if output_file.exists() and not force:
        print(f"→ Archivo ya existe, no se regenera: {output_file}")
        return

    print("\n=== Generando EPH limpia ===")
    print("Cargando data cruda...")

    df = load_raw_eph(input_folder)

    print(f"Filas cargadas: {len(df)}")
    print(f"Columnas: {len(df.columns)}")

    # Reemplazar códigos de no respuesta
    print("Aplicando limpieza de NA...")
    df = _replace_no_respuesta(df)

    # Convertir tipos
    print("Convirtiendo columnas numéricas...")
    df = _convert_numeric(df)

    # Crear PERIODO
    print("Creando columna PERIODO...")
    df = _create_period_column(df)

    # Exportar limpio
    print(f"Guardando archivo limpio en: {output_file}")
    df.to_csv(output_file, index=False, encoding="utf-8")

    print("✔ EPH limpia generada correctamente.\n")


# Para pruebas manuales:
if __name__ == "__main__":
    generar_eph_limpia("data/data_cruda/", "data/EPH_datos_limpios.csv")
