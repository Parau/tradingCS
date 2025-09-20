# Trading System - Day Trade e Position

Este projeto é um sistema de trading para desktop que utiliza dados históricos e em tempo real do MetaTrader 5 (MT5) para auxiliar na tomada de decisão. O sistema é composto por um backend em FastAPI, uma interface de controle em PyQt e um cliente web para visualização de gráficos.

## Arquitetura

O sistema é projetado com uma arquitetura de cliente-servidor desacoplada:

-   **Backend (Servidor FastAPI):** É o cérebro do sistema. É o único componente que se comunica diretamente com o terminal MT5. Ele serve dados históricos via HTTP REST, transmite dados em tempo real via WebSockets e gerencia a lógica de negócio.
-   **Painel de Controle (PyQt):** É a aplicação principal de desktop. Permite ao usuário iniciar/parar o servidor backend, monitorar o status da conexão com o MT5 e acessar as outras funcionalidades.
-   **Cliente Web (HTML/JS/Lightweight Charts):** Uma interface web leve para exibir gráficos de candlestick com dados históricos e em tempo real. Também exibe marcações customizadas.
-   **Tabela de Marcações (PyQt):** Uma janela separada onde o usuário pode inserir e gerenciar marcações (como regiões de POC) que são visualizadas no gráfico.

## Funcionalidades

-   **Dashboard Principal:** Inicia e monitora o servidor FastAPI e a conexão com o MT5.
-   **Gráfico Dinâmico:** Exibe dados do ativo (ex: WDOV25) em um gráfico de candlestick.
    -   Seleção de período (timeframe) e intervalo de datas.
    -   Atualizações em tempo real.
    -   Desenho de marcações customizadas (POC_VENDA, POC_COMPRA) como retângulos no gráfico.
-   **Tabela de Marcações:**
    -   Interface para adicionar, remover e gerenciar marcações.
    -   Função para salvar e carregar as marcações de/para um arquivo CSV.
    -   Botão para enviar as marcações para o gráfico em tempo real.

## Como Configurar e Executar

### 1. Pré-requisitos

-   Python 3.8+
-   Terminal MetaTrader 5 instalado.

### 2. Instalação

Clone o repositório e instale as dependências para o backend e para o frontend:

```bash
git clone <url-do-repositorio>
cd <diretorio-do-repositorio>

# Instalar dependências do backend
pip install -r backend/requirements.txt

# Instalar dependências do frontend PyQt
pip install -r frontend_pyqt/requirements.txt
```

### 3. Configuração do MetaTrader 5

A nova abordagem de conexão é muito mais simples. O sistema irá se conectar a uma instância do MetaTrader 5 que já esteja em execução no seu computador.

**Requisito:** Antes de iniciar o servidor, **certifique-se de que o seu terminal MetaTrader 5 está aberto e logado na sua conta.**

Não é mais necessário configurar credenciais em um arquivo `.env`.

### 4. Executando a Aplicação

Para iniciar o sistema, execute o painel de controle principal:

```bash
python frontend_pyqt/main_dashboard.py
```

### 5. Utilização

1.  Com o painel de controle aberto, clique em **"Iniciar Servidor FastAPI"**. O status na barra inferior deve mudar para "Rodando" e o status do MT5 para "Conectado".
2.  Clique em **"Abrir Gráfico"** para abrir a interface do gráfico no seu navegador.
3.  Clique em **"Tabela de Marcações"** para abrir a janela de gerenciamento de marcações.
4.  Na tabela, adicione algumas linhas com dados de Data, Hora, Preço e Tipo.
5.  Clique em **"Atualizar Gráfico"**. As marcações deverão aparecer como retângulos no gráfico aberto no navegador.
6.  Ao fechar o painel de controle, o servidor FastAPI será encerrado automaticamente.
