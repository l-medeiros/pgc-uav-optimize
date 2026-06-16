# Comparação MILP x Nearest Neighbor (rascunho)

Base para a discussão dos testes (a ser revisitada). Médias sobre 36 cenários
(6 contagens de sensor x 6 tamanhos de mapa) com 30 rodadas cada.

## Números gerais

| Métrica | MILP | NN | Diferença |
|---|---|---|---|
| AoI coletada por rodada | 309,7 | 145,4 | MILP +113% (2,13x) |
| AoI média final (menor = mais fresco) | 17,8 | 127,2 | MILP 86% menor (NN 7,1x pior) |
| Energia final (J) | 44.943 | 48.711 | MILP 7,7% menor |
| Distância total (m) | 1.933 | 1.272 | NN 34% menor |
| Sensores visitados | 8,33 | 8,22 | empate (1,4%) |

## Tópicos

- O MILP coleta **+113%** de AoI por rodada (2,13x) que o NN.
- O MILP mantém a AoI média final **86% menor** (17,8 vs 127,2): dados muito mais frescos.
- O MILP ainda gasta **7,7% menos** energia que o NN.
- O NN só "vence" em distância percorrida (**-34%**), mas isso não é vantagem: ele retorna cedo à base e fica pairando nos slots restantes, andando menos porém coletando menos.
- Nº de sensores visitados é praticamente igual (8,33 vs 8,22): a diferença não está em *quantos* visita, e sim em *quanta AoI* extrai e em manter os dados frescos (revisitas).
- O NN degrada em mapas grandes com poucos sensores (1000x1000 com 5 e 10 sensores): a escolha gulosa estoura bateria/slots antes de cobrir bem o conjunto; o MILP se mantém estável.

## Figuras (text/figs/)

- `nn_overall_bars.png` — barras de média geral nas 5 métricas.
- `nn_collected_aoi.png` — AoI coletada vs tamanho do mapa, facetas por nº de sensores.
- `nn_avg_final_aoi.png` — AoI média final vs tamanho do mapa, facetas por nº de sensores.
- `nn_energy.png` — energia final vs tamanho do mapa, facetas por nº de sensores.
