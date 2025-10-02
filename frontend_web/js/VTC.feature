# language: pt
  @VTC @indicador

  Funcionalidade: Cálculo e plotagem do indicador **VTC** a partir de um valor base (**VFR**)
  Como trader
  Quero calcular níveis fixos ao redor de um VFR
  Para visualizar regiões de preço equivalentes a ±0,5% (Δ) e ±0,25% (50% de Δ), além dos “Excessos” (±1,5·Δ)

  Contexto:
    Dado que o usuário informa um valor base VFR
    E que o delta Δ é definido como Δ = VFR × 0,005 (0,5%)
    E que os níveis devem ser arredondados para 2 casas decimais (arredondamento “half-up”)
    E que os níveis calculados são:
    | Rótulo     | Fórmula                       |
    | VTC        | VFR                           |
    | 50%+       | VFR + Δ/2                     |
    | 50%-       | VFR - Δ/2                     |
    | DELTA+     | VFR + Δ                       |
    | DELTA-     | VFR - Δ                       |
    | EXCES+     | VFR + 1,5×Δ                   |
    | EXCES-     | VFR - 1,5×Δ                   |

  Regra: Os rótulos devem refletir o sinal do desvio
  E “DELTA-” deve ser usado para o nível abaixo do VFR (evitar rotular como “VTC+delta” no nível negativo)

  Esquema do Cenário: Calcular níveis do VTC para um VFR informado
  Dado que o VFR informado é <VFR>
  Quando eu calcular Δ = VFR × 0,005 e os níveis {EXCES+, DELTA+, 50%+, VTC, 50%-, DELTA-, EXCES-}
  Então os níveis devem ser exatamente:
  | EXCES+   | DELTA+   | 50%+     | VTC      | 50%-     | DELTA-   | EXCES-   |
  | <EXCES+> | <DELTA+> | <50%+>   | <VTC>    | <50%->   | <DELTA-> | <EXCES-> |

  ```
  Exemplos:
    | VFR       | EXCES+   | DELTA+   | 50%+     | VTC      | 50%-     | DELTA-   | EXCES-   |
    | 5.317,00  | 5.356,88 | 5.343,59 | 5.330,29 | 5.317,00 | 5.303,71 | 5.290,41 | 5.277,12 |
    | 5.460,00  | 5.500,95 | 5.487,30 | 5.473,65 | 5.460,00 | 5.446,35 | 5.432,70 | 5.419,05 |
    | 5.345,00  | 5.385,09 | 5.371,73 | 5.358,36 | 5.345,00 | 5.331,64 | 5.318,27 | 5.304,91 |
  ```

