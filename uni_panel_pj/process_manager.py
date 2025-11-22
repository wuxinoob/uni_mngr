import subprocess
import sys
import os
from typing import Optional
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QHBoxLayout, QMenu,
    QSystemTrayIcon, QStyle, QPushButton, QListWidget, QListWidgetItem, QVBoxLayout, QStackedWidget, QLineEdit, QLayout, QFormLayout, QPlainTextEdit
)
from PySide6.QtCore import Qt, QTimer, QPoint, QRectF, Signal, QThread, QPropertyAnimation, QEasingCurve, QBuffer, QRect
from PySide6.QtGui import (
    QPainter, QColor, QAction, QPixmap, QGuiApplication,
    QIcon, QBrush, QPen, QFont, QImage, QRegion, 
)

from queue import Queue
import threading
import importlib.util
import importlib
import traceback
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

def read_output(stream,stdout_queue:Queue,process_name:str, process):
    """读取输出，并加入队列中"""
    try:
        for line in iter(stream.readline, ''):
            stdout_queue.put(process_name +" " +line.strip())
    finally:
        print("process end")
        stream.close()
#        process.wait()




#from uni_panel import base_execcute
class ProcessManager():
    """管理进程的创建结束，生命周期，捕获输出到队列中"""
    def __init__(self):
        self.stdout_queue = Queue()
        self.process_dict:dict[str, subprocess.Popen] = {} #持久进程列表
        self.ui_dict = {} #UI进程列表:dict[str, base_execcute]
        pass
    def add_task(self, task_name:str, task_cmd:str,task_type ,bind_ui) -> None:#bind_ui :Optional[base_execcute]
        assert task_type == "continue_process"
        process = subprocess.Popen( task_cmd, shell=True, stdout=subprocess.PIPE, 
                                    stderr=subprocess.STDOUT, stdin=subprocess.PIPE,
                                    encoding='gbk', bufsize=1,# 行缓冲
                                    )
        threading.Thread(target=read_output, args=(process.stdout, self.stdout_queue,
                                                   task_name, process)).start()
        self.process_dict[task_name] = process
        if bind_ui: # 绑定UI进程
            self.ui_dict[task_name] = bind_ui
    def remove_task(self, task_name:str) -> None:
        process = self.process_dict.get(task_name)
        if process:
            process.terminate()  # 终止子进程
            process.stdout.close()  # 关闭标准输出流
              # 等待子进程完全退出
    def restart_task(self, task_name:str) -> None:
        pass
    def change_task(self, task_name:str) -> None:
        pass
    def add_timer_task(self, task_name:str) -> None:
        pass
    def msg_handle(self):
        msg_handle = msg_handler(self.stdout_queue,self)
        threading.Thread(target=msg_handle.handle_msg, args=()).start()


class msg_handler():
    """管理队列中输出的传递（交给宏处理）"""
    
    def __init__(self, stdout_queue: Queue, linked_process_mngr: ProcessManager, plugin_dir: str = "hong", ):
        self.linked_process_mngr = linked_process_mngr
        self.queue = stdout_queue
        self.plugin_dir = os.path.join(current_dir, plugin_dir)
        # 存储加载的处理函数列表
        self.processors = [] 
        
        # 初始化时加载所有外部逻辑
        self._load_plugins()

    def _load_plugins(self):
        """动态加载 plugins 文件夹下的 .py 文件"""
        if not os.path.exists(self.plugin_dir):
            os.makedirs(self.plugin_dir)
            print(f"创建了插件目录: {self.plugin_dir}")
            return

        # 获取所有 .py 文件并排序（按文件名顺序执行）
        files = sorted([f for f in os.listdir(self.plugin_dir) if f.endswith('.py')])
        
        for filename in files:
            filepath = os.path.join(self.plugin_dir, filename)
            module_name = filename[:-3] # 去掉 .py
            
            try:
                # 动态导入模块的核心代码
                spec = importlib.util.spec_from_file_location(module_name, filepath)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # 检查模块中是否有约定的 'process' 函数
                    if hasattr(module, 'process'):
                        self.processors.append(module.process)
                        print(f"已加载插件: {filename}")
                    else:
                        print(f"跳过 {filename}: 未找到 'process' 函数")
            except Exception as e:
                print(f"加载插件 {filename} 失败: {e}")

    def handle_msg(self) -> None:
        """加入线程结束处理，并执行管道逻辑"""
        print("开始监听队列...")
        while True:
            line = self.queue.get()
            
            # 退出信号检查
            if line == "9527":
                print("收到退出信号，停止处理。")
                break
            
            # --- 核心管道处理逻辑 ---
            current_data = line
            try:
                for func in self.processors:
                    # 将上一个函数的输出作为下一个函数的输入
                    current_data = func(current_data, self)
                    
                    # 如果某个插件返回 None，通常意味着“丢弃该消息”或“中断处理”
                    if current_data is None:
                        break
                
                if current_data is not None:
                    print(f"最终处理结果: {current_data}")
                    # 这里可以将 current_data 发送到其他地方
                    
            except Exception as e:
                print(f"处理消息时发生错误: {e}")
                traceback.print_exc()
            # -----------------------