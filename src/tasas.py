# src/tasas.py

import pandas as pd
import os

def calcular_tasas(df):
    """
    Calcula TA, TE, TD solo para personas de 18 años o más.
    """

    # Filtrar población objetivo
    df = df[df["CH06"] >= 18]

    poblacion = len(df)
    ocupados = (df["ESTADO"] == 1).sum()
    desocupados = (df["ESTADO"] == 2).sum()
    pea = ocupados + desocupados

    TA = pea / poblacion if poblacion > 0 else 0
    TE = ocupados / poblacion if poblacion > 0 else 0
    TD = desocupados / pea if pea > 0 else 0

    return {"TA": TA, "TE": TE, "TD": TD}



def tasas_trimestrales(df):
    """
    Calcula TA, TE y TD por trimestre para aglomerados, usando solo población >= 18 años.
    """

    resultados = []

    # Filtrar adultos
    df = df[df["CH06"] >= 18]

    for (aglo, ano, trim), grupo in df.groupby(["AGLOMERADO", "ANO4", "TRIMESTRE"]):
        tasas = calcular_tasas(grupo)
        resultados.append({
            "AGLOMERADO": aglo,
            "ANO4": ano,
            "TRIMESTRE": trim,
            "TA": tasas["TA"],
            "TE": tasas["TE"],
            "TD": tasas["TD"],
        })

    return pd.DataFrame(resultados)


def exportar_tasas(df, carpeta="output/tasas"):
    """
    Exporta tasas trimestrales en CSV y XLSX.
    """

    os.makedirs(carpeta, exist_ok=True)

    csv_path = os.path.join(carpeta, "tasas_trimestrales.csv")
    xlsx_path = os.path.join(carpeta, "tasas_trimestrales.xlsx")

    df.to_csv(csv_path, index=False)
    df.to_excel(xlsx_path, index=False)

    return csv_path, xlsx_path
