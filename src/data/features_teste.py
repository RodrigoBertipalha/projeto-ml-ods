"""Monta a tabela célula × ano do recorte de teste (Petrolina/Juazeiro).

Para cada célula da grade e cada ano-alvo t (2017–2025):
    pct_veg_nativa_t2  % da célula com vegetação nativa no MapBiomas de t−2
    focos_t1           nº de focos (satélite de referência) de 1º/ago de t−2 a 31/jul de t−1
    desmat_acum_t1     fração da célula já desmatada no PRODES até t−1
    alvo               1 se a célula teve ≥ 0,01 km² (1 ha) de incremento PRODES no ano t

Justificativas em docs/decisoes-tecnicas.md.

Entradas: data/interim/grade_teste.parquet e data/raw/ (ver docs/fontes-de-dados.md).
Saída: data/interim/tabela_teste.parquet

Uso (na raiz do repositório):
    python src/data/features_teste.py
"""

import time
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.features import rasterize

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
GRADE = ROOT / "data" / "interim" / "grade_teste.parquet"
SAIDA = ROOT / "data" / "interim" / "tabela_teste.parquet"
MAPBIOMAS = RAW / "mapbiomas" / "mapbiomas_c10_petrolina_juazeiro_2015_2024.tif"

ANOS_ALVO = range(2017, 2026)  # 2016 fica de fora: sem PRODES 2015, o incremento de 2016 acumula 2 anos
BBOX = (-40.97, -10.0, -39.84, -8.61)  # recorte (lon/lat) usado nos downloads
LIMIAR_ALVO_KM2 = 0.01  # 1 ha, área mínima mapeável do PRODES; evita lascas de polígono na borda

# MapBiomas Col. 10: formações florestais (3, 4, 5, 6, 49) e não florestais
# (11, 12, 32, 50). Afloramento rochoso (29), água e usos antrópicos não contam.
VEG_NATIVA = [3, 4, 5, 6, 11, 12, 32, 49, 50]


def area_desmatada(grade) -> pd.DataFrame:
    """km² desmatados por célula e ano (PRODES), matriz cell_id × ano 2000–2025.

    Junta o acumulado até 2000 com os incrementos anuais e descarta polígonos
    RESERVATORIO (alagamento por represa, não é desmatamento).
    """
    partes = [gpd.read_file(f"zip://{RAW / 'prodes' / f}", columns=["main_class", "year"])
              for f in ("accumulated_deforestation_2000.zip", "yearly_deforestation.zip")]
    prodes = pd.concat(partes, ignore_index=True)
    prodes = prodes[prodes["main_class"] == "DESMATAMENTO"].to_crs(grade.crs)
    prodes["year"] = prodes["year"].astype(int)
    prodes.geometry = prodes.geometry.make_valid()

    pedacos = gpd.overlay(grade[["cell_id", "geometry"]], prodes[["year", "geometry"]],
                          how="intersection", keep_geom_type=True)
    pedacos["km2"] = pedacos.area / 1e6
    return (pedacos.pivot_table(index="cell_id", columns="year", values="km2",
                                aggfunc="sum", fill_value=0)
            .reindex(index=grade["cell_id"], columns=range(2000, max(ANOS_ALVO) + 1), fill_value=0))


def pct_vegetacao_nativa(grade) -> pd.DataFrame:
    """% de pixels de vegetação nativa por célula no MapBiomas do ano t−2.

    t−2 e não t−1: o mapa anual de t−1 pode já mostrar derrubadas de ago–dez
    de t−1, que o PRODES conta no rótulo de t (vazamento residual).

    Rasteriza o índice das células na grade do MapBiomas (cada pixel de 30 m
    vai para a célula que contém seu centro) e conta classes com bincount.
    Pixels sem dado (classe 0) ficam fora do denominador.
    """
    with rasterio.open(MAPBIOMAS) as src:
        celulas = grade.to_crs(src.crs)
        idx = rasterize(zip(celulas.geometry, range(1, len(celulas) + 1)),
                        out_shape=src.shape, transform=src.transform, fill=0, dtype="int32")
        linhas = []
        for t in ANOS_ALVO:
            classe = src.read(src.descriptions.index(f"classification_{t - 2}") + 1)
            valido = (idx > 0) & (classe > 0)
            total = np.bincount(idx[valido], minlength=len(celulas) + 1)[1:]
            nativa = np.bincount(idx[valido & np.isin(classe, VEG_NATIVA)],
                                 minlength=len(celulas) + 1)[1:]
            linhas.append(pd.DataFrame({"cell_id": celulas["cell_id"].to_numpy(), "ano": t,
                                        "pct_veg_nativa_t2": 100 * nativa / total}))
    return pd.concat(linhas, ignore_index=True)


def contar_focos(grade) -> pd.DataFrame:
    """Nº de focos por célula na janela de 1º/ago de t−2 a 31/jul de t−1.

    As imagens PRODES do ano t são de ago–dez de t, então o rótulo de t mede o
    desmatamento entre ago–dez de t−1 e ago–dez de t. A janela termina em
    31/jul de t−1, antes desse período: um foco que seja a própria queimada
    do desmatamento rotulado não entra como atributo (sem vazamento temporal).
    """
    anos_csv = range(min(ANOS_ALVO) - 2, max(ANOS_ALVO))
    focos = pd.concat(pd.read_csv(RAW / "queimadas" / f"focos_br_ref_{a}.zip",
                                  usecols=["lat", "lon", "data_pas"]) for a in anos_csv)
    focos = focos[focos["lon"].between(BBOX[0], BBOX[2]) & focos["lat"].between(BBOX[1], BBOX[3])]

    data = pd.to_datetime(focos["data_pas"])
    focos["ano"] = np.where(data.dt.month >= 8, data.dt.year + 2, data.dt.year + 1)

    pontos = gpd.GeoDataFrame(focos, geometry=gpd.points_from_xy(focos["lon"], focos["lat"]),
                              crs="EPSG:4326").to_crs(grade.crs)
    dentro = gpd.sjoin(pontos, grade[["cell_id", "geometry"]], predicate="within")
    return dentro.groupby(["cell_id", "ano"]).size().rename("focos_t1").reset_index()


def main():
    inicio = time.perf_counter()
    grade = gpd.read_parquet(GRADE)

    area = area_desmatada(grade)
    acumulado = area.cumsum(axis=1)
    prodes = pd.DataFrame({
        "cell_id": np.repeat(area.index.to_numpy(), len(ANOS_ALVO)),
        "ano": np.tile(list(ANOS_ALVO), len(area)),
        "desmat_acum_t1": acumulado[[t - 1 for t in ANOS_ALVO]].to_numpy().ravel().clip(max=1),
        "alvo": (area[list(ANOS_ALVO)].to_numpy().ravel() >= LIMIAR_ALVO_KM2).astype("int8"),
    })

    tabela = (prodes
              .merge(grade[["cell_id", "code_muni", "municipio", "uf"]], on="cell_id")
              .merge(pct_vegetacao_nativa(grade), on=["cell_id", "ano"])
              .merge(contar_focos(grade), on=["cell_id", "ano"], how="left"))
    tabela["focos_t1"] = tabela["focos_t1"].fillna(0).astype("int32")
    tabela = tabela[["cell_id", "ano", "code_muni", "municipio", "uf",
                     "pct_veg_nativa_t2", "focos_t1", "desmat_acum_t1", "alvo"]]

    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    tabela.to_parquet(SAIDA, index=False)

    resumo = tabela.groupby("ano")["alvo"].agg(celulas="size", positivos="sum", proporcao="mean")
    print(resumo.to_string(formatters={"proporcao": "{:.1%}".format}))
    print(f"Total: {tabela['alvo'].mean():.1%} positivos")
    print(tabela.drop(columns=["code_muni", "alvo", "ano"]).describe().round(3).to_string())
    print(f"{len(tabela)} linhas -> {SAIDA.relative_to(ROOT)} "
          f"({SAIDA.stat().st_size / 1e6:.2f} MB, {time.perf_counter() - inicio:.1f} s)")


if __name__ == "__main__":
    main()
