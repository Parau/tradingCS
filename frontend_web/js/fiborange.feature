# language: pt
    @fiborange @indicador
    Funcionalidade: Traçar níveis e canais do indicador Fiborange
    Como analista técnico
    Quero calcular linhas e canais a partir do preço de ajuste do dia anterior
    Para visualizar níveis de controle simétricos no gráfico

    Contexto:
        Dado que o "preço de ajuste" é o do dia anterior
        E que o "passo_entre_niveis" é 0,50% do ajuste (0.005 × ajuste)
        E que o "meio_canal" é 0,10% do ajuste (0.001 × ajuste)
        E que os cálculos são feitos em pontos (não percentuais compostos por nível)
        E que o arredondamento é aplicado apenas no resultado final
        E que o arredondamento final é para 2 casas decimais (padrão half-up)

    Regra: A linha central é o ajuste do dia anterior
        Cenário: Linha central
        Dado um ajuste A
        Quando eu calcular a linha central
        Então a "linha" deve ser igual a A

    Regra: Níveis a cada ±0,50% do ajuste
        # k é o número de passos de 0,50% em relação ao ajuste (negativo para baixo)
        Esquema do Cenário: Cálculo da linha do nível k
        Dado um ajuste <ajuste>
        Quando eu calcular a linha do nível <k>
        Então a "linha" deve ser igual a <linha_esperada>

        Exemplos:
            | ajuste  | k  | linha_esperada |
            | 5347,56 |  0 | 5347,56        |
            | 5347,56 |  1 | 5374,30        |  # 5347,56 + 0,5%
            | 5347,56 |  2 | 5401,04        |  # 5347,56 + 1,0%
            | 5347,56 | -1 | 5320,82        |  # 5347,56 - 0,5%
            | 5347,56 | -2 | 5294,08        |  # 5347,56 - 1,0%

    Regra: Cada linha possui um canal simétrico com largura fixa (±0,10% do ajuste)
        # O canal é traçado em pontos: base = linha - meio_canal, topo = linha + meio_canal
        Esquema do Cenário: Canal simétrico por nível
        Dado um ajuste <ajuste>
        E o "meio_canal" MC = 0,001 × <ajuste>
        Quando eu traçar o canal para a linha do nível <k>
        Então a "base" do canal deve ser <base_esperada>
        E o "topo" do canal deve ser <topo_esperado>
        E a distância entre "linha" e "base" deve ser igual à distância entre "topo" e "linha" (tolerância 0,01)

        Exemplos:
            | ajuste  | k  | base_esperada | topo_esperado |
            | 5347,56 |  0 | 5342,21       | 5352,91       |
            | 5347,56 | -1 | 5315,47       | 5326,17       |
            | 5347,56 | -2 | 5288,74       | 5299,43       |
            | 5347,56 |  1 | 5368,95       | 5379,65       |
            | 5347,56 |  2 | 5395,69       | 5406,38       |

    Regra: Arredondamento apenas no resultado final
        Cenário: Não compor arredondamentos intermediários
        Dado um ajuste A
        E passo = 0,005 × A e MC = 0,001 × A
        Quando eu calcular a linha_k exata = A + k × passo (sem arredondar)
        E calcular base_exata = linha_k exata - MC (sem arredondar)
        E calcular topo_exata = linha_k exata + MC (sem arredondar)
        E então arredondar linha_k, base_exata e topo_exata para 2 casas decimais
        Então os valores arredondados devem ser usados para comparação/plotagem

    Regra: Invariância da largura do canal por nível
        Cenário: O meio_canal não muda com k
        Dado um ajuste A e MC = 0,001 × A
        Quando eu calcular o canal para quaisquer níveis k1 e k2
        Então (topo_k1 - linha_k1) = (topo_k2 - linha_k2) = MC (tolerância 0,01)
        E (linha_k1 - base_k1) = (linha_k2 - base_k2) = MC (tolerância 0,01)