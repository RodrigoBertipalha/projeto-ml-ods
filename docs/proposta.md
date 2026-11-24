# Previsão de risco de desmatamento na Caatinga utilizando Machine Learning: um estudo em Petrolina (PE) e Juazeiro (BA)

## 1. ODS e justificativa

O projeto está vinculado à ODS 15 — Vida Terrestre, especialmente à meta 15.3, de combate à desertificação e recuperação de terras degradadas, e à meta 15.2, de combate ao desmatamento. A escolha justifica-se pela vulnerabilidade ambiental do semiárido, evidenciada pelo núcleo de desertificação de Cabrobó, e pela necessidade de ações preventivas de conservação da Caatinga.

## 2. Delimitação do problema

O estudo abrange Petrolina (PE) e Juazeiro (BA), utilizando células de 1 km², com rótulos de 2017 a 2025 e atributos temporalmente anteriores ao desfecho, conforme as decisões [D1 a D5](./decisoes-tecnicas.md). Serão considerados dados do PRODES, MapBiomas, queimadas, precipitação e estradas, sujeitos à avaliação de disponibilidade e vazamento. Excluem-se a fiscalização em tempo real, a identificação de infratores e a generalização para outros biomas.

## 3. Pergunta de pesquisa

Modelos de Machine Learning conseguem prever o risco anual de desmatamento em Petrolina e Juazeiro com desempenho em PR-AUC superior à linha de base por persistência?

## 4. Variável-alvo e tipo de aprendizado

Será utilizada classificação binária supervisionada desbalanceada, devido à disponibilidade de rótulos históricos e à proporção preliminar de 6,4% de positivos. O alvo será positivo (1) quando a célula apresentar incremento PRODES igual ou superior a 1 hectare (0,01 km²) no ano t, e negativo (0) abaixo desse limiar, considerando observações válidas.

## 5. Métrica de avaliação

A PR-AUC será a métrica primária por avaliar a relação entre precisão e revocação em dados desbalanceados, considerando tanto os gastos desnecessários de monitoramento quanto a não identificação de áreas ameaçadas. A acurácia isolada pode mascarar esses erros.

## 6. Público beneficiado e decisão operacional

O projeto busca apoiar órgãos ambientais e gestores públicos, beneficiando indiretamente as comunidades locais.

Se o modelo indicar risco de desmatamento igual ou superior ao limiar c, definido na validação, a equipe de monitoramento ambiental priorizará a análise da célula por imagens de satélite em até sete dias.

Falsos positivos geram gastos desnecessários de monitoramento; falsos negativos deixam áreas ameaçadas sem acompanhamento preventivo.

## 7. Riscos e limitações iniciais

Os riscos incluem desbalanceamento, qualidade dos dados, vazamento de informações e dependência espacial e temporal. Caso os modelos não superem o baseline ou apresentem baixa generalização, a estratégia será reavaliada. O modelo não deverá ser utilizado como evidência de infração ambiental.
