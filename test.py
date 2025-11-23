import sys
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QPushButton, 
                               QVBoxLayout, QWidget, QLabel, QHBoxLayout)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer, Property
from PySide6.QtGui import QFont, QPainter, QColor, QLinearGradient, QGuiApplication

class ToastNotification(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")
        
        # 初始化UI
        self.init_ui()
        
        # 获取屏幕尺寸
        screen = QGuiApplication.primaryScreen().availableGeometry()
        self.screen_width = screen.width()
        self.screen_height = screen.height()
        
        # 设置初始位置（屏幕右下角外）
        self.move(self.screen_width, self.screen_height - 150)
        
        # 动画
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        self.animation.setDuration(500)
        
        # 自动关闭计时器
        self.close_timer = QTimer()
        self.close_timer.timeout.connect(self.hide_notification)
        self.close_timer.setSingleShot(True)

    def init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)
        
        # 标题和关闭按钮
        header_layout = QHBoxLayout()
        
        self.title_label = QLabel("通知")
        self.title_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                font-weight: bold;
                font-size: 14px;
            }
        """)
        
        self.close_btn = QPushButton("×")
        self.close_btn.setFixedSize(20, 20)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #7f8c8d;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #e74c3c;
                background: rgba(231, 76, 60, 0.1);
                border-radius: 10px;
            }
        """)
        self.close_btn.clicked.connect(self.hide_notification)
        
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.close_btn)
        
        # 消息内容
        self.message_label = QLabel()
        self.message_label.setStyleSheet("""
            QLabel {
                color: #34495e;
                font-size: 13px;
                background: transparent;
            }
        """)
        self.message_label.setWordWrap(True)
        self.message_label.setMinimumWidth(300)
        self.message_label.setMaximumWidth(350)
        
        main_layout.addLayout(header_layout)
        main_layout.addWidget(self.message_label)
        
        self.setLayout(main_layout)

    def paintEvent(self, event):
        """绘制圆角和阴影效果"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制背景
        rect = self.rect().adjusted(0, 0, -1, -1)
        
        # 渐变背景
        gradient = QLinearGradient(rect.topLeft(), rect.bottomLeft())
        gradient.setColorAt(0, QColor(255, 255, 255, 240))
        gradient.setColorAt(1, QColor(240, 240, 240, 240))
        
        painter.setBrush(gradient)
        painter.setPen(QColor(200, 200, 200, 150))
        painter.drawRoundedRect(rect, 12, 12)
        
        # 绘制边框
        painter.setPen(QColor(220, 220, 220, 100))
        painter.drawRoundedRect(rect, 12, 12)

    def show_notification(self, title="通知", message="", duration=3000):
        """显示通知"""
        self.title_label.setText(title)
        self.message_label.setText(message)
        
        # 调整大小
        self.adjustSize()
        
        # 计算目标位置（屏幕右下角）
        target_x = self.screen_width - self.width() - 20
        target_y = self.screen_height - self.height() - 60
        
        # 设置动画
        start_rect = self.geometry()
        start_rect.moveTo(self.screen_width, target_y)
        end_rect = self.geometry()
        end_rect.moveTo(target_x, target_y)
        
        self.animation.setStartValue(start_rect)
        self.animation.setEndValue(end_rect)
        
        # 显示并开始动画
        self.show()
        self.animation.start()
        
        # 设置自动关闭
        self.close_timer.start(duration)

    def hide_notification(self):
        """隐藏通知"""
        # 设置退出动画
        start_rect = self.geometry()
        end_rect = self.geometry()
        end_rect.moveTo(self.screen_width, start_rect.y())
        
        self.animation.setStartValue(start_rect)
        self.animation.setEndValue(end_rect)
        self.animation.start()
        
        # 动画结束后隐藏
        QTimer.singleShot(500, self.hide)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
        # 创建通知窗口
        self.notification = ToastNotification()

    def init_ui(self):
        """初始化主窗口UI"""
        self.setWindowTitle("消息通知示例")
        self.setGeometry(100, 100, 400, 200)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        
        # 测试按钮
        btn1 = QPushButton("显示普通通知")
        btn1.clicked.connect(self.show_normal_notification)
        
        btn2 = QPushButton("显示警告通知")
        btn2.clicked.connect(self.show_warning_notification)
        
        btn3 = QPushButton("显示成功通知")
        btn3.clicked.connect(self.show_success_notification)
        
        layout.addWidget(btn1)
        layout.addWidget(btn2)
        layout.addWidget(btn3)
        
        central_widget.setLayout(layout)

    def show_normal_notification(self):
        """显示普通通知"""
        self.notification.show_notification(
            "系统通知", 
            "这是一个普通的系统通知消息，将在3秒后自动消失。",
            3000
        )

    def show_warning_notification(self):
        """显示警告通知"""
        self.notification.show_notification(
            "警告", 
            "这是一个警告消息！请注意系统状态。",
            5000
        )

    def show_success_notification(self):
        """显示成功通知"""
        self.notification.show_notification(
            "操作成功", 
            "您的操作已成功完成！数据已保存到数据库。",
            4000
        )

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 设置应用程序样式
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())