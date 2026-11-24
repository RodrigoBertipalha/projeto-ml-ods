# Decisões técnicas

Registro das escolhas de modelagem dos dados e por que foram feitas. Vale para
a tabela célula × ano (`src/data/features_teste.py`) e deve ser mantido na
versão regional (T7).

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
