import subprocess
import sys
import os
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QHBoxLayout, QMenu,
    QSystemTrayIcon, QStyle, QPushButton, QListWidget, QListWidgetItem, QVBoxLayout, QStackedWidget, QLineEdit, QLayout, QFormLayout, QPlainTextEdit, QComboBox
)
from PySide6.QtCore import Qt, QTimer, QPoint, QRectF, Signal, QThread, QPropertyAnimation, QEasingCurve, QBuffer, QRect, QProcess
from PySide6.QtGui import (
    QPainter, QColor, QAction, QPixmap, QGuiApplication,
    QIcon, QBrush, QPen, QFont, QImage, QRegion, 
)

from uni_panel_pj.Qt_process_manager import ProcessManager

class task_page(QWidget):
    def __init__(self, ProcessManager:ProcessManager):
        super().__init__()
        self.Vlayout = QVBoxLayout()
        self.QStackedWidget = QStackedWidget() #堆叠窗口

        self.task_list_widget = QComboBox() #选择窗口
        self.task_list_widget.currentIndexChanged.connect(self.task_list_idx_change)
        #self.Vlayout.addWidget(QPushButton("添加任务"))
        self.Vlayout.addWidget(self.task_list_widget)
        self.Vlayout.addWidget(self.QStackedWidget)
        self.setLayout(self.Vlayout)

        #self.task_list = [] #任务列表
        self.ProcessManager = ProcessManager
        
        #self.task_list_widget.addItems(self.task_list)

        self.add_default_task_page()
    def task_list_idx_change(self, idx:int):
        """修改stackedWidget页面"""
        self.QStackedWidget.setCurrentIndex(idx)
    def default_task_page(self, process_dict =None) -> QWidget:
        """默认任务页面,缺少定时任务设置，文件选择框"""
        widget = QWidget()
        Vlayout = QVBoxLayout()
        widget.setLayout(Vlayout)
        widget.setObjectName("ui_task_page_default")

        FormLayout = QFormLayout()
        task_name, task_cmd, cmd_args = QLineEdit(), QLineEdit(), QLineEdit()
        task_name.setObjectName("task_name")
        task_cmd.setObjectName("task_cmd")
        cmd_args.setObjectName("cmd_args")
        FormLayout.addRow("任务名称",task_name)
        FormLayout.addRow("运行程序",task_cmd)
        FormLayout.addRow("运行参数",cmd_args)
        PlainTextEdit = QPlainTextEdit()
        PlainTextEdit.setReadOnly(True)
        PushButton = QPushButton("创建任务")
        PushButton.clicked.connect(lambda: self.ProcessManager.add_task(task_name.text(), task_cmd.text(), cmd_args.text(), task_type="task", ui_obj=self))
        #PushButton.clicked.connect(lambda: self.add_text(widget.objectName()))
        Vlayout.addLayout(FormLayout)
        Vlayout.addWidget(PlainTextEdit)
        Vlayout.addWidget(PushButton)
        return widget
    def add_default_task_page(self):
        self.task_list_widget.addItem("新增任务")
        self.QStackedWidget.addWidget(self.default_task_page())
        self.QStackedWidget.setCurrentIndex(self.QStackedWidget.count())
    def add_config_task_page(self,process_dict:dict):
        """任务配置页面"""

        default_task_page = self.default_task_page()
        default_task_page.setObjectName(process_dict["name"])
        default_task_page.findChild(QLineEdit, "task_name").setText(process_dict["name"])
        default_task_page.findChild(QLineEdit, "task_cmd").setText(process_dict["command"])
        default_task_page.findChild(QLineEdit, "cmd_args").setText(process_dict["args"])

        self.task_list_widget.addItem(process_dict["name"])
        self.QStackedWidget.addWidget(default_task_page)
        return default_task_page

    def change_config_task_page(self, process_dict:dict):
        """修改当前任务配置页面"""
        print(process_dict)
    def del_config_task_page(self, process_dict:dict):
        """删除当前任务配置页面"""
        print(process_dict)
    def add_text(self, name:str):
        widget = self.findChild(QWidget, name)
        if widget:
            text_line = widget.findChild(QPlainTextEdit)
            text_line.appendPlainText("asdasdasd")

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
        self.task_page2 = task_page(self.ProcessManager)
        self.sidebar_list.append({"name":"任务管理", "instance": self.task_page})
        self.sidebar_list.append({"name":"任务管理2", "instance": self.task_page2})
        pass

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