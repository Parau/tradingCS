import json
import asyncio
from typing import List
import sys
import os

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field

# Adiciona o diretório shared ao path para importação das constantes
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'shared'))
from constants import MarkerTypeEnum

# Importa o gerenciador de conexões do módulo de websockets
from .websockets import manager

router = APIRouter()

# --- Modelos Pydantic para Validação ---

class MarkerItem(BaseModel):
    """Define a estrutura de um único item de marcação."""
    Data: str = Field(..., description="Data da marcação no formato YYYY-MM-DD")
    Hora: str = Field(..., description="Hora da marcação no formato HH:MM")
    Preco: float = Field(...,  description="Preço da marcação")
    Tipo: MarkerTypeEnum = Field(..., description="Tipo da marcação")


class MarkerData(BaseModel):
    """Define a estrutura do corpo da requisição para o endpoint de marcações."""
    symbol: str = Field(..., description="O símbolo do ativo ao qual as marcações se aplicam, ex: WDOV25")
    markers: List[MarkerItem]

# --- Endpoint HTTP ---

@router.post("/markers")
async def receive_and_broadcast_markers(data: MarkerData = Body(...)):
    """
    Recebe uma lista de marcações de um cliente (ex: PyQt UI) e
    as transmite para os clientes web conectados via WebSocket.
    """
    # O canal é composto pelo símbolo e pode ser estendido se necessário.
    # Por agora, vamos assumir que as marcações de um símbolo vão para todos os
    # websockets abertos para aquele símbolo, independente do timeframe.
    # Uma lógica mais granular poderia ser implementada se necessário.

    # Encontra todos os canais de websocket que começam com o símbolo.
    # Ex: se o symbol é "WDOV25", vai corresponder a "WDOV25-M1", "WDOV25-M5", etc.
    relevant_channels = [ch for ch in manager.active_connections if ch.startswith(data.symbol)]

    if not relevant_channels:
        # Ninguém está ouvindo, mas a requisição foi bem-sucedida.
        # Poderíamos logar isso ou apenas retornar.
        return {"status": "ok", "message": f"Nenhum cliente web ouvindo para o símbolo {data.symbol}."}

    try:
        # Prepara a mensagem para ser enviada via WebSocket.
        # O Pydantic já validou a estrutura, agora convertemos para um dict.
        message_payload = {
            "type": "markers",
            "data": [marker.dict(by_alias=True) for marker in data.markers]
        }
        message_str = json.dumps(message_payload)

        # Transmite a mensagem para todos os canais relevantes.
        broadcast_tasks = [manager.broadcast(message_str, channel) for channel in relevant_channels]
        await asyncio.gather(*broadcast_tasks)

        return {"status": "ok", "message": f"Marcações para {data.symbol} transmitidas para {len(relevant_channels)} canais."}

    except Exception as e:
        # Captura erros inesperados durante a transmissão
        raise HTTPException(status_code=500, detail=f"Erro ao transmitir marcações: {e}")
