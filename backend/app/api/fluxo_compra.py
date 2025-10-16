from fastapi import APIRouter, HTTPException, Path
from datetime import datetime, time
import pandas as pd
import pytz
import os

router = APIRouter()
SAO_PAULO_TZ = pytz.timezone("America/Sao_Paulo")
DATA_DIR = "backend/data"

from .history import fetch_rates_from_mt5, get_timeframe_map, parse_and_localize_time

def get_fluxo_compra_data(symbol: str, date_str: str, main_chart_data: list):
    """
    Reads and parses Fluxo Compra CSV data and aligns it with historical price data.
    """
    filename = f"{symbol}_FC_{date_str}.csv"
    filepath = os.path.join(DATA_DIR, filename)

    if not os.path.exists(filepath):
        return [] # Return empty list if the file doesn't exist for the given day

    try:
        df = pd.read_csv(filepath, sep='\t')
        df['DATETIME'] = pd.to_datetime(df['DATA'] + ' ' + df['HORA'], format='%Y.%m.%d %H:%M:%S')
        df['DATETIME'] = df['DATETIME'].apply(lambda x: SAO_PAULO_TZ.localize(x).astimezone(pytz.utc))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar o arquivo CSV: {e}")

    main_df = pd.DataFrame(main_chart_data)
    if main_df.empty:
        return []
    main_df['time'] = pd.to_datetime(main_df['time'], unit='s', utc=True)

    lines = []
    is_compra_active = False
    start_time = None

    all_events = []
    for _, row in df.iterrows():
        all_events.append({'time': row['DATETIME'], 'type': row['SINAL']})

    # Add a synthetic "end of day" event to handle open ranges
    last_time = main_df['time'].max()
    all_events.append({'time': last_time, 'type': 'END_OF_DAY'})

    all_events.sort(key=lambda x: x['time'])

    for event in all_events:
        if event['type'] == 'LIGA_COMPRA' and not is_compra_active:
            is_compra_active = True
            start_time = event['time']
        elif event['type'] == 'DESLIGA_COMPRA' and is_compra_active:
            is_compra_active = False
            end_time = event['time']
            segment_df = main_df[(main_df['time'] >= start_time) & (main_df['time'] <= end_time)]
            if not segment_df.empty:
                price = segment_df['close'].iloc[0] # Use the price at the start of the segment
                for _, candle in segment_df.iterrows():
                    lines.append({'time': int(candle['time'].timestamp()), 'value': price})
            start_time = None
        elif event['type'] == 'END_OF_DAY' and is_compra_active:
            end_time = event['time']
            segment_df = main_df[(main_df['time'] >= start_time) & (main_df['time'] <= end_time)]
            if not segment_df.empty:
                price = segment_df['close'].iloc[0]
                for _, candle in segment_df.iterrows():
                    lines.append({'time': int(candle['time'].timestamp()), 'value': price})
            is_compra_active = False


    return lines

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