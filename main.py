import os
import sys
import argparse
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont
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

    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 11))

    window = mainWindow(config_path)
    
    # 如果以 --autostart 模式启动，可以选择不显示主窗口
    # if not args.autostart:
    #     window.show()
    # else:
    #     print("以自启动模式运行，窗口保持隐藏。")
    
    # 暂时还是显示主窗口，以便用户查看
    window.show()

    sys.exit(app.exec())