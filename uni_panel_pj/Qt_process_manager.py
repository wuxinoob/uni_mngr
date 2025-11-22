import sys
import json
from PySide6.QtCore import QObject, QProcess, Signal, Slot, QCoreApplication, QTimer
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QTextEdit, QWidget

# -----------------------------------------------------------------------------
# 1. 进程管理器 (核心大脑)
# -----------------------------------------------------------------------------
class ProcessManager(QObject):
    # 发送给 UI 的信号
    sig_log = Signal(str)          # 普通日志
    task_msg = Signal(str)      # 任务消息
    sig_status_update = Signal(dict) # 状态更新
    ui_msg = Signal(str)           # UI更新专用 消息

    def __init__(self):
        super().__init__()
        self.task = {} # 存储 { "name": QProcess_instance }
        self.task_status = {} # 存储 { "name": {status: "running" | "stopped", task_type: "task", "dedicated_task", command: str, args: list} }


    def add_task(self, name:str, command:str, args, task_type:str, ui_obj):
        assert task_type in ["task", "dedicated_task"] #不同类型的任务处理
        if name in self.task:
            self.sig_log.emit(f"任务名 {name} 已经存在，请更改任务名或删除原任务")
            return
        process_dict = {"status": "stopped",
                        "task_type": task_type,
                        "command": command,
                        "args"  : args,   
                        "name"  : name,  
                        }
        self.task_status[name] = process_dict
        ui_obj.add_config_task_page(self.task_status[name])
        #在这一部分要添加前端的任务列表与新页面，写入配置文件持久化
    def change_task_attributes(self, name:str, command:str, args):
        if name in self.task_status:
            self.task_status[name]["command"] = command
            self.task_status[name]["args"] = args

            #更新前端显示
        else:
            self.sig_log.emit(f"任务 {name} 不存在")
            return
    def start_process(self, name:str):
        if name in self.task and self.task[name].state() != QProcess.NotRunning:
            self.sig_log.emit(f"任务 {name} 已经在运行中")
            return

        process = QProcess()
        process.setProgram(self.task_status[name]["command"])
        process.setArguments(self.task_status[name]["args"])
        
        # 关键：连接信号
        # 当有输出时，调用 handle_output
        process.readyReadStandardOutput.connect(lambda: self.handle_output(name))
        process.finished.connect(lambda: self.cleanup_process(name))
        
        self.task[name] = process
        process.start()
        self.sig_log.emit(f"启动进程: {name}")

    def clean_task(self, name):
        if name in self.task:
            self.task[name].kill()
        self.task.pop(name)
        self.task_status.pop(name)
        #要更新前端显示

    def stop_process(self, name):
        if name in self.task:
            self.task[name].kill()


    def load_config(self,config):
        pass
    def write_to_process(self, target_name, data_str):
        """向指定任务的 stdin 写入数据 需要重写"""
        if target_name in self.task:
            proc = self.task[target_name]
            if proc.state() == QProcess.Running:
                # 注意添加换行符，并转为 bytes
                proc.write((data_str + "\n").encode('utf-8'))
            else:
                self.sig_log.emit(f"错误: 目标任务 {target_name} 未运行")

    def handle_output(self, source_name):
        """
        核心消息处理器：读取子任务输出，并路由
        """
        proc = self.task[source_name]
        # 读取所有可用数据
        raw_data = proc.readAllStandardOutput().data().decode('utf-8').strip()
        
        # 可能一次读取多行，需要分割处理
        for line in raw_data.split('\n'):
            if not line: continue
            self.route_message(source_name, line)

    def route_message(self, source_name, message):
        """
        路由逻辑：决定消息是给 UI 还是给其他进程
        若
        """
        if self.task_status[source_name]["task_type"] == "task":
            warped_message = json.dumps({"message": message, "task_name": source_name})

            self.ui_msg.emit(warped_message)
        try:
            # 假设子进程输出的是 JSON
            # 格式: {"target": "ui"|"proc_b", "content": "..."}
            data = json.loads(message)
            target = data.get("target")
            content = data.get("content")

            if target == "ui":
                # 转发给前端
                self.sig_log.emit(f"[{source_name} -> UI]: {content}")
            
            elif target in self.task:
                # 转发给另一个进程 (IPC)
                self.sig_log.emit(f"[{source_name} -> {target}]: 转发数据")
                self.write_to_process(target, json.dumps(content)) # 再次序列化发送
            
            else:
                self.sig_log.emit(f"[{source_name}]: 未知目标 {message}")

        except json.JSONDecodeError:
            # 如果不是 JSON，直接显示为普通日志
            self.sig_log.emit(f"[{source_name} Raw]: {message}")

    def cleanup_process(self, name):
        self.sig_log.emit(f"进程 {name} 已结束")
        # 不一定要删掉 key，看需求，这里简单处理
        # del self.task[name]