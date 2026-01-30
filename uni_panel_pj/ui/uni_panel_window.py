import subprocess
import sys
import os
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QHBoxLayout, QMenu,
    QSystemTrayIcon, QStyle, QPushButton, QListWidget,
    QListWidgetItem, QVBoxLayout, QStackedWidget, QLineEdit,
    QLayout, QFormLayout, QPlainTextEdit, QComboBox, QDialog, QFileDialog, QDialogButtonBox,
    QSpinBox, QCheckBox ,QMessageBox, QMainWindow
)
from PySide6.QtCore import (Qt, QTimer, QPoint, QRectF, Signal, QThread, QPropertyAnimation, QEasingCurve, QBuffer, QRect, QProcess, Slot)
from PySide6.QtGui import (
    QPainter, QColor, QAction, QPixmap, QGuiApplication,
    QIcon, QBrush, QPen, QFont, QImage, QRegion, 
)
from typing import Optional
from uni_panel_pj.core.Qt_process_manager import ProcessManager
from uni_panel_pj.ui.task_page import task_page
from uni_panel_pj.ui.settings_page import SettingsPage
from uni_panel_pj.ui.animated_stacked_widget import AnimatedStackedWidget
import json
import qdarktheme


class mainWindow(QMainWindow):
    def __init__(self,config_path:str):
        super().__init__()
        self.setWindowTitle("通用面板")
        self.resize(800, 600)
        self.config_path = config_path
        self.main_config = {}
        self.sidebar_list:list[dict] = []

        self.ProcessManager = ProcessManager()
        self.task_page = task_page(self.ProcessManager)
        self.settings_page = SettingsPage()

        self.sidebar_list.append({"name":"任务管理", "instance": self.task_page})
        self.sidebar_list.append({"name":"设置", "instance": self.settings_page})

        self.backend_init() # 必须先初始化后端，让PM知道task_page的存在
        self.load_cfg() # 再加载配置文件，此时add_task可以安全地调用UI
        self.initUI()
        
        # 将加载好的配置应用到UI
        self.settings_page.load_settings(self.main_config)
        
        # 连接信号
        self.settings_page.setting_changed.connect(self._on_setting_changed)


    def load_cfg(self):
        # --- 加载主程序UI配置 ---
        self.ui_config_path = os.path.join(self.config_path, "UI_config.json")
        default_ui_config = {
            "theme": "dark",
            "master_autostart": True
        }
        try:
            if not os.path.exists(self.ui_config_path):
                self.main_config = default_ui_config
                self._save_main_config()
            else:
                with open(self.ui_config_path, "r", encoding='utf-8') as f:
                    self.main_config = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"无法加载UI配置文件，将使用默认配置: {e}")
            self.main_config = default_ui_config
        
        # 启动时应用主题
        self._apply_theme(self.main_config.get("theme", "dark"))

        # --- 加载进程管理器配置 ---
        process_config_path = os.path.join(self.config_path, "process_manager_config.json")
        if os.path.exists(process_config_path):
            try:
                with open(process_config_path, "r", encoding='utf-8') as f:
                    content = f.read()
                    if not content:
                        print("进程配置文件为空，跳过加载。")
                        return
                    config_data = json.loads(content)
                self.ProcessManager.load_config(config_data)
            except json.JSONDecodeError:
                print(f"错误: 配置文件 {process_config_path} 格式错误，无法解析。")
            except Exception as e:
                print(f"加载进程配置文件时发生未知错误: {e}")

    def _save_main_config(self):
        """保存主UI配置文件"""
        try:
            with open(self.ui_config_path, 'w', encoding='utf-8') as f:
                json.dump(self.main_config, f, indent=4, ensure_ascii=False)
        except IOError as e:
            print(f"错误: 保存UI配置文件失败: {e}")
            
    def _apply_theme(self, theme_name: str):
        """应用亮/暗主题"""
        print(f"应用主题: {theme_name}")
        qdarktheme.setup_theme(theme_name)

    @Slot(str, object)
    def _on_setting_changed(self, key: str, value: object):
        """处理来自设置页面的信号"""
        if key not in self.main_config or self.main_config[key] != value:
            print(f"设置项 '{key}' 已变更为 '{value}'")
            self.main_config[key] = value
            self._save_main_config()

            if key == "theme":
                self._apply_theme(value)
            elif key == "master_autostart":
                # 当总开关变化时，立即更新注册表状态
                self.ProcessManager._update_app_autostart_status()

    def backend_init(self):
        """后端初始化 & 传递必要的对象"""
        process_config_file_path = os.path.join(self.config_path, "process_manager_config.json")
        self.ProcessManager.set_config_path(process_config_file_path)
        self.ProcessManager.set_main_panel_config(self.main_config) # 传递主配置
        self.ProcessManager.add_obj(self,self.task_page)

    def initUI(self):
        central_wid = QWidget()
        self.setCentralWidget(central_wid)
        self.main_wid = QHBoxLayout(central_wid)
        self.main_wid.setContentsMargins(0, 0, 0, 0)
        
        self.siderBar = self.sideBar_init()
        self.content = self.content_init()

        # --- Sidebar Container ---
        self.sidebar_container = QWidget()
        sidebar_layout = QVBoxLayout(self.sidebar_container)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        
        self.collapse_btn = QPushButton()
        self.collapse_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowLeft))
        self.collapse_btn.setCheckable(True)
        self.collapse_btn.setChecked(True)
        self.collapse_btn.clicked.connect(self.toggle_sidebar)

        sidebar_layout.addWidget(self.collapse_btn)
        sidebar_layout.addWidget(self.siderBar)
        
        self.main_wid.addWidget(self.sidebar_container)
        self.main_wid.addWidget(self.content, 1) # Give content stretch factor

    def toggle_sidebar(self):
        if self.collapse_btn.isChecked():
            self.siderBar.show()
            self.collapse_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowLeft))
        else:
            self.siderBar.hide()
            self.collapse_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowRight))

    def sideBar_init(self) ->QListWidget:
        sideBar = QListWidget()
        sideBar.setFont(QFont("Segoe UI", 12))
        sideBar.setFixedWidth(150)
        sideBar.itemClicked.connect(self.onclick)
        for i, item_data in enumerate(self.sidebar_list):
            task = QListWidgetItem(item_data["name"])
            task.setData(Qt.UserRole, i)
            sideBar.addItem(task)
        return sideBar
        
    def content_init(self) -> QStackedWidget:
        content = AnimatedStackedWidget()
        for dict_obj in self.sidebar_list:
            page = dict_obj["instance"]
            content.addWidget(page)

        return content
    def onclick(self, item: QListWidgetItem) -> None:
        data =  item.data(Qt.UserRole)
        self.content.setCurrentIndex(data)
        # print(data) # Commented out for cleaner output
