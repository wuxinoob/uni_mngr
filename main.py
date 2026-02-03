import os
import sys
import argparse
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt
import PySide6.QtSvg # Ensure SVG support is loaded
from uni_panel_pj.ui.uni_panel_window import mainWindow

if __name__ == "__main__":
    # --- CLI Argument Parsing ---
    parser = argparse.ArgumentParser(description="UniPanel Task Manager.")
    parser.add_argument(
        '--autostart',
        action='store_true',
        help='An internal flag used when the application is launched on system startup.'
    )
    args = parser.parse_args()

    # --- Application Setup ---
    os.chdir(os.path.dirname(__file__))
    config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), r"uni_panel_pj/config"))

    # 设置 High DPI 策略
    if hasattr(Qt, 'HighDpiScaleFactorRoundingPolicy'):
        QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

    app = QApplication(sys.argv)
    app.setStyle("Fusion") # 使用 Fusion 风格作为基底
    app.setFont(QFont("Segoe UI", 11))
    
    window = mainWindow(config_path)
    
    # 如果以 --autostart 模式启动，可以选择不显示主窗口
    # For now, we'll always show the window, but this is where you'd hide it.
    window.show()

    sys.exit(app.exec())