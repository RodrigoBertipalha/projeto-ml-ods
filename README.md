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

A base completa acrescenta precipitação do **CHIRPS** e distância a vias principais do **OpenStreetMap**, com o controle de vazamento descrito nas [decisões técnicas](docs/decisoes-tecnicas.md). Origens, arquivos e hashes das fontes utilizadas estão em [fontes de dados](docs/fontes-de-dados.md). As licenças e bases legais das demais fontes ainda precisam ser documentadas; a licença do código do projeto não determina a licença dos datasets.

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

Com os arquivos de [fontes de dados](docs/fontes-de-dados.md) em `data/raw/` (conferir o SHA-256):

```powershell
python src/data/grade.py                 # data/interim/grade.parquet (11.278 células de 1 km)
python src/features/construir_base.py    # data/processed/base_celula_ano.parquet
```

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
