from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QHBoxLayout, QMenu,
    QSystemTrayIcon, QStyle, QPushButton, QListWidget, QListWidgetItem, QVBoxLayout, QStackedWidget, QPlainTextEdit, QTextBrowser, QTextEdit
)
from PySide6.QtCore import Qt, QTimer, QPoint, QRectF, Signal, QThread, QPropertyAnimation, QEasingCurve, QBuffer, QRect, QProcess
from PySide6.QtGui import (
    QPainter, QColor, QAction, QPixmap, QGuiApplication,
    QIcon, QBrush, QPen, QFont, QImage, QRegion
)
import sys

class config_widget(QWidget):
    def __init__(self,parent=None):
        super(self.__class__,self).__init__(parent)
        layout = QVBoxLayout()
        layout.addWidget(QLabel("config"))
        self.setLayout(layout)
    def setup(self):
        self.show()




class base_cmd_cexecute(QWidget):
    def __init__(self,exec_cmd:str=r"D:\Code\Y700\Python\uni_tool_mangr\task\lib\timer.py",name:str = "timer"):
        super().__init__()

        self.exec_cmd = exec_cmd
        self.p = None
        layout = QVBoxLayout()
        self.task_name = QLabel(name) 
        self.task_discription = QLabel("任务描述")
        hlayout1 = QHBoxLayout() 
        hlayout1.addWidget(self.task_name)
        hlayout1.addWidget(self.task_discription)


        self.taskConfig = QPushButton("任务配置")
        self.taskCmdLine = QTextEdit()
        self.taskCmdLine.setText(exec_cmd)
        hlayout2 = QHBoxLayout()
        hlayout2.addWidget(self.taskConfig)
        hlayout2.addWidget(self.taskCmdLine)


        self.cmd_wid = QTextBrowser()
        self.cmd_wid.setFontPointSize(30)

        
        self.start_button = QPushButton("start")
        self.start_button.clicked.connect(self.start_cmd)
        self.config_button = QPushButton("config")
        self.config_wid = config_widget()
        self.config_button.clicked.connect(self.config_wid.setup)


        layout.addLayout(hlayout1)
        layout.addLayout(hlayout2)
        layout.addWidget(self.cmd_wid)
        layout.addWidget(self.start_button)
        layout.addWidget(self.config_button)
        self.show()
        self.setLayout(layout)

    def load_config(self) -> dict[str,str]:
        return{}
    def start_cmd(self):
        if not self.p:
            self.p = QProcess()
            self.p.readyReadStandardOutput.connect(self.handle_output)
            self.p.readyReadStandardError.connect(self.handle_error)
            self.p.finished.connect(self.handle_finish)
            self.p.start("python",[self.exec_cmd])
            self.cmd_wid.append("starting...")

    def handle_output(self):
        data = self.p.readAllStandardOutput()
        data = bytes(data).decode(sys.stdout.encoding)
        self.message(data)
    def handle_error(self):
        data = self.p.readAllStandardError()
        data = bytes(data).decode(sys.stdout.encoding)
        self.message(data)

    def handle_finish(self):
        self.cmd_wid.append("finished")
    def message(self,data):
        self.cmd_wid.append(data)


if __name__ == "__main__":
    app = QApplication()
    wid = base_cmd_cexecute(exec_cmd=r"D:\Code\Y700\Python\uni_tool_mangr\task\lib\timer.py")
    app.exec()