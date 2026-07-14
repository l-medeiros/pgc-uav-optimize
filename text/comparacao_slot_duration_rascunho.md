# Efeito da duração do slot (Δt) em mapas grandes — heurísticas (rascunho)

> Rascunho de trabalho. Ainda **não** incorporado ao texto da tese.

## Contexto e mecanismo

O custo energético de um deslocamento é `P(V)·Δt` com `V = d/Δt`. O termo de arrasto parasita domina em alta velocidade e escala com `d³/Δt²`: **aumentar Δt reduz a energia de movimento** para uma mesma distância (voa-se mais devagar). Em contrapartida, o *hover* custa `P(0)·Δt` por slot, então **a energia de existência cresce linearmente com Δt**. Como a missão ocupa `TIME_SLOTS` slots (o UAV paira quando não se desloca), há um **teto de viabilidade**: se o simples pairar durante todos os slots já excede a bateria, nenhuma trajetória é viável.

Para a configuração do Parrot Anafi USA (`P(0) ≈ 168,5 W`, `TIME_SLOTS = 20` → 19 transições, `BATTERY_MAX = 141.372 J`), esse teto fica em **Δt ≈ 44,2 s**: acima disso, `(TIME_SLOTS−1)·P(0)·Δt > BATTERY_MAX` e a missão é inviável mesmo sem se mover.

## Piso de energia (só hover) por Δt

| Δt (s) | V p/ cruzar 1000 m | hover/slot (J) | piso (19 transições, kJ) | % bateria |
|---|---|---|---|---|
| 10 | 100 m/s | 1.685 | 32,0 | 23% |
| 20 | 50 m/s | 3.370 | 64,0 | 45% |
| 30 | 33 m/s | 5.055 | 96,0 | 68% |
| 40 | 25 m/s | 6.740 | 128,1 | 91% |
| 50 | 20 m/s | 8.424 | 160,1 | 113% ✗ inviável |

## AoI-Greedy: métricas vs Δt (média de 30 rodadas)

### P50-600

| Δt (s) | Visitados | AoI coletada | Energia (kJ) | % bateria |
|---|---|---|---|---|
| 10 | 9,0 | 853,8 | 59,7 | 42% |
| 20 | 9,0 | 853,8 | 66,2 | 47% |
| 30 | 9,0 | 853,8 | 92,9 | 66% |
| 40 | 9,0 | 853,8 | 122,9 | 87% |
| 50 | 0,0 ⚠️ | 0,0 | 160,1 | 113% |

### P50-800

| Δt (s) | Visitados | AoI coletada | Energia (kJ) | % bateria |
|---|---|---|---|---|
| 10 | 9,0 | 852,7 | 87,1 | 62% |
| 20 | 9,0 | 853,8 | 75,4 | 53% |
| 30 | 9,0 | 853,8 | 96,4 | 68% |
| 40 | 9,0 | 853,8 | 124,3 | 88% |
| 50 | 0,0 ⚠️ | 0,0 | 160,1 | 113% |

### P50-1000

| Δt (s) | Visitados | AoI coletada | Energia (kJ) | % bateria |
|---|---|---|---|---|
| 10 | 9,0 | 702,7 | 114,9 | 81% |
| 20 | 9,0 | 853,8 | 97,1 | 69% |
| 30 | 9,0 | 853,8 | 103,6 | 73% |
| 40 | 9,0 | 853,8 | 126,6 | 90% |
| 50 | 0,0 ⚠️ | 0,0 | 160,1 | 113% |

### P50-2000

| Δt (s) | Visitados | AoI coletada | Energia (kJ) | % bateria |
|---|---|---|---|---|
| 10 | 9,0 | 229,2 | 105,6 | 75% |
| 20 | 9,0 | 358,0 | 127,1 | 90% |
| 30 | 9,0 | 513,7 | 128,6 | 91% |
| 40 | 9,0 | 478,8 | 129,9 | 92% |
| 50 | 0,0 ⚠️ | 0,0 | 160,1 | 113% |

### P50-4000

| Δt (s) | Visitados | AoI coletada | Energia (kJ) | % bateria |
|---|---|---|---|---|
| 10 | 2,0 | 34,9 | 69,5 | 49% |
| 20 | 5,0 | 87,8 | 108,7 | 77% |
| 30 | 8,0 | 141,3 | 131,3 | 93% |
| 40 | 8,0 | 141,3 | 137,5 | 97% |
| 50 | 0,0 ⚠️ | 0,0 | 160,1 | 113% |

### P100-600

| Δt (s) | Visitados | AoI coletada | Energia (kJ) | % bateria |
|---|---|---|---|---|
| 10 | 9,0 | 1.540,8 | 54,6 | 39% |
| 20 | 9,0 | 1.540,8 | 66,0 | 47% |
| 30 | 9,0 | 1.540,8 | 93,6 | 66% |
| 40 | 9,0 | 1.540,8 | 123,9 | 88% |
| 50 | 0,0 ⚠️ | 0,0 | 160,1 | 113% |

### P100-800

| Δt (s) | Visitados | AoI coletada | Energia (kJ) | % bateria |
|---|---|---|---|---|
| 10 | 9,0 | 1.528,8 | 83,3 | 59% |
| 20 | 9,0 | 1.540,8 | 77,5 | 55% |
| 30 | 9,0 | 1.540,8 | 98,2 | 69% |
| 40 | 9,0 | 1.540,8 | 125,9 | 89% |
| 50 | 0,0 ⚠️ | 0,0 | 160,1 | 113% |

### P100-1000

| Δt (s) | Visitados | AoI coletada | Energia (kJ) | % bateria |
|---|---|---|---|---|
| 10 | 9,0 | 1.246,2 | 101,8 | 72% |
| 20 | 9,0 | 1.540,8 | 98,4 | 70% |
| 30 | 9,0 | 1.540,8 | 107,8 | 76% |
| 40 | 9,0 | 1.540,8 | 129,6 | 92% |
| 50 | 0,0 ⚠️ | 0,0 | 160,1 | 113% |

### P100-2000

| Δt (s) | Visitados | AoI coletada | Energia (kJ) | % bateria |
|---|---|---|---|---|
| 10 | 9,0 | 357,0 | 109,4 | 77% |
| 20 | 9,0 | 652,9 | 123,6 | 87% |
| 30 | 9,0 | 952,7 | 122,6 | 87% |
| 40 | 9,0 | 940,5 | 138,9 | 98% |
| 50 | 0,0 ⚠️ | 0,0 | 160,1 | 113% |

### P100-4000

| Δt (s) | Visitados | AoI coletada | Energia (kJ) | % bateria |
|---|---|---|---|---|
| 10 | 4,0 | 70,1 | 128,3 | 91% |
| 20 | 5,0 | 87,8 | 96,4 | 68% |
| 30 | 7,0 | 123,4 | 107,6 | 76% |
| 40 | 7,0 | 123,4 | 125,2 | 89% |
| 50 | 0,0 ⚠️ | 0,0 | 160,1 | 113% |

### P200-600

| Δt (s) | Visitados | AoI coletada | Energia (kJ) | % bateria |
|---|---|---|---|---|
| 10 | 9,0 | 2.386,9 | 52,2 | 37% |
| 20 | 9,0 | 2.386,9 | 66,3 | 47% |
| 30 | 9,0 | 2.386,9 | 94,5 | 67% |
| 40 | 9,0 | 2.386,9 | 125,0 | 88% |
| 50 | 0,0 ⚠️ | 0,0 | 160,1 | 113% |

### P200-800

| Δt (s) | Visitados | AoI coletada | Energia (kJ) | % bateria |
|---|---|---|---|---|
| 10 | 9,0 | 2.356,0 | 78,4 | 55% |
| 20 | 9,0 | 2.386,9 | 73,1 | 52% |
| 30 | 9,0 | 2.386,9 | 97,1 | 69% |
| 40 | 9,0 | 2.386,9 | 126,0 | 89% |
| 50 | 0,0 ⚠️ | 0,0 | 160,1 | 113% |

### P200-1000

| Δt (s) | Visitados | AoI coletada | Energia (kJ) | % bateria |
|---|---|---|---|---|
| 10 | 9,0 | 2.099,3 | 94,2 | 67% |
| 20 | 9,0 | 2.386,9 | 83,4 | 59% |
| 30 | 9,0 | 2.386,9 | 102,8 | 73% |
| 40 | 9,0 | 2.386,9 | 128,3 | 91% |
| 50 | 0,0 ⚠️ | 0,0 | 160,1 | 113% |

### P200-2000

| Δt (s) | Visitados | AoI coletada | Energia (kJ) | % bateria |
|---|---|---|---|---|
| 10 | 9,0 | 721,2 | 103,3 | 73% |
| 20 | 9,0 | 1.334,4 | 119,0 | 84% |
| 30 | 9,0 | 1.620,0 | 122,0 | 86% |
| 40 | 9,0 | 1.518,5 | 135,5 | 96% |
| 50 | 0,0 ⚠️ | 0,0 | 160,1 | 113% |

### P200-4000

| Δt (s) | Visitados | AoI coletada | Energia (kJ) | % bateria |
|---|---|---|---|---|
| 10 | 8,6 | 308,2 | 119,7 | 85% |
| 20 | 9,0 | 524,3 | 110,9 | 78% |
| 30 | 9,0 | 590,3 | 121,4 | 86% |
| 40 | 9,0 | 544,2 | 130,1 | 92% |
| 50 | 0,0 ⚠️ | 0,0 | 160,1 | 113% |

## Comparação entre heurísticas (energia em kJ, cenário P100-2000)

| Δt (s) | NN | AoI-Greedy | Score-Greedy |
|---|---|---|---|
| 10 | 47,9 | 109,4 | 108,2 |
| 20 | 63,0 | 123,6 | 102,7 |
| 30 | 92,0 | 122,6 | 113,0 |
| 40 | 123,2 | 138,9 | 132,5 |
| 50 | 160,1 | 160,1 | 160,1 |

## Leitura dos resultados

- **Δt reduz a energia de movimento:** para o mesmo caminho, subir de Δt=10 s para 20–30 s corta o consumo (voo mais lento, menos arrasto), e as velocidades ficam realistas (50–33 m/s para cruzar 1000 m, contra 100 m/s a Δt=10 s), atacando a limitação de velocidades irreais do modelo.
- **Mas há um teto por causa do hover:** a energia de existência cresce com Δt e, acima de **~44 s**, pairar durante a missão já estoura a bateria. A Δt=50 s as heurísticas colapsam para 0 visitas.
- **Existe um ponto ótimo intermediário** (em torno de Δt=20–30 s nesta configuração): energia de movimento já bastante reduzida e velocidades realistas, sem que o custo de hover domine. Δt é, portanto, uma alavanca útil para mapas grandes, porém limitada.
- **Não altera a tratabilidade do MILP:** Δt muda apenas os coeficientes de energia, não o número de variáveis (≈ N²·T). O modelo exato continua intratável em alta contagem de sensores.

