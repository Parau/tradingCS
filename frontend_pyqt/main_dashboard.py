import sys
import subprocess
import webbrowser
import os
import requests

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStatusBar, QMessageBox
)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import QTimer, QProcess, QProcessEnvironment

# Importa a janela da tabela de marcações
from marker_table_window import MarkerTableWindow

# Import absoluto para capture_manager - funciona quando executado diretamente
try:
    from capture_manager import CaptureManager
except ImportError:
    # Fallback para import relativo se estiver sendo importado como módulo
    from .capture_manager import CaptureManager

class MainDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.server_process = None
        self.marker_table_window = None # Para manter a referência
        self.capture_manager = None

        self.init_ui()
        self.setup_status_timer()

    def init_ui(self):
        self.setWindowTitle("Trading System - Painel de Controle")
        self.setGeometry(150, 150, 450, 200)

        # Widget central e layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Layout dos botões de ação
        action_layout = QHBoxLayout()

        self.btn_toggle_server = QPushButton("Iniciar Servidor FastAPI")
        self.btn_toggle_server.clicked.connect(self.toggle_server)
        action_layout.addWidget(self.btn_toggle_server)

        self.btn_open_chart = QPushButton("Abrir Gráfico")
        self.btn_open_chart.clicked.connect(self.open_chart)
        self.btn_open_chart.setEnabled(False) # Habilitado quando o servidor estiver rodando
        action_layout.addWidget(self.btn_open_chart)

        self.btn_marker_table = QPushButton("Tabela de Marcações")
        self.btn_marker_table.clicked.connect(self.open_marker_table)
        action_layout.addWidget(self.btn_marker_table)

        main_layout.addLayout(action_layout)

        # Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.server_status_label = QLabel("Servidor: Parado")
        self.mt5_status_label = QLabel("MT5: Desconectado")
        self.status_bar.addWidget(self.server_status_label)
        self.status_bar.addPermanentWidget(self.mt5_status_label)

        # Adicionar toolbar
        self.toolbar = self.addToolBar("Principal")
        self._setup_ui()

    def _setup_ui(self):
        # Adicionar ação de captura à toolbar
        capture_action = QAction("📹 Captura de Tela", self)
        capture_action.setToolTip("Sistema de captura de múltiplas regiões")
        capture_action.triggered.connect(self._open_capture_system)

        # Adicionar à toolbar existente ou criar nova seção
        if hasattr(self, 'toolbar'):
            self.toolbar.addAction(capture_action)

    def setup_status_timer(self):
        self.timer = QTimer(self)
        self.timer.setInterval(3000)  # Verifica a cada 3 segundos
        self.timer.timeout.connect(self.check_status)
        self.timer.start()

    def toggle_server(self):
        if self.server_process is None:
            self.start_server()
        else:
            self.stop_server()

    def start_server(self):
        self.server_status_label.setText("Servidor: Iniciando...")
        # O caminho para o script de execução do backend
        backend_run_script = os.path.join(os.path.dirname(__file__), '..', 'backend', 'run.py')

        # Usa o mesmo executável python que está rodando este app
        python_executable = sys.executable

        try:
            # Usamos QProcess para melhor integração com o event loop do PyQt
            self.server_process = QProcess(self)
            self.server_process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)

            # Força o subprocesso a usar UTF-8, resolvendo erros de decodificação no Windows
            env = QProcessEnvironment.systemEnvironment()
            env.insert("PYTHONUTF8", "1")
            self.server_process.setProcessEnvironment(env)

            self.server_process.readyReadStandardOutput.connect(self.handle_server_output)
            self.server_process.start(python_executable, [backend_run_script])

            self.btn_toggle_server.setText("Parar Servidor FastAPI")
        except Exception as e:
            self.server_status_label.setText(f"Servidor: Erro ao iniciar ({e})")
            self.server_process = None

    def stop_server(self):
        if self.server_process:
            self.server_process.terminate()
            self.server_process.waitForFinished(3000) # Espera 3s para o processo terminar
            self.server_process = None

        self.server_status_label.setText("Servidor: Parado")
        self.mt5_status_label.setText("MT5: Desconectado")
        self.btn_toggle_server.setText("Iniciar Servidor FastAPI")
        self.btn_open_chart.setEnabled(False)

    def handle_server_output(self):
        if self.server_process:
            byte_data = self.server_process.readAllStandardOutput().data()
            try:
                output = byte_data.decode('utf-8').strip()
            except UnicodeDecodeError:
                output = byte_data.decode(sys.stdout.encoding, errors='replace').strip()
            #print(f"[FastAPI Server]: {output}") if output else None

    def check_status(self):
        # Verifica se o processo ainda está rodando
        if self.server_process is None or self.server_process.state() == QProcess.ProcessState.NotRunning:
            self.stop_server() # Garante que o estado da UI esteja limpo
            return

        # Se o processo está rodando, verifica a saúde da API
        try:
            response = requests.get("http://127.0.0.1:8000/health", timeout=1)
            if response.status_code == 200:
                self.server_status_label.setText("Servidor: Rodando")
                self.btn_open_chart.setEnabled(True)
                # Se o servidor está OK, verifica o status do MT5
                self.check_mt5_status()
            else:
                self.server_status_label.setText("Servidor: Sem resposta")
                self.btn_open_chart.setEnabled(False)
        except requests.ConnectionError:
            # Pode acontecer enquanto o servidor está iniciando
            self.server_status_label.setText("Servidor: Conectando...")
            self.btn_open_chart.setEnabled(False)
            self.mt5_status_label.setText("MT5: Desconectado")


    def check_mt5_status(self):
        try:
            response = requests.get("http://127.0.0.1:8000/mt5-status", timeout=1)
            if response.status_code == 200 and response.json().get("connected"):
                self.mt5_status_label.setText("MT5: Conectado")
                self.mt5_status_label.setStyleSheet("color: lightgreen;")
            else:
                self.mt5_status_label.setText("MT5: Desconectado")
                self.mt5_status_label.setStyleSheet("color: red;")
        except requests.ConnectionError:
            self.mt5_status_label.setText("MT5: Verificando...")
            self.mt5_status_label.setStyleSheet("")


    def open_chart(self):
        # Abre a URL raiz, que agora é servida pelo FastAPI
        webbrowser.open('http://127.0.0.1:8000/')

    def open_marker_table(self):
        # Cria a janela se ela não existir, ou a traz para frente se já existir
        if self.marker_table_window is None or not self.marker_table_window.isVisible():
            self.marker_table_window = MarkerTableWindow()
            self.marker_table_window.show()
        else:
            self.marker_table_window.activateWindow()
            self.marker_table_window.raise_()

    def _open_capture_system(self):
        """Abre o sistema de captura de tela."""
        try:
            if not self.capture_manager:
                self.capture_manager = CaptureManager()
                self.capture_manager.error_occurred.connect(self._show_capture_error)

            # Tenta carregar configuração padrão
            if self.capture_manager.load_config():
                self.capture_manager.start_capture()
            else:
                # Se não conseguir carregar, abre diálogo de configuração
                try:
                    from capture_region_config_dialog import CaptureRegionConfigDialog
                except ImportError:
                    from .capture_region_config_dialog import CaptureRegionConfigDialog
                    
                dialog = CaptureRegionConfigDialog([], self.capture_manager, self)
                dialog.exec()

        except Exception as e:
            self._show_capture_error(f"Erro ao inicializar sistema de captura: {e}")

    def _show_capture_error(self, error_message: str):
        """Exibe erro do sistema de captura."""
        QMessageBox.critical(self, "Erro - Sistema de Captura", error_message)

    def closeEvent(self, event):
        """Trata fechamento da aplicação."""
        # Para sistema de captura se estiver rodando
        if self.capture_manager:
            self.capture_manager.stop_capture()

        # Garante que o servidor FastAPI seja encerrado ao fechar a janela
        self.stop_server()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    dashboard = MainDashboard()
    dashboard.show()
    sys.exit(app.exec())
