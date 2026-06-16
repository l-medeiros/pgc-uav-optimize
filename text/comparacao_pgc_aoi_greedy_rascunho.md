# Comparação PGC x AoI-Greedy (rascunho)

Base para a discussão dos testes (a ser revisitada). Médias sobre 36 cenários
(6 contagens de sensor x 6 tamanhos de mapa) com 30 rodadas cada.

AoI-Greedy: a cada passo visita o sensor de maior AoI ainda viável (bateria +
slots), com desempate por proximidade. É a heurística construtiva mais alinhada
ao objetivo do PGC (maximizar AoI coletada).

## Números gerais

| Métrica | PGC | AoI-Greedy | Diferença |
|---|---|---|---|
| AoI coletada por rodada | 309,7 | 298,5 | PGC +3,7% (AoI-G chega muito perto) |
| AoI média final (menor = mais fresco) | 17,8 | 29,5 | PGC 40% menor |
| Energia final (J) | 44.943 | 64.571 | AoI-G gasta +43,7% |
| Distância total (m) | 1.933 | 1.719 | AoI-G 11% menor |
| Sensores visitados | 8,33 | 8,19 | empate (1,7%) |

## Tópicos

- O AoI-Greedy fica a apenas **-3,6%** do PGC em AoI coletada (298,5 vs 309,7): por ser construtivo e alinhado ao objetivo, quase alcança o ótimo nesta métrica.
- Em frescor (AoI média final) o PGC ainda lidera: **40% menor** (17,8 vs 29,5), mas o AoI-Greedy fica muito mais perto do PGC do que o NN.
- O ponto fraco do AoI-Greedy é **energia**: gasta **+43,7%** que o PGC (64.571 vs 44.943 J). Ele persegue AoI/frescor sem ponderar o custo energético.
- É exatamente aí que o PGC ganha: por ser multiobjetivo lexicográfico (minimiza energia e depois maximiza AoI), entrega quase a mesma AoI gastando bem menos.
- Nº de sensores visitados praticamente igual (8,33 vs 8,19): a diferença está na eficiência energética, não na cobertura.

## Figuras (text/figs/)

- `cmp_pgc_aoigreedy_overall_bars.png` barras de média geral nas 5 métricas.
- `cmp_pgc_aoigreedy_collected_aoi.png` AoI coletada vs tamanho do mapa, facetas por nº de sensores.
- `cmp_pgc_aoigreedy_avg_final_aoi.png` AoI média final vs tamanho do mapa, facetas por nº de sensores.
- `cmp_pgc_aoigreedy_energy.png` energia final vs tamanho do mapa, facetas por nº de sensores.
