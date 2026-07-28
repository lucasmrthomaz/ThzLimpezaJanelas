import sys
import os
import faulthandler

# Ativa o report de falhas (C-level errors) do Python para capturar erros do C++ (Qt)
faulthandler.enable()

# Garante que o diretório do script está no PATH do Python
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

# Alterna para o diretório do script para que caminhos relativos funcionem corretamente
os.chdir(script_dir)

from PySide6.QtWidgets import QApplication
from window import Window

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    w = Window()
    w.show()
    sys.exit(app.exec())
