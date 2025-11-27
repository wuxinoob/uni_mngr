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



class complex_config_page(QDialog):
    def __init__(self, dict:Optional[dict] = None):
        super().__init__()
        self.setWindowTitle("任务配置")
        self.resize(450, 300)
        self.main_layout = QVBoxLayout()
        self.Form = QFormLayout()
        self.main_layout.addLayout(self.Form)
        self.dict = dict if dict else {}
        self.setup_ui()

        self.load_config_to_ui()
        
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept) # 点击OK触发 accept()
        self.button_box.rejected.connect(self.reject) # 点击Cancel触发 reject()
        self.main_layout.addWidget(self.button_box)
        self.setLayout(self.main_layout)
        self.show()
    def setup_ui(self):
        self.task_path, self.task_cmd, self.cmd_args = QLineEdit(), QLineEdit(), QLineEdit()
        
        self.task_cmd.setObjectName("task_cmd")
        self.task_cmd.setPlaceholderText("请输入程序路径，必选")
        self.task_cmd_btn = QPushButton("选择程序")
        self.task_cmd_btn.clicked.connect(self.task_cmd_select)
        self.task_cmd_layout = QHBoxLayout()
        self.task_cmd_layout.addWidget(self.task_cmd)
        self.task_cmd_layout.addWidget(self.task_cmd_btn)
        self.cmd_args.setObjectName("cmd_args")
        self.cmd_args.setPlaceholderText("请输入程序参数，可留空")
        self.task_path.setObjectName("task_path")
        self.task_path.setPlaceholderText("请输入程序运行目录，可留空")
        self.task_path_btn = QPushButton("选择目录")
        self.task_path_btn.clicked.connect(self.task_path_select)
        self.task_path_layout = QHBoxLayout()
        self.task_path_layout.addWidget(self.task_path)
        self.task_path_layout.addWidget(self.task_path_btn)
        
        self.max_exec_time = QSpinBox()
        self.max_exec_time.setRange(0, 3600)
        self.max_exec_time.setSuffix("秒")
        self.max_exec_time.setSpecialValueText("无限制")
        self.max_exec_time.setToolTip("设置最大运行时间（秒）。输入 0 表示不限制时间。")
        self.start_up = QCheckBox("开机启动")
        self.start_up.setToolTip("设置任务是否开机启动")
        self.auto_restart = QCheckBox("自动重启")
        self.auto_restart.setToolTip("当达到任务最大运行时间，或进程退出后，是否自动重启任务")
        self.start_time_hour = QSpinBox()
        self.start_time_hour.setRange(0, 23)
        self.start_time_hour.setSuffix("时")
        self.start_time_minute = QSpinBox()
        self.start_time_minute.setRange(0, 59)
        self.start_time_minute.setSuffix("分")
        self.enable_timer = QCheckBox("定时启动")
        self.enable_timer.setToolTip("设置任务是否定时启动")
        self.set_time_layout = QHBoxLayout()
        self.set_time_layout.addWidget(QLabel("定时启动（每日）"))
        self.set_time_layout.addWidget(self.start_time_hour)
        self.set_time_layout.addWidget(self.start_time_minute)
        self.set_time_layout.addWidget(self.enable_timer)
        self.set_time_layout.addWidget(self.start_up)
        self.set_time_layout.addWidget(self.auto_restart)

        self.main_layout.addLayout(self.set_time_layout)
        self.Form.addRow("运行时间",self.max_exec_time)
        self.Form.addRow("运行路径",self.task_path_layout)
        self.Form.addRow("运行程序",self.task_cmd_layout)
        self.Form.addRow("运行参数",self.cmd_args)

    def task_path_select(self):
        file_path = QFileDialog.getExistingDirectory(self, "选择目录",)
        if file_path:
            self.task_path.setText(file_path)
    def task_cmd_select(self):
        file_name,_ = QFileDialog.getOpenFileName(self, "选择程序",)
        if file_name:
            self.task_cmd.setText(file_name)
    def load_config_to_ui(self):
        if self.dict and self.dict != {}: 
            self.task_cmd.setText(self.dict["task_cmd"])
            self.task_path.setText(self.dict["task_path"])
            self.cmd_args.setText(self.dict["cmd_args"])
            self.start_up.setChecked(self.dict["start_up"])
            self.auto_restart.setChecked(self.dict["auto_restart"])
            self.max_exec_time.setValue(self.dict["max_exec_time"])
            self.start_time_hour.setValue(self.dict["start_time_hour"])
            self.start_time_minute.setValue(self.dict["start_time_minute"])
            self.enable_timer.setChecked(self.dict["enable_timer"])

    def accept(self) -> None:
        self.return_dict = {
            "task_cmd": self.task_cmd.text(),
            "task_path": self.task_path.text(),
            "cmd_args": self.cmd_args.text(),
            "start_up": self.start_up.isChecked(),
            "auto_restart": self.auto_restart.isChecked(),
            "max_exec_time": self.max_exec_time.value(),
            "start_time_hour": self.start_time_hour.value(),
            "start_time_minute": self.start_time_minute.value(),
            "enable_timer": self.enable_timer.isChecked(),
        }
        for i in self.dict:
            if i not in self.return_dict:
                self.return_dict[i] = self.dict[i]
        return super().accept()






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
    def default_task_page(self, ) -> QWidget:
        """默认任务页面,name 和其他参数是分开的"""
        widget = QWidget()
        Vlayout = QVBoxLayout()
        widget.setLayout(Vlayout)
        widget.setObjectName("ui_task_page_default")
        task_name = QLineEdit()
        task_complex_page = QPushButton("详细任务配置")
        dict = {}
        task_complex_page.clicked.connect(lambda: self.config_load_complex_page(dict))
        PushButton = QPushButton("创建任务")
        PushButton.setObjectName("task_create")
        PushButton.clicked.connect(lambda: self.submit_task(task_name.text(),dict))
        #PushButton.clicked.connect(lambda: self.add_text(widget.objectName()))

        Vlayout.addWidget(task_name)
        Vlayout.addWidget(task_complex_page)
        Vlayout.addWidget(PushButton)


        return widget
    def config_load_complex_page(self,dict:dict):
        TaskConfigDialog = complex_config_page(dict)
        result = TaskConfigDialog.exec()
        if result == QDialog.Accepted:
            for key in TaskConfigDialog.return_dict:   #更新dict
                dict[key] = TaskConfigDialog.return_dict[key]
            print("dict已被更新")
    def submit_task(self,name:str,dict:dict):
        if not name:
            self.alert("请输入任务名称")
            return
        if dict["task_cmd"] == "":
            self.alert("请输入任务命令")
            return
        dict["name"] = name
        self.ProcessManager.add_task(dict,self)
    def alert(self,msg:str):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("提示")
        msg_box.setText(msg)
        msg_box.setIcon(QMessageBox.Information)  # 设置图标为信息类型
        msg_box.exec()

    def add_default_task_page(self):
        self.task_list_widget.addItem("新增任务")
        self.QStackedWidget.addWidget(self.default_task_page())
        self.QStackedWidget.setCurrentIndex(self.QStackedWidget.count())
        
    def add_config_task_page(self,process_dict:dict):
        """任务配置页面"""
        widget = QWidget()
        Vlayout = QVBoxLayout()
        widget.setLayout(Vlayout)
        widget.setObjectName(process_dict["name"])
        task_name = QLineEdit()
        task_name.setText(process_dict["name"])
        task_complex_page = QPushButton("详细任务配置")
        dict = process_dict
        task_complex_page.clicked.connect(lambda: self.config_load_complex_page(dict))


        output = QPlainTextEdit()
        output.setReadOnly(True)
        output.setObjectName("output")

        Vlayout.addWidget(task_name)
        Vlayout.addWidget(task_complex_page)
        Vlayout.addWidget(output)
        run_Hlayout = QHBoxLayout()
        runButton = QPushButton("运行")
        runButton.setObjectName("task_run")
        runButton.clicked.connect(lambda: self.ProcessManager.start_process(process_dict["name"]))
        stopButton = QPushButton("停止")
        stopButton.setObjectName("task_stop")
        stopButton.clicked.connect(lambda: self.ProcessManager.stop_process(process_dict["name"]))
        restartButton = QPushButton("重启")
        restartButton.setObjectName("task_restart")
        run_Hlayout.addWidget(runButton)
        run_Hlayout.addWidget(stopButton)
        run_Hlayout.addWidget(restartButton)
        Vlayout.addLayout(run_Hlayout)

        self.task_list_widget.addItem(process_dict["name"])
        self.QStackedWidget.addWidget(widget)
        return widget

    def change_config_task_page(self, process_dict:dict):
        """修改当前任务配置页面"""
        print(process_dict)
    def del_config_task_page(self, process_dict:dict):
        """删除当前任务配置页面"""
        print(process_dict)
    def add_text(self,name,text:str):
        self.findChild(QWidget,name=name).findChild(QPlainTextEdit,name="output").appendPlainText(text)


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