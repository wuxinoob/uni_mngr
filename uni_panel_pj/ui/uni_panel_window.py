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
        self.sidebar_list:list[dict] = []
        self.ProcessManager = ProcessManager()
        self.task_page = task_page(self.ProcessManager)
        self.sidebar_list.append({"name":"任务管理", "instance": self.task_page})        
        self.backend_init()
        self.initUI()
    def load_cfg(self,config_path:str):
        if not os.path.exists(os.path.join(config_path, "UI_CONFIG.json")):
            with open(os.path.join(_path, "UI_CONFIG.json"), "r+") as f:
                pass
        else:
            pass #主窗口页面的配置文件
        if os.path.exists(os.path.join(config_path, "process_manager_config.json")):
            with open(os.path.join(config_path, "process_manager_config.json"), "r+") as f:
                pass
        else:
            with open(os.path.join(config_path, "process_manager_config.json"), "r+") as f:
                self.ProcessManager.load_config(json.load(f))

        pass


    def backend_init(self):
        """自启动程序"""
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
