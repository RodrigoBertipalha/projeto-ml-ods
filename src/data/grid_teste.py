"""Gera a grade de 1 km do recorte de teste (Petrolina-PE e Juazeiro-BA).

Saída: data/interim/grade_teste.parquet (GeoParquet, EPSG:31984) com
cell_id, code_muni, municipio, uf, geometry.

Uso (na raiz do repositório):
    python src/data/grid_teste.py
"""

import time
from pathlib import Path

import geobr
import geopandas as gpd
import numpy as np
import shapely

ROOT = Path(__file__).resolve().parents[2]
SAIDA = ROOT / "data" / "interim" / "grade_teste.parquet"

MUNICIPIOS = [2611101, 2918407]  # Petrolina-PE, Juazeiro-BA (códigos IBGE)
ANO_MALHA = 2022                 # malha municipal IBGE usada pelo geobr
CRS = "EPSG:31984"               # SIRGAS 2000 / UTM 24S: métrico, cobre o Sertão do S. Francisco
TAM = 1000                       # lado da célula, em metros


def carregar_municipios() -> gpd.GeoDataFrame:
    """Baixa os limites oficiais (geobr/IBGE) e reprojeta para UTM."""
    muni = geobr.read_municipality(code_muni=MUNICIPIOS, year=ANO_MALHA,
                                   simplified=False, show_progress=False)
    muni = muni.to_crs(CRS)
    muni["code_muni"] = muni["code_muni"].astype("int64")
    return muni[["code_muni", "name_muni", "abbrev_state", "geometry"]].rename(
        columns={"name_muni": "municipio", "abbrev_state": "uf"})


def gerar_grade(limites: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Cria células de TAM x TAM m cobrindo a extensão dos limites.

    A origem é arredondada para múltiplos de TAM, então a grade fica alinhada
    a uma malha fixa do CRS: a mesma célula terá a mesma geometria e o mesmo
    cell_id quando a grade for gerada para a região inteira (T7).
    """
    xmin, ymin, xmax, ymax = limites.total_bounds
    xs = np.arange(np.floor(xmin / TAM) * TAM, xmax, TAM)
    ys = np.arange(np.floor(ymin / TAM) * TAM, ymax, TAM)
    x0, y0 = (a.ravel() for a in np.meshgrid(xs, ys))

    # cell_id = canto inferior esquerdo em km (ex.: "E0325_N9035")
    ids = [f"E{x // TAM:04.0f}_N{y // TAM:04.0f}" for x, y in zip(x0, y0)]
    return gpd.GeoDataFrame({"cell_id": ids},
                            geometry=shapely.box(x0, y0, x0 + TAM, y0 + TAM),
                            crs=CRS)


def filtrar_por_centroide(grade, limites) -> gpd.GeoDataFrame:
    """Mantém só células cujo centroide cai dentro de um município.

    Cada célula fica com exatamente um município (sem dupla contagem na
    divisa PE/BA) e a soma das células aproxima a área real do recorte.
    """
    centroides = grade.set_geometry(grade.centroid)
    dentro = gpd.sjoin(centroides, limites, how="inner", predicate="within")
    dentro = dentro.drop_duplicates("cell_id")  # salvaguarda p/ centroide na divisa
    sel = grade.merge(dentro[["cell_id", "code_muni", "municipio", "uf"]], on="cell_id")
    return sel[["cell_id", "code_muni", "municipio", "uf", "geometry"]]


def main():
    inicio = time.perf_counter()
    limites = carregar_municipios()
    grade = filtrar_por_centroide(gerar_grade(limites), limites)

    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    grade.to_parquet(SAIDA, index=False)

    area_km2 = limites.set_index("municipio").area / 1e6
    resumo = grade.groupby("municipio").size().to_frame("celulas")
    resumo["area_ibge_km2"] = area_km2.round(0)
    print(resumo.to_string())
    print(f"Total: {len(grade)} células -> {SAIDA.relative_to(ROOT)} "
          f"({SAIDA.stat().st_size / 1e6:.2f} MB, {time.perf_counter() - inicio:.1f} s)")


if __name__ == "__main__":
    main()
