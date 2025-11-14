import subprocess
import sys
import os
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

class msg_handler():
    """管理队列中输出的传递（交给宏处理）"""
    def __init__(self,stdout_queue:Queue):
        self.queue = stdout_queue
        pass
    def handle_msg(self) -> None:
        """加入线程结束处理"""
        while True:
            line = self.queue.get()
            if line == "9527":
                break
            pass# 宏处理

class ProcessManager():
    """管理进程的创建结束，生命周期，捕获输出到队列中"""
    def __init__(self):
        self.stdout_queue = Queue()
        process_dict = {}
        pass
    def add_task(self, task_name:str, task_cmd:str,task_type) -> None:
        pass
    def remove_task(self, task_name:str) -> None:
        pass
    def restart_task(self, task_name:str) -> None:
        pass
    def read_output(self,stream):
        try:
            for line in iter(stream.readline, ''):
                self.stdout_queue.put((line.strip()))
        finally:
            stream.close()
    def msg_handle(self):
        msg_handle = msg_handler(self.stdout_queue)
        threading.Thread(target=msg_handle.handle_msg, args=()).start()


