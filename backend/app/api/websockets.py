import asyncio
import json
from collections import defaultdict
from typing import Dict, List

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Query

from .. import mt5_connector
from ..mt5_connector import TIMEFRAME_MAP
from .history import fetch_rates_from_mt5, parse_and_localize_time
import pandas as pd

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        # Dicionário para manter conexões ativas por canal (ex: "WDOV25-M5")
        self.active_connections: Dict[str, List[WebSocket]] = defaultdict(list)
        # Dicionário para rastrear as tarefas de polling em background
        self.polling_tasks: Dict[str, asyncio.Task] = {}

    async def connect(self, websocket: WebSocket, channel: str):
        await websocket.accept()
        self.active_connections[channel].append(websocket)
        print(f"Nova conexão no canal {channel}. Total de conexões: {len(self.active_connections[channel])}")

        # Inicia a tarefa de polling se for a primeira conexão no canal
        if channel not in self.polling_tasks:
            print(f"Iniciando tarefa de polling para o canal {channel}...")
            self.polling_tasks[channel] = asyncio.create_task(self.poll_mt5_data(channel))

    def disconnect(self, websocket: WebSocket, channel: str):
        self.active_connections[channel].remove(websocket)
        print(f"Conexão fechada no canal {channel}. Total de conexões: {len(self.active_connections[channel])}")

        # Para a tarefa de polling se não houver mais ninguém no canal
        if not self.active_connections[channel]:
            print(f"Última conexão fechada. Parando tarefa de polling para o canal {channel}...")
            if channel in self.polling_tasks:
                self.polling_tasks[channel].cancel()
                del self.polling_tasks[channel]

    async def broadcast(self, message: str, channel: str):
        # Cria uma cópia da lista para evitar problemas de concorrência se a lista for modificada
        connections = self.active_connections[channel][:]
        for connection in connections:
            try:
                await connection.send_text(message)
            except WebSocketDisconnect:
                # A desconexão será tratada no endpoint principal
                pass
            except Exception as e:
                print(f"Erro ao enviar mensagem para o cliente no canal {channel}: {e}")

    async def poll_mt5_data(self, channel: str):
        symbol, timeframe_str = channel.split('-')
        timeframe_mt5 = TIMEFRAME_MAP[timeframe_str]
        last_candle_time = 0

        while True:
            try:
                mt5 = mt5_connector.get_mt5_instance()
                if not mt5_connector.is_connected():
                    await asyncio.sleep(5)
                    continue

                # Pega a vela mais recente
                rates = mt5.copy_rates_from_pos(symbol, timeframe_mt5, 0, 1)

                if rates is not None and len(rates) > 0:
                    candle = rates[0]
                    current_candle_time = int(candle['time'])

                    if current_candle_time >= last_candle_time:
                        last_candle_time = current_candle_time

                        candle_data = {
                            "time": current_candle_time,
                            "open": candle['open'],
                            "high": candle['high'],
                            "low": candle['low'],
                            "close": candle['close'],
                        }

                        message = json.dumps({"type": "candle", "data": candle_data})
                        await self.broadcast(message, channel)

                # Espera um tempo antes da próxima verificação.
                # Um valor curto (1s) garante atualizações rápidas do candle atual.
                await asyncio.sleep(1)

            except asyncio.CancelledError:
                print(f"Tarefa de polling para {channel} foi cancelada.")
                break
            except Exception as e:
                print(f"Erro na tarefa de polling para {channel}: {e}")
                await asyncio.sleep(10) # Espera um pouco mais em caso de erro

# Instância global do gerenciador
manager = ConnectionManager()

@router.websocket("/ws/candles")
async def websocket_endpoint(
    websocket: WebSocket,
    symbol: str = Query(...),
    timeframe: str = Query(..., regex="^(M1|M5|M15|M30|H1)$")
):
    if timeframe not in TIMEFRAME_MAP:
        # Idealmente, o cliente não deveria nem conseguir conectar com timeframe inválido,
        # mas é uma boa prática verificar.
        await websocket.close(code=4000, reason="Timeframe inválido")
        return

    channel = f"{symbol}-{timeframe}"
    await manager.connect(websocket, channel)

    try:
        while True:
            # Mantém a conexão viva, esperando por mensagens do cliente (se houver)
            # ou até que o cliente se desconecte.
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, channel)
