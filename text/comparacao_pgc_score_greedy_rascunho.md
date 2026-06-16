# Comparação PGC x Score-Greedy (rascunho)

Base para a discussão dos testes (a ser revisitada). Médias sobre 36 cenários
(6 contagens de sensor x 6 tamanhos de mapa) com 30 rodadas cada.

Score-Greedy: a cada passo visita o sensor de maior razão AoI/distância ainda
viável (bateria + slots), com desempate por proximidade. É a variante da
AoI-Greedy que pondera urgência e custo de deslocamento.

## Números gerais

| Métrica | PGC | Score-Greedy | Diferença |
|---|---|---|---|
| AoI coletada por rodada | 309,7 | 300,5 | PGC +3,1% (Score-G chega muito perto) |
| AoI média final (menor = mais fresco) | 17,8 | 28,5 | PGC 38% menor |
| Energia final (J) | 44.943 | 57.738 | Score-G gasta +28,5% |
| Distância total (m) | 1.933 | 1.502 | Score-G 22% menor |
| Sensores visitados | 8,33 | 8,24 | empate (1,1%) |

## Tópicos

- O Score-Greedy fica a apenas **-3,0%** do PGC em AoI coletada (300,5 vs 309,7): praticamente empata na métrica-alvo.
- Em frescor o PGC ainda lidera (**38% menor**: 17,8 vs 28,5), mas o Score-Greedy fica muito perto.
- O Score-Greedy gasta **+28,5%** de energia que o PGC. Continua perdendo em eficiência, porém bem menos que a AoI-Greedy.
- Distância: o Score-Greedy anda **22% menos** que o PGC, refletindo a ponderação por proximidade no critério de escolha.

## Score-Greedy x AoI-Greedy

A razão AoI/distância recupera eficiência sem perder coleta:

- AoI coletada: **+0,7%** (300,5 vs 298,5), praticamente igual.
- Energia: **-10,6%** (57.738 vs 64.571 J).
- Distância: **-12,6%** (1.502 vs 1.719 m).
- Frescor: ligeiramente melhor (28,5 vs 29,5).

Ou seja, o Score-Greedy domina a AoI-Greedy: mesma AoI coletada por menos energia
e menos distância. É a melhor heurística do conjunto e a mais próxima do PGC.

## Figuras (text/figs/)

- `cmp_pgc_scoregreedy_overall_bars.png` barras de média geral nas 5 métricas.
- `cmp_pgc_scoregreedy_collected_aoi.png` AoI coletada vs tamanho do mapa, facetas por nº de sensores.
- `cmp_pgc_scoregreedy_avg_final_aoi.png` AoI média final vs tamanho do mapa, facetas por nº de sensores.
- `cmp_pgc_scoregreedy_energy.png` energia final vs tamanho do mapa, facetas por nº de sensores.
