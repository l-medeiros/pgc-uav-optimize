# Comparação em larga escala — heurísticas onde o MILP não é tratável (rascunho)

> Rascunho de trabalho. Ainda **não** incorporado ao texto da tese.

## Contexto

Cenários de larga escala gerados para avaliar as heurísticas construtivas em instâncias nas quais o modelo exato (MILP/Gurobi) deixa de ser tratável. O número de variáveis binárias do MILP cresce com N²·T (N = sensores + base, T = slots), e observou-se que a partir de **30 sensores em mapa 1000×1000 m** o solver já fica muito lento / trava dentro do `TimeLimit` de 60 s. Toda a grade abaixo está, portanto, além da região viável do MILP e é resolvida apenas pelas heurísticas.

**Parâmetros:** Parrot Anafi USA; `SLOT_DURATION = 10 s`; `TIME_SLOTS = 20`; `BATTERY_MAX = 141.372 J`; 30 rodadas por cenário (AoI encadeada entre rodadas).

**Grade:** n ∈ {50, 75, 100, 150, 200} sensores × L ∈ {600, 800, 1000} m (posições uniformes, seed fixa — ver `generate_large_scenarios.py`).

## Tempo de execução

Tempo de parede por rodada (mediana das 30), **incluindo a inicialização do interpretador Python (~25–30 ms)** — ou seja, é um teto; o algoritmo em si é mais rápido. Comparar com o MILP, que nessas escalas não retorna solução dentro dos 60 s.

| Cenário | NN | AoI-Greedy | Score-Greedy |
|---|---|---|---|
| P50-600 | 28 ms | 29 ms | 32 ms |
| P50-800 | 29 ms | 29 ms | 32 ms |
| P50-1000 | 30 ms | 30 ms | 30 ms |
| P75-600 | 31 ms | 32 ms | 32 ms |
| P75-800 | 31 ms | 32 ms | 32 ms |
| P75-1000 | 32 ms | 32 ms | 33 ms |
| P100-600 | 36 ms | 34 ms | 36 ms |
| P100-800 | 35 ms | 33 ms | 35 ms |
| P100-1000 | 33 ms | 33 ms | 34 ms |
| P150-600 | 43 ms | 41 ms | 41 ms |
| P150-800 | 43 ms | 42 ms | 41 ms |
| P150-1000 | 42 ms | 41 ms | 41 ms |
| P200-600 | 48 ms | 49 ms | 49 ms |
| P200-800 | 49 ms | 50 ms | 50 ms |
| P200-1000 | 49 ms | 53 ms | 50 ms |

Todas as heurísticas resolvem cada rodada em algumas dezenas de milissegundos até n = 200, contra o MILP que não conclui em 60 s a partir de ~30 sensores.

## Métricas médias (30 rodadas)

### collected_aoi (maior = melhor)

| Cenário | NN | AoI-Greedy | Score-Greedy |
|---|---|---|---|
| P50-600 | 159,3 | **853,8** | 837,3 |
| P50-800 | 159,3 | **852,7** | 809,3 |
| P50-1000 | 159,3 | 702,7 | **735,8** |
| P75-600 | 159,3 | **1.219,3** | 1.178,0 |
| P75-800 | 159,3 | **1.191,7** | 1.128,8 |
| P75-1000 | 159,3 | 960,6 | **975,8** |
| P100-600 | 159,3 | **1.540,8** | 1.514,1 |
| P100-800 | 159,3 | **1.528,8** | 1.381,5 |
| P100-1000 | 159,3 | **1.246,2** | 1.084,6 |
| P150-600 | 159,3 | **2.051,8** | 1.691,4 |
| P150-800 | 159,3 | **2.029,8** | 1.570,8 |
| P150-1000 | 159,3 | **1.692,9** | 1.363,6 |
| P200-600 | 159,3 | **2.386,9** | 1.701,9 |
| P200-800 | 159,3 | **2.356,0** | 1.615,5 |
| P200-1000 | 159,3 | **2.099,3** | 1.464,0 |

### avg_final_aoi (menor = melhor)

| Cenário | NN | AoI-Greedy | Score-Greedy |
|---|---|---|---|
| P50-600 | 243,11 | **49,90** | 58,75 |
| P50-800 | 243,11 | **52,33** | 63,26 |
| P50-1000 | 243,11 | 92,47 | **80,76** |
| P75-600 | 260,24 | **72,67** | 90,27 |
| P75-800 | 260,24 | **76,98** | 102,56 |
| P75-1000 | 260,24 | **114,53** | 118,27 |
| P100-600 | 268,81 | **93,82** | 114,83 |
| P100-800 | 268,81 | **95,03** | 135,95 |
| P100-1000 | 268,81 | **125,69** | 156,87 |
| P150-600 | 277,37 | **131,23** | 170,76 |
| P150-800 | 277,37 | **132,11** | 181,94 |
| P150-1000 | 277,37 | **154,36** | 188,64 |
| P200-600 | 281,65 | **162,13** | 204,62 |
| P200-800 | 281,65 | **162,91** | 203,87 |
| P200-1000 | 281,65 | **170,54** | 212,66 |

### energy_final (menor = melhor)

| Cenário | NN | AoI-Greedy | Score-Greedy |
|---|---|---|---|
| P50-600 | **34.273** | 59.732 | 49.045 |
| P50-800 | **29.741** | 87.116 | 69.843 |
| P50-1000 | **53.501** | 114.947 | 94.369 |
| P75-600 | **30.465** | 53.417 | 42.961 |
| P75-800 | **38.688** | 96.217 | 62.831 |
| P75-1000 | **36.695** | 102.120 | 85.922 |
| P100-600 | **30.571** | 54.606 | 41.935 |
| P100-800 | **31.271** | 83.274 | 55.187 |
| P100-1000 | **35.868** | 101.778 | 66.477 |
| P150-600 | **30.500** | 51.534 | 40.087 |
| P150-800 | **31.061** | 84.264 | 48.645 |
| P150-1000 | **33.452** | 92.498 | 53.249 |
| P200-600 | **30.882** | 52.237 | 35.168 |
| P200-800 | **30.344** | 78.373 | 43.721 |
| P200-1000 | **30.296** | 94.245 | 49.386 |

### total_distance (maior = melhor)

| Cenário | NN | AoI-Greedy | Score-Greedy |
|---|---|---|---|
| P50-600 | 909 | **1.744** | 1.321 |
| P50-800 | 920 | **2.402** | 1.701 |
| P50-1000 | 1.778 | **3.104** | 2.242 |
| P75-600 | 623 | **1.443** | 1.121 |
| P75-800 | 1.044 | **2.225** | 1.488 |
| P75-1000 | 1.202 | **2.626** | 1.965 |
| P100-600 | 511 | **1.422** | 968 |
| P100-800 | 643 | **1.776** | 1.226 |
| P100-1000 | 959 | **2.542** | 1.524 |
| P150-600 | 529 | **1.261** | 904 |
| P150-800 | 568 | **1.765** | 1.070 |
| P150-1000 | 764 | **2.259** | 1.255 |
| P200-600 | 395 | **1.147** | 699 |
| P200-800 | 650 | **1.640** | 1.054 |
| P200-1000 | 620 | **1.958** | 1.142 |

### Sensores visitados por rodada

Constante em **9** para as três heurísticas em todos os 15 cenários. O gargalo não é o número de sensores, e sim `TIME_SLOTS = 20`: cada coleta consome cerca de 2 slots (deslocamento + *hover*), mais o retorno à base, o que limita o número de visitas por rodada independentemente de haver 50 ou 200 sensores disponíveis. Aumentar `n` amplia o *pool* de sensores desatualizados que uma heurística sensível à AoI pode explorar, mas não aumenta quantas coletas cabem na janela de tempo.

## Observações (contagem de melhores por cenário, de 15)

| Heurística | AoI coletada | AoI final (frescor) | Energia |
|---|---|---|---|
| NN | 0 | 0 | 15 |
| AoI-Greedy | 13 | 14 | 0 |
| Score-Greedy | 2 | 1 | 0 |

## Leitura dos resultados

- **Tempo:** todas as heurísticas concluem cada rodada em dezenas de milissegundos até n = 200, enquanto o MILP não retorna solução dentro dos 60 s nessas escalas. Esse é o ponto central: as heurísticas viabilizam instâncias fora do alcance do modelo exato.
- **NN não escala em qualidade:** por ignorar a AoI e revisitar sempre os sensores mais próximos, coleta uma AoI praticamente constante (~159) e mantém a pior AoI final, independentemente de `n`. Em compensação, é sempre o de menor energia (visita vizinhos).
- **AoI-Greedy domina a coleta e o frescor:** vence a AoI coletada em 13/15 e a AoI final em 14/15, e o ganho cresce com `n` (mais sensores desatualizados para priorizar). O custo é a maior energia, pois busca sensores distantes de alta AoI sem ponderar deslocamento.
- **Score-Greedy é o equilíbrio:** fica próximo do AoI-Greedy em coleta, porém com energia sensivelmente menor (pondera AoI por distância), ao custo de um frescor um pouco pior.
- **Gargalo de slots:** com `TIME_SLOTS = 20`, o número de coletas por rodada satura em ~9. Aumentar a densidade de sensores beneficia apenas as heurísticas sensíveis à AoI, que passam a ter mais alvos relevantes para escolher dentro do mesmo orçamento de visitas.

