from fastapi import APIRouter, HTTPException, Path
from datetime import datetime, time
import pandas as pd
import pytz
import os
import logging

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()
SAO_PAULO_TZ = pytz.timezone("America/Sao_Paulo")
DATA_DIR = "backend/data"

from .history import fetch_rates_from_mt5, get_timeframe_map, parse_and_localize_time

def get_fluxo_compra_data(symbol: str, date_str: str, main_chart_data: list):
    """
    Reads and parses Fluxo Compra CSV data and aligns it with historical price data.
    """
    base_symbol = symbol.split('$')[0]
    filename = f"{base_symbol}_FC_{date_str}.csv"
    filepath = os.path.join(DATA_DIR, filename)
    logger.info(f"Procurando arquivo de fluxo de compra: {filepath}")

    if not os.path.exists(filepath):
        logger.warning(f"Arquivo de fluxo não encontrado para {symbol} na data {date_str}.")
        return [] # Return empty list if the file doesn't exist for the given day

    try:
        df = pd.read_csv(filepath, sep=',')
        df['DATETIME'] = pd.to_datetime(df['DATA'] + ' ' + df['HORA'], format='%Y.%m.%d %H:%M:%S')
        df['DATETIME'] = df['DATETIME'].apply(lambda x: SAO_PAULO_TZ.localize(x).astimezone(pytz.utc))
        logger.info(f"Arquivo {filename} lido com sucesso, {len(df)} sinais encontrados.")
    except Exception as e:
        logger.error(f"Erro ao processar o arquivo CSV {filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar o arquivo CSV: {e}")

    main_df = pd.DataFrame(main_chart_data)
    if main_df.empty:
        logger.warning("Dados históricos de candles estão vazios. Não é possível gerar o fluxo de compra.")
        return []
    main_df['time_dt'] = pd.to_datetime(main_df['time'], unit='s', utc=True)

    # 1. Find all active segments and their start prices
    active_segments = []
    is_compra_active = False
    start_time = None
    last_time = main_df['time_dt'].max()

    # Create a sorted list of all signals
    signals = [{'time': dt, 'type': sig} for dt, sig in zip(df['DATETIME'], df['SINAL'])]
    signals.sort(key=lambda x: x['time'])


    for signal in signals:
        if signal['type'] == 'LIGA_COMPRA' and not is_compra_active:
            is_compra_active = True
            start_time = signal['time']
        elif signal['type'] == 'DESLIGA_COMPRA' and is_compra_active:
            is_compra_active = False
            end_time = signal['time']
            # Find the price at the start of the segment
            start_candle = main_df[main_df['time_dt'] >= start_time].iloc[0]
            active_segments.append({'start': start_time, 'end': end_time, 'price': start_candle['close']})
            start_time = None

    # Handle case where the last signal was LIGA_COMPRA
    if is_compra_active and start_time:
        start_candle = main_df[main_df['time_dt'] >= start_time].iloc[0]
        active_segments.append({'start': start_time, 'end': last_time, 'price': start_candle['close']})

    # 2. Generate a point for every candle, marking it as active or not
    output_points = []
    for _, candle in main_df.iterrows():
        candle_time = candle['time_dt']
        is_in_segment = False
        flow_price = candle['close'] # Default to candle's own close price

        for segment in active_segments:
            if segment['start'] <= candle_time <= segment['end']:
                is_in_segment = True
                flow_price = segment['price'] # Use the segment's start price
                break

        output_points.append({
            'time': int(candle['time']),
            'value': flow_price,
            'active': is_in_segment
        })

    logger.info(f"Retornando {len(output_points)} pontos de dados para a linha de fluxo de compra.")
    return output_points

@router.get("/history/fluxo_compra/{symbol}/{date}/{timeframe}")
async def get_fluxo_compra(
    symbol: str = Path(..., description="Símbolo do ativo (ex: WDO)"),
    date: str = Path(..., description="Data no formato YYYY-MM-DD"),
    timeframe: str = Path(..., description="Timeframe (ex: M1, M5)")
):
    """
    Fornece dados de Fluxo de Compra para um ativo em uma data específica,
    alinhado com os candles do gráfico principal.
    """
    try:
        dt = datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de data inválido. Use YYYY-MM-DD.")

    start_utc = SAO_PAULO_TZ.localize(datetime.combine(dt.date(), time(9,0))).astimezone(pytz.utc)
    end_utc = SAO_PAULO_TZ.localize(datetime.combine(dt.date(), time(18,30))).astimezone(pytz.utc)

    timeframe_map = get_timeframe_map()
    if timeframe not in timeframe_map:
        raise HTTPException(status_code=400, detail=f"Timeframe inválido: '{timeframe}'.")

    timeframe_mt5 = timeframe_map[timeframe]

    main_chart_data = fetch_rates_from_mt5(symbol, timeframe_mt5, start_utc, end_utc)

    if not main_chart_data:
        return []

    return get_fluxo_compra_data(symbol, date, main_chart_data)