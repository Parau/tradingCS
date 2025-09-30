"""
Janela de overlay para exibir contornos das regiões capturadas.

Cria uma janela transparente e "click-through" que desenha
retângulos pontilhados nas posições das regiões de captura.
"""

import logging
from typing import List

from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QPainter, QPen, QColor
from PyQt6.QtWidgets import QWidget, QApplication


class OverlayWindow(QWidget):
    """
    Janela de overlay transparente para mostrar contornos das capturas.
    
    Desenha retângulos pontilhados nas coordenadas das regiões
    de captura configuradas, permitindo visualizar as áreas
    sendo monitoradas.
    """
    
    def __init__(self, regions: List, manager, parent=None):
        super().__init__(parent)
        self.regions = regions
        self.manager = manager
        self.logger = logging.getLogger(__name__)
        
        # Configuração de estilo padrão
        self.line_color = QColor("white")
        self.line_thickness = 2
        
        self._setup_window()

    def _setup_window(self):
        """Configura a janela de overlay."""
        # Configurações de transparência e click-through
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)  # Atualizado em: 2024-12-28 — PyQt6 moveu constantes para WidgetAttribute
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)  # Atualizado em: 2024-12-28 — PyQt6 moveu constantes para WidgetAttribute
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |  # Atualizado em: 2024-12-28 — PyQt6 moveu constantes para WindowType
            Qt.WindowType.WindowStaysOnTopHint |  # Atualizado em: 2024-12-28 — PyQt6 moveu constantes para WindowType
            Qt.WindowType.Tool  # Atualizado em: 2024-12-28 — PyQt6 moveu constantes para WindowType
        )
        
        # Posiciona sobre toda a área do desktop - Atualizado em: 2024-12-28 — PyQt6 não tem desktop()
        app = QApplication.instance()
        screens = app.screens()
        
        # Calcula área total de todos os monitores
        if screens:
            total_rect = screens[0].geometry()
            for screen in screens[1:]:
                screen_rect = screen.geometry()
                total_rect = total_rect.united(screen_rect)
        else:
            # Fallback se não houver telas
            total_rect = QRect(0, 0, 1920, 1080)
        
        self.setGeometry(total_rect)
        self.logger.info(f"Overlay criado cobrindo área: {total_rect}")

    def set_style(self, color: str, thickness: int):
        """
        Define o estilo dos contornos.
        
        Args:
            color: Cor das linhas (nome ou hex)
            thickness: Espessura das linhas em pixels
        """
        self.line_color = QColor(color)
        self.line_thickness = thickness
        self.update()  # Força redesenho

    def paintEvent(self, event):
        """
        Desenha os retângulos de overlay.
        
        Args:
            event: Evento de pintura
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)  # Atualizado em: 2024-12-28 — PyQt6 moveu constantes para RenderHint
        
        # Configura caneta pontilhada
        pen = QPen(self.line_color)
        pen.setWidth(self.line_thickness)
        pen.setStyle(Qt.PenStyle.DashLine)  # Atualizado em: 2024-12-28 — PyQt6 moveu constantes para PenStyle
        painter.setPen(pen)
        
        # Desenha retângulo para cada região - Atualizado em: 2024-12-28 — PyQt6 não tem desktop()
        app = QApplication.instance()
        screens = app.screens()
        
        for region in self.regions:
            try:
                # Converte coordenadas da região para coordenadas globais
                if region.display_id - 1 >= len(screens):
                    continue
                    
                screen = screens[region.display_id - 1]
                screen_geometry = screen.geometry()
                
                global_x = screen_geometry.x() + region.x1
                global_y = screen_geometry.y() + region.y1
                width = region.width
                height = region.height
                
                # Desenha o retângulo
                painter.drawRect(global_x, global_y, width, height)
                
                # Opcional: desenha texto identificador
                if self.line_thickness >= 2:  # Só se a linha for visível
                    painter.drawText(
                        global_x + 5, 
                        global_y + 15, 
                        f"{region.window_name}"
                    )
                    
            except Exception as e:
                self.logger.error(f"Erro ao desenhar overlay para região: {e}")

    def closeEvent(self, event):
        """Trata o fechamento da janela de overlay."""
        self.logger.info("Fechando janela de overlay")
        event.accept()
