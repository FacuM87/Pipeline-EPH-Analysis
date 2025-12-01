import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as ctx
from matplotlib.ticker import FuncFormatter
import os

PATH_MAPA = "./data/aglomerados_eph.json"

NOMBRES = {
    31: "Ushuaia – Río Grande",
    34: "Mar del Plata – Batán"
}

# ==========================================================
#   VERSIONADO AUTOMÁTICO
# ==========================================================

def versionar_archivo(path):
    """Genera archivo.png → archivo_v2.png → archivo_v3.png ..."""
    if not os.path.exists(path):
        return path
    
    base, ext = os.path.splitext(path)
    version = 2

    while True:
        nuevo = f"{base}_v{version}{ext}"
        if not os.path.exists(nuevo):
            return nuevo
        version += 1


# ==========================================================

def cargar_mapa(path=PATH_MAPA):
    gdf = gpd.read_file(path)
    if gdf.crs is not None:
        gdf = gdf.to_crs(epsg=4326)
    return gdf

def unir_ingresos(gdf, df_ing):
    gdf["AGLOMERADO"] = gdf["eph_codagl"].astype(int)
    return gdf.merge(df_ing, on="AGLOMERADO", how="inner")

def generar_mapa_individual(gdf, aglo, vmin, vmax, output_name, carpeta_salida=None):

    sub = gdf[gdf["AGLOMERADO"] == aglo]
    sub_web = sub.to_crs(epsg=3857).dissolve()

    fig, ax = plt.subplots(figsize=(7, 7))

    sub_web.plot(
        column="INGRESO_REAL_PROM",
        cmap="viridis",
        legend=True,
        edgecolor="black",
        linewidth=1,
        vmin=vmin,
        vmax=vmax,
        ax=ax,
        alpha=0.6
    )

    ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik)

    nombre = NOMBRES.get(aglo, f"Aglomerado {aglo}")
    ax.set_title(f"Ingreso real promedio 2025\n{nombre}", fontweight="bold")
    ax.axis("off")

    cbar = ax.get_figure().axes[-1]
    cbar.yaxis.set_major_formatter(
        FuncFormatter(lambda x, pos: "$" + format(int(x), ",").replace(",", "."))
    )

    plt.tight_layout()

    if carpeta_salida:
        os.makedirs(carpeta_salida, exist_ok=True)
        output_name = os.path.join(carpeta_salida, output_name)

    # ==========================================================
    #   APLICAMOS VERSIONADO AQUÍ
    # ==========================================================
    output_name = versionar_archivo(output_name)

    plt.savefig(output_name, dpi=300, bbox_inches="tight")
    plt.close()

def generar_mapas(df_ingresos, carpeta_salida="output/mapas"):

    gdf = cargar_mapa()
    gdf = unir_ingresos(gdf, df_ingresos)

    vmin = df_ingresos["INGRESO_REAL_PROM"].min()
    vmax = df_ingresos["INGRESO_REAL_PROM"].max()

    generar_mapa_individual(gdf, 31, vmin, vmax, "mapa_2025_ing_real_31.png", carpeta_salida)
    generar_mapa_individual(gdf, 34, vmin, vmax, "mapa_2025_ing_real_34.png", carpeta_salida)

    return True
