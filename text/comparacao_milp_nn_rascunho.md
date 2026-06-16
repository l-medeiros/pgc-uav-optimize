# Comparação PGC x NN x AoI-Greedy (rascunho)

Base para a discussão dos testes (a ser revisitada). Médias sobre 36 cenários
(6 contagens de sensor x 6 tamanhos de mapa) com 30 rodadas cada.

## Números gerais

| Métrica | PGC | NN | AoI-Greedy |
|---|---|---|---|
| AoI coletada por rodada | 309,7 | 145,4 | 298,5 |
| AoI média final (menor = mais fresco) | 17,8 | 127,2 | 29,5 |
| Energia final (J) | 44.943 | 48.711 | 64.571 |
| Distância total (m) | 1.933 | 1.272 | 1.719 |
| Sensores visitados | 8,33 | 8,22 | 8,19 |

## Tópicos

- AoI coletada: AoI-Greedy fica a apenas **-4%** do PGC (298,5 vs 309,7) e coleta **+105%** que o NN. O NN fica **-53%** abaixo do PGC.
- Frescor (AoI média final): PGC é o melhor (17,8). AoI-Greedy fica próximo (29,5), bem melhor que o NN (127,2, ou **7,1x pior** que o PGC).
- Energia: aqui o AoI-Greedy é o pior, gasta **+43,7%** que o PGC (64.571 vs 44.943 J) e mais que o NN. Ele paga energia para perseguir sensores distantes e manter o frescor.
- Distância: NN percorre menos (1.272 m), seguido de AoI-Greedy (1.719) e PGC (1.933). Andar menos não é vantagem: o NN coleta pouco porque volta cedo à base.
- Sensores visitados: praticamente iguais nas três (cerca de 8,2 a 8,3). A diferença está em *quanta* AoI cada um extrai e em manter os dados frescos, não em *quantos* sensores visita.

## Leitura rápida

- O AoI-Greedy valida a hipótese do survey: por ser construtivo e alinhado ao objetivo, chega bem perto do PGC em AoI coletada e frescor.
- O preço do AoI-Greedy é energia: ele não otimiza o trade-off AoI x energia como o PGC (multiobjetivo lexicográfico), então gasta bem mais para um ganho marginal de AoI.
- Isso abre espaço para a próxima heurística (Score Greedy = AoI / distância), que tende a recuperar parte dessa eficiência energética.

## Figuras (text/figs/)

Cada figura traz as três curvas/barras (PGC azul, NN laranja, AoI-Greedy verde).

- `nn_overall_bars.png` barras de média geral nas 5 métricas.
- `nn_collected_aoi.png` AoI coletada vs tamanho do mapa, facetas por nº de sensores.
- `nn_avg_final_aoi.png` AoI média final vs tamanho do mapa, facetas por nº de sensores.
- `nn_energy.png` energia final vs tamanho do mapa, facetas por nº de sensores.
