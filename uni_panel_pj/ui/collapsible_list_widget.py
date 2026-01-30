# -*- coding: utf-8 -*-
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QListWidget, 
    QListWidgetItem, QSizePolicy, QStyledItemDelegate, QStyle, QStyleOptionViewItem
)
from PySide6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve, QSize, Signal
)
from PySide6.QtGui import QIcon, QPainter

class CollapsibleListWidget(QWidget):
    """一个带有折叠/展开动画的QListWidget封装"""
    
    # 代理 QListWidget 的 itemClicked 信号
    itemClicked = Signal(QListWidgetItem)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.is_collapsed = False
        self.expanded_width = 150
        self.collapsed_width = 55 # 宽度需要足够容纳图标

        # --- UI 组件 ---
        self.toggle_button = QPushButton()
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(False) # 默认展开
        self._update_button_icon()

        self.list_widget = QListWidget()
        self.list_widget.setItemDelegate(IconOnlyDelegate(self.list_widget))

        # --- 布局 ---
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        layout.addWidget(self.toggle_button)
        layout.addWidget(self.list_widget)

        # --- 动画 ---
        self.animation = QPropertyAnimation(self, b"maximumWidth")
        self.animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self.animation.setDuration(300) # 300ms 动画时长

        # --- 连接信号 ---
        self.toggle_button.clicked.connect(self.toggle_collapse)
        self.list_widget.itemClicked.connect(self.itemClicked)

        # --- 初始化状态 ---
        self.setMaximumWidth(self.expanded_width)
        self.list_widget.viewMode = QListWidget.ViewMode.ListMode
        
    def _update_button_icon(self):
        """根据折叠状态更新按钮图标"""
        style = self.style()
        icon = style.standardIcon(QStyle.StandardPixmap.SP_ArrowLeft) if not self.is_collapsed else style.standardIcon(QStyle.StandardPixmap.SP_ArrowRight)
        self.toggle_button.setIcon(icon)

    def toggle_collapse(self):
        """触发折叠/展开动画"""
        self.is_collapsed = not self.is_collapsed
        self._update_button_icon()

        # 更新委托的折叠状态
        delegate = self.list_widget.itemDelegate()
        if isinstance(delegate, IconOnlyDelegate):
            delegate.set_collapsed(self.is_collapsed)

        # 启动动画
        start_width = self.width()
        end_width = self.collapsed_width if self.is_collapsed else self.expanded_width
        self.animation.setStartValue(start_width)
        self.animation.setEndValue(end_width)
        self.animation.start()

        # 立即重绘以更新item的显示
        self.list_widget.viewport().update()

    # --- 代理方法，方便外部调用 ---
    def addItem(self, item: QListWidgetItem):
        """代理 QListWidget.addItem"""
        # 确保图标大小合适
        item.setSizeHint(QSize(item.sizeHint().width(), 40)) 
        self.list_widget.addItem(item)
    
    def setFont(self, font):
        """代理 setFont"""
        self.list_widget.setFont(font)
        
    def item(self, row):
        return self.list_widget.item(row)

# 为了实现文本的“缩进”（即隐藏），我们需要一个自定义委托
class IconOnlyDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_collapsed = False

    def set_collapsed(self, collapsed: bool):
        self._is_collapsed = collapsed

    def paint(self, painter: QPainter, option, index):
        # 如果是折叠状态，则不绘制文本
        if self._is_collapsed:
            # 复制一份 option 来修改
            option_copy = QStyleOptionViewItem(option)
            option_copy.text = ""
            super().paint(painter, option_copy, index)
        else:
            super().paint(painter, option, index)

    def sizeHint(self, option, index):
        # 保持原始尺寸提示，防止列表在折叠时跳动
        return super().sizeHint(option, index)
