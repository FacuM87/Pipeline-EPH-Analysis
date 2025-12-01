"""
Módulo de cálculo de ingreso real usando IPC.
Responsabilidades:
- Merge entre EPH limpia e IPC
- Cálculo de ingreso real para cada persona
- Filtrado de ocupados
- Preparación de DF para análisis geoespacial o comparaciones
"""

import pandas as pd
import numpy as np

from src.loader import load_ipc

def deflactar_ingreso(df_eph, ipc_df, ano_base=2025, trimestre_base=2):
    """
    Calcula ingreso real deflactado a un período base (ej: 2025-T2).
    Parámetros:
        df_eph: EPH limpia (DataFrame)
        ipc_df: DataFrame del IPC (load_ipc)
        ano_base: año base para deflactar (default=2025)
        trimestre_base: trimestre base (default=2)
    """
    df = df_eph.copy()

    # Asegurar columnas numéricas
    df["ANO4"] = pd.to_numeric(df["ANO4"], errors="coerce")
    df["TRIMESTRE"] = pd.to_numeric(df["TRIMESTRE"], errors="coerce")

    # Merge con IPC
    df = df.merge(
        ipc_df,
        how="left",
        on=["ANO4", "TRIMESTRE"]
    )

    # Obtener IPC del período base
    ipc_base = ipc_df[
        (ipc_df["ANO4"] == ano_base) &
        (ipc_df["TRIMESTRE"] == trimestre_base)
    ]["IPC"].iloc[0]

    # Calcular ingreso real
    df["INGRESO_REAL"] = df["P47T"] * (ipc_base / df["IPC"])

    return df


def filtrar_ocupados(df):
    """
    Filtra ocupados según variable ESTADO:
    - 1 = ocupado
    """
    return df[df["ESTADO"] == 1].copy()


def filtrar_adultos(df):
    """
    Filtra personas de 18 años o más.
    """
    if "CH06" in df.columns:
        return df[df["CH06"] >= 18].copy()
    return df


def ingreso_promedio_por_aglomerado(df, aglomerados_target=None):
    """
    Calcula ingreso real promedio (ponderado) por aglomerado.
    """

    if aglomerados_target is not None:
        df = df[df["AGLOMERADO"].isin(aglomerados_target)]

    def wmean(x, w):
        x, w = np.array(x, float), np.array(w, float)
        m = ~np.isnan(x) & (w > 0)
        return np.sum(x[m] * w[m]) / np.sum(w[m]) if m.any() else np.nan

    tabla = (
        df.groupby("AGLOMERADO")
          .apply(lambda t: wmean(t["INGRESO_REAL"], t["PONDERA"]))
          .reset_index()
          .rename(columns={0: "INGRESO_REAL_PROM"})
    )

    return tabla


# --- Función principal que se usará desde main.py ---

def calcular_ingresos(df_eph, ipc_path, ano_base=2025, trimestre_base=2, aglos=None):
    """
    Pipeline completo para:
    1) cargar IPC
    2) deflactar
    3) filtrar ocupados
    4) retornar df con ingreso real
    5) retornar tabla con ingreso por aglomerado
    """

    ipc_df = load_ipc(ipc_path)

    # 1) Deflactar
    df_defl = deflactar_ingreso(df_eph, ipc_df, ano_base, trimestre_base)

    # 2) Filtrar solo adultos (aplica a todos los análisis posteriores)
    df_defl = filtrar_adultos(df_defl)

    # 3) Filtrar ocupados (entre adultos)
    df_ocup = filtrar_ocupados(df_defl)


    tabla_aglo = ingreso_promedio_por_aglomerado(df_ocup, aglos)

    # NUEVO: tabla trimestral para gráficos 2016–2025
    tabla_aglo_trim = ingreso_promedio_trimestral_por_aglomerado(df_ocup, aglos)

    return df_defl, df_ocup, tabla_aglo, tabla_aglo_trim



def ingreso_promedio_trimestral_por_aglomerado(df, aglomerados_target=None):
    """
    Calcula ingreso real promedio trimestral (ponderado) por aglomerado.
    Devuelve: AGLOMERADO | ANO4 | TRIMESTRE | INGRESO_REAL_PROM
    """

    if aglomerados_target is not None:
        df = df[df["AGLOMERADO"].isin(aglomerados_target)]

    def wmean(x, w):
        x, w = np.array(x, float), np.array(w, float)
        m = ~np.isnan(x) & (w > 0)
        return np.sum(x[m] * w[m]) / np.sum(w[m]) if m.any() else np.nan

    tabla = (
        df.groupby(["AGLOMERADO", "ANO4", "TRIMESTRE"], group_keys=False)
          .apply(lambda t: wmean(t["INGRESO_REAL"], t["PONDERA"]))
          .reset_index()
          .rename(columns={0: "INGRESO_REAL_PROM"})
          .sort_values(["AGLOMERADO", "ANO4", "TRIMESTRE"])
    )

    return tabla


if __name__ == "__main__":
    print("Este módulo no se ejecuta solo. Usar desde main.py")
