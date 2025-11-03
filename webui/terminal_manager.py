# terminal_manager.py
import subprocess
import shlex
import threading
import uuid
from queue import Queue

class TerminalInstance:
    """封装一个终端进程及其相关资源"""
    def __init__(self, command):
        self.id = str(uuid.uuid4())
        self.command = command
        self.process = None
        self.output_queue = Queue()
        self.thread = threading.Thread(target=self._capture_output)
        self.is_running = False

    def start(self):
        """启动子进程和输出捕获线程"""
        try:
            # 在Windows上，cmd /c a_command & a_command_2 可以执行多个命令
            # powershell -Command "..." 是更强大的选择
            args = ['powershell', '-Command', self.command]
            
            self.process = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                bufsize=1,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP # 在Windows上确保能独立终止
            )
            self.is_running = True
            self.thread.start()
        except Exception as e:
            # 如果启动失败，将错误信息放入队列
            self.output_queue.put(f"Failed to start command: {e}\n")
            self.is_running = False

    def _capture_output(self):
        """在后台线程中运行，实时读取并推送输出到队列"""
        # 将命令本身作为第一行输出
        self.output_queue.put(f"PS> {self.command}\n\n")

        for line in iter(self.process.stdout.readline, ''):
            self.output_queue.put(line)

        self.process.stdout.close()
        return_code = self.process.wait()
        self.output_queue.put(f"\n[Process finished with exit code {return_code}]\n")
        self.is_running = False
        self.output_queue.put(None) # 发送结束信号

    def get_output_generator(self):
        """提供一个生成器，从队列中获取输出"""
        while True:
            line = self.output_queue.get()
            if line is None: # 遇到结束信号
                break
            yield line

    def to_dict(self):
        """返回终端信息，用于API"""
        return {'id': self.id, 'command': self.command, 'is_running': self.is_running}

class TerminalManager:
    """单例模式的终端管理器"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TerminalManager, cls).__new__(cls)
            cls._instance.terminals = {}
        return cls._instance

    def start_terminal(self, command):
        instance = TerminalInstance(command)
        self.terminals[instance.id] = instance
        instance.start()
        return instance

    def get_terminal(self, terminal_id):
        return self.terminals.get(terminal_id)

    def list_terminals(self):
        return [t.to_dict() for t in self.terminals.values()]

# 创建一个全局单例
manager = TerminalManager()