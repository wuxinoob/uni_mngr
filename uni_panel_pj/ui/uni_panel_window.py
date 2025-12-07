import subprocess
import sys
import os
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QHBoxLayout, QMenu,
    QSystemTrayIcon, QStyle, QPushButton, QListWidget,
    QListWidgetItem, QVBoxLayout, QStackedWidget, QLineEdit,
    QLayout, QFormLayout, QPlainTextEdit, QComboBox, QDialog, QFileDialog, QDialogButtonBox,
    QSpinBox, QCheckBox ,QMessageBox
)
from PySide6.QtCore import Qt, QTimer, QPoint, QRectF, Signal, QThread, QPropertyAnimation, QEasingCurve, QBuffer, QRect, QProcess
from PySide6.QtGui import (
    QPainter, QColor, QAction, QPixmap, QGuiApplication,
    QIcon, QBrush, QPen, QFont, QImage, QRegion, 
)
from typing import Optional
from uni_panel_pj.Qt_process_manager import ProcessManager
from uni_panel_pj.ui.task_page import task_page



class mainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.sidebar_list:list[dict] = []
        self.ProcessManager = ProcessManager()
        self.backend_init()
        self.initUI()
    def backend_init(self):
        """自启动程序"""
        self.task_page = task_page(self.ProcessManager)
        self.sidebar_list.append({"name":"任务管理", "instance": self.task_page})

    def initUI(self):
        self.central_wid = QWidget()
        self.main_wid = QHBoxLayout()
        self.siderBar = self.sideBar_init()
        self.content = self.content_init()

        self.main_wid.addWidget(self.siderBar)
        self.main_wid.addWidget(self.content)

        self.central_wid.setLayout(self.main_wid)
        self.central_wid.show()
    def sideBar_init(self) ->QListWidget:
        sideBar = QListWidget()
        sideBar.setFont(QFont("Arial", 15))
        sideBar.setFixedWidth(100)
        sideBar.itemClicked.connect(self.onclick)
        for i in range(len(self.sidebar_list)):
            task = QListWidgetItem(self.sidebar_list[i]["name"])
            task.setData(Qt.UserRole,i)
            sideBar.addItem(task)
        return sideBar
    def content_init(self) -> QStackedWidget:
        content = QStackedWidget()
        for dict_obj in self.sidebar_list:
            page = dict_obj["instance"]
            content.addWidget(page)

        return content
    def onclick(self, item: QListWidgetItem) -> None:
        data =  item.data(Qt.UserRole)
        self.content.setCurrentIndex(data)
        print(data)
app = QApplication([])
window = mainWindow()
app.exec()