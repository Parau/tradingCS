## Objetivo
Capturar múltiplos trechos de tela (de um ou mais monitores) e exibi-los em janelas independentes. Cada janela pode conter uma ou mais capturas. Renderizar um contorno pontilhado semi-transparente no desktop indicando as regiões capturadas.

## CSV de configuração
Arquivo define janelas e regiões (retângulos) a capturar.
### Exemplo
NOME_JANELA, ID_DISPLAY,X1, Y1, X2, Y2
VisaoGeral, 1, 15,10,  200, 200
VisaoGeral, 1, 430, 15, 830, 200
Simples, 2, 300, 50, 600, 450
Orientação, 2, 500, 400, 700, 600

### explicação campos
NOME_JANELA: string que agrupa capturas na mesma janela.
ID_DISPLAY: inteiro (1..N no mss).
X1,Y1: canto superior esquerdo em pixels relativo ao topo do monitor ID_DISPLAY.
X2,Y2: canto inferior direito do mesmo monitor.

### validações
* X2 > X1, Y2 > Y1.
* Retângulo deve caber dentro da resolução do monitor.
* ID_DISPLAY deve existir.
* Linhas inválidas são ignoradas e logadas como warning.

## Comportamento das janelas
* Cada valor distinto de NOME_JANELA cria uma janela.
* A janela exibe as capturas listadas para aquele código, empilhadas em layout (grid ou vertical).
* Redimensionar a janela redimensiona o conteúdo (escala uniforme preservando proporção de cada captura).
* Taxa de atualização configurável (ex.: 1–30 FPS; padrão 5 FPS).
* Opção “sempre no topo” por janela.
* Opção de alterar o ID_DISPLAY,X1, Y1, X2, Y2 de cada captura apresentada pela janela.
* Opção de configuração dos respectivos overlay das áreas capturadas e apresentadas na janela:
  - Toggle: --overlay on|off (padrão: off).
  - Cor e espessura configuráveis (padrão: branco, 2 px, tracejado).
* A configuração das opções fica em um botão configurar (icone) na janela para que não ocupem área útil da tela que deve priorizar espeço para mostrar o conteúdo capturado.

## Overlay (contorno pontilhado)
* Janela transparente e “click-through” (quando suportado) que desenha retângulos pontilhados nas posições definidas pelo CSV (em coordenadas do desktop).
