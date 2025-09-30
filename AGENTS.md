# Sobre este arquivo
Este documento serve como um guia técnico para futuros programadores e Agentes de IA  trabalhem neste projeto. Ele resume a arquitetura, convenções e pontos críticos de implementação.

## Sobre o sistema
Este projeto é um trading system que usa dados históricos e em tempo real para auxiliar no processo de tomada de decisão de operações day trade e position. É um sistema de trading que roda em um computador local, para um único usuário, com foco em simplicidade de desenvolvimento e manutenção.


## Arquitetura Geral
O sistema é composto por três componentes principais que rodam de forma independente:

1.  **`backend/`**: Um servidor **FastAPI** que centraliza toda a lógica de negócio e comunicação com o MetaTrader 5 (MT5).
2.  **`frontend_pyqt/`**: Uma aplicação de desktop **PyQt6** que funciona como o painel de controle principal.
3.  **`frontend_web/`**: Uma interface web de cliente para visualização de gráficos, baseada em HTML, CSS e JavaScript.

**Princípio Fundamental:** O backend FastAPI é o cérebro e a única fonte de dados do MT5. Todos os outros componentes são clientes de sua API.

### Stack de Tecnologia
- **Servidor Backend:** use FastAPI. Toda a lógica de I/O é assíncrona (`async/await`).
- **Painel de Controle (frontend_pyqt):** Use **PyQt** para a interface gráfica de desktop.
- **Comunicação Cliente-Servidor:** Use **HTTP** para requisições de ação/dados históricos e **WebSockets** para dados em tempo real.
- **cliente web (frontend_web):** para as funcionalidades web do sistema usar html, javascript, tailwind e tradingview lightweight-charts
- **Dados ativos bolsa B3:** biblioteca python no servidor acessando MT5 (MetaTrader5).

### Dados Históricos
- Devem ser servidos por endpoints **HTTP RESTful** no FastAPI.
- A API deve consultar os dados históricos diretamente do MT5 sob demanda.
- Implemente um **cache em memória** nos endpoints de dados históricos para minimizar chamadas repetidas ao MT5.

### Dados em tempo real
- Usando websockets

## Documentação (uso de comentários dentro do código de programação)
### Formato
- Usao o padrão OpenAPI para as api do sistema.
- Usar o padrão JSDoc para código javascript e TSDoc para typescript.
- reStructuredText (reST) para código python usando o estilo Google.
- Documentação padrão Markdown.
- Gherkin para para explicar e registrar o comportamento esperado do sistema e as regras de negócio (arquivo com extenção `.feature`).
ótimo ponto — isso acontece mesmo: muitos agentes “limpam” comentários durante refatorações. Abaixo vai um bloco pronto para colar no seu **AGENTS.md** (em PT-BR), com políticas claras para **preservar, atualizar e enriquecer comentários**, sem apagá-los por engano.
### Comentários no código (política para agentes)
**ATENÇÃO (resumo):** Comentários são parte do código e **não devem ser removidos** durante geração ou refatoração. Eles registram a lógica, decisões históricas, riscos, links de referência e alertas operacionais. Mantenha-os **atuais**, **fiéis** e **presentes**.
#### Princípios
1. **Preservar por padrão:** Nunca apague comentários existentes sem justificativa explícita no PR.
2. **Atualizar junto com o código:** Se alterar uma função/trecho, revise e atualize os comentários adjacentes para refletir o comportamento atual.
3. **Respeitar avisos e alertas:** Comentários que indiquem riscos, requisitos legais, segurança, performance, débitos técnicos ou “gotchas” **são obrigatórios** e devem permanecer.
4. **Fonte de decisões:** Comentários explicam *por que* algo é assim (decisões, trade-offs, links). Não remova essa história.
5. **Sinalizar divergências:** Se um comentário estiver desatualizado, **não o elimine** — corrija-o e adicione nota do que mudou.
#### O que fazer (DO)
* **Antes de editar:** ler comentários do bloco, arquivo e módulo para entender contexto e decisões anteriores.
* **Ao refatorar:** migrar comentários relevantes para o novo local (mesma função, wrapper, utilidade, etc.).
* **Ao atualizar:** manter links úteis (RFCs, issues, artigos); se algum link quebrar, substitua por um equivalente ou inclua o título/DOI.
* **Docstrings e cabeçalhos:** garantir que docstrings descrevam argumentos, retorno, efeitos colaterais e invariantes.
* **Marcação de decisões:** quando fizer uma mudança que invalida uma decisão antiga, acrescente uma linha “Atualizado em: AAAA-MM-DD — motivo”.
#### O que evitar (DON’T)
* Remover comentários por “limpeza” automática.
* Resumir comentários técnicos a ponto de perder informação crítica.
* Apagar TODOs/FIXMEs/REFERÊNCIAS sem resolver o item ou registrar o motivo no PR.
#### Checklist para PRs gerados pelo agente
* [ ] Comentários importantes foram **preservados** e/ou **migrados** para o novo local.
* [ ] Comentários foram **atualizados** para refletir o comportamento atual.
* [ ] Links e referências foram verificados (substituir se quebrados).
* [ ] Decisões alteradas estão anotadas com **“Atualizado em: AAAA-MM-DD — motivo”**.
* [ ] Nenhum TODO/FIXME foi apagado sem resolução ou justificativa clara no PR.
#### Remoção excepcional
Só remova um comentário se for **inequivocamente obsoleto** ou enganoso. Nesse caso:
* Inclua no diff uma nota: *“Removido comentário obsoleto: <resumo> (por quê)”*.
* Se a informação ainda tiver valor histórico, mova-a para o início do código e mencione isso no local em que originalmente o comentário estava presente.
 
## Fluxo de Execução e Setup

-   **Ponto de Entrada:** A aplicação é iniciada executando o dashboard principal:
    ```bash
    python frontend_pyqt/main_dashboard.py
    ```
-   **Dependências:** O projeto tem duas listas de dependências separadas. Ambas devem ser instaladas:
    ```bash
    conda install --file backend/requirements.txt
    conda install --file frontend_pyqt/requirements.txt
    ```
-   **Conexão com MT5:** O backend se conecta a uma instância do MT5. Se ele não estiver em execução o backend é responsável por executar o MT5. Na inicialização do MT5 não é necessário enviar credenciais pois ele já está logado na conta adequada.

## Detalhes do Backend (`backend/`)

-   **Servidor de Arquivos:** O servidor FastAPI é responsável por servir os arquivos estáticos do cliente web (`index.html`, etc.). A rota `/` serve o `index.html` e os assets (JS, CSS) são servidos a partir de `/static/`.
-   **Comunicação com PyQt:** O dashboard em PyQt inicia e para o processo do servidor FastAPI usando `QProcess`.
-   **Manipulação de Fuso Horário (Timezone):** Esta foi uma fonte de muitos bugs. A estratégia final e correta é:
    -   O backend espera receber do cliente strings de data/hora "ingênuas" (sem fuso horário), representando a intenção do usuário em seu horário local.
    -   A função `parse_and_localize_time` em `history.py` assume que qualquer timestamp ingênuo está no fuso horário `America/Sao_Paulo` e o converte para **UTC** antes de fazer a consulta no MT5.
    -   A API **sempre** retorna timestamps **UTC puros e corretos**, sem nenhuma manipulação ou "hack".

## 4. Detalhes do Frontend Web (`frontend_web/`)

-   **Biblioteca de Gráficos:** Usa **Lightweight Charts**.
-   **Tratamento de Fuso Horário na Exibição:**
    -   O frontend é o **único** responsável por formatar os timestamps UTC recebidos do backend para a exibição correta no fuso horário `America/Sao_Paulo`.
-   **Plugin de Desenho de Retângulo (`rectangle_plugin.js`):** Trata de forma específica os markes recebidos de receive_and_broadcast_markers.
    -  Para desenvolvimento foi usado como referência o código de exemplo da documentação oficial do Lightweight Charts: https://github.com/tradingview/lightweight-charts/blob/master/plugin-examples/src/plugins/rectangle-drawing-tool/rectangle-drawing-tool.ts
-   **Gerenciamento de Primitivos:** O `main.js` é responsável por gerenciar o ciclo de vida dos retângulos. Ele mantém um array de primitivos ativos, os remove (`detachPrimitive`) e anexa (`attachPrimitive`) novos a cada atualização recebida via WebSocket.
