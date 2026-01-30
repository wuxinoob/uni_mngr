# -*- coding: utf-8 -*-
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QFormLayout, 
    QComboBox, QCheckBox, QLabel, QSlider, QFontComboBox, QSpinBox
)
from PySide6.QtCore import Signal, Slot, Qt
from PySide6.QtGui import QFont

class SettingsPage(QWidget):
    """设置页面UI"""
    # 定义信号，当设置项发生变化时发出
    # 信号会发出 setting_name 和 value
    setting_changed = Signal(str, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("settings_page")
        
        # --- 主布局 ---
        main_layout = QVBoxLayout(self)
        
        # --- 通用设置组 ---
        general_group = QGroupBox("通用设置")
        general_layout = QFormLayout(general_group)

        # 主题选择
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["暗色 (Dark)", "亮色 (Light)"])
        general_layout.addRow(QLabel("应用主题:"), self.theme_combo)

        # 字体设置
        self.font_combo = QFontComboBox()
        self.font_combo.setEditable(False) # 仅选择
        # 设置字体过滤器，只显示可缩放字体，避免位图字体带来的问题
        self.font_combo.setFontFilters(QFontComboBox.FontFilter.ScalableFonts)
        self.font_combo.setMaximumWidth(200) # 限制宽度，防止撑破布局
        # 限制下拉列表的宽度，防止过长
        self.font_combo.view().setMinimumWidth(200)
        self.font_combo.view().setMaximumWidth(300)
        
        general_layout.addRow(QLabel("界面字体:"), self.font_combo)

        # 字号设置
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 24)
        self.font_size_spin.setSuffix(" pt")
        general_layout.addRow(QLabel("字体大小:"), self.font_size_spin)

        # 窗口不透明度
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(50, 100) # 50% - 100%
        self.opacity_slider.setSingleStep(1)
        self.opacity_slider.setValue(100)
        self.opacity_slider.setToolTip("调整窗口的透明度")
        general_layout.addRow(QLabel("窗口不透明度:"), self.opacity_slider)

        # 开机自启总开关
        self.autostart_checkbox = QCheckBox("开机时自动启动 UniPanel")
        self.autostart_checkbox.setToolTip(
            "如果禁用此项，所有任务的'开机启动'设置都将无效。"
        )
        general_layout.addRow(self.autostart_checkbox)

        main_layout.addWidget(general_group)
        main_layout.addStretch() # 将设置项推到顶部

        # --- 连接信号和槽 ---
        self.theme_combo.currentTextChanged.connect(self._on_theme_changed)
        self.autostart_checkbox.stateChanged.connect(self._on_autostart_changed)
        self.opacity_slider.valueChanged.connect(self._on_opacity_changed)
        self.font_combo.currentFontChanged.connect(self._on_font_changed)
        self.font_size_spin.valueChanged.connect(self._on_font_size_changed)

    def _on_theme_changed(self, theme_text: str):
        """当主题下拉框变化时发出信号"""
        theme_map = {
            "暗色 (Dark)": "dark",
            "亮色 (Light)": "light"
        }
        theme_value = theme_map.get(theme_text, "dark")
        self.setting_changed.emit("theme", theme_value)

    def _on_autostart_changed(self, state: int):
        """当自启复选框变化时发出信号"""
        is_enabled = state == 2 # 2 for Qt.Checked
        self.setting_changed.emit("master_autostart", is_enabled)

    def _on_opacity_changed(self, value: int):
        """当不透明度滑块变化时发出信号"""
        opacity_float = value / 100.0
        self.setting_changed.emit("window_opacity", opacity_float)

    def _on_font_changed(self, font: QFont):
        self.setting_changed.emit("app_font", font.family())

    def _on_font_size_changed(self, size: int):
        self.setting_changed.emit("app_font_size", size)

    @Slot(dict)
    def load_settings(self, settings: dict):
        """
        从字典加载设置并更新UI。
        :param settings: 包含设置项的字典
        """
        # 加载主题设置
        theme_value = settings.get("theme", "dark")
        theme_map = {
            "dark": "暗色 (Dark)",
            "light": "亮色 (Light)"
        }
        self.theme_combo.setCurrentText(theme_map.get(theme_value, "暗色 (Dark)"))

        # 加载自启设置
        autostart_enabled = settings.get("master_autostart", True)
        self.autostart_checkbox.setChecked(autostart_enabled)
        
        # 加载不透明度
        opacity = settings.get("window_opacity", 1.0)
        self.opacity_slider.setValue(int(opacity * 100))

        # 加载字体设置
        font_family = settings.get("app_font", "Segoe UI")
        self.font_combo.setCurrentFont(QFont(font_family))
        
        font_size = settings.get("app_font_size", 11)
        self.font_size_spin.setValue(font_size)
