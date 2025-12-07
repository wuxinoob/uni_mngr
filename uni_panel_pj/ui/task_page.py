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
from typing import Optional, Dict
from uni_panel_pj.core.Qt_process_manager import ProcessManager

class complex_config_page(QDialog):
    def __init__(self, config:Optional[dict] = None,create_new:bool = False,modify_task:bool = False):
        super().__init__()
        self.modify_task = modify_task
        self.create_new = create_new
        self.setWindowTitle("任务配置")
        self.resize(450, 300)
        self.main_layout = QVBoxLayout()
        self.Form = QFormLayout()
        self.main_layout.addLayout(self.Form)
        self.config = config if config else {}
        self.return_dict = {}
        self.setup_ui()

        self.load_config_to_ui()
        
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.main_layout.addWidget(self.button_box)
        self.setLayout(self.main_layout)

    def setup_ui(self):
        self.task_path, self.task_cmd, self.cmd_args = QLineEdit(), QLineEdit(), QLineEdit()
        self.task_name = QLineEdit()
        self.task_name.setPlaceholderText("请输入任务名称，必选")
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
        self.Form.addRow("任务名称",self.task_name)
        self.Form.addRow("运行时间",self.max_exec_time)
        self.Form.addRow("运行路径",self.task_path_layout)
        self.Form.addRow("运行程序",self.task_cmd_layout)
        self.Form.addRow("运行参数",self.cmd_args)
        if self.modify_task:
            self.task_name.setReadOnly(True)
            self.task_name.setToolTip("已创建的任务不可修改任务名")
    def task_path_select(self):
        file_path = QFileDialog.getExistingDirectory(self, "选择目录",)
        if file_path:
            self.task_path.setText(file_path)
    def task_cmd_select(self):
        file_name,_ = QFileDialog.getOpenFileName(self, "选择程序",)
        if file_name:
            self.task_cmd.setText(file_name)
            
    def load_config_to_ui(self):
        if self.config:
            self.task_name.setText(self.config.get("name", ""))
            self.task_cmd.setText(self.config.get("task_cmd", ""))
            self.task_path.setText(self.config.get("task_path", ""))
            self.cmd_args.setText(self.config.get("cmd_args", ""))
            self.start_up.setChecked(self.config.get("start_up", False))
            self.auto_restart.setChecked(self.config.get("auto_restart", False))
            self.max_exec_time.setValue(self.config.get("max_exec_time", 0))
            self.start_time_hour.setValue(self.config.get("start_time_hour", 0))
            self.start_time_minute.setValue(self.config.get("start_time_minute", 0))
            self.enable_timer.setChecked(self.config.get("enable_timer", False))

    def accept(self) -> None:
        if not self.task_name.text():
            self.alert("任务名称不能为空")
            return
        if not self.task_cmd.text():
            self.alert("程序路径不能为空")
            return

        ui_dict = {
            "name": self.task_name.text(),
            "task_cmd": self.task_cmd.text(),
            "task_path": self.task_path.text(),
            "cmd_args": self.cmd_args.text(),
            "start_up": self.start_up.isChecked(),
            "auto_restart": self.auto_restart.isChecked(),
            "max_exec_time": self.max_exec_time.value(),
            "start_time_hour": self.start_time_hour.value(),
            "start_time_minute": self.start_time_minute.value(),
            "enable_timer": self.enable_timer.isChecked(),
            "show_type": "secondlevel_page"
        }

        is_modified = False
        if not self.create_new:
            for key, value in ui_dict.items():
                if self.config.get(key) != value:
                    is_modified = True
                    break

        if (not is_modified) and self.modify_task:#未修改配置，则直接结束
            return super().reject()
        if is_modified:
            reply = QMessageBox.question(self, '保存修改?', '任务配置已修改，是否保存?',
                                         QMessageBox.Save | QMessageBox.Cancel, QMessageBox.Save)
            if reply == QMessageBox.Cancel:
                return 

        self.return_dict = ui_dict
        super().accept()
    def reject(self) -> None:
        return super().reject()
    def alert(self,msg:str):
        QMessageBox.information(self, "提示", msg)


class task_page(QWidget):
    def __init__(self, ProcessManager:ProcessManager):
        super().__init__()
        self.ProcessManager = ProcessManager
        self.output_widgets: Dict[str, QPlainTextEdit] = {}
        self.status_labels: Dict[str, QLabel] = {}
        self.ui_init()
        self.add_new_task_page()
        self.ProcessManager.sig_status_update.connect(self.update_task_status)
        self.ProcessManager.sig_task_cleaned.connect(self.del_config_task_page)

    def ui_init(self):
        self.main_Hlayout = QHBoxLayout()
        left_sidebar_layout = QVBoxLayout()

        self.task_list = QListWidget()
        self.task_list.currentRowChanged.connect(self.task_list_idx_change)
        self.task_list.setFixedWidth(120)

        self.QStackedWidget = QStackedWidget()

        add_task_btn = QPushButton("添加任务")
        add_task_btn.clicked.connect(self.handle_add_new_task_button)

        left_sidebar_layout.addWidget(add_task_btn)
        left_sidebar_layout.addWidget(self.task_list)
        
        self.main_Hlayout.addLayout(left_sidebar_layout)
        self.main_Hlayout.addWidget(self.QStackedWidget)
        self.setLayout(self.main_Hlayout)

    def handle_add_new_task_button(self):
        self.add_new_task({})

    def add_new_task(self, config_dict: dict, is_new:bool = True):
        TaskConfigDialog = complex_config_page(config_dict, create_new=is_new)
        result = TaskConfigDialog.exec()
        if result == QDialog.Accepted:
            config_dict.update(TaskConfigDialog.return_dict)
            self.ProcessManager.add_task(config_dict)

    def task_list_idx_change(self, idx: int):
        self.QStackedWidget.setCurrentIndex(idx)

    def create_new_task_page(self) -> QWidget:
        widget = QWidget()
        Vlayout = QVBoxLayout()
        widget.setLayout(Vlayout)
        
        label = QLabel("点击左上角 '添加任务' 来创建新任务")
        label.setAlignment(Qt.AlignCenter)
        Vlayout.addWidget(label)
        
        return widget

    def alert(self,msg:str):
        QMessageBox.information(self, "提示", msg)

    def add_new_task_page(self):
        self.task_list.addItem("新增任务")
        self.QStackedWidget.addWidget(self.create_new_task_page())
        self.QStackedWidget.setCurrentIndex(self.QStackedWidget.count() - 1)
        
    def add_config_task_page(self, process_dict: dict):
        widget = QWidget()
        Vlayout = QVBoxLayout()
        widget.setLayout(Vlayout)
        widget.setObjectName(process_dict["name"])

        # --- Header Layout ---
        header_layout = QHBoxLayout()
        task_name_label = QLabel(f"任务: {process_dict['name']}")
        status_label = QLabel(process_dict.get("status", "stopped"))
        self.status_labels[process_dict["name"]] = status_label
        header_layout.addWidget(task_name_label)
        header_layout.addWidget(status_label)
        header_layout.addStretch() # Add spacer to push the next widgets to the right
        
        task_complex_page = QPushButton("详细任务配置")
        task_complex_page.clicked.connect(lambda: self.change_config_task_page(process_dict))
        header_layout.addWidget(task_complex_page)
        Vlayout.addLayout(header_layout)

        output = QPlainTextEdit()
        output.setReadOnly(True)
        self.output_widgets[process_dict["name"]] = output

        Vlayout.addWidget(output)

        input_layout = QHBoxLayout()
        input_field = QLineEdit()
        input_field.setPlaceholderText("在这里输入并回车发送消息...")
        send_button = QPushButton("发送")
        
        input_layout.addWidget(input_field)
        input_layout.addWidget(send_button)
        Vlayout.addLayout(input_layout)
        
        # Connect signals
        send_button.clicked.connect(lambda: self.send_input_to_task(process_dict["name"], input_field))
        input_field.returnPressed.connect(lambda: self.send_input_to_task(process_dict["name"], input_field))

        run_Hlayout = QHBoxLayout()
        runButton = QPushButton("运行")
        runButton.clicked.connect(lambda: self.ProcessManager.start_process(process_dict["name"]))
        stopButton = QPushButton("停止")
        stopButton.clicked.connect(lambda: self.ProcessManager.stop_process(process_dict["name"]))
        restartButton = QPushButton("重启")
        restartButton.clicked.connect(lambda: self.ProcessManager.restart_process(process_dict["name"]))
        deleteButton = QPushButton("清除任务")
        deleteButton.setStyleSheet("background-color: #ff4d4d;")
        deleteButton.clicked.connect(lambda: self.handle_delete_task(process_dict["name"]))

        run_Hlayout.addWidget(runButton)
        run_Hlayout.addWidget(stopButton)
        run_Hlayout.addWidget(restartButton)
        run_Hlayout.addWidget(deleteButton)
        Vlayout.addLayout(run_Hlayout)

        item = QListWidgetItem(process_dict["name"])
        self.task_list.addItem(item)
        self.QStackedWidget.addWidget(widget)
        return widget

    def update_task_status(self, status_info: dict):
        task_name = status_info.get("name")
        status = status_info.get("status")
        if task_name in self.status_labels:
            label = self.status_labels[task_name]
            label.setText(status)
            # Optional: Style the label based on status
            if status == "running":
                label.setStyleSheet("color: green; font-weight: bold;")
            elif status == "stopped":
                label.setStyleSheet("color: red;")
            elif status == "starting":
                label.setStyleSheet("color: orange;")
            else:
                label.setStyleSheet("") # Reset to default

    def send_input_to_task(self, task_name: str, input_widget: QLineEdit):
        text = input_widget.text()
        if text:
            self.ProcessManager.write_to_process(task_name, text)
            input_widget.clear()

    def handle_delete_task(self, task_name: str):
        reply = QMessageBox.question(self, '确认清除', f"你确定要清除任务 '{task_name}' 吗?\n此操作不可恢复。",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.ProcessManager.clean_task(task_name)

    def change_config_task_page(self, process_dict:dict):
        """修改当前任务配置页面"""
        # This method can be expanded to update the UI if a task's config changes
        TaskConfigDialog = complex_config_page(process_dict, create_new=False, modify_task=True)
        result = TaskConfigDialog.exec()
        if result == QDialog.Accepted:
            process_dict.update(TaskConfigDialog.return_dict)
            self.ProcessManager.modify_task(process_dict, self)
        print(f"UI received request to update for task: {process_dict['name']}")

    def del_config_task_page(self, name_to_delete: str):
        """删除当前任务配置页面"""
        # Remove from widget caches
        if name_to_delete in self.output_widgets:
            del self.output_widgets[name_to_delete]
        if name_to_delete in self.status_labels:
            del self.status_labels[name_to_delete]
            
        # Find and remove from QListWidget and QStackedWidget
        for i in range(self.task_list.count()):
            item = self.task_list.item(i)
            if item and item.text() == name_to_delete:
                # Remove from list
                self.task_list.takeItem(i)
                # Remove from stack
                widget_to_remove = self.QStackedWidget.widget(i)
                self.QStackedWidget.removeWidget(widget_to_remove)
                if widget_to_remove:
                    widget_to_remove.deleteLater()
                break

    def add_text(self, name: str, text: str):
        if name in self.output_widgets:
            self.output_widgets[name].appendPlainText(text)
