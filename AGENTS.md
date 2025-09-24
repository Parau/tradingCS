# Guia do Agente para o Trading System

Este documento serve como um guia técnico para futuros agentes (como eu) que trabalhem neste projeto. Ele resume a arquitetura, convenções e pontos críticos de implementação.

## 1. Arquitetura Geral

O sistema é composto por três componentes principais que rodam de forma independente:

1.  **`backend/`**: Um servidor **FastAPI** que centraliza toda a lógica de negócio e comunicação com o MetaTrader 5 (MT5).
2.  **`frontend_pyqt/`**: Uma aplicação de desktop **PyQt** que funciona como o painel de controle principal.
3.  **`frontend_web/`**: Uma interface web de cliente para visualização de gráficos, baseada em HTML, CSS e JavaScript.

**Princípio Fundamental:** O backend FastAPI é o cérebro e a única fonte de dados do MT5. Todos os outros componentes são clientes de sua API.

## 2. Fluxo de Execução e Setup

-   **Ponto de Entrada:** A aplicação é iniciada executando o dashboard principal:
    ```bash
    python frontend_pyqt/main_dashboard.py
    ```
-   **Dependências:** O projeto tem duas listas de dependências separadas. Ambas devem ser instaladas:
    ```bash
    pip install -r backend/requirements.txt
    pip install -r frontend_pyqt/requirements.txt
    ```
-   **Conexão com MT5:** O backend se conecta a uma instância do MT5 que já deve estar **em execução e logada**. Nenhuma credencial é necessária no código.

## 3. Detalhes do Backend (`backend/`)

-   **Servidor de Arquivos:** O servidor FastAPI é responsável por servir os arquivos estáticos do cliente web (`index.html`, etc.). A rota `/` serve o `index.html` e os assets (JS, CSS) são servidos a partir de `/static/`.
-   **Comunicação com PyQt:** O dashboard em PyQt inicia e para o processo do servidor FastAPI usando `QProcess`.
    -   **IMPORTANTE (Windows):** A variável de ambiente `PYTHONUTF8=1` é definida para o subprocesso para evitar `UnicodeDecodeError` ao ler o output do servidor.
-   **Manipulação de Fuso Horário (Timezone):** Esta foi uma fonte de muitos bugs. A estratégia final e correta é:
    -   O backend espera receber do cliente strings de data/hora "ingênuas" (sem fuso horário), representando a intenção do usuário em seu horário local.
    -   A função `parse_and_localize_time` em `history.py` assume que qualquer timestamp ingênuo está no fuso horário `America/Sao_Paulo` e o converte para **UTC** antes de fazer a consulta no MT5.
    -   A API **sempre** retorna timestamps **UTC puros e corretos**, sem nenhuma manipulação ou "hack".

## 4. Detalhes do Frontend Web (`frontend_web/`)

-   **Biblioteca de Gráficos:** Usa **Lightweight Charts**.
-   **Tratamento de Fuso Horário na Exibição:**
    -   O frontend é o **único** responsável por formatar os timestamps UTC recebidos do backend para a exibição correta no fuso horário local.
    -   Isso é feito usando a opção `timeScale.tickMarkFormatter` na criação do gráfico. Esta função deve converter o timestamp UTC para a string de hora local desejada (ex: `America/Sao_Paulo`).
-   **Plugin de Desenho de Retângulo (`rectangle_plugin.js`):** Este foi o componente mais complexo.
    -   **Requisito da API:** Para criar um primitivo de desenho customizado, é **obrigatório** implementar a interface `ISeriesPrimitive` completa. A classe principal (`RectanglePrimitive` no nosso caso) deve ter todos os métodos a seguir, mesmo que alguns não sejam usados e apenas retornem `[]`:
        -   `paneViews()`
        -   `timeAxisViews()`
        -   `priceAxisViews()`
        -   `priceAxisPaneViews()`
        -   `timeAxisPaneViews()`
    -   **Estrutura de Classes:** A implementação correta segue um padrão de 3 classes: a `RectanglePrimitive` (fonte de dados), `RectanglePaneView` (cálculo de coordenadas) e `RectanglePaneRenderer` (desenho no canvas).
    -   **Desenho no Canvas:** Toda a lógica de desenho dentro do Renderer **deve** ser encapsulada em uma chamada `target.useBitmapCoordinateSpace(scope => { ... })`. Tentar desenhar diretamente no contexto não funciona.
-   **Gerenciamento de Primitivos:** O `main.js` é responsável por gerenciar o ciclo de vida dos retângulos. Ele mantém um array de primitivos ativos, os remove (`detachPrimitive`) e anexa (`attachPrimitive`) novos a cada atualização recebida via WebSocket.
