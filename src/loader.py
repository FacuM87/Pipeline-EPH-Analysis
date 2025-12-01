"""
Loader utilities for the TP - carga y normalización de datasets EPH / IPC / AGLOMERADOS.

Funciones públicas:
- load_raw_eph(folder): lee todos los txt (o csv) crudos en una carpeta y devuelve un DataFrame concatenado.
- load_clean_eph(path): lee el EPH_datos_limpios.csv ya generado.
- load_ipc(path): lee el csv del IPC y lo normaliza.
- load_aglomerados(path): lee el geojson de aglomerados.

Notas:
- Detecta separador entre ';' y ',' automáticamente para archivos crudos.
- Normaliza nombres de columnas a mayúsculas consistentes donde aplica (mantiene el estilo del dataset original).
- No hace limpieza profunda: eso queda en cleaning.py.
"""

from pathlib import Path
import pandas as pd
import numpy as np

DEFAULT_ENCODING = "latin1"

STANDARD_COLS_MAP = {
    "ANO4": "ANO4",
    "TRIMESTRE": "TRIMESTRE",
    "AGLOMERADO": "AGLOMERADO",
    "ESTADO": "ESTADO",
    "PONDERA": "PONDERA",
    "P47T": "P47T",
    "CH06": "CH06", 
}

def _detect_sep_and_read(path: str, encoding: str = DEFAULT_ENCODING) -> pd.DataFrame:
    """
    Intenta leer el archivo con separador ';' y ',' y devuelve el DataFrame leído.
    """
    for sep in [";", ","]:
        try:
            df = pd.read_csv(path, sep=sep, encoding=encoding, low_memory=False)

            if df.shape[1] > 3:
                return df
        except Exception:
            continue

    return pd.read_csv(path, encoding=encoding, low_memory=False)

def load_raw_eph(folder: str, pattern: str = "*.txt") -> pd.DataFrame:
    """
    Lee todos los archivos crudos de la carpeta `folder` (por defecto *.txt) y los concatena.
    No realiza limpieza de valores 9/99 ni filtrados: solo carga y normaliza nombres básicos.
    """
    folder = Path(folder)
    files = sorted(folder.glob(pattern))
    if not files:
        raise FileNotFoundError(f"No se encontraron archivos crudos en: {folder.resolve()} con patrón {pattern}")

    dfs = []
    for f in files:
        df = _detect_sep_and_read(str(f))

        # Normalizar nombres columna a mayúsculas sin espacios externos
        df.columns = [c.strip().upper() for c in df.columns]
        dfs.append(df)

    combined = pd.concat(dfs, ignore_index=True)
    # Intentar garantizar columnas importantes existen (si no, crearlas con NaN)
    for col in STANDARD_COLS_MAP.keys():
        if col not in combined.columns:
            combined[col] = np.nan

    return combined

def load_clean_eph(path: str) -> pd.DataFrame:
    """
    Lee un archivo EPH ya limpio (EPH_datos_limpios.csv).
    Normaliza nombres de columnas a mayúsculas estándar.
    """
    df = pd.read_csv(path, encoding=DEFAULT_ENCODING, low_memory=False)
    df.columns = [c.strip().upper() for c in df.columns]
    # Asegurar columnas clave existan
    for col in STANDARD_COLS_MAP.keys():
        if col not in df.columns:
            df[col] = np.nan
    return df

def load_ipc(path: str) -> pd.DataFrame:
    """
    Lee el deflator IPC y normaliza nombres de columnas esperadas.
    Espera columnas como ANO4, TRIMESTRE, IPC_INDEX (o IPC).
    """
    df = pd.read_csv(path, encoding=DEFAULT_ENCODING, low_memory=False)
    df.columns = [c.strip().upper() for c in df.columns]

    # Aceptar alias IPC_INDEX o IPC
    if "IPC_INDEX" in df.columns:
        df = df.rename(columns={"IPC_INDEX": "IPC"})
    elif "IPC" not in df.columns:
        raise KeyError("El archivo IPC no contiene la columna 'IPC_INDEX' ni 'IPC'.")

    # Asegurar ANO4 y TRIMESTRE presentes
    if "ANO4" not in df.columns or "TRIMESTRE" not in df.columns:
        raise KeyError("El archivo IPC debe contener 'ANO4' y 'TRIMESTRE'.")

    # Forzar tipos numéricos
    df["ANO4"] = pd.to_numeric(df["ANO4"], errors="coerce")
    df["TRIMESTRE"] = pd.to_numeric(df["TRIMESTRE"], errors="coerce")
    df["IPC"] = pd.to_numeric(df["IPC"], errors="coerce")

    return df

def load_aglomerados(path: str):
    """
    Lee el geojson de aglomerados con geopandas.
    Deja la columna EPH_CODAGL como mayúscula si existe.
    """
    import geopandas as gpd
    gdf = gpd.read_file(path)
    gdf.columns = [c.strip().upper() for c in gdf.columns]
    # Normalizar nombre de la columna de código de aglomerado si existe
    if "EPH_CODAGL" in gdf.columns:
        gdf = gdf.rename(columns={"EPH_CODAGL": "EPH_CODAGL"})
    return gdf
