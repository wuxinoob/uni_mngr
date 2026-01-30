import sys
import json
from PySide6.QtCore import QObject, QProcess, Signal, Slot, QCoreApplication, QTimer
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QTextEdit, QWidget
import time
from datetime import datetime
import copy
from uni_panel_pj.core.os_utils import manage_app_autostart

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
        self.config_path = ""
        self.main_panel_config = {}
        self.sig_log.connect(self.print_log)

        # 设置定时任务检查器
        self.schedule_timer = QTimer(self)
        self.schedule_timer.timeout.connect(self.check_scheduled_tasks)
        self.schedule_timer.start(30000) # 每30秒检查一次

    def add_obj(self, main_window: QWidget,task_page: QWidget):
        self.main_window = main_window
        self.task_page = task_page

    def set_config_path(self, path:str):
        self.config_path = path

    def set_main_panel_config(self, config: dict):
        """接收主程序的配置字典"""
        self.main_panel_config = config

    def _save_config(self):
        """保存配置到JSON文件，会移除QProcess等无法序列化的实例"""
        if not self.config_path:
            self.sig_log.emit("错误: 配置文件路径未设置，无法保存。")
            return

        tasks_to_save = copy.deepcopy(self.task_status)
        for name, task_data in tasks_to_save.items():
            if "instance" in task_data:
                del task_data["instance"]

        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(tasks_to_save, f, indent=4, ensure_ascii=False)
            self.sig_log.emit("配置已保存。")
        except Exception as e:
            self.sig_log.emit(f"错误: 保存配置文件失败: {e}")

    def _update_app_autostart_status(self):
        """检查所有任务，并统一设置应用的开机自启状态"""
        # 首先检查总开关
        if not self.main_panel_config.get("master_autostart", True):
            manage_app_autostart(False)
            self.sig_log.emit("主程序开机自启已禁用，将移除所有自启任务。")
            return
            
        should_autostart = any(task.get("start_up") for task in self.task_status.values())
        manage_app_autostart(should_autostart)

    def check_scheduled_tasks(self):
        now = datetime.now()
        current_time = (now.hour, now.minute)
        # self.sig_log.emit(f"检查定时任务: 当前时间 {current_time}")

        for name, task in self.task_status.items():
            if task.get("enable_timer"):
                scheduled_time = (task.get("start_time_hour"), task.get("start_time_minute"))
                if current_time == scheduled_time and task.get("status") != "running":
                    self.sig_log.emit(f"触发定时任务: {name}")
                    self.start_process(name)

    def add_task(self, process_dict:dict):
        if process_dict["name"] in self.task_status:
            self.sig_log.emit(f"任务名 {process_dict['name']} 已经存在，此为加载操作，跳过重复添加。")
            return
            
        process_dict["status"] = "stopped"
        self.task_status[process_dict["name"]] = process_dict
        
        if process_dict["show_type"] == "secondlevel_page":
            self.task_page.add_config_task_page(self.task_status[process_dict["name"]])
        
        self._save_config()
        self._update_app_autostart_status()
        
    def modify_task(self, process_dict:dict, ui_obj):
        """任务名不变，只有参数变，先停止任务，再修改配置"""
        task_name = process_dict["name"]
        self.stop_process(task_name)
        process_dict["status"] = "stopped"
        self.task_status[task_name] = process_dict

        self._save_config()
        self._update_app_autostart_status()

    def change_task_attributes(self, name:str, command:str, args):
        if name in self.task_status:
            self.task_status[name]["task_cmd"] = command
            self.task_status[name]["cmd_args"] = args
            if self.task_status[name]["status"] == "running":
                self.stop_process(name)
            self._save_config()
            self._update_app_autostart_status()
        else:
            self.sig_log.emit(f"任务 {name} 不存在")
            return
            
    def start_process(self, name:str):
        if self.task_status.get(name,{}).get("status") in ["running","starting"] :
            self.sig_log.emit(f"任务 {name} 已经在运行中")
            return

        process = QProcess()
        process.setProgram(self.task_status[name]["task_cmd"])
        process.setArguments(self.task_status[name]["cmd_args"].split(" "))
        work_dir = self.task_status[name].get("task_path")
        if work_dir:
            process.setWorkingDirectory(work_dir)

        process.stateChanged.connect(lambda state:self.task_status_update(name, state))
        process.errorOccurred.connect(lambda error: self.sig_log.emit(f"错误: {error}"))
        process.finished.connect(lambda: self._on_task_finished(name))
        process.setProcessChannelMode(QProcess.MergedChannels)
        process.readyRead.connect(lambda: self.handle_output(name))
        
        self.task_status[name]["instance"] = process
        process.start()
        self.sig_log.emit(f"启动进程: {name},{self.task_status[name]['task_cmd']} {self.task_status[name]['cmd_args']}")

    def _on_task_finished(self, name: str):
        self.sig_log.emit(f"任务 {name} 已结束。")
        task_config = self.task_status.get(name)
        if task_config and task_config.get("auto_restart") and task_config.get("status") != "running":
            self.sig_log.emit(f"任务 '{name}' 设置了自动重启，将在1秒后重启...")
            QTimer.singleShot(1000, lambda: self.start_process(name))

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
            task_to_delete = self.task_status.pop(name)
            instance = task_to_delete.get("instance")

            if instance and instance.state() == QProcess.Running:
                instance.kill()

            self.sig_log.emit(f"任务 {name} 已被清除")
            self.sig_task_cleaned.emit(name)
            
            self._save_config()
            self._update_app_autostart_status()
        else:
            self.sig_log.emit(f"试图清除一个不存在的任务: {name}")

    def stop_process(self, name):
        task_info = self.task_status.get(name, {})
        if task_info.get("status") != "running":
            # self.sig_log.emit(f"任务 {name} 不在运行中，无法停止")
            return
        
        original_restart_policy = task_info.get("auto_restart", False)
        if original_restart_policy:
            self.task_status[name]["auto_restart"] = False

        instance = task_info.get("instance")
        if instance:
            instance.kill()

        if original_restart_policy:
            QTimer.singleShot(100, lambda: self.task_status[name].__setitem__("auto_restart", original_restart_policy))

    def restart_process(self, name):
        self.stop_process(name)
        QTimer.singleShot(1000, lambda: self.start_process(name))
    
    def load_config(self,config_data:dict):
        self.sig_log.emit("开始加载任务配置...")
        if not isinstance(config_data, dict):
            self.sig_log.emit("警告: 配置文件格式不正确，应为字典。")
            return
        
        is_autostart_launch = "--autostart" in sys.argv

        for name, task_dict in config_data.items():
            if "name" not in task_dict:
                task_dict["name"] = name
            self.add_task(task_dict)
            
            if is_autostart_launch and task_dict.get("start_up"):
                self.sig_log.emit(f"自启动模式: 启动任务 {name}。")
                self.start_process(name)
                
        self._update_app_autostart_status()
        self.sig_log.emit("任务配置加载完毕。")

    def write_to_process(self, target_name, data_str):
        if target_name in self.task_status:
            proc = self.task_status[target_name].get("instance")
            if proc and proc.state() == QProcess.Running:
                proc.write((data_str + "\n").encode('utf-8'))
            else:
                self.sig_log.emit(f"错误: 目标任务 {target_name} 未运行或不存在")

    def handle_output(self, source_name):
        proc = self.task_status[source_name].get("instance")
        if not proc: return
        data_bytes = proc.readAll().data()
        try:
            raw_data = data_bytes.decode('utf-8').strip()
        except UnicodeDecodeError:
            try:
                raw_data = data_bytes.decode('gbk').strip()
            except UnicodeDecodeError as e:
                self.sig_log.emit(f"错误: 解码来自 {source_name} 的输出失败: {e}")
                return

        for line in raw_data.split('\n'):
            if not line: continue
            self.route_message(source_name, line)
            
    def route_message(self, source_name, message):
        if (source_name in self.task_status) and self.task_status[source_name]["show_type"]=="secondlevel_page":
            self.task_page.add_text(source_name, message)

    def get_running_tasks(self) -> list[str]:
        """返回所有正在运行的任务名称列表"""
        return [name for name, task in self.task_status.items() if task.get("status") == "running"]

    def stop_all_tasks(self):
        """停止所有正在运行的任务"""
        running_tasks = self.get_running_tasks()
        self.sig_log.emit(f"正在停止所有任务: {running_tasks}")
        for name in running_tasks:
            self.stop_process(name)
            
    def print_log(self, message):
        print(message)
