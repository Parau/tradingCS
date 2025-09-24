## Sobre o sistema
Este projeto é um trading system que usa dados históricos e em tempo real para auxiliar no processo de tomada de decisão de operações day trade e position. É um sistema de trading que roda em um computador local, para um único usuário, com foco em simplicidade de desenvolvimento e manutenção.

## Stack de Tecnologia
- **Servidor Backend:** use FastAPI. Toda a lógica de I/O é assíncrona (`async/await`).
- **Painel de Controle:** Use **PyQt** para a interface gráfica de desktop.
- **Comunicação Cliente-Servidor:** Use **HTTP** para requisições de ação/dados históricos e **WebSockets** para dados em tempo real.
- **cliente web:** para as funcionalidades web do sistema usar html, javascript, tailwind e tradingview lightweight-charts
- **Dados ativos bolsa B3:** biblioteca python no servidor acessando MT5 (MetaTrader5).

## Princípios Gerais
- **Cérebro Central:** O servidor **FastAPI** é o componente central que orquestra todos os dados e a lógica.
- **Fonte de Dados Única:** A API FastAPI é o **único** processo que se comunica diretamente com o terminal **MetaTrader 5 (MT5)**.
- **Arquitetura de Clientes:** Todos os outros componentes (GUI PyQt, scripts de backtesting, cliente web) atuam como **clientes** da API FastAPI.
- **Processos Separados:** A GUI PyQt, o servidor FastAPI e os processos de backtesting devem rodar de forma independente.
- **OpenAPI:** Usa o padrão OpenAPI no código fonte para documentar todas API.
- **reStructuredText:** Usar o padrão reST estilo Google para documentar todos os códigos de programação python
- **JSDoc e TSDoc:** Usar o padrão JSDoc para documentar todos os códigos de programação Javascipt e páginas web e TSDoc para códigos de programação Typescript.

## Princípios para o Fluxo de Dados

### Dados Históricos
- Devem ser servidos por endpoints **HTTP RESTful** no FastAPI.
- A API deve consultar os dados históricos diretamente do MT5 sob demanda.
- Implemente um **cache em memória** nos endpoints de dados históricos para minimizar chamadas repetidas ao MT5.

### Dados em Tempo Real
- Quando necessário acesso a dados de tempo real uma **tarefa de background assíncrona** (`asyncio.create_task`) dentro do processo FastAPI deve buscar continuamente os novos ticks/barras do MT5 usando **transmissão (broadcast) via WebSocket**.

### Backtesting
- Deve ser executado como um **processo separado**, iniciado pela GUI PyQt usando a biblioteca `subprocess`.
- O script de backtest **NÃO** se conecta ao MT5. Ele obtém os dados históricos necessários fazendo uma requisição **HTTP** para a API FastAPI.
- Os resultados do backtest devem ser salvos em um arquivo que a GUI irá ler e exibir após a conclusão.

## Funcionalidades
### Aplicativo principal
- Dashboard usando PyQt.
- Permite iniciar e monitorar o servidor fastAPI.
- Da acesso as funcionalidades:
  - `Gráfico WDOV25`
  - `tabela marcação`
- Status de conexão MT5 em tempo real

### `Gráfico WDOV25`
- cliente web que se comunica via fastAPI e apresenta um gráfico lightweight-charts do tipo candlestick com o WDOV25
- Tem dois campos que pode ser selecionado: a data de início e a data final dos dados que serão mostrados no gráfico
- Tem um campo que permite selecionar o tempo do gráfico (1, 5, 15, 30 e 60 minutos).
- Mostra os dados históricos e em tempo real do ativo.
- Além dos dados do ativo WDOV25 recebe de forma atualizada os dados gerados pela funcionalidade `tabela marcação` para desenhar marcações no gráfico candlestick.
- o lightweight-charts não tem suporte a desenho de retangulos. para implementar esta funcionalidade deve ser usado o recurso de plugin. Este link https://github.com/tradingview/lightweight-charts/blob/master/plugin-examples/src/plugins/rectangle-drawing-tool/rectangle-drawing-tool.ts tem o exemplo de um Rectangle Drawing Tool. Não implementamos o recurso de desenhar, mas o código mostra como criar um plugin e como desenhar um retângulo na tela.
- Janela redimensionável

### `tabela marcação`
- Janela com UI PyQT que apresenta uma caixa de texto e uma Tabela editável com colunas: Data, Hora, preco (preço), Tipo.
- Na caixa de texto deve ser indicado o nome do ativo assoaciado a tabela. por exemplo WDOV25.
- Operações na tabela:
  - Adicionar/Remover linhas
  - Carregar/Salvar CSV
- Tipos de marcação:
  - **POC_VENDA**: Retângulo vermelho pontilhado
  - **POC_COMPRA**: Retângulo verde pontilhado
- Janela redimensionável. Pode ser posicionada em qualquer lugar no desktop. Tem suporte a multiplos monitores.
- Os dados desta tabela são usados para desenhar marcações no gráfico `Gráfico WDOV25`.
- Possui um botão chamado atualizar gráfico. Quando pressionado ele envia os dados atuais da tabela para a fastAPI que envia os dados para o `Gráfico WDOV25` poder atualizar as marcações em seu gráfico candlestick. 
- Para cada `tipo` um desenho diferente:
  * POC_VENDA: desenha um retângulo de borda vermelha e linha pontilhada em que o início do retângulo é a `data` e `hora` e o final é 18h da `data`. A posição Y é dada pelo preço que vai de `preco` que vai de preco-1,00 até preco+1,00.
  * POC_COMPRA: mesmo que o PC_VENDA mas da cor verde.

### fastAPI
- Gerencia a inicialização do MT5 no sistema. Inicializar 1x na startup do FastAPI; reconectar em caso de falha. Não bloquear event loop.
- Tem um endpoint para dados históricos /api/history . O sistema atualmente dá suporte ao WDOV25 mas a API deve permitir a chamada de qualquer ativo existente no MT5
- Dados em tempo real do MT5 exemplo /ws/candles?symbol=WDOV25&timeframe=M5 o retorno é em um formato compatível com o lightweight-charts.
- Tem um endpoint para tratar os dados da `tabela marcação` /api/markers . O sistema atualmente dá suporte ao WDOV25 mas a API deve permitir associar a marcação o nome de qualquer ativo existente no MT5 
- Retorna dados compatíveis com o formato do Lightweight Charts

# Detalhes fastAPI
## `/api/history/{symbol}`
**Método:** `GET`
**URL:** `/api/history/{symbol}`

### Parâmetros
| Nome        | Local          | Tipo   | Obrigatório | Descrição                                                                                                      | Exemplo               |
| ----------- | -------------- | ------ | ----------- | -------------------------------------------------------------------------------------------------------------- | --------------------- |
| `symbol`    | Path (na URL)  | string | Sim         | Símbolo do ativo a ser consultado.                                                                             | `WDOV25`              |
| `timeframe` | Query (na URL) | string | Sim         | Período do gráfico. Formato “amigável” mapeado no backend para o MT5. Valores: `M1`, `M5`, `M15`, `M30`, `H1`. | `M5`                  |
| `start`     | Query (na URL) | string | Sim         | Data/hora **ISO-8601** de início (ex.: `YYYY-MM-DDTHH:MM:SS` com ou sem timezone).                             | `2025-09-19T09:00:00` |
| `end`       | Query (na URL) | string | Sim         | Data/hora **ISO-8601** de fim.                                                                                 | `2025-09-19T18:00:00` |

### Exemplo de requisição
```
GET http://127.0.0.1:8000/api/history/WDOV25?timeframe=M5&start=2025-09-20T10:00:00&end=2025-09-20T10:15:00
```

### Formato da resposta (200 OK)
A resposta é um **JSON** com um array de velas no formato compatível com o **Lightweight Charts**.
O campo `time` é um **Unix timestamp (segundos, UTC)** obtido do `copy_rates_range` do MetaTrader 5.

```json
[
  {
    "time": 1758392400,
    "open": 5402.5,
    "high": 5405.0,
    "low": 5402.0,
    "close": 5404.5
  },
  {
    "time": 1758392700,
    "open": 5404.5,
    "high": 5406.0,
    "low": 5403.5,
    "close": 5405.0
  },
  {
    "time": 1758393000,
    "open": 5405.0,
    "high": 5405.5,
    "low": 5401.0,
    "close": 5401.5
  }
]
```

### Observações rápidas

* **Timezone:** se `start`/`end` vierem **sem offset**, padronize para `America/Sao_Paulo` no backend e converta para **UTC** antes de chamar o MT5.
* **Mapeamento timeframe:** `M1→TIMEFRAME_M1`, `M5→TIMEFRAME_M5`, `M15→TIMEFRAME_M15`, `M30→TIMEFRAME_M30`, `H1→TIMEFRAME_H1`.
* **Compatibilidade LW Charts:** o gráfico aceita campos extra no objeto (serão ignorados). Se quiser, você pode incluir outros dados como `tickVolume`, `spread`, `realVolume` sem quebrar a renderização.

