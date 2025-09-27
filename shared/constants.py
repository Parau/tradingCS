"""
Constantes compartilhadas do sistema de trading.

Este módulo centraliza constantes utilizadas em múltiplos componentes
do sistema (backend FastAPI e frontend PyQt), garantindo consistência
e facilitando manutenção futura.

Localização: Diretório `shared/` na raiz do projeto para facilitar
importação tanto pelo backend quanto pelo frontend.
"""

from typing import List, Literal

# Tipos de marcação suportados pelo sistema
# Utilizados tanto na validação do backend quanto na UI do frontend
MARKER_TYPES: List[str] = ["POC_VENDA", "POC_COMPRA", "AJUSTE"]

# Tipo literal para validação de tipos no Pydantic (backend)
MarkerTypeEnum = Literal['POC_VENDA', 'POC_COMPRA', 'AJUSTE']
