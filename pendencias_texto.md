# Pendências do Texto

## Objetivos desalinhados (`text/objetivos.tex`)

O terceiro objetivo específico diz "comparando resultados ao que já existe na literatura", mas o trabalho **não faz essa comparação** — a metodologia só analisa os próprios experimentos internamente.

Também há um item comentado que menciona "minimização da AoI", o que é semanticamente oposto ao que o modelo faz (maximização da AoI coletada).

### Reescrita proposta dos objetivos específicos

1. Formular o problema como MILP com tempo discreto e horizonte de missão finito.
2. Modelar dois objetivos conflitantes — maximização da AoI coletada e minimização do consumo energético — combinados via função ponderada.
3. Implementar a formulação no Gurobi e validar sobre 36 cenários sintéticos variando quantidade de sensores e tamanho da área.
4. Avaliar o impacto de diferentes configurações de cenário sobre as métricas de desempenho (AoI final, energia consumida, distância percorrida).
5. Comparar o comportamento do modelo para dois UAVs com parâmetros físicos distintos (DJI Matrice 300 RTK e Parrot Anafi USA).

---

## Outros itens pendentes

- **3.3 Modelo de energia UAV** — placeholder vazio em vermelho; intro promete cobrir este tópico na Seção 3.
- **3.4 Modelo de comunicação de UAV** — placeholder vazio em vermelho; mesmo caso.
- **Conclusão** — seção inexistente; obrigatória para o PGC.
- **Tag `\tag{10}` duplicada** — usada em `$E_1 = 0$` (energia) e `$A_{j,1} = A_j^0$` (AoI).
- **TODO gráfico comparativo** em `text/metodologia.tex:113` — gráfico entre DJI Matrice 300 RTK e Parrot Anafi USA.
- **`\pretextual`** em `text/main.tex:17` — comando de abnTeX2 num documento `article`; pode gerar erro dependendo do template final.
