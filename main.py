import os
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont
from uni_panel_pj.ui.uni_panel_window import mainWindow
import sys
import qdarktheme

if __name__ == "__main__":
    os.chdir(os.path.dirname(__file__))
    config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), r"uni_panel_pj/config"))

    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 11))
    qdarktheme.enable_hi_dpi()
    qdarktheme.setup_theme("dark")

    window = mainWindow(config_path)
    window.show()
    sys.exit(app.exec())