import os
from PySide6.QtWidgets import QApplication
from uni_panel_pj.ui.uni_panel_window import mainWindow
import sys

if __name__ == "__main__":
    os.chdir(os.path.dirname(__file__))
    config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), r"uni_panel_pj/config"))

    app = QApplication(sys.argv)
    window = mainWindow(config_path)
    #window.show()
    sys.exit(app.exec())