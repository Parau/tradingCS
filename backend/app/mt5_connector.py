import MetaTrader5 as mt5
import asyncio
import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

# --- Variáveis Globais ---
_is_connected = False

# --- Funções de Conexão ---

async def initialize_mt5():
    """
    Inicializa a conexão com o terminal MetaTrader 5.
    Tenta reconectar em caso de falha.
    """
    global _is_connected

    login = int(os.getenv("MT5_LOGIN", "123456"))
    password = os.getenv("MT5_PASSWORD", "password")
    server = os.getenv("MT5_SERVER", "server")
    path = os.getenv("MT5_PATH", "") # Ex: C:\\Program Files\\MetaTrader 5\\terminal64.exe

    while not _is_connected:
        print("Tentando conectar ao MetaTrader 5...")
        # A inicialização do MT5 pode ser bloqueante, mas é feita apenas uma vez no startup.
        # Para cenários mais complexos, poderia ser movido para um executor de thread.
        initialized = mt5.initialize(
            path=path if path else None,
            login=login,
            password=password,
            server=server
        )

        if initialized:
            print("Conexão com MetaTrader 5 estabelecida com sucesso.")
            _is_connected = True
        else:
            print(f"Falha ao conectar ao MT5. Código de erro: {mt5.last_error()}")
            print("Tentando novamente em 10 segundos...")
            await asyncio.sleep(10)

def shutdown_mt5():
    """
    Encerra a conexão com o MetaTrader 5.
    """
    global _is_connected
    if _is_connected:
        mt5.shutdown()
        _is_connected = False
        print("Conexão com MetaTrader 5 encerrada.")

def is_connected():
    """
    Verifica se a conexão com o MT5 está ativa.
    """
    return _is_connected

# Mapeamento de timeframes amigáveis para constantes do MT5
# Definido aqui para evitar importações circulares.
TIMEFRAME_MAP = {
    "M1": mt5.TIMEFRAME_M1,
    "M5": mt5.TIMEFRAME_M5,
    "M15": mt5.TIMEFRAME_M15,
    "M30": mt5.TIMEFRAME_M30,
    "H1": mt5.TIMEFRAME_H1,
}

def get_mt5_instance():
    """
    Retorna a instância do MT5 se conectado.
    """
    if not _is_connected:
        # Em uma aplicação real, poderíamos tentar reconectar aqui ou lançar uma exceção.
        # Por enquanto, vamos apenas logar um aviso.
        print("Aviso: Tentativa de uso do MT5 sem conexão ativa.")
        return None
    return mt5
