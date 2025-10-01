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
    Layout otimizado para maximizar espaço de exibição do conteúdo capturado.
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
        """Configura a interface da janela otimizada para maximizar área de captura."""
        # Layout principal sem margens para maximizar espaço
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)  # Margens mínimas
        layout.setSpacing(2)  # Espaçamento mínimo entre elementos
        
        # Barra de controle compacta e minimalista
        control_layout = QHBoxLayout()
        control_layout.setContentsMargins(2, 2, 2, 2)  # Margens mínimas
        control_layout.setSpacing(2)  # Espaçamento mínimo entre botões
        
        # Botões com tamanho ainda mais compacto
        button_size = 24  # Reduzido de 30 para 24 pixels
        
        # Botão de configuração
        config_btn = QPushButton("⚙")
        config_btn.setFixedSize(button_size, button_size)
        config_btn.setToolTip("Configurações")
        config_btn.clicked.connect(self._show_config_dialog)
        config_btn.setStyleSheet("""
            QPushButton {
                border: 1px solid #666;
                border-radius: 3px;
                background-color: #f0f0f0;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
        """)
        
        # Botão sempre no topo
        self.always_on_top_btn = QPushButton("📌")
        self.always_on_top_btn.setFixedSize(button_size, button_size)
        self.always_on_top_btn.setToolTip("Sempre no topo")
        self.always_on_top_btn.setCheckable(True)
        self.always_on_top_btn.clicked.connect(self._toggle_always_on_top)
        self.always_on_top_btn.setStyleSheet("""
            QPushButton {
                border: 1px solid #666;
                border-radius: 3px;
                background-color: #f0f0f0;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:checked {
                background-color: #4a90e2;
                color: white;
            }
        """)
        
        # Label compacto com nome da janela (opcional, pode ser removido para mais espaço)
        window_label = QLabel(self.window_name)
        window_label.setStyleSheet("""
            QLabel {
                font-size: 10px;
                color: #666;
                font-weight: bold;
            }
        """)
        window_label.setMaximumHeight(16)  # Altura mínima
        
        # Organiza controles de forma compacta
        control_layout.addWidget(config_btn)
        control_layout.addWidget(self.always_on_top_btn)
        control_layout.addWidget(window_label)
        control_layout.addStretch()  # Empurra botões para a esquerda
        
        # Área de capturas otimizada para ocupar máximo espaço
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        # CORRIGIDO: Atualizado em: 2024-12-28 — PyQt6 usa ScrollBarAlwaysOff em vez de ScrollBarNever
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)  # Scroll vertical apenas quando necessário
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)  # Nunca exibe scroll horizontal
        scroll_area.setFrameStyle(0)  # Remove borda do scroll area
        
        captures_widget = QWidget()
        
        # Layout das capturas otimizado
        self.captures_layout = QVBoxLayout(captures_widget)
        self.captures_layout.setContentsMargins(0, 0, 0, 0)  # Remove margens completamente
        self.captures_layout.setSpacing(1)  # Espaçamento mínimo entre capturas
        
        # Cria widgets de exibição para cada região
        for region in self.regions:
            display_widget = CaptureDisplayWidget(region)
            
            # Otimiza o widget de exibição para ocupar mais espaço
            display_widget.setStyleSheet("""
                QLabel {
                    border: 1px solid #ddd;
                    background-color: #fafafa;
                    margin: 0px;
                }
            """)
            display_widget.setMinimumSize(150, 100)  # Tamanho mínimo maior para melhor visualização
            
            self.display_widgets.append(display_widget)
            self.captures_layout.addWidget(display_widget)
        
        scroll_area.setWidget(captures_widget)
        
        # Adiciona elementos ao layout principal priorizando espaço de captura
        layout.addLayout(control_layout)  # Controles ocupam espaço mínimo
        layout.addWidget(scroll_area, 1)  # Área de captura recebe todo o espaço restante (stretch factor = 1)

    def _setup_window_properties(self):
        """Configura propriedades da janela otimizada para exibição de conteúdo."""
        self.setWindowTitle(f"📹 {self.window_name}")  # Título mais compacto
        self.resize(450, 350)  # Tamanho inicial ligeiramente maior para melhor visualização
        
        # Remove decorações desnecessárias se possível
        # self.setWindowFlags(Qt.WindowType.FramelessWindowHint)  # Opcional: janela sem borda
        
        # Define ícone se disponível
        try:
            self.setWindowIcon(QIcon("📹"))  # Fallback para emoji
        except:
            pass
        
        # Otimizações de renderização
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent)  # Otimização de pintura
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)  # Remove background sistema

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
