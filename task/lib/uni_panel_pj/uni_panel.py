import subprocess
import sys
import os
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QHBoxLayout, QMenu,
    QSystemTrayIcon, QStyle, QPushButton, QListWidget, QListWidgetItem, QVBoxLayout, QStackedWidget, QLineEdit, QLayout, QFormLayout, QPlainTextEdit
)
from PySide6.QtCore import Qt, QTimer, QPoint, QRectF, Signal, QThread, QPropertyAnimation, QEasingCurve, QBuffer, QRect, QProcess
from PySide6.QtGui import (
    QPainter, QColor, QAction, QPixmap, QGuiApplication,
    QIcon, QBrush, QPen, QFont, QImage, QRegion, 
)

from process_manager import ProcessManager
class base_execcute(QWidget):
    """gui 交互界面 process_manager中 进程的可视化前端"""
    def __init__(self, name:str, content:str, config:dict, ProcessManager:ProcessManager):
        super().__init__()
        self.name = name
        self.interface = self.create_interface(content)
        self.setLayout(self.interface)
        self.ProcessManager = ProcessManager

    def create_interface(self,content:str) -> QLayout:
        discription_key = QLabel("任务描述")
        discription_val = QLabel(content)
        form_layout = QFormLayout()
        form_layout.addRow(discription_key, discription_val)
        form_layout.setFormAlignment(Qt.AlignCenter)
        self.cli_wid = QPlainTextEdit("default output")
        self.cli_wid.setReadOnly(True)
        bottom = QPushButton(content)
        self.default_interact_layout = self.default_interact()
        layout = QVBoxLayout()
        layout.addLayout(form_layout)
        layout.addWidget(self.cli_wid)
        layout.addWidget(bottom)
        layout.addLayout(self.default_interact_layout)
        layout.setAlignment(Qt.AlignCenter)
        return layout
    def default_interact(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        start = QPushButton("start")
        restart = QPushButton("restart")
        stop = QPushButton("stop")
        layout.addWidget(start)
        layout.addWidget(restart)
        layout.addWidget(stop)
        start.clicked.connect(self.start)
        restart.clicked.connect(self.restart)
        stop.clicked.connect(self.stop)
        return layout
    def start(self):
        self.ProcessManager.add_task(self.name, "dir test.py", "continue_process",self)# manbo
    def restart(self):
        pass
    def stop(self):
        self.ProcessManager.remove_task(self.name)
    def exit(self):
        pass
    def write_cli(self, data:str) -> None:
        self.cli_wid.appendPlainText(data)
class home_page(QWidget):
    """home界面"""
class task_page(QWidget):
    """多任务管理界面"""

class mainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.ProcessManager = ProcessManager()
        self.ProcessManager.msg_handle()
        self.backend_init()
        self.initUI()
    def backend_init(self):
        #a = 
        self.TaskList = []
        self.TaskList.append(base_execcute("gost", "启动gost", {"":""}, self.ProcessManager))
        self.TaskList.append(base_execcute("webui", "启动webui", {"":""}, self.ProcessManager))

    def initUI(self):
        self.central_wid = QWidget()
        self.main_wid = QHBoxLayout()
        self.main_wid.setContentsMargins(0,0,0,0)
        self.main_wid.addSpacing(0)
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
        for i in range(len(self.TaskList)):
            task = QListWidgetItem(self.TaskList[i].name)
            task.setData(Qt.UserRole,i)
            sideBar.addItem(task)
        return sideBar
    def content_init(self) -> QStackedWidget:
        content = QStackedWidget()
        for page in self.TaskList:
            content.addWidget(page)

        return content
    def onclick(self, item: QListWidgetItem) -> None:
        data =  item.data(Qt.UserRole)
        self.content.setCurrentIndex(data)
        print(data)
app = QApplication([])
window = mainWindow()
app.exec()