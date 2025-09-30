import sys
import csv
import json
import requests
import os
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QLineEdit, QFileDialog, QComboBox,
    QHeaderView, QMessageBox, QLabel
)
from PyQt6.QtCore import Qt, QTimer

# Importa constantes compartilhadas do diretório shared
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))
from constants import MARKER_TYPES

class MarkerTableWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.api_url = "http://127.0.0.1:8000/api/markers"
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Tabela de Marcações")
        self.setGeometry(100, 100, 600, 400)

        # Layout principal
        layout = QVBoxLayout()

        # Layout superior para o nome do ativo
        top_layout = QHBoxLayout()
        self.symbol_input = QLineEdit("WDOV25")
        self.symbol_input.setPlaceholderText("Nome do Ativo (ex: WDOV25)")
        top_layout.addWidget(self.symbol_input)

        layout.addLayout(top_layout)

        # Tabela
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Data", "Hora", "Preco", "Tipo"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        # Layout de botões
        button_layout = QHBoxLayout()

        btn_add = QPushButton("Adicionar Linha")
        btn_add.clicked.connect(self.add_row)
        button_layout.addWidget(btn_add)

        btn_remove = QPushButton("Remover Linha")
        btn_remove.clicked.connect(self.remove_row)
        button_layout.addWidget(btn_remove)

        btn_load = QPushButton("Carregar CSV")
        btn_load.clicked.connect(self.load_csv)
        button_layout.addWidget(btn_load)

        btn_save = QPushButton("Salvar CSV")
        btn_save.clicked.connect(self.save_csv)
        button_layout.addWidget(btn_save)

        layout.addLayout(button_layout)

        # Botão de atualização do gráfico
        self.btn_update_chart = QPushButton("Atualizar Gráfico")
        self.btn_update_chart.setStyleSheet("background-color: #2563eb; color: white; padding: 10px; font-weight: bold;")
        self.btn_update_chart.clicked.connect(self.update_chart)
        layout.addWidget(self.btn_update_chart)

        # Adicionar QLabel para mensagens de status temporárias
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: green; font-weight: bold;")
        layout.addWidget(self.status_label)

        self.setLayout(layout)

    def add_row(self):
        row_position = self.table.rowCount()
        self.table.insertRow(row_position)

        # Adiciona um QComboBox na coluna "Tipo" usando constantes compartilhadas
        combo_box = QComboBox()
        combo_box.addItems(MARKER_TYPES)
        self.table.setCellWidget(row_position, 3, combo_box)

    def remove_row(self):
        current_row = self.table.currentRow()
        if current_row > -1:
            self.table.removeRow(current_row)

    def load_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "Carregar CSV", "", "CSV Files (*.csv)")
        if path:
            try:
                with open(path, 'r', newline='', encoding='utf-8') as file:
                    reader = csv.reader(file)
                    self.table.setRowCount(0) # Limpa a tabela
                    header = next(reader) # Pula o cabeçalho
                    for row_data in reader:
                        row = self.table.rowCount()
                        self.table.insertRow(row)
                        self.table.setItem(row, 0, QTableWidgetItem(row_data[0]))
                        self.table.setItem(row, 1, QTableWidgetItem(row_data[1]))
                        self.table.setItem(row, 2, QTableWidgetItem(row_data[2]))

                        combo_box = QComboBox()
                        combo_box.addItems(MARKER_TYPES)
                        combo_box.setCurrentText(row_data[3])
                        self.table.setCellWidget(row, 3, combo_box)
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Não foi possível carregar o arquivo CSV: {e}")


    def save_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Salvar CSV", "", "CSV Files (*.csv)")
        if path:
            try:
                with open(path, 'w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    headers = [self.table.horizontalHeaderItem(i).text() for i in range(self.table.columnCount())]
                    writer.writerow(headers)
                    for row in range(self.table.rowCount()):
                        row_data = []
                        for col in range(self.table.columnCount()):
                            if col == 3: # Coluna do ComboBox
                                item = self.table.cellWidget(row, col).currentText()
                            else:
                                item = self.table.item(row, col).text() if self.table.item(row, col) else ""
                            row_data.append(item)
                        writer.writerow(row_data)
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Não foi possível salvar o arquivo CSV: {e}")

    def update_chart(self):
        symbol = self.symbol_input.text()
        if not symbol:
            QMessageBox.warning(self, "Aviso", "Por favor, insira o nome do ativo.")
            return

        markers_data = []
        for row in range(self.table.rowCount()):
            try:
                data = self.table.item(row, 0).text()
                hora = self.table.item(row, 1).text()
                preco = float(self.table.item(row, 2).text().replace(",", "."))
                tipo = self.table.cellWidget(row, 3).currentText()

                markers_data.append({
                    "Data": data,
                    "Hora": hora,
                    "Preco": preco,
                    "Tipo": tipo
                })
            except (AttributeError, ValueError) as e:
                QMessageBox.warning(self, "Erro de Dados", f"Verifique os dados na linha {row + 1}. Todos os campos devem ser preenchidos corretamente.\nErro: {e}")
                return

        payload = {
            "symbol": symbol,
            "markers": markers_data
        }

        try:
            self.btn_update_chart.setText("Enviando...")
            self.btn_update_chart.setEnabled(False)

            response = requests.post(self.api_url, json=payload, timeout=10)
            response.raise_for_status() # Lança exceção para códigos de erro HTTP

            # Substituir QMessageBox por mensagem temporária no QLabel
            self.status_label.setText("Os dados de marcação foram enviados para o gráfico.")
            QTimer.singleShot(3000, lambda: self.status_label.setText(""))  # Limpa após 3 segundos

        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "Erro de Conexão", f"Não foi possível enviar os dados para a API: {e}")
        finally:
            self.btn_update_chart.setText("Atualizar Gráfico")
            self.btn_update_chart.setEnabled(True)

# Bloco para permitir que a janela seja executada de forma independente para testes
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MarkerTableWindow()
    window.show()
    sys.exit(app.exec())
