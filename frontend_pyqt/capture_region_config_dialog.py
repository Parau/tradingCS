"""
Diálogo de configuração para regiões de captura e opções do sistema.

Permite editar coordenadas das regiões, configurar FPS,
overlay e outras opções do sistema de captura.
"""

import logging
import csv
from typing import List
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
                           QGroupBox, QFormLayout, QSpinBox, QLineEdit,
                           QCheckBox, QComboBox, QPushButton, QTableWidget,
                           QTableWidgetItem, QHeaderView, QColorDialog,
                           QLabel, QSlider, QMessageBox, QWidget, QApplication)  # Atualizado em: 2024-12-28 — Adicionado QApplication ao import para resolver erro de nome não definido
from PyQt6.QtGui import QColor


class CaptureRegionConfigDialog(QDialog):
    """
    Diálogo de configuração completo do sistema de captura.
    
    Organizado em abas para diferentes aspectos da configuração:
    - Regiões: edição das coordenadas e displays
    - Sistema: FPS, overlay, etc.
    """
    
    def __init__(self, regions: List, manager, parent=None):
        super().__init__(parent)
        self.regions = regions
        self.manager = manager
        self.logger = logging.getLogger(__name__)
        
        self._setup_ui()
        self._load_current_config()

    def _setup_ui(self):
        """Configura a interface do diálogo."""
        self.setWindowTitle("Configurações de Captura")
        self.setModal(True)
        self.resize(600, 400)
        
        layout = QVBoxLayout(self)
        
        # Abas principais
        tab_widget = QTabWidget()
        
        # Aba de regiões
        regions_tab = self._create_regions_tab()
        tab_widget.addTab(regions_tab, "Regiões")
        
        # Aba de sistema
        system_tab = self._create_system_tab()
        tab_widget.addTab(system_tab, "Sistema")
        
        # Aba de overlay
        overlay_tab = self._create_overlay_tab()
        tab_widget.addTab(overlay_tab, "Overlay")
        
        layout.addWidget(tab_widget)
        
        # Botões de ação
        buttons_layout = QHBoxLayout()
        
        self.save_positions_btn = QPushButton("Salvar Posição Janelas")
        self.save_positions_btn.clicked.connect(self._save_window_positions)
        
        self.apply_btn = QPushButton("Aplicar")
        self.apply_btn.clicked.connect(self._apply_changes)
        
        self.ok_btn = QPushButton("OK")
        self.ok_btn.clicked.connect(self._ok_clicked)
        
        self.cancel_btn = QPushButton("Cancelar")
        self.cancel_btn.clicked.connect(self.reject)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.save_positions_btn)
        buttons_layout.addWidget(self.apply_btn)
        buttons_layout.addWidget(self.ok_btn)
        buttons_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(buttons_layout)

    def _create_regions_tab(self):
        """Cria aba de configuração das regiões."""
        # Criar widget container - Atualizado em: 2024-12-28 — QTabWidget precisa de QWidget, não QLayout
        regions_widget = QWidget()
        layout = QVBoxLayout(regions_widget)
        
        # Tabela de regiões
        self.regions_table = QTableWidget()
        self.regions_table.setColumnCount(6)
        self.regions_table.setHorizontalHeaderLabels([
            "Janela", "Display", "X1", "Y1", "X2", "Y2"
        ])
        
        # Ajusta colunas - Atualizado em: 2024-12-28 — PyQt6 moveu constantes para ResizeMode
        header = self.regions_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in range(1, 6):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        
        layout.addWidget(self.regions_table)
        
        # Botões de região
        region_buttons = QHBoxLayout()
        
        add_region_btn = QPushButton("Adicionar Região")
        add_region_btn.clicked.connect(self._add_region)
        
        remove_region_btn = QPushButton("Remover Região")
        remove_region_btn.clicked.connect(self._remove_region)
        
        region_buttons.addWidget(add_region_btn)
        region_buttons.addWidget(remove_region_btn)
        region_buttons.addStretch()
        
        layout.addLayout(region_buttons)
        
        return regions_widget

    def _create_system_tab(self):
        """Cria aba de configurações do sistema."""
        # Criar widget container - Atualizado em: 2024-12-28 — QTabWidget precisa de QWidget, não QLayout
        system_widget = QWidget()
        container = QVBoxLayout(system_widget)
        
        group = QGroupBox("Configurações Gerais")
        layout = QFormLayout(group)
        
        # FPS
        self.fps_spinbox = QSpinBox()
        self.fps_spinbox.setRange(1, 30)
        self.fps_spinbox.setSuffix(" FPS")
        layout.addRow("Taxa de Atualização:", self.fps_spinbox)
        
        # Sempre no topo (global)
        self.global_always_on_top = QCheckBox("Todas as janelas sempre no topo")
        layout.addRow(self.global_always_on_top)
        
        container.addWidget(group)
        container.addStretch()
        
        return system_widget

    def _create_overlay_tab(self):
        """Cria aba de configurações do overlay."""
        # Criar widget container - Atualizado em: 2024-12-28 — QTabWidget precisa de QWidget, não QLayout
        overlay_widget = QWidget()
        container = QVBoxLayout(overlay_widget)
        
        group = QGroupBox("Configurações do Overlay")
        layout = QFormLayout(group)
        
        # Habilitar overlay
        self.overlay_enabled = QCheckBox("Exibir contornos no desktop")
        layout.addRow(self.overlay_enabled)
        
        # Cor
        color_layout = QHBoxLayout()
        self.overlay_color_label = QLabel("■")
        self.overlay_color_label.setStyleSheet("font-size: 20px; color: white;")
        
        self.color_btn = QPushButton("Escolher Cor")
        self.color_btn.clicked.connect(self._choose_overlay_color)
        
        color_layout.addWidget(self.overlay_color_label)
        color_layout.addWidget(self.color_btn)
        color_layout.addStretch()
        
        layout.addRow("Cor:", color_layout)
        
        # Espessura
        thickness_layout = QHBoxLayout()
        self.thickness_slider = QSlider(Qt.Orientation.Horizontal)  # Atualizado em: 2024-12-28 — PyQt6 moveu constantes para Orientation
        self.thickness_slider.setRange(1, 10)
        self.thickness_slider.valueChanged.connect(self._update_thickness_label)
        
        self.thickness_label = QLabel("2 px")
        
        thickness_layout.addWidget(self.thickness_slider)
        thickness_layout.addWidget(self.thickness_label)
        
        layout.addRow("Espessura:", thickness_layout)
        
        container.addWidget(group)
        container.addStretch()
        
        return overlay_widget

    def _load_current_config(self):
        """Carrega configuração atual nos controles."""
        config = self.manager.get_config()
        
        # Sistema
        self.fps_spinbox.setValue(config['fps'])
        
        # Overlay
        self.overlay_enabled.setChecked(config['overlay_enabled'])
        self.thickness_slider.setValue(config['overlay_thickness'])
        self._update_thickness_label()
        self._set_overlay_color(config['overlay_color'])
        
        # Regiões
        self._populate_regions_table()

    def _populate_regions_table(self):
        """Popula a tabela com as regiões atuais."""
        self.regions_table.setRowCount(len(self.regions))
        
        for i, region in enumerate(self.regions):
            self.regions_table.setItem(i, 0, QTableWidgetItem(region.window_name))
            self.regions_table.setItem(i, 1, QTableWidgetItem(str(region.display_id)))
            self.regions_table.setItem(i, 2, QTableWidgetItem(str(region.x1)))
            self.regions_table.setItem(i, 3, QTableWidgetItem(str(region.y1)))
            self.regions_table.setItem(i, 4, QTableWidgetItem(str(region.x2)))
            self.regions_table.setItem(i, 5, QTableWidgetItem(str(region.y2)))

    def _add_region(self):
        """Adiciona nova linha para região."""
        row = self.regions_table.rowCount()
        self.regions_table.insertRow(row)
        
        # Valores padrão
        self.regions_table.setItem(row, 0, QTableWidgetItem("NovaJanela"))
        self.regions_table.setItem(row, 1, QTableWidgetItem("1"))
        self.regions_table.setItem(row, 2, QTableWidgetItem("0"))
        self.regions_table.setItem(row, 3, QTableWidgetItem("0"))
        self.regions_table.setItem(row, 4, QTableWidgetItem("100"))
        self.regions_table.setItem(row, 5, QTableWidgetItem("100"))

    def _remove_region(self):
        """Remove região selecionada."""
        current_row = self.regions_table.currentRow()
        if current_row >= 0:
            self.regions_table.removeRow(current_row)

    def _choose_overlay_color(self):
        """Abre diálogo de seleção de cor."""
        color = QColorDialog.getColor(QColor(self.manager.overlay_color), self)
        if color.isValid():
            self._set_overlay_color(color.name())

    def _set_overlay_color(self, color_name: str):
        """Define cor do overlay nos controles."""
        self.overlay_color = color_name
        self.overlay_color_label.setStyleSheet(f"font-size: 20px; color: {color_name};")

    def _update_thickness_label(self):
        """Atualiza label da espessura."""
        value = self.thickness_slider.value()
        self.thickness_label.setText(f"{value} px")

    def _save_window_positions(self):
        """
        Salva as posições atuais das janelas de captura em config_capture_win_pos.csv.
        
        Coleta informações de cada janela: nome, display ID, posição X/Y, largura e altura.
        """
        try:
            csv_path = Path("config_capture_win_pos.csv")
            
            # Coleta dados das janelas
            window_data = []
            app = self.manager.app if hasattr(self.manager, 'app') else None
            if not app:
                app = QApplication.instance()
            
            screens = app.screens() if app else []
            
            for window_name, window in self.manager.capture_windows.items():
                try:
                    # Obtém geometria da janela
                    geometry = window.geometry()
                    x, y = geometry.x(), geometry.y()
                    width, height = geometry.width(), geometry.height()
                    
                    # Determina o display ID baseado na posição da janela
                    display_id = 1  # Padrão
                    for i, screen in enumerate(screens):
                        screen_geom = screen.geometry()
                        if screen_geom.contains(x, y):
                            display_id = i + 1  # IDs começam em 1
                            break
                    
                    window_data.append({
                        'window_name': window_name,
                        'display_id': display_id,
                        'x': x,
                        'y': y,
                        'width': width,
                        'height': height
                    })
                    
                except Exception as e:
                    self.logger.warning(f"Erro ao obter dados da janela {window_name}: {e}")
            
            # Salva no CSV
            with open(csv_path, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                
                # Cabeçalho
                writer.writerow(['NOME_JANELA', 'ID_DISPLAY', 'X', 'Y', 'LARGURA', 'ALTURA'])
                
                # Dados
                for data in window_data:
                    writer.writerow([
                        data['window_name'],
                        str(data['display_id']),
                        str(data['x']),
                        str(data['y']),
                        str(data['width']),
                        str(data['height'])
                    ])
            
            self.logger.info(f"Posições das janelas salvas em: {csv_path}")
            QMessageBox.information(self, "Sucesso", f"Posições salvas em {csv_path}")
            
        except Exception as e:
            error_msg = f"Erro ao salvar posições das janelas: {e}"
            self.logger.error(error_msg)
            QMessageBox.critical(self, "Erro", error_msg)

    def _apply_changes(self):
        """Aplica mudanças sem fechar diálogo."""
        try:
            # Atualizar configurações do sistema
            self.manager.set_fps(self.fps_spinbox.value())
            self.manager.set_overlay_enabled(self.overlay_enabled.isChecked())
            self.manager.set_overlay_style(
                self.overlay_color, 
                self.thickness_slider.value()
            )
            
            # Atualizar regiões - Atualizado em: 2024-12-28 — Implementada atualização de regiões
            self._update_regions_from_table()
            
            QMessageBox.information(self, "Sucesso", "Configurações aplicadas!")
            
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao aplicar configurações: {e}")

    def _update_regions_from_table(self):
        """
        Atualiza as regiões do manager baseado nos dados da tabela.
        
        Recria as regiões com os novos valores e reinicia o sistema de captura
        se necessário.
        """
        from capture_manager import CaptureRegion  # Import local para evitar circular
        
        new_regions = []
        window_name = None  # Nome da janela sendo editada
        
        # Lê dados da tabela e cria novas regiões para esta janela
        for row in range(self.regions_table.rowCount()):
            try:
                # Extrai dados da linha
                window_name_item = self.regions_table.item(row, 0)
                display_id_item = self.regions_table.item(row, 1)
                x1_item = self.regions_table.item(row, 2)
                y1_item = self.regions_table.item(row, 3)
                x2_item = self.regions_table.item(row, 4)
                y2_item = self.regions_table.item(row, 5)
                
                # Verifica se todos os campos estão preenchidos
                if not all([window_name_item, display_id_item, x1_item, y1_item, x2_item, y2_item]):
                    self.logger.warning(f"Linha {row + 1} tem campos vazios, ignorando")
                    continue
                
                # Obtém o nome da janela sendo editada (todos devem ter o mesmo nome)
                if window_name is None:
                    window_name = window_name_item.text().strip()
                
                # Cria nova região
                region = CaptureRegion(
                    window_name=window_name_item.text().strip(),
                    display_id=int(display_id_item.text()),
                    x1=int(x1_item.text()),
                    y1=int(y1_item.text()),
                    x2=int(x2_item.text()),
                    y2=int(y2_item.text())
                )
                
                # Valida a região antes de adicionar
                if self.manager._validate_region(region):
                    new_regions.append(region)
                else:
                    self.logger.warning(f"Região na linha {row + 1} é inválida")
                    
            except (ValueError, TypeError) as e:
                self.logger.warning(f"Erro ao processar linha {row + 1}: {e}")
                continue
        
        # IMPORTANTE: Atualiza apenas as regiões desta janela, mantendo as outras
        # Atualizado em: 2024-12-28 — Corrigido para preservar regiões de outras janelas
        current_window_name = self.regions[0].window_name if self.regions else None
        
        # Filtra todas as regiões do manager que NÃO pertencem à janela atual
        other_regions = [r for r in self.manager.regions if r.window_name != current_window_name]
        
        # Combina as regiões atualizadas com as regiões de outras janelas
        all_regions = other_regions + new_regions
        
        # Atualiza o manager com todas as regiões
        self.manager.update_regions(all_regions)
        
        # Atualiza a referência local apenas para as regiões desta janela
        self.regions = new_regions

    def _save_regions_to_csv(self):
        """
        Salva todas as regiões no arquivo CSV.
        
        Atualiza o arquivo CSV com todas as regiões do manager (de todas as janelas).
        """
        try:
            csv_path = Path(self.manager.csv_file_path)
            
            # Backup do arquivo original
            if csv_path.exists():
                backup_path = csv_path.with_suffix('.csv.backup')
                if backup_path.exists():
                    backup_path.unlink()
                csv_path.rename(backup_path)
                self.logger.info(f"Backup criado: {backup_path}")
            
            # Escreve novo arquivo com TODAS as regiões do manager
            with open(csv_path, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                
                # Cabeçalho
                writer.writerow(['NOME_JANELA', 'ID_DISPLAY', 'X1', 'Y1', 'X2', 'Y2'])
                
                # Salva TODAS as regiões do manager (que já foram atualizadas pelo _apply_changes)
                for region in self.manager.regions:
                    writer.writerow([
                        region.window_name,
                        str(region.display_id),
                        str(region.x1),
                        str(region.y1),
                        str(region.x2),
                        str(region.y2)
                    ])
                        
            self.logger.info(f"Configurações salvas em: {csv_path} - Total de regiões: {len(self.manager.regions)}")
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar CSV: {e}")
            raise

    def _ok_clicked(self):
        """Aplica mudanças e fecha diálogo."""
        try:
            self._apply_changes()
            self._save_regions_to_csv()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar configurações: {e}")
            
            # Salva no CSV
            self._save_regions_to_csv()
            
            # Fecha o diálogo
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar configurações: {e}")
            self.accept()
            # Fecha o diálogo
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar configurações: {e}")
            self.accept()

