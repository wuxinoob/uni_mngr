import sys
import shlex  # 导入 shlex 模块，用于安全地解析命令行字符串

from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QHBoxLayout, QGroupBox,
    QPushButton, QVBoxLayout, QPlainTextEdit, QTextBrowser,
    QFormLayout, QLineEdit, QCheckBox, QTimeEdit
)
from PySide6.QtCore import Qt, QTimer, QProcess, QTime

# --- 常量定义 ---
# 定义进程状态的枚举，方便管理和阅读
STATE_STOPPED = 0
STATE_RUNNING = 1
STATE_FINISHED = 2

class AdvancedTaskRunner(QWidget):
    """
    一个高级的任务执行器窗口部件。
    它允许用户配置、运行、停止和重启一个外部命令（如 Python 脚本），
    并提供了定时启动和自启动的选项。
    """
    def __init__(self,
                 task_name: str = "默认任务",
                 exec_cmd: str = r"python -u D:\path\to\your\script.py", # 使用 -u 确保输出不被缓冲
                 working_dir: str = "",
                 description: str = "这是一个任务的详细描述。"):
        super().__init__()

        # --- 内部状态和变量初始化 ---
        self.p = None  # 用于存储 QProcess 对象的引用，初始为 None
        self.process_state = STATE_STOPPED  # 初始化进程状态为“停止”
        self._is_restarting = False  # 一个标志，用于处理重启逻辑

        # --- UI 初始化 ---
        self.init_ui(task_name, exec_cmd, working_dir, description)

        # --- 启动定时器，用于检查是否到达定时启动时间 ---
        self.schedule_timer = QTimer(self)
        self.schedule_timer.timeout.connect(self.check_schedule)
        self.schedule_timer.start(10000)  # 每 10 秒检查一次

        # --- 检查是否需要自启动 ---
        if self.autostart_checkbox.isChecked():
            # 使用 QTimer.singleShot(0, ...) 可以在主事件循环开始后立即执行，
            # 确保UI完全加载后再启动任务，避免阻塞。
            QTimer.singleShot(0, self.start_task)

    def init_ui(self, task_name, exec_cmd, working_dir, description):
        """
        初始化用户界面。
        """
        main_layout = QVBoxLayout(self) # 主垂直布局

        # --- 任务基本信息区域 ---
        info_group = QGroupBox("任务信息")
        info_layout = QFormLayout()

        self.task_name_label = QLabel(task_name)
        self.task_description_label = QLabel(description)
        info_layout.addRow("任务名称:", self.task_name_label)
        info_layout.addRow("任务描述:", self.task_description_label)
        info_group.setLayout(info_layout)

        # --- 任务配置区域 ---
        config_group = QGroupBox("任务配置")
        config_layout = QFormLayout()

        # 命令行输入
        self.task_cmd_line = QLineEdit(exec_cmd)
        self.task_cmd_line.setToolTip("输入要执行的完整命令，例如: python -u my_script.py")
        config_layout.addRow("执行命令:", self.task_cmd_line)

        # 工作目录输入
        self.working_dir_line = QLineEdit(working_dir)
        self.working_dir_line.setToolTip("设置命令执行时的工作目录，留空则使用默认目录")
        config_layout.addRow("工作目录:", self.working_dir_line)

        # 定时和自启动选项
        schedule_layout = QHBoxLayout()
        self.schedule_checkbox = QCheckBox("定时启动")
        self.schedule_time_edit = QTimeEdit(QTime.currentTime())
        self.schedule_time_edit.setDisplayFormat("HH:mm")
        schedule_layout.addWidget(self.schedule_checkbox)
        schedule_layout.addWidget(self.schedule_time_edit)
        config_layout.addRow(schedule_layout)

        self.autostart_checkbox = QCheckBox("程序启动时自动运行此任务")
        config_layout.addRow(self.autostart_checkbox)
        
        config_group.setLayout(config_layout)

        # --- 任务控制区域 ---
        control_group = QGroupBox("任务控制")
        control_layout = QHBoxLayout()
        
        self.status_label = QLabel("状态: 未运行") # 状态显示标签

        self.start_button = QPushButton("启动")
        self.start_button.clicked.connect(self.start_task)

        self.stop_button = QPushButton("停止")
        self.stop_button.clicked.connect(self.stop_task)

        self.restart_button = QPushButton("重启")
        self.restart_button.clicked.connect(self.restart_task)
        
        control_layout.addWidget(self.status_label)
        control_layout.addStretch() # 添加伸缩，让按钮靠右
        control_layout.addWidget(self.start_button)
        control_layout.addWidget(self.stop_button)
        control_layout.addWidget(self.restart_button)
        control_group.setLayout(control_layout)

        # --- 输出日志区域 ---
        self.output_browser = QTextBrowser()
        self.output_browser.setStyleSheet("background-color: #2b2b2b; color: #f0f0f0;") # 设置一个深色主题
        self.output_browser.setFontPointSize(12)

        # --- 将所有区域添加到主布局 ---
        main_layout.addWidget(info_group)
        main_layout.addWidget(config_group)
        main_layout.addWidget(control_group)
        main_layout.addWidget(self.output_browser, 1) # 第二个参数 1 表示此控件会占据所有可用垂直空间

        self.setLayout(main_layout)
        self.setWindowTitle("高级任务执行器")
        self.resize(800, 600)
        self.show()

        # 初始化按钮状态
        self.update_button_states()

    def start_task(self):
        """
        启动任务。
        """
        # 如果进程已经在运行，则不执行任何操作
        if self.p and self.p.state() == QProcess.ProcessState.Running:
            self.log_message("任务已在运行中。")
            return

        # 创建一个新的 QProcess 实例
        self.p = QProcess()
        
        # --- 连接信号到槽函数 ---
        self.p.readyReadStandardOutput.connect(self.handle_stdout) # 标准输出
        self.p.readyReadStandardError.connect(self.handle_stderr)   # 标准错误
        self.p.finished.connect(self.handle_finish)                  # 进程结束
        self.p.stateChanged.connect(self.handle_state_change)      # 进程状态改变

        # --- 配置进程 ---
        # 设置工作目录
        work_dir = self.working_dir_line.text()
        if work_dir:
            self.p.setWorkingDirectory(work_dir)
            self.log_message(f"设置工作目录为: {work_dir}")

        # 解析命令行
        cmd_text = self.task_cmd_line.text()
        try:
            # shlex.split 可以正确处理带引号的参数，比 " ".split() 更安全
            parts = shlex.split(cmd_text)
            program = parts[0]
            arguments = parts[1:]
        except Exception as e:
            self.log_message(f"错误：无法解析命令 '{cmd_text}'. 错误信息: {e}")
            self.p = None
            return

        # --- 启动进程 ---
        self.log_message(f"正在启动任务: {cmd_text}")
        self.p.start(program, arguments)
    
    def stop_task(self):
        """
        停止当前正在运行的任务。
        """
        if self.p and self.p.state() == QProcess.ProcessState.Running:
            self.log_message("正在停止任务...")
            self.p.kill() # 强制终止进程及其所有子进程
        else:
            self.log_message("任务未在运行。")
    
    def restart_task(self):
        """
        重启任务。先停止，然后在停止后自动启动。
        """
        if self.p and self.p.state() == QProcess.ProcessState.Running:
            self._is_restarting = True  # 设置重启标志
            self.log_message("正在准备重启任务...")
            self.stop_task() # 调用停止方法
        else:
            # 如果任务没有运行，重启就等同于启动
            self.log_message("任务未运行，直接启动。")
            self.start_task()

    # --- QProcess 信号处理槽函数 ---

    def handle_stdout(self):
        """处理标准输出。"""
        data = self.p.readAllStandardOutput()
        # 将字节数据解码为字符串，使用系统默认编码
        text = bytes(data).decode(sys.stdout.encoding, errors='ignore')
        self.log_message(text.strip())

    def handle_stderr(self):
        """处理标准错误。"""
        data = self.p.readAllStandardError()
        text = bytes(data).decode(sys.stderr.encoding, errors='ignore')
        # 为了醒目，可以在错误信息前加上标记
        self.log_message(f"[错误] {text.strip()}")

    def handle_finish(self, exit_code, exit_status):
        """当进程结束后被调用。"""
        self.process_state = STATE_FINISHED
        self.log_message(f"任务已结束。退出代码: {exit_code}, 退出状态: {exit_status.name}")

        # 检查是否是重启流程的一部分
        if self._is_restarting:
            self._is_restarting = False # 重置重启标志
            self.log_message("...任务已停止，现在自动重新启动。")
            # 延时一小段时间再启动，给系统一点缓冲时间
            QTimer.singleShot(500, self.start_task)
        else:
            # 如果不是重启，则彻底清理资源
            self.p = None
        
        self.update_button_states()

    def handle_state_change(self, state):
        """当进程状态改变时被调用，用于更新UI。"""
        if state == QProcess.ProcessState.NotRunning:
            # 注意：这里的 NotRunning 可能是启动失败或已结束
            # 具体状态由 handle_finish 来最终确定
            if self.process_state != STATE_FINISHED:
                self.process_state = STATE_STOPPED
        elif state == QProcess.ProcessState.Starting:
            self.log_message("任务正在启动...")
        elif state == QProcess.ProcessState.Running:
            self.process_state = STATE_RUNNING
            self.log_message("任务已成功启动并正在运行。")
        self.update_button_states()

    # --- 辅助和逻辑函数 ---

    def log_message(self, message: str):
        """向日志浏览器添加一条消息。"""
        self.output_browser.append(message)

    def update_button_states(self):
        """根据当前进程状态，更新按钮的可用性和状态标签的文本。"""
        if self.process_state == STATE_RUNNING:
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.restart_button.setEnabled(True)
            self.status_label.setText("状态: <font color='green'>运行中</font>")
        else: # 包括 STATE_STOPPED 和 STATE_FINISHED
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.restart_button.setEnabled(False) # 只有在运行时才能重启
            if self.process_state == STATE_STOPPED:
                self.status_label.setText("状态: 未运行")
            else: # STATE_FINISHED
                self.status_label.setText("状态: <font color='red'>已结束</font>")

    def check_schedule(self):
        """由定时器调用，检查是否到达预定的启动时间。"""
        # 如果“定时启动”未勾选，或者任务已经在运行，则直接返回
        if not self.schedule_checkbox.isChecked() or (self.p and self.p.state() == QProcess.ProcessState.Running):
            return

        # 获取当前时间和设定的时间
        current_time = QTime.currentTime()
        scheduled_time = self.schedule_time_edit.time()

        # 检查小时和分钟是否匹配
        if current_time.hour() == scheduled_time.hour() and current_time.minute() == scheduled_time.minute():
            self.log_message(f"到达预定时间 {scheduled_time.toString('HH:mm')}，自动启动任务。")
            self.start_task()

    def closeEvent(self, event):
        """
        重写窗口关闭事件，确保在关闭窗口时，子进程也被终止。
        """
        self.log_message("窗口即将关闭，正在清理任务...")
        self.stop_task() # 尝试优雅地停止任务
        # 如果进程还在，等待一小段时间
        if self.p:
            if not self.p.waitForFinished(1000): # 等待1秒
                self.log_message("任务未能正常退出，强制终止。")
                self.p.kill()
        
        event.accept() # 接受关闭事件


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 示例：创建一个执行测试脚本的任务
    # 为了方便测试，可以创建一个简单的 timer.py 脚本:
    # import time
    # import sys
    # print("Timer script started.")
    # sys.stdout.flush()
    # for i in range(10):
    #     print(f"Tick {i+1}")
    #     sys.stdout.flush() # 强制刷新缓冲区，让输出立即显示
    #     time.sleep(1)
    # print("Timer script finished.")

    # 请将下面的路径替换为您自己的测试脚本路径
    cmd = r'python -u D:\Code\Y700\Python\uni_tool_mangr\task\lib\timer.py' # 使用-u参数确保python输出不缓冲
    
    # 创建并显示主窗口
    main_window = AdvancedTaskRunner(exec_cmd=cmd)
    
    sys.exit(app.exec())