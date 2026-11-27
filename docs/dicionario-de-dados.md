# Dicionário de dados

Base `data/processed/base_celula_ano.parquet`: uma linha por célula de 1 km ×
ano-alvo *t* (2017–2025). 101.502 linhas, 14 colunas, sem valores nulos.
Justificativa de cada janela temporal em [decisões técnicas](decisoes-tecnicas.md)
(D1–D11); origem dos arquivos em [fontes de dados](fontes-de-dados.md).

> Gerado por `src/data/dicionario.py` a partir da base com SHA-256
> `53204c087c38f4c468f3d05e22d0eebf66f94e2b7599525bcef487a6b566763a`. Não editar à mão: rodar o script de novo.

| Coluna | Tipo | Unidade | Faixa observada | Significado | Fonte | Referência temporal | Uso |
|---|---|---|---|---|---|---|---|
| `cell_id` | str | — | 11.278 valores distintos (ex.: `E0285_N9022`, `E0286_N9022`) | Célula de 1 km; canto inferior esquerdo em km no EPSG:31984 (E = leste, N = norte) | Grade do projeto (`src/data/grade.py`) | fixo | identificador — **não usar como atributo** |
| `ano` | int64 | ano | 2017 a 2025 (mediana 2021) | Ano-alvo *t* do rótulo | — | *t* | identificador — **não usar como atributo** (usar para separar treino/teste no tempo) |
| `code_muni` | int64 | — | 2 valores distintos (ex.: `2611101`, `2918407`) | Código IBGE do município que contém o centro da célula | IBGE, malha municipal 2022 (geobr) | fixo | identificador — **não usar como atributo** |
| `municipio` | str | — | 2 valores distintos (ex.: `Juazeiro`, `Petrolina`) | Nome do município | IBGE, malha municipal 2022 (geobr) | fixo | identificador — **não usar como atributo** |
| `uf` | str | — | 2 valores distintos (ex.: `BA`, `PE`) | Sigla da UF | IBGE, malha municipal 2022 (geobr) | fixo | identificador — **não usar como atributo** |
| `bloco_espacial` | str | — | 143 valores distintos (ex.: `B028_902`, `B029_899`) | Bloco de 10 × 10 km que contém a célula (D11) | Derivado da grade | fixo | identificador — **não usar como atributo** (usar para validação cruzada espacial) |
| `pct_veg_nativa_t2` | float64 | % | 0,00 a 100,00 (mediana 52,94) | Parte da célula com vegetação nativa (classes 3, 4, 5, 6, 11, 12, 32, 49, 50) | MapBiomas Col. 10 | ano civil t−2 (D3) | atributo |
| `focos_t1` | int32 | focos | 0 a 3 (mediana 0) | Focos de queimada dentro da célula | INPE/BDQueimadas, satélite de referência | 1º/ago t−2 a 31/jul t−1 (D2) | atributo |
| `focos_5km_t1` | int32 | focos | 0 a 28 (mediana 0) | Focos de queimada a até 5 km do centro da célula | INPE/BDQueimadas, satélite de referência | 1º/ago t−2 a 31/jul t−1 (D2, D7) | atributo |
| `chuva_t1_mm` | float32 | mm | 165,04 a 760,58 (mediana 417,84) | Chuva acumulada no pixel de 0,05° que contém o centro da célula | CHIRPS v2.0 diário | 1º/ago t−2 a 31/jul t−1 (D8) | atributo |
| `dist_via_principal_km` | float64 | km | 0,00 a 31,04 (mediana 5,71) | Distância do centro da célula à via principal mais próxima (motorway, trunk, primary, secondary) | OpenStreetMap (Geofabrik) | malha de 1º/jan/2020, fixa (D9) | atributo |
| `desmat_acum_t1` | float64 | fração (0–1) | 0,00 a 1,00 (mediana 0,08) | Parte da célula já desmatada (acumulado até 2000 + incrementos) | PRODES Caatinga | até t−1 | atributo |
| `alvo_t1` | int8 | 0/1 | 0: 94.539 / 1: 6.963 | 1 se houve ≥ 1 ha de incremento PRODES na célula em t−1 | PRODES Caatinga | t−1 (D10) | atributo; entrada do baseline de persistência |
| `alvo` | int8 | 0/1 | 0: 95.055 / 1: 6.447 | 1 se houve ≥ 1 ha de incremento PRODES na célula em *t* | PRODES Caatinga | *t* (D1, D4) | **variável-alvo** |

Identificadores servem para juntar tabelas, separar treino/teste (por `ano` e
por `bloco_espacial`) e analisar subgrupos; usá-los como atributo deixaria o
modelo decorar células, municípios ou anos.
