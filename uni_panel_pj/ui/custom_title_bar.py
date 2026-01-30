# -*- coding: utf-8 -*-
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QStyle
from PySide6.QtCore import Qt, QPoint, Signal
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
        self.maximize_button = QPushButton("⬜")
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

    def set_icon(self, icon):
        self.icon_label.setPixmap(icon.pixmap(24, 24))

    def set_title(self, title):
        self.title_label.setText(title)

    # --- 窗口控制槽函数 ---
    def on_minimize_clicked(self):
        self.parent_window.showMinimized()

    def on_maximize_clicked(self):
        if self.parent_window.isMaximized():
            self.parent_window.showNormal()
        else:
            self.parent_window.showMaximized()

    def on_close_clicked(self):
        self.parent_window.close()

    # --- 鼠标事件处理，用于拖动窗口 ---
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = True
            self._drag_start_pos = event.globalPosition().toPoint() - self.parent_window.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._is_dragging and event.buttons() & Qt.MouseButton.LeftButton:
            new_pos = event.globalPosition().toPoint() - self._drag_start_pos
            self.parent_window.move(new_pos)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._is_dragging = False
        event.accept()
        
    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """双击标题栏最大化/恢复"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.on_maximize_clicked()
            event.accept()
