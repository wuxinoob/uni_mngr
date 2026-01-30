# -*- coding: utf-8 -*-
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QFormLayout, 
    QComboBox, QCheckBox, QLabel
)
from PySide6.QtCore import Signal, Slot

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

    @Slot(dict)
    def load_settings(self, settings: dict):
        """
        从字典加载设置并更新UI。
        :param settings: 包含设置项的字典, e.g., {"theme": "dark", "master_autostart": True}
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
