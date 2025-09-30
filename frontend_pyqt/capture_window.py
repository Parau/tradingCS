"""
Janela de exibição de capturas de tela.

Exibe uma ou mais regiões capturadas em layout grid/vertical,
com opções de configuração e redimensionamento proporcional.
"""

import logging
from typing import List

from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QPixmap, QPainter, QIcon
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QScrollArea, QPushButton, QApplication)

try:
    from capture_region_config_dialog import CaptureRegionConfigDialog
except ImportError:
    from .capture_region_config_dialog import CaptureRegionConfigDialog


class CaptureDisplayWidget(QLabel):
    """
    Widget que exibe uma captura de tela específica.
    
    Mantém proporção original e permite redimensionamento.
    """
    
    def __init__(self, region, parent=None):
        super().__init__(parent)
        self.region = region
        self.original_pixmap = None
        self.setMinimumSize(100, 100)
        self.setStyleSheet("border: 1px solid gray;")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Atualizado em: 2024-12-28 — PyQt6 moveu constantes para AlignmentFlag
        self.setText(f"Região: {region.display_id}\n({region.x1},{region.y1})-({region.x2},{region.y2})")

    def set_capture(self, pixmap: QPixmap):
        """
        Define a captura a ser exibida.
        
        Args:
            pixmap: Imagem capturada
        """
        self.original_pixmap = pixmap
        self._update_display()

    def _update_display(self):
        """Atualiza a exibição com o pixmap redimensionado."""
        if not self.original_pixmap:
            return
            
        # Redimensiona mantendo proporção
        scaled_pixmap = self.original_pixmap.scaled(
            self.size(), 
            Qt.AspectRatioMode.KeepAspectRatio,  # Atualizado em: 2024-12-28 — PyQt6 moveu constantes para AspectRatioMode
            Qt.TransformationMode.SmoothTransformation  # Atualizado em: 2024-12-28 — PyQt6 moveu constantes para TransformationMode
        )
        self.setPixmap(scaled_pixmap)

    def resizeEvent(self, event):
        """Redimensiona o conteúdo quando a janela é redimensionada."""
        super().resizeEvent(event)
        self._update_display()


class CaptureWindow(QWidget):
    """
    Janela principal de exibição de capturas.
    
    Exibe múltiplas regiões de captura em layout grid,
    com opções de configuração e controle.
    """
    
    def __init__(self, window_name: str, regions: List, manager, parent=None):
        super().__init__(parent)
        self.window_name = window_name
        self.regions = regions
        self.manager = manager
        self.logger = logging.getLogger(__name__)
        
        # Widgets de exibição
        self.display_widgets: List[CaptureDisplayWidget] = []
        
        self._setup_ui()
        self._setup_window_properties()

    def _setup_ui(self):
        """Configura a interface da janela."""
        layout = QVBoxLayout(self)
        
        # Barra de controle (mínima)
        control_layout = QHBoxLayout()
        
        # Botão de configuração
        config_btn = QPushButton("⚙")
        config_btn.setFixedSize(30, 30)
        config_btn.setToolTip("Configurações")
        config_btn.clicked.connect(self._show_config_dialog)
        
        # Botão sempre no topo
        self.always_on_top_btn = QPushButton("📌")
        self.always_on_top_btn.setFixedSize(30, 30)
        self.always_on_top_btn.setToolTip("Sempre no topo")
        self.always_on_top_btn.setCheckable(True)
        self.always_on_top_btn.clicked.connect(self._toggle_always_on_top)
        
        control_layout.addWidget(config_btn)
        control_layout.addWidget(self.always_on_top_btn)
        control_layout.addStretch()
        
        # Área de capturas
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        captures_widget = QWidget()
        self.captures_layout = QVBoxLayout(captures_widget)  # Pode mudar para grid depois
        
        # Cria widgets de exibição para cada região
        for region in self.regions:
            display_widget = CaptureDisplayWidget(region)
            self.display_widgets.append(display_widget)
            self.captures_layout.addWidget(display_widget)
        
        scroll_area.setWidget(captures_widget)
        
        layout.addLayout(control_layout)
        layout.addWidget(scroll_area)

    def _setup_window_properties(self):
        """Configura propriedades da janela."""
        self.setWindowTitle(f"Captura: {self.window_name}")
        self.resize(400, 300)
        
        # Define ícone se disponível
        try:
            self.setWindowIcon(QIcon("📹"))  # Fallback para emoji
        except:
            pass

    def _show_config_dialog(self):
        """Exibe diálogo de configuração."""
        dialog = CaptureRegionConfigDialog(self.regions, self.manager, self)
        if dialog.exec() == dialog.DialogCode.Accepted:  # Atualizado em: 2024-12-28 — PyQt6 moveu constantes para DialogCode
            # Atualizar regiões se necessário
            self.logger.info(f"Configuração atualizada para janela {self.window_name}")

    def _toggle_always_on_top(self):
        """Alterna modo 'sempre no topo'."""
        if self.always_on_top_btn.isChecked():
            self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)  # Atualizado em: 2024-12-28 — PyQt6 moveu constantes para WindowType
            self.always_on_top_btn.setToolTip("Desabilitar sempre no topo")
        else:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowStaysOnTopHint)  # Atualizado em: 2024-12-28 — PyQt6 moveu constantes para WindowType
            self.always_on_top_btn.setToolTip("Sempre no topo")
        
        self.show()  # Necessário para aplicar mudanças de flags

    def update_captures(self):
        """
        Atualiza todas as capturas de tela desta janela.
        
        Captura cada região configurada e atualiza os widgets correspondentes.
        """
        app = QApplication.instance()
        screens = app.screens()
        
        for i, (region, widget) in enumerate(zip(self.regions, self.display_widgets)):
            try:
                # Captura a região específica
                if region.display_id - 1 >= len(screens):
                    self.logger.error(f"Display {region.display_id} não existe")
                    continue
                    
                screen = screens[region.display_id - 1]  # 0-indexed
                
                # CORRIGIDO: Não precisa ajustar para coordenadas globais
                # O grabWindow de um screen específico já espera coordenadas relativas àquele screen
                # As coordenadas X1,Y1 do CSV já são relativas ao display específico
                
                # Captura a tela usando coordenadas RELATIVAS ao monitor
                pixmap = screen.grabWindow(0, region.x1, region.y1, 
                                         region.width, region.height)
                
                # Para depuração: registra as coordenadas e dimensões usadas
                self.logger.debug(f"Captura em Display {region.display_id}: ({region.x1},{region.y1}) "
                               f"tamanho {region.width}x{region.height}")
                
                widget.set_capture(pixmap)
                
            except Exception as e:
                self.logger.error(f"Erro ao capturar região {i}: {e}")

    def closeEvent(self, event):
        """Trata o fechamento da janela."""
        self.logger.info(f"Fechando janela de captura: {self.window_name}")
        event.accept()
