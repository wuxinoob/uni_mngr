import subprocess
import sys
import os
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QHBoxLayout, QMenu,
    QSystemTrayIcon, QStyle, QPushButton, QListWidget,
    QListWidgetItem, QVBoxLayout, QStackedWidget, QLineEdit,
    QLayout, QFormLayout, QPlainTextEdit, QComboBox, QDialog, QFileDialog, QDialogButtonBox,
    QSpinBox, QCheckBox ,QMessageBox, QMainWindow
)
from PySide6.QtCore import Qt, QTimer, QPoint, QRectF, Signal, QThread, QPropertyAnimation, QEasingCurve, QBuffer, QRect, QProcess
from PySide6.QtGui import (
    QPainter, QColor, QAction, QPixmap, QGuiApplication,
    QIcon, QBrush, QPen, QFont, QImage, QRegion, 
)
from typing import Optional
from uni_panel_pj.core.Qt_process_manager import ProcessManager
from uni_panel_pj.ui.task_page import task_page
from uni_panel_pj.ui.animated_stacked_widget import AnimatedStackedWidget
import json


class mainWindow(QMainWindow):
    def __init__(self,config_path:str):
        super().__init__()
        self.setWindowTitle("通用面板")
        self.resize(800, 600)
        self.config_path = config_path
        self.sidebar_list:list[dict] = []

        self.ProcessManager = ProcessManager()
        self.task_page = task_page(self.ProcessManager)
        self.sidebar_list.append({"name":"任务管理", "instance": self.task_page})     

        self.backend_init()
        self.initUI()
        self.load_cfg() # 加载配置文件

    def load_cfg(self):
        # 主窗口相关的配置（如果需要）
        ui_config_path = os.path.join(self.config_path, "UI_CONFIG.json")
        if os.path.exists(ui_config_path):
            pass # 以后可以从这里加载UI状态

        # 加载进程管理器相关的配置
        process_config_path = os.path.join(self.config_path, "process_manager_config.json")
        if os.path.exists(process_config_path):
            try:
                with open(process_config_path, "r", encoding='utf-8') as f:
                    content = f.read()
                    if not content:
                        print("配置文件为空，跳过加载。")
                        return
                    config_data = json.loads(content)
                self.ProcessManager.load_config(config_data)
            except json.JSONDecodeError:
                print(f"错误: 配置文件 {process_config_path} 格式错误，无法解析。")
            except Exception as e:
                print(f"加载配置文件时发生未知错误: {e}")


    def backend_init(self):
        """后端初始化 & 传递必要的对象"""
        process_config_file_path = os.path.join(self.config_path, "process_manager_config.json")
        self.ProcessManager.set_config_path(process_config_file_path)
        self.ProcessManager.add_obj(self,self.task_page)

    def initUI(self):
        central_wid = QWidget()
        self.setCentralWidget(central_wid)
        self.main_wid = QHBoxLayout(central_wid)
        self.main_wid.setContentsMargins(0, 0, 0, 0)
        
        self.siderBar = self.sideBar_init()
        self.content = self.content_init()

        # --- Sidebar Container ---
        self.sidebar_container = QWidget()
        sidebar_layout = QVBoxLayout(self.sidebar_container)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        
        self.collapse_btn = QPushButton()
        self.collapse_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowLeft))
        self.collapse_btn.setCheckable(True)
        self.collapse_btn.setChecked(True)
        self.collapse_btn.clicked.connect(self.toggle_sidebar)

        sidebar_layout.addWidget(self.collapse_btn)
        sidebar_layout.addWidget(self.siderBar)
        
        self.main_wid.addWidget(self.sidebar_container)
        self.main_wid.addWidget(self.content, 1) # Give content stretch factor

    def toggle_sidebar(self):
        if self.collapse_btn.isChecked():
            self.siderBar.show()
            self.collapse_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowLeft))
        else:
            self.siderBar.hide()
            self.collapse_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowRight))

    def sideBar_init(self) ->QListWidget:
        sideBar = QListWidget()
        sideBar.setFont(QFont("Segoe UI", 12))
        sideBar.setFixedWidth(150)
        sideBar.itemClicked.connect(self.onclick)
        for i in range(len(self.sidebar_list)):
            task = QListWidgetItem(self.sidebar_list[i]["name"])
            task.setData(Qt.UserRole,i)
            sideBar.addItem(task)
        return sideBar
    def content_init(self) -> QStackedWidget:
        content = AnimatedStackedWidget()
        for dict_obj in self.sidebar_list:
            page = dict_obj["instance"]
            content.addWidget(page)

        return content
    def onclick(self, item: QListWidgetItem) -> None:
        data =  item.data(Qt.UserRole)
        self.content.setCurrentIndex(data)
        # print(data) # Commented out for cleaner output
