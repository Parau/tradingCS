"""
Gerenciador principal do sistema de captura de tela.

Este módulo coordena a captura de múltiplas regiões de tela e sua exibição
em janelas independentes, seguindo configuração definida em arquivo CSV.
"""

import csv
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path

from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QScreen

try:
    from capture_window import CaptureWindow
    from overlay_window import OverlayWindow
except ImportError:
    from .capture_window import CaptureWindow
    from .overlay_window import OverlayWindow


@dataclass
class CaptureRegion:
    """
    Representa uma região de captura de tela.
    
    Args:
        window_name: Nome da janela que exibirá esta captura
        display_id: ID do monitor (1..N)
        x1, y1: Coordenadas do canto superior esquerdo
        x2, y2: Coordenadas do canto inferior direito
    """
    window_name: str
    display_id: int
    x1: int
    y1: int
    x2: int
    y2: int

    @property
    def width(self) -> int:
        return self.x2 - self.x1

    @property
    def height(self) -> int:
        return self.y2 - self.y1


class CaptureManager(QObject):
    """
    Gerenciador principal do sistema de captura de tela.
    
    Responsável por:
    - Carregar configuração do CSV
    - Criar e gerenciar janelas de captura
    - Controlar overlay de contornos
    - Coordenar atualizações em tempo real
    """
    
    error_occurred = pyqtSignal(str)
    
    def __init__(self, csv_file_path: str = "config_capture_rect.csv"):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.csv_file_path = csv_file_path
        
        # Configurações padrão
        self.fps = 5
        self.overlay_enabled = False
        self.overlay_color = "white"
        self.overlay_thickness = 2
        
        # Estado interno
        self.regions: List[CaptureRegion] = []
        self.capture_windows: Dict[str, CaptureWindow] = {}
        self.overlay_window: Optional[OverlayWindow] = None
        self.update_timer = QTimer()
        
        self._setup_timer()
        self._log_available_displays()

    def _log_available_displays(self):
        """
        Imprime informações sobre todos os displays disponíveis no sistema.
        
        Lista cada display com seu ID (para uso no CSV), nome, resolução e posição.
        Útil para configurar corretamente as regiões de captura.
        """
        app = QApplication.instance()
        if not app:
            self.logger.warning("QApplication não encontrada para listar displays")
            return
            
        screens = app.screens()
        
        print("\n" + "="*60)
        print("SISTEMA DE CAPTURA - DISPLAYS DISPONÍVEIS")
        print("="*60)
        
        if not screens:
            print("❌ Nenhum display encontrado!")
            self.logger.error("Nenhum display disponível no sistema")
            return
        
        print(f"📺 Total de displays encontrados: {len(screens)}")
        print()
        
        for i, screen in enumerate(screens):
            display_id = i + 1  # IDs começam em 1 para o CSV
            geometry = screen.geometry()
            available_geometry = screen.availableGeometry()
            
            print(f"Display ID: {display_id}")
            print(f"  Nome: {screen.name()}")
            print(f"  Resolução: {geometry.width()} x {geometry.height()} pixels")
            print(f"  Posição: ({geometry.x()}, {geometry.y()})")
            print(f"  Área total: {geometry.width()} x {geometry.height()}")
            print(f"  Área disponível: {available_geometry.width()} x {available_geometry.height()}")
            print(f"  DPI: {screen.logicalDotsPerInch():.1f}")
            print(f"  Fator de escala: {screen.devicePixelRatio():.2f}")
            
            # Indica se é o display primário
            if screen == app.primaryScreen():
                print(f"  🌟 Display PRIMÁRIO")
            
            print()
        
        print("💡 DICA: Use o 'Display ID' no campo ID_DISPLAY do seu CSV")
        print("💡 Coordenadas X1,Y1,X2,Y2 são relativas ao display específico")
        print("💡 Exemplo para capturar canto superior esquerdo do Display 1:")
        print("   NOME_JANELA, ID_DISPLAY, X1, Y1, X2, Y2")
        print("   MinhaJanela, 1, 0, 0, 300, 200")
        print("="*60 + "\n")
        
        # Log também para o arquivo de log
        self.logger.info(f"Sistema iniciado com {len(screens)} display(s) disponível(is)")
        for i, screen in enumerate(screens):
            geometry = screen.geometry()
            self.logger.info(f"Display {i+1}: {screen.name()} - "
                           f"{geometry.width()}x{geometry.height()} @ ({geometry.x()},{geometry.y()})")

    def _setup_timer(self):
        """Configura o timer de atualização das capturas."""
        self.update_timer.timeout.connect(self._update_captures)
        self.update_timer.setInterval(1000 // self.fps)  # Converte FPS para milliseconds

    def load_config(self, csv_file_path: Optional[str] = None) -> bool:
        """
        Carrega configuração do arquivo CSV.
        
        Args:
            csv_file_path: Caminho do arquivo CSV (opcional)
            
        Returns:
            True se carregou com sucesso, False caso contrário
        """
        if csv_file_path:
            self.csv_file_path = csv_file_path
            
        try:
            regions = self._parse_csv()
            if not regions:
                self.error_occurred.emit("Nenhuma região válida encontrada no CSV")
                return False
                
            self.regions = regions
            self.logger.info(f"Carregadas {len(self.regions)} regiões de captura")
            return True
            
        except Exception as e:
            error_msg = f"Erro ao carregar configuração: {str(e)}"
            self.logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return False

    def _parse_csv(self) -> List[CaptureRegion]:
        """
        Analisa o arquivo CSV e retorna lista de regiões válidas.
        
        Returns:
            Lista de regiões de captura válidas
        """
        regions = []
        csv_path = Path(self.csv_file_path)
        
        if not csv_path.exists():
            raise FileNotFoundError(f"Arquivo CSV não encontrado: {self.csv_file_path}")
        
        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file, skipinitialspace=True)
            
            for row_num, row in enumerate(reader, start=2):  # Start at 2 for header
                try:
                    region = self._parse_csv_row(row)
                    if region and self._validate_region(region):
                        regions.append(region)
                        
                except Exception as e:
                    self.logger.warning(f"Linha {row_num} inválida: {e}")
                    
        return regions

    def _parse_csv_row(self, row: Dict[str, str]) -> Optional[CaptureRegion]:
        """
        Converte uma linha do CSV em CaptureRegion.
        
        Args:
            row: Dicionário com dados da linha CSV
            
        Returns:
            CaptureRegion se válida, None caso contrário
        """
        try:
            return CaptureRegion(
                window_name=row['NOME_JANELA'].strip(),
                display_id=int(row['ID_DISPLAY']),
                x1=int(row['X1']),
                y1=int(row['Y1']),
                x2=int(row['X2']),
                y2=int(row['Y2'])
            )
        except (KeyError, ValueError) as e:
            raise ValueError(f"Formato inválido: {e}")

    def _validate_region(self, region: CaptureRegion) -> bool:
        """
        Valida se uma região de captura é válida.
        
        Args:
            region: Região a ser validada
            
        Returns:
            True se válida, False caso contrário
        """
        # Validar dimensões
        if region.x2 <= region.x1 or region.y2 <= region.y1:
            self.logger.warning(f"Dimensões inválidas para {region.window_name}: "
                              f"({region.x1},{region.y1}) -> ({region.x2},{region.y2})")
            return False
        
        # Validar se display existe - Atualizado em: 2024-12-28 — PyQt6 não tem desktop()
        app = QApplication.instance()
        screens = app.screens()
        if region.display_id < 1 or region.display_id > len(screens):
            self.logger.warning(f"Display ID inválido: {region.display_id}")
            return False
        
        # Validar se região cabe no monitor
        screen = screens[region.display_id - 1]  # 0-indexed
        screen_geometry = screen.geometry()
        if (region.x2 > screen_geometry.width() or 
            region.y2 > screen_geometry.height() or
            region.x1 < 0 or region.y1 < 0):
            self.logger.warning(f"Região fora dos limites do monitor {region.display_id}")
            return False
            
        return True

    def start_capture(self):
        """Inicia o sistema de captura."""
        if not self.regions:
            self.error_occurred.emit("Nenhuma região configurada. Carregue um arquivo CSV primeiro.")
            return
            
        self._create_capture_windows()
        self._create_overlay_window()
        self.update_timer.start()
        self.logger.info("Sistema de captura iniciado")

    def stop_capture(self):
        """Para o sistema de captura."""
        self.update_timer.stop()
        self._close_all_windows()
        self.logger.info("Sistema de captura parado")

    def _create_capture_windows(self):
        """Cria janelas de captura baseadas nas regiões configuradas."""
        # Agrupa regiões por nome da janela
        windows_regions = {}
        for region in self.regions:
            if region.window_name not in windows_regions:
                windows_regions[region.window_name] = []
            windows_regions[region.window_name].append(region)
        
        # Cria uma janela para cada grupo
        for window_name, regions in windows_regions.items():
            window = CaptureWindow(window_name, regions, self)
            self.capture_windows[window_name] = window
            window.show()

    def _create_overlay_window(self):
        """Cria janela de overlay se habilitada."""
        if self.overlay_enabled:
            self.overlay_window = OverlayWindow(self.regions, self)
            self.overlay_window.set_style(self.overlay_color, self.overlay_thickness)
            self.overlay_window.show()

    def _update_captures(self):
        """Atualiza todas as capturas de tela."""
        for window in self.capture_windows.values():
            window.update_captures()

    def _close_all_windows(self):
        """Fecha todas as janelas abertas."""
        for window in self.capture_windows.values():
            window.close()
        self.capture_windows.clear()
        
        if self.overlay_window:
            self.overlay_window.close()
            self.overlay_window = None

    # Métodos de configuração
    def set_fps(self, fps: int):
        """Define a taxa de atualização (FPS)."""
        self.fps = max(1, min(30, fps))  # Limita entre 1-30 FPS
        self.update_timer.setInterval(1000 // self.fps)
        self.logger.info(f"FPS definido para: {self.fps}")

    def set_overlay_enabled(self, enabled: bool):
        """Habilita/desabilita o overlay."""
        self.overlay_enabled = enabled
        
        if enabled and not self.overlay_window and self.regions:
            self._create_overlay_window()
        elif not enabled and self.overlay_window:
            self.overlay_window.close()
            self.overlay_window = None

    def set_overlay_style(self, color: str, thickness: int):
        """Define estilo do overlay."""
        self.overlay_color = color
        self.overlay_thickness = thickness
        
        if self.overlay_window:
            self.overlay_window.set_style(color, thickness)

    def get_config(self) -> Dict:
        """Retorna configuração atual."""
        return {
            'fps': self.fps,
            'overlay_enabled': self.overlay_enabled,
            'overlay_color': self.overlay_color,
            'overlay_thickness': self.overlay_thickness,
            'csv_file': self.csv_file_path,
            'regions_count': len(self.regions)
        }

    def update_regions(self, new_regions: List[CaptureRegion]):
        """
        Atualiza as regiões de captura e reinicia o sistema se necessário.
        
        Args:
            new_regions: Lista de novas regiões de captura
        """
        was_running = self.update_timer.isActive()
        
        # Para o sistema se estiver rodando
        if was_running:
            self.stop_capture()
        
        # Atualiza as regiões
        self.regions = new_regions
        
        # Reinicia se estava rodando
        if was_running:
            self.start_capture()  # Sempre reinicia para recriar as janelas
            
        self.logger.info(f"Regiões atualizadas: {len(new_regions)} regiões ativas")
