# Fontes de dados

Arquivos brutos usados no projeto. Ficam em `data/raw/` (fora do git) e foram
baixados manualmente; nenhum script grava nessa pasta. O SHA-256 permite
verificar que cada membro do grupo está usando exatamente os mesmos arquivos:

```powershell
Get-ChildItem data\raw -Recurse -File | Get-FileHash -Algorithm SHA256
```

Recorte de teste (T3): retângulo lon −40,97 a −39,84, lat −10,00 a −8,61
(EPSG:4674/4326), que contém Petrolina-PE (2611101) e Juazeiro-BA (2918407).
Data de acesso de todos os arquivos: **23/11/2026**.

## PRODES Caatinga — INPE/TerraBrasilis

Polígonos de desmatamento por ano, obtidos do GeoServer do TerraBrasilis (WFS)
já filtrados pelo retângulo do recorte. CRS EPSG:4674.

| Arquivo (`data/raw/prodes/`) | Tamanho | SHA-256 |
|---|---|---|
| `yearly_deforestation.zip` | 13.505.718 B (12,9 MB) | `8e90e91066d2c395684fe1254f54f15e752d195fba36776018ce501b7753886b` |
| `accumulated_deforestation_2000.zip` | 11.431.697 B (10,9 MB) | `c45d504b7a589be05351b44bb43d3909cfd262a3e98e69f1ce5f508a8da04eea` |

URLs de origem (a segunda troca apenas o nome da camada):

```
https://terrabrasilis.dpi.inpe.br/geoserver/prodes-caatinga-nb/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=prodes-caatinga-nb:yearly_deforestation&bbox=-40.97,-10.0,-39.84,-8.61&outputFormat=SHAPE-ZIP
https://terrabrasilis.dpi.inpe.br/geoserver/prodes-caatinga-nb/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=prodes-caatinga-nb:accumulated_deforestation_2000&bbox=-40.97,-10.0,-39.84,-8.61&outputFormat=SHAPE-ZIP
```

Observações:
- `yearly_deforestation`: 30.855 polígonos; anos 2004, 2006, 2008, 2010, 2011,
  2013, 2014 e anual de 2016 a 2025 (não há 2015, então 2016 acumula dois anos).
- Imagens de cada ano *t* são de agosto a dezembro de *t*.
- `main_class` tem `DESMATAMENTO` e `RESERVATORIO` (área alagada por represa);
  só `DESMATAMENTO` é usado.
- `accumulated_deforestation_2000`: 7.884 polígonos, desmatamento até 2000.

## Focos de queimada — INPE/Programa Queimadas (BDQueimadas)

CSV anual do Brasil inteiro, apenas satélite de referência (Aqua, tarde), que é
o usado pelo INPE para comparar anos. Colunas: `id_bdq`, `foco_id`, `lat`,
`lon`, `data_pas` (UTC), `pais`, `estado`, `municipio`, `bioma`.

Origem: `https://dataserver-coids.inpe.br/queimadas/queimadas/focos/csv/anual/Brasil_sat_ref/<arquivo>`

| Arquivo (`data/raw/queimadas/`) | Tamanho | SHA-256 |
|---|---|---|
| `focos_br_ref_2014.zip` | 3.712.702 B (3,5 MB) | `db34a8c4bc4c1c77769a186f7d384bc0f866ce3699fa739c7cd34e2cd2048792` |
| `focos_br_ref_2015.zip` | 4.469.819 B (4,3 MB) | `72d1aac5db423d5226e0ba2efadb457c25df99fc3fdb5a3e7c271ebb69560d5e` |
| `focos_br_ref_2016.zip` | 3.782.229 B (3,6 MB) | `aa26dc356923f573eb80bb5bef1bfa9ff27423cd382e2cc240ab0cf2ee9be73b` |
| `focos_br_ref_2017.zip` | 4.088.867 B (3,9 MB) | `f1300f35c866ca7c2d699a3f806eba533d80272ab479a436005aa98451684d3c` |
| `focos_br_ref_2018.zip` | 5.278.250 B (5,0 MB) | `f6d6168071d365073a3ba7e277f9464739f3f502cc411c9f64399c4ea740390d` |
| `focos_br_ref_2019.zip` | 7.766.490 B (7,4 MB) | `58a6fe69d282d087822aade262826bf2139f2554781d0e37b672567369e4f733` |
| `focos_br_ref_2020.zip` | 8.786.351 B (8,4 MB) | `fba793aa304863445dad6d434dd57bd0e904d97f50d9652a729c30ddf8fb7686` |
| `focos_br_ref_2021.zip` | 7.623.094 B (7,3 MB) | `9edeb229c078b98df37d17b460bed74a0d13bd0688a530386ca815ba2f8a68e6` |
| `focos_br_ref_2022.zip` | 8.256.945 B (7,9 MB) | `75538cbfb99bbbe543cb786d7b8f7650537a1333327f8bf17cda7178c01878ea` |
| `focos_br_ref_2023.zip` | 7.458.410 B (7,1 MB) | `4cc635d1adf1a7f59d18640ff13a8779cb3b0f2aecbc867dacc86959d892b880` |
| `focos_br_ref_2024.zip` | 10.727.110 B (10,2 MB) | `a2cec2f67483a4a95956a471d5cbdb7b3cbd93b21c9b87c845a649ef89abf4e1` |

## MapBiomas Coleção 10 — cobertura e uso da terra

Exportado do Google Earth Engine com `src/data/gee_mapbiomas.js` (asset
`projects/mapbiomas-public/assets/brazil/lulc/v1`, `collection_id = 10`,
`version = v1`). Export levou 3 min (iniciado em 23/11/2026 23:25 BRT). GeoTIFF `uint8`, 10 bandas
`classification_2015` … `classification_2024`, EPSG:4326, grade nativa de
~30 m (0,000269°), 4194 × 5161 pixels. Licença CC-BY-4.0.

| Arquivo (`data/raw/mapbiomas/`) | Tamanho | SHA-256 |
|---|---|---|
| `mapbiomas_c10_petrolina_juazeiro_2015_2024.tif` | 9.029.347 B (8,6 MB) | `3cadb353a68137bead4c06b01ab2f4e0323fd49c1daffa42dd30f681c689bc9a` |

Citação: Souza et al. (2020). *Reconstructing Three Decades of Land Use and
Land Cover Changes in Brazilian Biomes with Landsat Archive and Earth Engine*.
Remote Sensing 12(17). https://doi.org/10.3390/rs12172735

## Grade e limites municipais — IBGE via geobr

Não fica em `data/raw/`: `src/data/grid_teste.py` baixa a malha municipal IBGE
2022 pelo pacote `geobr` (cache do próprio pacote) e gera
`data/interim/grade_teste.parquet`.
