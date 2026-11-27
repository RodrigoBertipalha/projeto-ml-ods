"""Gera docs/dicionario-de-dados.md a partir da base processada.

Tipo e faixa observada vêm do próprio parquet (não são digitados); unidade,
significado, fonte e referência temporal vêm de COLUNAS abaixo. Falha se a base
tiver coluna sem descrição ou se uma coluna descrita sumir da base.

Uso (na raiz do repositório, depois de construir_base.py):
    python src/data/dicionario.py
"""

import hashlib
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "data" / "processed" / "base_celula_ano.parquet"
SAIDA = ROOT / "docs" / "dicionario-de-dados.md"

ID = "identificador — **não usar como atributo**"

# coluna: (unidade, significado, fonte, referência temporal, uso)
COLUNAS = {
    "cell_id": ("—", "Célula de 1 km; canto inferior esquerdo em km no EPSG:31984 (E = leste, N = norte)",
                "Grade do projeto (`src/data/grade.py`)", "fixo", ID),
    "ano": ("ano", "Ano-alvo *t* do rótulo", "—", "*t*", ID + " (usar para separar treino/teste no tempo)"),
    "code_muni": ("—", "Código IBGE do município que contém o centro da célula",
                  "IBGE, malha municipal 2022 (geobr)", "fixo", ID),
    "municipio": ("—", "Nome do município", "IBGE, malha municipal 2022 (geobr)", "fixo", ID),
    "uf": ("—", "Sigla da UF", "IBGE, malha municipal 2022 (geobr)", "fixo", ID),
    "bloco_espacial": ("—", "Bloco de 10 × 10 km que contém a célula (D11)", "Derivado da grade", "fixo",
                       ID + " (usar para validação cruzada espacial)"),
    "pct_veg_nativa_t2": ("%", "Parte da célula com vegetação nativa (classes 3, 4, 5, 6, 11, 12, 32, 49, 50)",
                          "MapBiomas Col. 10", "ano civil t−2 (D3)", "atributo"),
    "focos_t1": ("focos", "Focos de queimada dentro da célula", "INPE/BDQueimadas, satélite de referência",
                 "1º/ago t−2 a 31/jul t−1 (D2)", "atributo"),
    "focos_5km_t1": ("focos", "Focos de queimada a até 5 km do centro da célula",
                     "INPE/BDQueimadas, satélite de referência", "1º/ago t−2 a 31/jul t−1 (D2, D7)", "atributo"),
    "chuva_t1_mm": ("mm", "Chuva acumulada no pixel de 0,05° que contém o centro da célula",
                    "CHIRPS v2.0 diário", "1º/ago t−2 a 31/jul t−1 (D8)", "atributo"),
    "dist_via_principal_km": ("km", "Distância do centro da célula à via principal mais próxima "
                              "(motorway, trunk, primary, secondary)", "OpenStreetMap (Geofabrik)",
                              "malha de 1º/jan/2020, fixa (D9)", "atributo"),
    "desmat_acum_t1": ("fração (0–1)", "Parte da célula já desmatada (acumulado até 2000 + incrementos)",
                       "PRODES Caatinga", "até t−1", "atributo"),
    "alvo_t1": ("0/1", "1 se houve ≥ 1 ha de incremento PRODES na célula em t−1",
                "PRODES Caatinga", "t−1 (D10)", "atributo; entrada do baseline de persistência"),
    "alvo": ("0/1", "1 se houve ≥ 1 ha de incremento PRODES na célula em *t*", "PRODES Caatinga",
             "*t* (D1, D4)", "**variável-alvo**"),
}


def milhar(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def faixa(serie: pd.Series) -> str:
    if pd.api.types.is_numeric_dtype(serie) and serie.name not in ("code_muni",):
        if serie.nunique() <= 2:
            return " / ".join(f"{v}: {milhar(n)}" for v, n in serie.value_counts().sort_index().items())
        casas = 0 if pd.api.types.is_integer_dtype(serie) else 2
        return f"{serie.min():.{casas}f} a {serie.max():.{casas}f} (mediana {serie.median():.{casas}f})".replace(".", ",")
    valores = serie.drop_duplicates().sort_values()
    exemplos = ", ".join(f"`{v}`" for v in valores.head(2))
    return f"{milhar(len(valores))} valores distintos (ex.: {exemplos})"


def main():
    base = pd.read_parquet(BASE)
    sem_descricao = set(base.columns) - set(COLUNAS)
    sumidas = set(COLUNAS) - set(base.columns)
    if sem_descricao or sumidas:
        raise SystemExit(f"Dicionário desatualizado. Sem descrição: {sorted(sem_descricao)}; "
                         f"fora da base: {sorted(sumidas)}")

    linhas = ["| Coluna | Tipo | Unidade | Faixa observada | Significado | Fonte | Referência temporal | Uso |",
              "|---|---|---|---|---|---|---|---|"]
    for col in base.columns:
        unidade, significado, fonte, referencia, uso = COLUNAS[col]
        linhas.append(f"| `{col}` | {base[col].dtype} | {unidade} | {faixa(base[col])} | "
                      f"{significado} | {fonte} | {referencia} | {uso} |")

    sha = hashlib.sha256(BASE.read_bytes()).hexdigest()
    texto = f"""# Dicionário de dados

Base `data/processed/base_celula_ano.parquet`: uma linha por célula de 1 km ×
ano-alvo *t* (2017–2025). {milhar(len(base))} linhas, {base.shape[1]} colunas, sem valores nulos.
Justificativa de cada janela temporal em [decisões técnicas](decisoes-tecnicas.md)
(D1–D11); origem dos arquivos em [fontes de dados](fontes-de-dados.md).

> Gerado por `src/data/dicionario.py` a partir da base com SHA-256
> `{sha}`. Não editar à mão: rodar o script de novo.

{chr(10).join(linhas)}

Identificadores servem para juntar tabelas, separar treino/teste (por `ano` e
por `bloco_espacial`) e analisar subgrupos; usá-los como atributo deixaria o
modelo decorar células, municípios ou anos.
"""
    SAIDA.write_text(texto, encoding="utf-8")
    print(f"{SAIDA.relative_to(ROOT)}: {base.shape[1]} colunas documentadas")


if __name__ == "__main__":
    main()
