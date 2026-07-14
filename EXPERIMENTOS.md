# Heurísticas em larga escala

**Objetivo:** rodar as heurísticas construtivas (NN, AoI-Greedy, Score-Greedy) em instâncias de larga
escala e avaliar resultados e trade-offs. Detalhe por cenário em
`text/comparacao_larga_escala_rascunho.md` e `text/comparacao_slot_duration_rascunho.md`.
*Ainda não incorporado à tese.*

**Comum a todos:** Parrot Anafi USA, `TIME_SLOTS = 20`, bateria 141,4 kJ, 30 rodadas por cenário
(AoI encadeada), posições com seed fixa.

## Track 1: escala em número de sensores (Δt = 10 s)

**Cenários:** `n ∈ {50, 75, 100, 150, 200}` × `L ∈ {600, 800, 1000}` m.

**Resultados:**

- **Rodam?** Sim. As três heurísticas resolvem todos os 15 cenários sem problema, inclusive n = 200.
- **Em quanto tempo?** Cerca de 30 a 50 ms por rodada, mesmo no maior cenário.
- **Dão bons resultados e qual a melhor?**

  | Heurística | Coleta e frescor | Energia | Avaliação |
  |---|---|---|---|
  | AoI-Greedy | melhor | maior | melhor qualidade; ganho cresce com n |
  | Score-Greedy | quase igual à AoI-Greedy | menor | melhor equilíbrio qualidade × energia |
  | NN | fraca | menor | não escala em qualidade (coleta cerca de 159 constante, ignora a AoI) |

  A melhor em qualidade é a **AoI-Greedy**; se energia importar, a **Score-Greedy** entrega quase a
  mesma coleta gastando menos.
- **Observação:** o número de coletas por rodada satura em cerca de 9 por causa de `TIME_SLOTS = 20`
  (cada coleta custa cerca de 2 slots), e não pelo número de sensores. Aumentar n apenas amplia o
  *pool* de sensores que as heurísticas sensíveis à AoI podem priorizar.

## Track 2: duração do slot (Δt) em mapas grandes

**Cenários:** `Δt ∈ {10, 20, 30, 40, 50}` s × `n ∈ {50, 100, 200}` × `L ∈ {600, 800, 1000, 2000, 4000}` m.

**Trade-off central:** aumentar Δt faz o UAV voar mais devagar.

- Energia de **movimento** proporcional a `1/Δt²`, então **cai** (e a velocidade fica realista: de
  100 para 33 m/s).
- Energia de **hover** proporcional a `Δt`, então **sobe**. Como a missão ocupa os 20 slots, há um
  teto de viabilidade em Δt de cerca de 44 s (acima disso, só pairar já estoura a bateria).

**Resultados:**

- **Δt destrava mapas grandes** que a Δt = 10 s eram inviáveis. Exemplo (AoI-Greedy):

  | Cenário | Δt = 10 s | Δt = 30 s |
  |---|---|---|
  | P50-4000 | 2 visitas | **8 visitas** |
  | P50-2000 (AoI coletada) | 229 | **514** |

- **Ponto ótimo em Δt de 20 a 30 s:** energia de movimento já bastante reduzida e velocidade
  realista, sem o hover dominar. A Δt = 50 s tudo colapsa (0 visitas).
