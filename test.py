import sys
import subprocess
import threading
import queue
from PySide6.QtWidgets import QApplication, QMainWindow, QTextEdit, QVBoxLayout, QWidget, QPushButton
from PySide6.QtCore import QTimer

# 1. 共享队列，用于线程间通信
message_queue = queue.Queue()

def stream_reader(process_id, stream):
    """线程执行的函数，负责读取一个流并放入队列"""
    try:
        for line in iter(stream.readline, ''):
            message_queue.put((process_id, line.strip()))
    finally:
        stream.close()

class ProcessManager:
    def __init__(self):
        self.processes = {}  # { 'id': {'process': Popen_object, 'threads': []} }

    def start_process(self, process_id, command):
        if process_id in self.processes:
            print(f"Process {process_id} is already running.")
            return

        print(f"Starting process {process_id} with command: {' '.join(command)}")
        # 注意: python -u 表示无缓冲输出，非常重要！
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
            encoding='utf-8',
            errors='ignore',
            bufsize=1, # 行缓冲
            # creationflags=subprocess.CREATE_NEW_PROCESS_GROUP # Windows
        )

        # 为 stdout 和 stderr 创建监听线程
        stdout_thread = threading.Thread(target=stream_reader, args=(process_id, process.stdout), daemon=True)
        stderr_thread = threading.Thread(target=stream_reader, args=(f"{process_id}_ERR", process.stderr), daemon=True)

        stdout_thread.start()
        stderr_thread.start()

        self.processes[process_id] = {'process': process, 'threads': [stdout_thread, stderr_thread]}

    def stop_process(self, process_id):
        if process_id in self.processes:
            print(f"Stopping process {process_id}...")
            p_info = self.processes.pop(process_id)
            p_info['process'].terminate()  # 发送 SIGTERM
            try:
                p_info['process'].wait(timeout=2) # 等待2秒
            except subprocess.TimeoutExpired:
                p_info['process'].kill() # 强制杀死
            print(f"Process {process_id} stopped.")
    
    def send_message_to_process(self, target_id, message):
        if target_id in self.processes:
            process = self.processes[target_id]['process']
            if process.poll() is None: # 进程仍在运行
                try:
                    # 必须加换行符，让对方的 readline() 能读到
                    process.stdin.write(message + '\n')
                    process.stdin.flush()
                except Exception as e:
                    print(f"Error writing to {target_id}: {e}")
    
    def stop_all(self):
        for process_id in list(self.processes.keys()):
            self.stop_process(process_id)

class ControlPanel(QMainWindow):
    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        self.setWindowTitle("Process Control Panel (Native Python)")

        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        
        self.start_a_button = QPushButton("Start Process A")
        self.start_b_button = QPushButton("Start Process B")
        self.stop_a_button = QPushButton("Stop Process A")
        self.stop_b_button = QPushButton("Stop Process B")

        layout = QVBoxLayout()
        layout.addWidget(self.log_display)
        layout.addWidget(self.start_a_button)
        layout.addWidget(self.start_b_button)
        layout.addWidget(self.stop_a_button)
        layout.addWidget(self.stop_b_button)
        
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # 连接信号
        self.start_a_button.clicked.connect(lambda: self.manager.start_process('ProcA', ['python', '-u', 'my_script.py']))
        self.start_b_button.clicked.connect(lambda: self.manager.start_process('ProcB', ['python', '-u', 'process_b.py']))
        self.stop_a_button.clicked.connect(lambda: self.manager.stop_process('ProcA'))
        self.stop_b_button.clicked.connect(lambda: self.manager.stop_process('ProcB'))

        # 2. 设置定时器，定期从队列中读取消息
        self.timer = QTimer(self)
        self.timer.setInterval(100)  # 每100毫秒
        self.timer.timeout.connect(self.process_queue)
        self.timer.start()

    def process_queue(self):
        """处理消息队列中的所有消息"""
        while not message_queue.empty():
            try:
                source_id, message = message_queue.get_nowait()
                self.log_display.append(f"[{source_id}]: {message}")
                
                # 在这里处理和转发消息
                self.parse_and_forward(source_id, message)
            except queue.Empty:
                break # 队列空了，退出循环
    
    def parse_and_forward(self, source_id, message):
        """解析消息并转发"""
        # 假设协议是 [CMD:TARGET_ID:PAYLOAD]
        if message.startswith('[CMD:') and ']' in message:
            parts = message[5:-1].split(':', 2)
            if len(parts) == 2:
                target_id, payload = parts
                self.log_display.append(f"--- FORWARDING from {source_id} to {target_id}: {payload} ---")
                self.manager.send_message_to_process(target_id, payload)

    def closeEvent(self, event):
        """关闭窗口时清理所有子进程"""
        self.manager.stop_all()
        event.accept()

if __name__ == '__main__':
    # 创建子进程脚本文件 (用于测试)
    with open("my_script.py", "w") as f:
        f.write("""
import sys, time
print("Process A started.")
sys.stdout.flush()
for i in range(10):
    time.sleep(2)
    print(f"Process A heartbeat {i+1}")
    if i == 2:
        # 发送命令给B
        print("[CMD:ProcB:Hello from A!]")
    sys.stdout.flush()
print("Process A finished.")
""")
    with open("process_b.py", "w") as f:
        f.write("""
import sys, time
print("Process B started, waiting for input...")
sys.stdout.flush()
for line in sys.stdin:
    print(f"Process B received: {line.strip()}")
    sys.stdout.flush()
""")
    
    app = QApplication(sys.argv)
    manager = ProcessManager()
    window = ControlPanel(manager)
    window.show()
    sys.exit(app.exec())