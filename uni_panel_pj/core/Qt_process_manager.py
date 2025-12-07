import sys
import json
from PySide6.QtCore import QObject, QProcess, Signal, Slot, QCoreApplication, QTimer
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QTextEdit, QWidget
import time
from datetime import datetime

# -----------------------------------------------------------------------------
# 1. 进程管理器
# -----------------------------------------------------------------------------
class ProcessManager(QObject):
    # 发送给 UI 的信号
    sig_log = Signal(str)          # 普通日志
    task_msg = Signal(str)      # 任务消息
    sig_status_update = Signal(dict) # 状态更新
    sig_task_cleaned = Signal(str)   # 任务被清除
    ui_msg = Signal(str)           # UI更新专用 消息
    
    def __init__(self):
        super().__init__()
        self.task_status = {} # 存储 { "name": {status: "running" | "stopped", ...} }
        self.sig_log.connect(self.print_log)

        # 设置定时任务检查器
        self.schedule_timer = QTimer(self)
        self.schedule_timer.timeout.connect(self.check_scheduled_tasks)
        self.schedule_timer.start(30000) # 每30秒检查一次

    def add_obj(self, main_window: QWidget,task_page: QWidget):
        self.main_window = main_window
        self.task_page = task_page
    def check_scheduled_tasks(self):
        now = datetime.now()
        current_time = (now.hour, now.minute)
        self.sig_log.emit(f"检查定时任务: 当前时间 {current_time}")

        for name, task in self.task_status.items():
            if task.get("enable_timer"):
                scheduled_time = (task.get("start_time_hour"), task.get("start_time_minute"))
                # 如果时间匹配，并且任务当前未运行
                if current_time == scheduled_time and task.get("status") != "running":
                    self.sig_log.emit(f"触发定时任务: {name}")
                    self.start_process(name)

    def add_task(self, process_dict:dict):
        #if ui_obj is task_page:
        if process_dict["name"] in self.task_status:
            self.sig_log.emit(f"任务名 {process_dict['name']} 已经存在，请更改任务名或删除原任务")
            return
        process_dict["status"] = "stopped"
        self.task_status[process_dict["name"]] = process_dict
        if process_dict["show_type"] == "secondlevel_page":
            self.task_page.add_config_task_page(self.task_status[process_dict["name"]])
        
        #在这一部分要添加前端的任务列表与新页面，写入配置文件持久化
    def modify_task(self, process_dict:dict, ui_obj):
        """任务名不变，只有参数变，先停止任务，再修改配置"""
        self.stop_process(process_dict["name"])
        process_dict["status"] = "stopped"
        self.task_status[process_dict["name"]] = process_dict
    def change_task_attributes(self, name:str, command:str, args):
        if name in self.task_status:
            self.task_status[name]["task_cmd"] = command
            self.task_status[name]["cmd_args"] = args
            if self.task_status[name]["status"] == "running":
                self.stop_process(name)
            #更新前端显示
        else:
            self.sig_log.emit(f"任务 {name} 不存在")
            return
    def start_process(self, name:str):
        if self.task_status.get(name,{}).get("status") in ["running","starting"] :
            self.sig_log.emit(f"任务 {name} 已经在运行中")
            return

        process = QProcess()
        process.setProgram(self.task_status[name]["task_cmd"])
        process.setArguments(self.task_status[name]["cmd_args"].split(" "))#str->list[str]
        process.stateChanged.connect(lambda state:self.task_status_update(name, state))
        process.errorOccurred.connect(lambda error: self.sig_log.emit(f"错误: {error}"))
        process.finished.connect(lambda: self.sig_log.emit(f"完成！"))
        # 关键：连接信号
        # 当有输出时，调用 handle_output
        process.setProcessChannelMode(QProcess.MergedChannels)
        process.readyRead.connect(lambda: self.handle_output(name))

        
        self.task_status[name]["instance"] = process
        process.start()
        self.sig_log.emit(f"启动进程: {name},{self.task_status[name]['task_cmd']} {self.task_status[name]['cmd_args']}")

    def task_status_update(self,name, state, ):
        current_status = ""
        if state == QProcess.Running:
            current_status = "running"
        elif state == QProcess.NotRunning:
            current_status = "stopped"
        elif state == QProcess.Starting:
            current_status = "starting"
        
        if self.task_status.get(name, {}).get("status") != current_status:
            self.task_status[name]["status"] = current_status
            self.sig_log.emit(f"{name}运行状态变为{current_status}")
            self.sig_status_update.emit({'name': name, 'status': current_status})
        
        
    def clean_task(self, name):
        if name in self.task_status:
            instance = self.task_status[name].get("instance")
            if instance and instance.state() == QProcess.Running:
                instance.kill()
            self.task_status.pop(name)
            self.sig_log.emit(f"任务 {name} 已被清除")
            self.sig_task_cleaned.emit(name)
        else:
            self.sig_log.emit(f"试图清除一个不存在的任务: {name}")

    def stop_process(self, name):
        if self.task_status.get(name, {}).get("status") != "running":
            self.sig_log.emit(f"任务 {name} 不在运行中，无法停止")
            return
        instance = self.task_status[name].get("instance")
        if instance:
            instance.kill()

    def restart_process(self, name):
        self.stop_process(name)
        time.sleep(1)
        self.start_process(name)
    

    def load_config(self,config):
        pass
    def write_to_process(self, target_name, data_str):
        """向指定任务的 stdin 写入数据 需要重写"""
        if target_name in self.task_status:
            proc = self.task_status[target_name].get("instance")
            if proc and proc.state() == QProcess.Running:
                # 注意添加换行符，并转为 bytes
                proc.write((data_str + "\n").encode('utf-8'))
            else:
                self.sig_log.emit(f"错误: 目标任务 {target_name} 未运行或不存在")

    def handle_output(self, source_name):
        """
        核心消息处理器：读取子任务输出，并路由
        """
        proc = self.task_status[source_name].get("instance")
        if not proc: return
        # 读取所有可用数据
        data_bytes = proc.readAll().data()
        try:
            raw_data = data_bytes.decode('utf-8').strip()
        except Exception as e:
            self.sig_log.emit(f"错误: 读取数据时发生错误: {e}")
            raw_data = data_bytes.decode('gbk').strip()

        self.sig_log.emit(f"{source_name} 输出: {raw_data},{data_bytes}")
        # 可能一次读取多行，需要分割处理
        for line in raw_data.split('\n'):
            if not line: continue
            self.route_message(source_name, line)
    def route_message(self, source_name, message):
        """demo逻辑： 收到就往前端发"""
        if (source_name in self.task_status) and self.task_status[source_name]["show_type"]=="secondlevel_page":
            self.task_page.add_text(source_name, message)
            
    def print_log(self, message):
        print(message)
