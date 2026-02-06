# -*- coding: utf-8 -*-
import os
import sys
import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QSpinBox, 
    QComboBox, QLineEdit, QPushButton, QHBoxLayout, 
    QFileDialog, QCheckBox, QLabel, QGroupBox, QStyle, QSlider
)
from PySide6.QtCore import Qt, Slot
from uni_panel_pj.core.Qt_process_manager import ProcessManager

class EyeCarePage(QWidget):
    def __init__(self, process_manager: ProcessManager, parent=None):
        super().__init__(parent)
        self.pm = process_manager
        self.task_name = "EyeCare"
        
        # 计算脚本的绝对路径
        # 假设结构: uni_panel_pj/ui/eye_care_page.py -> uni_panel_pj/subtools/eye_care/eye_care.py
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir) # uni_panel_pj
        self.script_path = os.path.join(project_root, "subtools", "eye_care", "eye_care.py")
        
        self.setup_ui()
        self.init_task()
        
        # 连接信号
        self.pm.sig_status_update.connect(self.on_process_status_changed)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # --- 状态栏 ---
        status_group = QGroupBox("状态控制")
        status_layout = QHBoxLayout(status_group)
        
        self.status_label = QLabel("状态: 未知")
        self.status_label.setStyleSheet("font-weight: bold;")
        
        self.btn_start = QPushButton("启动护眼")
        self.btn_start.setObjectName("runButton") # 复用样式
        self.btn_start.clicked.connect(self.start_process)
        
        self.btn_stop = QPushButton("停止护眼")
        self.btn_stop.setObjectName("stopButton") # 复用样式
        self.btn_stop.clicked.connect(self.stop_process)
        
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        status_layout.addWidget(self.btn_start)
        status_layout.addWidget(self.btn_stop)
        
        layout.addWidget(status_group)
        
        # --- 配置区域 ---
        config_group = QGroupBox("参数设置 (实时生效)")
        form_layout = QFormLayout(config_group)
        
        # 工作/休息时间
        self.spin_work = QSpinBox()
        self.spin_work.setRange(1, 120)
        self.spin_work.setSuffix(" 分钟")
        self.spin_work.valueChanged.connect(self.sync_config)
        
        self.spin_rest = QSpinBox()
        self.spin_rest.setRange(1, 60)
        self.spin_rest.setSuffix(" 分钟")
        self.spin_rest.valueChanged.connect(self.sync_config)
        
        form_layout.addRow("工作时长:", self.spin_work)
        form_layout.addRow("休息时长:", self.spin_rest)
        
        # 主题
        self.combo_theme = QComboBox()
        self.combo_theme.addItems(["Dark", "Light", "Aqua", "Minimal"])
        self.combo_theme.currentTextChanged.connect(self.sync_config)
        form_layout.addRow("界面主题:", self.combo_theme)
        
        # 图片路径
        path_layout = QHBoxLayout()
        self.line_image = QLineEdit()
        self.line_image.setPlaceholderText("选择休息时显示的图片（留空则为纯色）")
        self.line_image.textChanged.connect(self.sync_config)
        
        btn_browse = QPushButton("选择...")
        btn_browse.clicked.connect(self.browse_image)
        
        path_layout.addWidget(self.line_image)
        path_layout.addWidget(btn_browse)
        form_layout.addRow("休息图片:", path_layout)
        
        # 图片透明度
        self.slider_opacity = QSlider(Qt.Orientation.Horizontal)
        self.slider_opacity.setRange(0, 100)
        self.slider_opacity.setValue(80)
        self.slider_opacity.valueChanged.connect(self.sync_config)
        form_layout.addRow("图片透明度:", self.slider_opacity)
        
        # 自启动
        self.check_autostart = QCheckBox("随面板自动启动")
        self.check_autostart.toggled.connect(self.update_autostart)
        form_layout.addRow("开机启动:", self.check_autostart)

        # 淡入淡出时间
        self.spin_fade = QSpinBox()
        self.spin_fade.setRange(100, 5000)
        self.spin_fade.setSingleStep(100)
        self.spin_fade.setSuffix(" 毫秒")
        self.spin_fade.setValue(1000)
        self.spin_fade.valueChanged.connect(self.sync_config)
        form_layout.addRow("动画时间:", self.spin_fade)
        
        layout.addWidget(config_group)
        layout.addStretch()

    def init_task(self):
        """确保 ProcessManager 中存在该任务"""
        if self.task_name not in self.pm.task_status:
            # 构造默认任务配置
            task_config = {
                "name": self.task_name,
                "task_cmd": sys.executable, # 使用当前的 python 解释器
                "cmd_args": "", # 将在 sync_config 中设置
                "task_path": os.path.dirname(self.script_path),
                "start_up": False,
                "auto_restart": False, # 默认为 False，防止崩溃循环
                "show_type": "hidden", 
                "enable_timer": False
            }
            self.pm.add_task(task_config)
        
        # 先加载配置，再同步，防止覆盖
        self.load_config_from_file()
        self.sync_config()
        
        # 同步 UI 状态与 PM 状态
        task_info = self.pm.task_status.get(self.task_name)
        if task_info:
            # 1. 同步运行状态
            self.update_ui_state(task_info.get("status", "stopped"))
            # 2. 同步自启复选框 (阻塞信号以防循环触发保存)
            self.check_autostart.blockSignals(True)
            self.check_autostart.setChecked(task_info.get("start_up", False))
            self.check_autostart.blockSignals(False)

    def load_config_from_file(self):
        """从磁盘加载配置并更新 UI"""
        config_path = os.path.join(os.path.dirname(self.script_path), "config.json")
        if not os.path.exists(config_path):
            return

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            
            # 阻塞信号，防止在设置 UI 时触发 sync_config
            self.blockSignals(True)
            
            if "work_minutes" in config:
                self.spin_work.setValue(config["work_minutes"])
            if "rest_minutes" in config:
                self.spin_rest.setValue(config["rest_minutes"])
            if "theme" in config:
                self.combo_theme.setCurrentText(config["theme"])
            if "image_path" in config and config["image_path"]:
                self.line_image.setText(config["image_path"])
            if "rest_image_opacity" in config:
                self.slider_opacity.setValue(int(config["rest_image_opacity"] * 100))
            if "fade_duration" in config:
                self.spin_fade.setValue(config["fade_duration"])
                
            self.blockSignals(False)
            print(f"[EyeCarePage]: Loaded config from {config_path}")
            
        except Exception as e:
            print(f"[EyeCarePage]: Failed to load config: {e}")
            self.blockSignals(False)

    @Slot(dict)
    def on_process_status_changed(self, status_info):
        if status_info.get("name") == self.task_name:
            self.update_ui_state(status_info.get("status"))

    def update_ui_state(self, status):
        self.status_label.setText(f"状态: {status}")
        if status == "running":
            self.status_label.setStyleSheet("color: #2ecc71; font-weight: bold;")
            self.btn_start.setEnabled(False)
            self.btn_stop.setEnabled(True)
        else:
            self.status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
            self.btn_start.setEnabled(True)
            self.btn_stop.setEnabled(False)

    def start_process(self):
        # 启动前确保配置是最新的
        self.sync_config()
        self.pm.start_process(self.task_name)

    def stop_process(self):
        self.pm.stop_process(self.task_name)

    def browse_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择图片", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if file_path:
            self.line_image.setText(file_path)

    def update_autostart(self, checked):
        task_info = self.pm.task_status.get(self.task_name)
        if task_info:
            task_info["start_up"] = checked
            self.pm._save_config()
            self.pm._update_app_autostart_status()

    def sync_config(self):
        """将当前 UI 配置发送给子进程"""
        config_data = {
            "command": "update_config",
            "value": {
                "work_minutes": self.spin_work.value(),
                "rest_minutes": self.spin_rest.value(),
                "theme": self.combo_theme.currentText(),
                "image_path": self.line_image.text() if self.line_image.text() else None,
                "rest_image_opacity": self.slider_opacity.value() / 100.0,
                "fade_duration": self.spin_fade.value()
            }
        }
        
        # 1. 实时发送 (如果运行中)
        task_info = self.pm.task_status.get(self.task_name)
        if task_info and task_info.get("status") == "running":
            json_str = json.dumps(config_data)
            self.pm.write_to_process(self.task_name, json_str)
            
        # 2. 保存到文件供下次启动
        self.save_config_to_file(config_data["value"])

    def save_config_to_file(self, config_dict):
        config_path = os.path.join(os.path.dirname(self.script_path), "config.json")
        try:
            # 1. 读取现有配置
            existing_config = {}
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    existing_config = json.load(f)
            
            # 2. 更新配置
            existing_config.update(config_dict)
            
            # 3. 写入文件
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(existing_config, f, indent=4)
        except Exception as e:
            print(f"Error saving eye care config: {e}")
            
        # 更新任务启动参数
        task_info = self.pm.task_status.get(self.task_name)
        if task_info:
            # 使用引号包裹路径，防止空格导致参数解析错误
            expected_args = f'"{self.script_path}" --config-file "{config_path}"'
            if task_info.get("cmd_args") != expected_args:
                task_info["cmd_args"] = expected_args
                self.pm._save_config()
