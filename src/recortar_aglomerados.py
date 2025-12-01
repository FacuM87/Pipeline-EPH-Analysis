"""
recortar_aglomerados.py

Genera un archivo reducido EPH_datos_limpios_31_34.csv
a partir del archivo completo EPH_datos_limpios.csv.

✔ Solo se genera si NO existe el recortado
✔ Reduce tamaño de ~1.9M filas → ~60–80k filas
✔ No afecta ningún cálculo posterior
✔ Deja el archivo listo para que main.py lo use

"""

import os
import pandas as pd


def generar_archivo_recortado(path_limpio, path_recortado, aglos=[31, 34]):
    """
    Genera un archivo reducido con solo aglomerados relevantes.
    Solo se ejecuta si el archivo recortado NO existe.

    Parámetros:
        path_limpio: ruta al archivo limpio completo
        path_recortado: ruta donde guardar el archivo reducido
        aglos: lista de aglomerados a conservar (default [31, 34])
    """

    # Si ya existe, NO lo generamos de nuevo
    if os.path.exists(path_recortado):
        print(f"✔ Archivo recortado ya existe: {path_recortado}")
        print("  → Se usará ese archivo en el pipeline.")
        return

    # Si no existe el archivo limpio completo → error
    if not os.path.exists(path_limpio):
        raise FileNotFoundError(
            f"❌ No se encontró {path_limpio}. "
            "Primero generá EPH_datos_limpios.csv con cleaning.py."
        )

    print("\n🔪 Generando archivo recortado SOLO para aglos 31 y 34...")

    # Cargar archivo limpio grande
    df = pd.read_csv(path_limpio, low_memory=False)
    print(f"  → Filas totales: {len(df)}")

    # Filtrar solo aglomerados indicados
    df_reduced = df[df["AGLOMERADO"].isin(aglos)].copy()
    print(f"  → Filas luego del recorte (aglos {aglos}): {len(df_reduced)}")

    # Guardar archivo reducido
    df_reduced.to_csv(path_recortado, index=False, encoding="utf-8")
    print(f"✔ Archivo recortado generado en: {path_recortado}\n")
