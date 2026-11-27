# Previsão de risco de desmatamento na Caatinga (ODS 15)

Projeto Integrador de Machine Learning — FACAPE, 2026.2.

## Configuração (uma vez por clone)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
git config core.hooksPath .githooks   # ativa o bloqueio de arquivos > 20 MB no commit
```

Os dados (`data/raw/`, `data/interim/`, `data/processed/`) nunca são versionados.

## Objetivo

O projeto está vinculado ao **ODS 15 — Vida Terrestre**, em especial às metas 15.2 (combate ao desmatamento) e 15.3 (combate à desertificação e recuperação de terras degradadas). Busca avaliar se modelos de aprendizado de máquina conseguem prever o risco anual de desmatamento em Petrolina (PE) e Juazeiro (BA) com PR-AUC superior à de uma linha de base por persistência.

A intenção é apoiar órgãos ambientais na priorização de células para análise por imagens de satélite, conforme um limiar definido na validação. Consulte a [proposta](docs/proposta.md) e as [decisões técnicas](docs/decisoes-tecnicas.md).

## Dados

O estudo utiliza células de 1 km² e rótulos anuais de 2017 a 2025. O alvo indica incremento de desmatamento PRODES de pelo menos 1 hectare na célula e no ano. As fontes utilizadas no recorte de teste são:

- **PRODES Caatinga (INPE/TerraBrasilis):** incrementos anuais e desmatamento acumulado.
- **MapBiomas Coleção 10:** cobertura e uso da terra; dados sob licença CC BY 4.0, exportados pelo Google Earth Engine.
- **Programa Queimadas (INPE):** focos de queimadas do satélite de referência.
- **IBGE, via geobr:** limites municipais para construção da grade.

A base completa acrescenta precipitação do **CHIRPS** e distância a vias principais do **OpenStreetMap**, com o controle de vazamento descrito nas [decisões técnicas](docs/decisoes-tecnicas.md). Origens, arquivos e hashes das fontes utilizadas estão em [fontes de dados](docs/fontes-de-dados.md); cada coluna da base está descrita no [dicionário de dados](docs/dicionario-de-dados.md).

### Licenças dos dados

A licença MIT do repositório vale para o código, não para os dados. Cada base mantém a sua:

| Base | Licença | Atribuição |
|---|---|---|
| PRODES Caatinga (INPE/TerraBrasilis) | CC BY-SA 4.0 | INPE, Programa BiomasBR/PRODES |
| Focos de queimada (INPE/BDQueimadas) | Dados abertos do INPE (licença específica não indicada na página de download) | INPE, Programa Queimadas |
| MapBiomas Coleção 10 | CC BY 4.0 | Projeto MapBiomas; Souza et al. (2020) |
| CHIRPS v2.0 | Domínio público (CC0) | Climate Hazards Center/UCSB; Funk et al. (2015) |
| OpenStreetMap (Geofabrik) | ODbL 1.0 | © OpenStreetMap contributors |
| Malha municipal (IBGE, via geobr) | Dados públicos do IBGE | IBGE |

A base derivada (`data/processed/`) herda as cláusulas de compartilhamento pela mesma licença do PRODES (CC BY-SA 4.0) e do OSM (ODbL) se for redistribuída.

**LGPD:** a base não contém dados pessoais. Cada linha é uma célula de terreno de 1 km² num ano, sem informação sobre proprietários, ocupantes ou qualquer pessoa identificável; por isso a LGPD (Lei 13.709/2018) não se aplica. A redistribuição da base processada como release aguarda confirmação do professor sobre as licenças de compartilhamento pela mesma licença.

## Estrutura do repositório

```text
configs/              Configurações do projeto
data/raw/             Dados brutos locais
data/processed/       Dados processados locais
src/data/             Obtenção e preparação dos dados
src/features/         Construção de atributos
src/models/           Modelagem
src/evaluation/       Avaliação
notebooks/            Análises exploratórias
experiments/          Registros de experimentos
reports/figures/      Figuras geradas
reports/tables/       Tabelas geradas
article/              Artigo
docs/                 Proposta, fontes e decisões técnicas
slides/               Apresentação
```

A estrutura completa exigida para a entrega também prevê arquivos de pipeline, experimentos, artigo e apresentação, a serem desenvolvidos nas respectivas tarefas.

## Reprodução

MapBiomas e CHIRPS são exportados manualmente no Google Earth Engine
([MapBiomas](src/data/gee_mapbiomas.js) e [CHIRPS](src/data/gee_chirps.js))
e copiados para `data/raw/mapbiomas/` e `data/raw/chirps/`. Os demais dados são
baixados e conferidos pelo script `src/data/download.py`, que cria apenas arquivos
ausentes e verifica seus hashes. Consulte [fontes de dados](docs/fontes-de-dados.md).

### Ambiente em contêiner

O Docker prepara o ambiente Python com dependências fixadas. A execução padrão
verifica as bibliotecas e informa a semente; o treinamento ainda será implementado
na T12/T13. Na raiz do projeto, com Docker instalado:

```bash
docker build -t projeto-ml .
docker run --rm projeto-ml
```

A semente padrão é `42` e pode ser alterada com `-e SEED=123`. A imagem não
inclui dados. Depois de obter os dados brutos, monte a pasta `data` para gerar a
grade e a base processada e preservá-las no computador:

```bash
docker run --rm -v "$(pwd)/data:/app/data" projeto-ml make data
```

`make data` executa `src/data/grade.py` e `src/features/construir_base.py`; a
malha municipal é baixada via `geobr`. Para obter as fontes e gerar o dicionário
fora do contêiner, consulte os comandos abaixo:

```bash
python src/data/download.py
python src/data/dicionario.py
```

`make train` e `make all` retornam erro até o treinamento ser implementado. A
redistribuição dos dados processados como release aguarda confirmação das licenças,
conforme a seção de dados; não há download automático dessa base nesta etapa.

## Resultados

A avaliação dos modelos e a comparação com a linha de base ainda serão realizadas. A métrica principal prevista é a PR-AUC.

## Limitações

O estudo se restringe a Petrolina e Juazeiro; não se propõe a generalizar para outros biomas nem a identificar infratores ou fiscalizar em tempo real. Entre os riscos estão o desbalanceamento, a qualidade dos dados, o vazamento de informações e a dependência espacial e temporal. O modelo não deve ser usado como evidência de infração ambiental.

## Integrantes

- Rodrigo Otavio Bertipalha de Paula Martins
- Pamela Cardoso Araujo
- Lucas Henrique Cipriano Lima
- Sebastião Araujo Rodrigues

## Licença

Este projeto está disponível sob a licença MIT; consulte [LICENSE](LICENSE).
