# -*- coding: utf-8 -*-
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QStyle
from PySide6.QtCore import Qt, QPoint, Signal, Slot
from PySide6.QtGui import QMouseEvent

class CustomTitleBar(QWidget):
    """自定义标题栏，支持拖动和窗口控制"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.setFixedHeight(40)

        # --- UI 组件 ---
        self.icon_label = QLabel()
        self.title_label = QLabel("通用面板")
        self.minimize_button = QPushButton("—")
        self.maximize_button = QPushButton() # Text set dynamically
        self.close_button = QPushButton("✕")

        # --- 样式和布局 ---
        self.setAutoFillBackground(True)
        
        # 按钮固定宽度
        self.minimize_button.setFixedSize(40, 40)
        self.maximize_button.setFixedSize(40, 40)
        self.close_button.setFixedSize(40, 40)

        # 设置 objectName 以便在 QSS 中应用样式
        self.setObjectName("customTitleBar")
        self.minimize_button.setObjectName("minimizeButton")
        self.maximize_button.setObjectName("maximizeButton")
        self.close_button.setObjectName("closeButton")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 0, 0)
        layout.setSpacing(10)
        
        layout.addWidget(self.icon_label)
        layout.addWidget(self.title_label)
        layout.addStretch()
        layout.addWidget(self.minimize_button)
        layout.addWidget(self.maximize_button)
        layout.addWidget(self.close_button)

        # --- 连接信号 ---
        self.minimize_button.clicked.connect(self.on_minimize_clicked)
        self.maximize_button.clicked.connect(self.on_maximize_clicked)
        self.close_button.clicked.connect(self.on_close_clicked)

        # --- 拖动所需变量 ---
        self._is_dragging = False
        self._drag_start_pos = QPoint()
        self._connection_established = False # 确保信号只连接一次

        self.update_maximize_icon() # Set initial icon

    def showEvent(self, event):
        """在窗口显示时，确保信号已连接"""
        if self.parent_window and not self._connection_established:
            self.parent_window.windowHandle().windowStateChanged.connect(self.update_maximize_icon)
            self._connection_established = True
        super().showEvent(event)

    def set_icon(self, icon):
        self.icon_label.setPixmap(icon.pixmap(24, 24))

    def set_title(self, title):
        self.title_label.setText(title)

    @Slot()
    def update_maximize_icon(self):
        """根据窗口状态更新最大化/恢复按钮的图标"""
        if self.parent_window and self.parent_window.isMaximized():
            self.maximize_button.setText("🗗") # Restore icon
            self.maximize_button.setToolTip("Restore")
        else:
            self.maximize_button.setText("🗖") # Maximize icon
            self.maximize_button.setToolTip("Maximize")


    # --- 窗口控制槽函数 ---
    def on_minimize_clicked(self):
        self.parent_window.showMinimized()

    def on_maximize_clicked(self):
        if self.parent_window.isMaximized():
            self.parent_window.showNormal()
        else:
            self.parent_window.showMaximized()
        # The icon will be updated via the windowStateChanged signal

    def on_close_clicked(self):
        self.parent_window.close()

    # --- 鼠标事件处理 ---
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.parent_window.isMaximized():
                return 
            
            # 使用系统原生移动，极大提升流畅度并支持 Windows 分屏特性
            # 注意：startSystemMove 会阻塞直到拖动结束
            self.parent_window.windowHandle().startSystemMove()
            event.accept()

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """双击标题栏最大化/恢复"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.on_maximize_clicked()
            event.accept()
