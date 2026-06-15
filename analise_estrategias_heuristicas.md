# Análise de Estratégias Heurísticas para Comparação com o MILP

> Referência base: Wei et al. (2022) — *UAV-Assisted Data Collection for Internet of Things: A Survey*

---

## Contexto do Problema

**Entrada (idêntica para todas as estratégias):**
- Posições dos sensores: `sensors_LxL.csv` — campos `id, x, y` (coordenadas em metros)
- Estado de AoI: `aoi_state.csv` — campos `sensor_id, aoi` (acumulado entre rodadas)
- Base fixa em (0, 0)
- Horizonte temporal: `T_f = 20 slots × 10 s = 200 s` por rodada
- Capacidade de bateria: `E_max` (Joules; configurável por drone)
- Modelo de potência: rotary-wing P(V) — Zeng et al. (2019)

**Saída esperada (para comparação justa):**
- Sequência de nós visitados (path)
- Energia total consumida
- AoI coletada (soma dos valores de AoI no momento da visita)
- AoI média final, sensores visitados, distância total

---

## Estratégias Identificadas no Survey (Wei et al., 2022)

### 1. Nearest Neighbor (NN) — TSP guloso

**Descrição:** Partindo da base, o UAV sempre se desloca para o sensor mais próximo ainda não visitado. Repete até esgotar bateria ou slots de tempo.

**Adaptação para nosso problema:**
- A cada passo, calcular custo energético de ir ao sensor mais próximo;
- Se `energia acumulada + custo(atual → próximo) + custo(próximo → base) ≤ E_max` e ainda há slots disponíveis, visitar;
- Caso contrário, retornar à base.

**Implementabilidade:** Alta pura Python, sem biblioteca externa.

**Limitação:** Ignora completamente a AoI; tende a desperdiçar energia em sensores com dados recentes.

---

### 2. AoI-Greedy (guloso por urgência)

**Descrição:** A cada passo, visitar o sensor com maior AoI que ainda seja alcançável dentro da restrição de bateria e tempo.

**Adaptação:**
- Ordenar sensores por `aoi_j` decrescente;
- Verificar viabilidade (energia e tempo de retorno) antes de cada visita.

**Implementabilidade:** Alta pura Python, diretamente alinhada ao objetivo do modelo.

**Por que é boa candidata:** É uma heurística construtiva que aproxima o objetivo do MILP (maximizar AoI coletada). Esperamos que seja a heurística com melhor desempenho frente ao MILP.

---

### 3. Score Greedy (AoI / distância)

**Descrição:** Variante da AoI-Greedy. A cada passo, escolher o sensor com maior razão `AoI_j / dist(atual, j)`, priorizando sensores urgentes e próximos ao mesmo tempo.

**Implementabilidade:**  Alta apenas modifica a função de scoring do AoI-Greedy.

**Interesse:** Captura o trade-off entre urgência e custo de deslocamento, mais fiel ao MILP multiobjetivo.

---

### 4. Hilbert Curve (curva de preenchimento espacial)

**Descrição:** Projetar as coordenadas dos sensores sobre uma curva de Hilbert 2D. Ordenar os sensores pela sua posição na curva (índice 1D). Visitar nessa ordem até esgotar bateria/tempo.

**Adaptação:**
- Normalizar coordenadas `(x, y)` para o intervalo `[0, 2^p - 1]` (tipicamente p = 8 ou 10);
- Calcular índice Hilbert de cada sensor;
- Ordenar por índice e percorrer respeitando restrições.

**Implementabilidade:**  ?? Acho que precisaría de uma biblioteca ou implementar a curva na mão

---

### 5. MST DFS (Minimum Spanning Tree + busca em profundidade)

**Descrição:** Construir a Árvore Geradora Mínima (MST) sobre o conjunto de sensores + base (usando distância euclidiana como peso). Percorrer a MST em DFS a partir da base. Cortar quando bateria/tempo se esgota.

**Adaptação:**
- Usar Kruskal ou Prim para construir a MST;
- DFS retorna uma sequência de sensores;
- Truncar a sequência na primeira aresta que violaria `E_max` ou `T_f`.

**Implementabilidade:**  ?? talvez precise de alguma lib também

---

### 6. Voronoi + Centróides

**Descrição:** Particionar a área em células de Voronoi (uma por sensor). O UAV visita os centróides de células agrupadas ou os próprios sensores em ordem definida pela geometria dos polígonos de Voronoi.

**Aplicabilidade ao nosso problema:** Baixa para coleta em sensores pontuais.  
Voronoi é mais útil quando o UAV precisa cobrir regiões geográficas sem alvos fixos, ou quando há mais de um sensor por célula. No nosso caso, cada sensor já é um ponto alvo — a decomposição de Voronoi não agrega informação de roteamento.

**Possível uso limitado:** Ordenar a sequência de visita pelos vizinhos de Voronoi (sensores que compartilham fronteira de célula visitados em sequência). Equivalente a uma heurística geométrica de proximidade — similar ao NN com fundamento geométrico mais formal.

---

### 7. Random Baseline

**Descrição:** Visitar sensores em ordem aleatória (com semente fixa para reprodutibilidade), respeitando restrições de bateria e tempo.

**Implementabilidade:**  Alta fácil fazer com uma lib de random() ou coisa do tipo.

**Papel:** Limite inferior de desempenho. Demonstra que o MILP (e as demais heurísticas) superam uma estratégia sem inteligência.


**Fluxo de execução idêntico ao MILP:**
1. Carregar `sensors.csv` e `aoi_state.csv`
2. Executar heurística → obter sequência de visitas
3. Simular voo slot a slot: calcular energia, atualizar AoI
4. Salvar métricas no mesmo formato `round_summary_*.csv`
5. Executar 30 rodadas por cenário (os mesmos 36 cenários P_{ns-L})