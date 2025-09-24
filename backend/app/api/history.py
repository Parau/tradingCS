from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, timezone
import pandas as pd
import pytz
from functools import lru_cache

from .. import mt5_connector
from ..mt5_connector import TIMEFRAME_MAP

router = APIRouter()

# Timezone de São Paulo para usar como padrão
SAO_PAULO_TZ = pytz.timezone("America/Sao_Paulo")

_TIMEFRAME_MAP = None

def get_timeframe_map():
    """
    Retorna o mapeamento de timeframes. Inicializa na primeira chamada
    para garantir que a conexão com o MT5 já exista.
    
    Returns:
        dict: Mapeamento de strings para constantes MT5
        
    Raises:
        HTTPException: Se o MT5 não estiver disponível
    """
    global _TIMEFRAME_MAP
    if _TIMEFRAME_MAP is None:
        mt5 = mt5_connector.get_mt5_instance()
        if not mt5:
             raise HTTPException(status_code=503, detail="Serviço MT5 indisponível para mapear timeframes.")
        _TIMEFRAME_MAP = {
            "M1": mt5.TIMEFRAME_M1, "M5": mt5.TIMEFRAME_M5, "M15": mt5.TIMEFRAME_M15,
            "M30": mt5.TIMEFRAME_M30, "H1": mt5.TIMEFRAME_H1,
        }
    return _TIMEFRAME_MAP

def parse_and_localize_time(time_str: str) -> datetime:
    """
    Converte uma string ISO 8601 para um objeto datetime timezone-aware em UTC.
    
    Para sistemas de trading, é crítico normalizar todos os horários para UTC
    internamente, mesmo que o usuário trabalhe em horário local do mercado.
    
    Args:
        time_str (str): String no formato ISO-8601
        
    Returns:
        datetime: Objeto datetime em UTC, timezone-aware
        
    Raises:
        HTTPException: Se o formato da string for inválido
        
    Note:
        Se time_str não tiver timezone, assume America/Sao_Paulo (horário B3)
    """
    try:
        dt = datetime.fromisoformat(time_str)
        if dt.tzinfo is None:
            # Se não tiver fuso horário, assume que é de São Paulo
            dt = SAO_PAULO_TZ.localize(dt)
        # Converte para UTC para a chamada ao MT5
        return dt.astimezone(timezone.utc)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail=f"Formato de data/hora inválido: '{time_str}'. Use ISO-8601.")

@lru_cache(maxsize=128)
def fetch_rates_from_mt5(symbol: str, timeframe_mt5: int, start_utc: datetime, end_utc: datetime):
    """
    Função cacheável que busca dados históricos do MT5.
    
    Args:
        symbol (str): Símbolo do ativo (ex: 'WDOV25')
        timeframe_mt5 (int): Constante de timeframe do MT5
        start_utc (datetime): Data/hora início em UTC
        end_utc (datetime): Data/hora fim em UTC
        
    Returns:
        list: Lista de dicionários com dados OHLC compatíveis com Lightweight Charts
        
    Raises:
        HTTPException: Se o MT5 não estiver conectado
        
    Note:
        O campo 'time' retornado é Unix timestamp (epoch seconds) em UTC,
        conforme esperado pelos sistemas de charting financeiro.
    """
    print(f"Buscando dados no MT5 para {symbol} de {start_utc} a {end_utc}...")
    mt5 = mt5_connector.get_mt5_instance()
    if not mt5_connector.is_connected():
        raise HTTPException(status_code=503, detail="Serviço MT5 indisponível.")

    # MT5 espera datetimes em UTC
    rates = mt5.copy_rates_range(symbol, timeframe_mt5, start_utc, end_utc)

    if rates is None or len(rates) == 0:
        print(f"Nenhum dado retornado do MT5. Erro: {mt5.last_error()}")
        return []

    # Converte para DataFrame do Pandas para facilitar a manipulação
    df = pd.DataFrame(rates)
    # Converte a coluna 'time' para o formato de timestamp Unix (segundos), que é o que a LW-Charts espera
    df['time'] = df['time'].astype(int)
    # Renomeia colunas se necessário (o MT5 já retorna 'open', 'high', 'low', 'close')
    # Seleciona apenas as colunas necessárias para a resposta
    df = df[['time', 'open', 'high', 'low', 'close']]

    # Converte o DataFrame para uma lista de dicionários e retorna
    return df.to_dict(orient='records')

@router.get("/history/{symbol}")
async def get_history(
    symbol: str,
    timeframe: str = Query(..., regex="^(M1|M5|M15|M30|H1)$"),
    start: str = Query(..., description="Data de início no formato ISO-8601"),
    end: str = Query(..., description="Data de fim no formato ISO-8601")
):
    """
    Fornece dados históricos de candlesticks para um ativo.
    
    Este endpoint segue as práticas padrão de sistemas de trading:
    - Aceita horários em ISO-8601 (com ou sem timezone)
    - Normaliza internamente para UTC
    - Retorna timestamps Unix (epoch seconds) compatíveis com charting libs
    
    Args:
        symbol (str): Símbolo do ativo
        timeframe (str): Período (M1, M5, M15, M30, H1)
        start (str): Data/hora início
        end (str): Data/hora fim
        
    Returns:
        list: Array de objetos OHLC com timestamps Unix
        
    Example:
        GET /api/history/WDOV25?timeframe=M5&start=2025-09-20T09:00:00&end=2025-09-20T18:00:00
    """
    timeframe_map = get_timeframe_map()
    if timeframe not in timeframe_map:
        raise HTTPException(status_code=400, detail=f"Timeframe inválido: '{timeframe}'. Use M1, M5, M15, M30 ou H1.")

    timeframe_mt5 = timeframe_map[timeframe]
    start_utc = parse_and_localize_time(start)
    end_utc = parse_and_localize_time(end)

    if start_utc >= end_utc:
        raise HTTPException(status_code=400, detail="A data de início deve ser anterior à data de fim.")

    try:
        # A chamada à função cacheada é síncrona, mas como o I/O do MT5 é rápido
        # e a função é cacheada, o impacto no event loop é minimizado.
        # Para operações muito longas, usaríamos `run_in_executor`.
        data = fetch_rates_from_mt5(symbol, timeframe_mt5, start_utc, end_utc)
        if not data:
             # Retorna lista vazia com status 200 se não houver dados no período,
             # mas o MT5 não deu erro.
            return []
        return data
    except Exception as e:
        # Captura outras exceções inesperadas
        raise HTTPException(status_code=500, detail=f"Erro interno ao buscar dados: {e}")
