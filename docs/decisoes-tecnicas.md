# Decisões técnicas

Registro das escolhas de modelagem dos dados e por que foram feitas. D1–D5
vêm do teste da T3; D6–D10 da base completa (T7). Implementação em
`src/data/grade.py` e `src/features/construir_base.py`.

Notação: *t* é o ano do rótulo; atributos usam apenas informação anterior a *t*.

## Contexto temporal do PRODES Caatinga

Todas as imagens PRODES de um ano *t* são de **agosto a dezembro de *t***
(verificado em `image_date` no recorte de teste). Logo, o incremento do ano *t*
é o desmatamento ocorrido **entre a imagem de t−1 e a imagem de t**. As
decisões D2 e D3 partem disso: um atributo só é seguro se descreve o período
anterior a ago–dez de t−1.

## D1. Rótulos 2017–2025

**Decisão:** anos-alvo 2017 a 2025; 2016 fica fora.

**Justificativa:** no recorte, o PRODES Caatinga tem incrementos em 2004, 2006,
2008, 2010, 2011, 2013, 2014 e é anual só a partir de 2016. Não existe 2015,
então o incremento de 2016 acumula dois anos (1.865 polígonos contra 700–1.200
nos anos seguintes) e inflaria os positivos. Com 2017–2025 mantemos 9 anos de
rótulo, todos anuais; o PRODES 2025 já está publicado.

## D2. Focos de queimada na janela 1º/ago de t−2 a 31/jul de t−1

**Decisão:** `focos_t1` conta os focos do satélite de referência nessa janela
de 12 meses.

**Justificativa:** usar o ano civil t−1 incluiria focos de ago–dez de t−1, que
podem ser a própria queimada do desmatamento rotulado em *t* (vazamento
temporal). A janela termina antes de qualquer imagem PRODES do período do
rótulo. O satélite de referência (Aqua, tarde) é o usado pelo INPE para séries
temporais; somar todos os satélites tornaria os anos incomparáveis.

## D3. Vegetação nativa do MapBiomas de t−2

**Decisão:** `pct_veg_nativa_t2` usa o mapa MapBiomas Col. 10 do ano t−2
(2015–2023), não o de t−1.

**Justificativa:** o mapa anual de t−1 é feito com imagens do ano inteiro e
pode já mostrar uma derrubada de set–dez de t−1, que o PRODES registra no
rótulo de *t*. Isso seria um vazamento residual. O mapa de t−2 é totalmente
anterior ao período do rótulo. Custo: um ano a mais de defasagem no atributo.

**Classes de vegetação nativa:** 3, 4, 5, 6, 49 (florestais) e 11, 12, 32, 50
(não florestais). Afloramento rochoso (29), água e usos antrópicos não contam;
pixels sem dado (0) saem do denominador.

## D4. Rótulo positivo com ≥ 0,01 km² (1 ha) desmatado

**Decisão:** `alvo = 1` se a área de incremento PRODES dentro da célula no ano
*t* for ≥ 0,01 km².

**Justificativa:** 1 ha é a área mínima mapeável do PRODES. Com o critério
anterior (> 0), um polígono vizinho que encostava na célula gerava uma lasca de
poucos m² e virava positivo. Efeito no recorte: positivos caíram de 8,3% para
6,4% (cerca de 23% dos positivos eram lascas).

## D5. Fica para a T7

**Decisão:** focos em raio maior que a célula, chuva (CHIRPS) e distância a
estradas (OSM) não entram na T3.

**Justificativa:** a T3 é um teste do processo num recorte pequeno; a issue
pede ao menos 3 atributos + rótulo, já atendidos. `focos_t1` é esparso (0,6%
das células-ano têm foco), então contar focos num raio/vizinhança deve ser
avaliado com a região inteira. CHIRPS e OSM exigem downloads e cuidados
próprios (o OSM é um retrato atual, sem histórico, e precisa de tratamento
contra vazamento).

*Resolvida na T7: ver D7–D9.*

## D6. Base completa = recorte da T1 (Petrolina + Juazeiro)

**Decisão:** a base da T7 usa a mesma grade de 11.278 células da T3.

**Justificativa:** a T1 fechou o recorte final em Petrolina + Juazeiro. Os
scripts de teste foram promovidos (`grid_teste.py` → `grade.py`,
`features_teste.py` → `construir_base.py`) em vez de duplicados.

## D7. Focos num raio de 5 km (`focos_5km_t1`)

**Decisão:** além de `focos_t1` (dentro da célula), conta os focos a até 5 km
do centro da célula, na mesma janela da D2. Os focos são lidos com margem de
~33 km além do recorte, para não zerar artificialmente as células de borda.

**Justificativa:** dentro da célula só 0,5% das células-ano têm foco; no raio
de 5 km (~80 km²), 20,1%. Fogo na vizinhança indica pressão de uso na região
mesmo quando não cai na célula.

## D8. Chuva CHIRPS na janela da D2 (`chuva_t1_mm`)

**Decisão:** chuva acumulada (CHIRPS, 0,05°) de 1º/ago de t−2 a 31/jul de
t−1, lida no pixel que contém o centro da célula.

**Justificativa:** mesma janela dos focos, anterior ao período do rótulo. O
ano civil t−1 incluiria ago–dez de t−1, já dentro do período do rótulo. O
pixel (~5,5 km) é maior que a célula, então amostrar o centro basta.

## D9. Distância à via principal, malha OSM de jan/2020 (`dist_via_principal_km`)

**Decisão:** distância do centro da célula à via mais próxima entre
`motorway`, `trunk`, `primary` e `secondary` (e seus `_link`), na versão
Geofabrik de 1º/jan/2020, fixa para todos os anos. Vias lidas com margem de
~33 km além do recorte.

**Justificativa:** o OSM atual mede esforço de mapeamento e traz vazamento: no
recorte, o comprimento de vias mapeadas cresceu ×4,5 de 2016 a 2024
(terciárias/não classificadas ×16), enquanto as vias principais cresceram só
19% (consulta à ohsome API em 24/11/2026). Jan/2020 é a versão mais antiga na
Geofabrik; a API histórica (ohsome) recusou a extração de geometria (HTTP 403).

**Limitação:** para os rótulos 2017–2020 a malha é posterior ao período do
atributo. Como as vias principais cresceram ~15% de 2016 a 2020, o efeito é
pequeno, mas existe; citar na seção de limitações do artigo.

## D10. Rótulo do ano anterior (`alvo_t1`)

**Decisão:** inclui `alvo_t1` (≥ 1 ha de incremento PRODES em t−1).

**Justificativa:** é a entrada do baseline por persistência (T12) e um
atributo legítimo: o incremento de t−1 vem de imagens de ago–dez de t−1,
anteriores ao período do rótulo de t. Para t = 2017, `alvo_t1` usa o PRODES
2016, que acumula dois anos (D1); a taxa de `alvo_t1` em 2017 é, por isso,
maior.

## Colunas excluídas por vazamento

Calculadas ou disponíveis, mas **não** entram na base:

| Coluna/informação | Por que fica de fora |
|---|---|
| Área de incremento PRODES no ano *t* | É o próprio alvo em forma contínua; usada só para gerar `alvo` e descartada |
| Desmatamento acumulado até *t* | Contém o incremento de *t* |
| MapBiomas de t−1 e *t* | Podem já mostrar a derrubada rotulada em *t* (D3) |
| Focos e chuva de ago/t−1 em diante | Período do rótulo; podem ser a própria queimada do desmatamento (D2, D8) |
| Malha OSM atual | Vias mapeadas depois, inclusive as abertas para o desmatamento (D9) |
| Polígonos PRODES `RESERVATORIO` | Não são desmatamento (alagamento de represa) |

**Identificadores, não atributos:** `cell_id`, `ano`, `code_muni`,
`municipio`, `uf`. Servem para juntar tabelas, separar treino/teste no tempo
e no espaço e analisar subgrupos (T16); não devem entrar no modelo.

## Outras decisões de implementação

- **CRS de trabalho:** SIRGAS 2000 / UTM 24S (EPSG:31984), métrico, cobre o
  Sertão do São Francisco.
- **Grade de 1 km com origem alinhada a múltiplos de 1 km:** o mesmo `cell_id`
  e a mesma geometria na grade de teste e na regional.
- **Célula pertence ao município que contém seu centroide:** sem dupla
  contagem na divisa PE/BA; a soma das células reproduz a área IBGE (erro < 0,1%).
- **Polígonos PRODES `RESERVATORIO` excluídos:** são áreas alagadas por
  represas, não desmatamento.
- **`desmat_acum_t1`:** acumulado PRODES até 2000 + incrementos até t−1, como
  fração da célula (limitado a 1).
