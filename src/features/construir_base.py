"""Monta a base célula × ano do projeto (Petrolina/Juazeiro, T7).

Para cada célula da grade e cada ano-alvo t (2017–2025):
    pct_veg_nativa_t2      % da célula com vegetação nativa no MapBiomas de t−2
    focos_t1               nº de focos (satélite de referência) na célula, de 1º/ago de t−2 a 31/jul de t−1
    focos_5km_t1           idem, num raio de 5 km do centro da célula
    chuva_t1_mm            chuva acumulada (CHIRPS) na mesma janela, no centro da célula
    dist_via_principal_km  distância do centro da célula à via principal mais próxima (OSM jan/2020)
    desmat_acum_t1         fração da célula já desmatada no PRODES até t−1
    alvo_t1                1 se houve ≥ 1 ha de incremento PRODES em t−1 (persistência, baseline T12)
    alvo                   1 se a célula teve ≥ 0,01 km² (1 ha) de incremento PRODES no ano t

Justificativas e colunas excluídas por vazamento em docs/decisoes-tecnicas.md.

Entradas: data/interim/grade.parquet e data/raw/ (ver docs/fontes-de-dados.md).
Saída: data/processed/base_celula_ano.parquet

Uso (na raiz do repositório):
    python src/features/construir_base.py
"""

import hashlib
import time
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import pyogrio
import rasterio
from rasterio.features import rasterize

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
GRADE = ROOT / "data" / "interim" / "grade.parquet"
SAIDA = ROOT / "data" / "processed" / "base_celula_ano.parquet"
MAPBIOMAS = RAW / "mapbiomas" / "mapbiomas_c10_petrolina_juazeiro_2015_2024.tif"
CHIRPS = RAW / "chirps" / "chirps_petrolina_juazeiro_t2017_2025.tif"
OSM = RAW / "osm" / "nordeste-200101.osm.pbf"

ANOS_ALVO = range(2017, 2026)  # 2016 fica de fora: sem PRODES 2015, o incremento de 2016 acumula 2 anos
BBOX = (-40.97, -10.0, -39.84, -8.61)  # recorte (lon/lat) usado nos downloads
LIMIAR_ALVO_KM2 = 0.01  # 1 ha, área mínima mapeável do PRODES; evita lascas de polígono na borda
RAIO_FOCOS_M = 5000
MARGEM_GRAUS = 0.3  # ~33 km além do recorte, para focos e vias logo após a borda

# MapBiomas Col. 10: formações florestais (3, 4, 5, 6, 49) e não florestais
# (11, 12, 32, 50). Afloramento rochoso (29), água e usos antrópicos não contam.
VEG_NATIVA = [3, 4, 5, 6, 11, 12, 32, 49, 50]

# Só vias principais: no recorte cresceram 19% no OSM de 2016 a 2024, contra
# ×16 das terciárias/não classificadas (esforço de mapeamento, não obra).
VIAS_PRINCIPAIS = ["motorway", "motorway_link", "trunk", "trunk_link",
                   "primary", "primary_link", "secondary", "secondary_link"]


def bbox_com_margem():
    xmin, ymin, xmax, ymax = BBOX
    return (xmin - MARGEM_GRAUS, ymin - MARGEM_GRAUS, xmax + MARGEM_GRAUS, ymax + MARGEM_GRAUS)


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


def carregar_focos(crs) -> gpd.GeoDataFrame:
    """Focos do satélite de referência com o ano-alvo t a que pertencem.

    Janela de 1º/ago de t−2 a 31/jul de t−1. As imagens PRODES do ano t são de
    ago–dez de t, então o rótulo de t mede o desmatamento entre ago–dez de t−1
    e ago–dez de t. A janela termina antes desse período: um foco que seja a
    própria queimada do desmatamento rotulado não entra como atributo.
    """
    xmin, ymin, xmax, ymax = bbox_com_margem()
    anos_csv = range(min(ANOS_ALVO) - 2, max(ANOS_ALVO))
    focos = pd.concat(pd.read_csv(RAW / "queimadas" / f"focos_br_ref_{a}.zip",
                                  usecols=["lat", "lon", "data_pas"]) for a in anos_csv)
    focos = focos[focos["lon"].between(xmin, xmax) & focos["lat"].between(ymin, ymax)]

    data = pd.to_datetime(focos["data_pas"])
    focos["ano"] = np.where(data.dt.month >= 8, data.dt.year + 2, data.dt.year + 1)
    focos = focos[focos["ano"].isin(ANOS_ALVO)]
    return gpd.GeoDataFrame(focos[["ano"]], geometry=gpd.points_from_xy(focos["lon"], focos["lat"]),
                            crs="EPSG:4326").to_crs(crs)


def contar_focos(grade, focos) -> pd.DataFrame:
    """Focos dentro da célula e num raio de RAIO_FOCOS_M do seu centro, por ano-alvo."""
    na_celula = (gpd.sjoin(focos, grade[["cell_id", "geometry"]], predicate="within")
                 .groupby(["cell_id", "ano"]).size().rename("focos_t1"))
    centros = grade[["cell_id"]].set_geometry(grade.centroid)
    no_raio = (gpd.sjoin(centros, focos, predicate="dwithin", distance=RAIO_FOCOS_M)
               .groupby(["cell_id", "ano"]).size().rename("focos_5km_t1"))
    return pd.concat([na_celula, no_raio], axis=1).reset_index()


def chuva(grade) -> pd.DataFrame:
    """Chuva CHIRPS (mm) no pixel de 0,05° que contém o centro da célula.

    A banda chuva_t{t} soma a chuva de 1º/ago de t−2 a 31/jul de t−1, a mesma
    janela dos focos. Pixel (~5,5 km) é maior que a célula, então amostrar o
    centro equivale a uma média ponderada.
    """
    with rasterio.open(CHIRPS) as src:
        centros = grade.centroid.to_crs(src.crs)
        valores = np.array(list(src.sample(zip(centros.x, centros.y))))
        bandas = [src.descriptions.index(f"chuva_t{t}") for t in ANOS_ALVO]
    return pd.DataFrame({
        "cell_id": np.repeat(grade["cell_id"].to_numpy(), len(ANOS_ALVO)),
        "ano": np.tile(list(ANOS_ALVO), len(grade)),
        "chuva_t1_mm": valores[:, bandas].ravel(),
    })


def distancia_via_principal(grade) -> pd.DataFrame:
    """Distância (km) do centro da célula à via principal mais próxima.

    Malha OSM de 1º/jan/2020, a versão mais antiga disponível na Geofabrik;
    fixa para todos os anos (limitação em docs/decisoes-tecnicas.md).
    """
    filtro = "highway IN ({})".format(", ".join(f"'{v}'" for v in VIAS_PRINCIPAIS))
    vias = pyogrio.read_dataframe(OSM, layer="lines", columns=["highway"],
                                  bbox=bbox_com_margem(), where=filtro).to_crs(grade.crs)
    centros = grade[["cell_id"]].set_geometry(grade.centroid)
    perto = gpd.sjoin_nearest(centros, vias, distance_col="dist_m").drop_duplicates("cell_id")
    return pd.DataFrame({"cell_id": perto["cell_id"], "dist_via_principal_km": perto["dist_m"] / 1000})


def sha256(caminho: Path) -> str:
    return hashlib.sha256(caminho.read_bytes()).hexdigest()


def main():
    inicio = time.perf_counter()
    grade = gpd.read_parquet(GRADE)

    # A área desmatada em t só gera o alvo e é descartada: nunca vira atributo.
    area = area_desmatada(grade)
    acumulado = area.cumsum(axis=1)
    anos_t1 = [t - 1 for t in ANOS_ALVO]
    prodes = pd.DataFrame({
        "cell_id": np.repeat(area.index.to_numpy(), len(ANOS_ALVO)),
        "ano": np.tile(list(ANOS_ALVO), len(area)),
        "desmat_acum_t1": acumulado[anos_t1].to_numpy().ravel().clip(max=1),
        "alvo_t1": (area[anos_t1].to_numpy().ravel() >= LIMIAR_ALVO_KM2).astype("int8"),
        "alvo": (area[list(ANOS_ALVO)].to_numpy().ravel() >= LIMIAR_ALVO_KM2).astype("int8"),
    })

    base = (prodes
            .merge(grade[["cell_id", "code_muni", "municipio", "uf"]], on="cell_id")
            .merge(pct_vegetacao_nativa(grade), on=["cell_id", "ano"])
            .merge(contar_focos(grade, carregar_focos(grade.crs)), on=["cell_id", "ano"], how="left")
            .merge(chuva(grade), on=["cell_id", "ano"])
            .merge(distancia_via_principal(grade), on="cell_id"))
    for col in ("focos_t1", "focos_5km_t1"):
        base[col] = base[col].fillna(0).astype("int32")
    base = base[["cell_id", "ano", "code_muni", "municipio", "uf",
                 "pct_veg_nativa_t2", "focos_t1", "focos_5km_t1", "chuva_t1_mm",
                 "dist_via_principal_km", "desmat_acum_t1", "alvo_t1", "alvo"]]
    assert len(base) == len(grade) * len(ANOS_ALVO) and not base.isna().any().any()

    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    base.to_parquet(SAIDA, index=False)

    resumo = base.groupby("ano")["alvo"].agg(celulas="size", positivos="sum", proporcao="mean")
    print(resumo.to_string(formatters={"proporcao": "{:.1%}".format}))
    print(f"Total: {base['alvo'].mean():.1%} positivos")
    print(base.drop(columns=["code_muni", "ano"]).describe().round(3).to_string())
    print(f"{len(base)} linhas -> {SAIDA.relative_to(ROOT)} "
          f"({SAIDA.stat().st_size / 1e6:.2f} MB, {time.perf_counter() - inicio:.1f} s)")
    print(f"SHA-256: {sha256(SAIDA)}")


if __name__ == "__main__":
    main()
