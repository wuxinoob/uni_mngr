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
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QHBoxLayout, QMenu,
    QSystemTrayIcon, QStyle, QPushButton, QListWidget,
    QListWidgetItem, QVBoxLayout, QStackedWidget, QLineEdit,
    QLayout, QFormLayout, QPlainTextEdit, QComboBox, QDialog, QFileDialog, QDialogButtonBox,
    QSpinBox, QCheckBox ,QMessageBox, QMainWindow, QFrame, QGraphicsDropShadowEffect
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
from uni_panel_pj.ui.collapsible_list_widget import CollapsibleListWidget
from uni_panel_pj.ui.custom_title_bar import CustomTitleBar
from uni_panel_pj.ui.eye_care_page import EyeCarePage
import json
import qdarktheme


class mainWindow(QMainWindow):
    def __init__(self,config_path:str):
        super().__init__()
        self.setWindowTitle("通用面板")
        self.resize(830, 630) # 稍微加大一点以适应阴影边距
        
        # 设置无边框窗口和背景透明
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # 设置图标（使用内置标准图标作为占位符）
        self.app_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        self.setWindowIcon(self.app_icon)

        self.config_path = config_path
        self.main_config = {}
        self.sidebar_list:list[dict] = []

        self.ProcessManager = ProcessManager()
        # 尽早设置路径，防止组件初始化时添加任务报错
        process_config_file_path = os.path.join(self.config_path, "process_manager_config.json")
        self.ProcessManager.set_config_path(process_config_file_path)

        self.task_page = task_page(self.ProcessManager)
        self.eye_care_page = EyeCarePage(self.ProcessManager)
        self.settings_page = SettingsPage()

        self.sidebar_list.append({"name":"任务管理", "instance": self.task_page})
        self.sidebar_list.append({"name":"护眼助手", "instance": self.eye_care_page})
        self.sidebar_list.append({"name":"设置", "instance": self.settings_page})

        self.backend_init() # 必须先初始化后端，让PM知道task_page的存在
        self.load_cfg() # 再加载配置文件，此时add_task可以安全地调用UI
        self.initUI()
        self._init_tray_icon() # 初始化系统托盘图标
        
        # 将加载好的配置应用到UI
        self.settings_page.load_settings(self.main_config)
        
        # 连接信号
        self.settings_page.setting_changed.connect(self._on_setting_changed)

    def _init_tray_icon(self):
        """初始化系统托盘图标和菜单"""
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.app_icon)
        self.tray_icon.setToolTip("UniPanel")

        tray_menu = QMenu()
        show_action = QAction("显示", self)
        exit_action = QAction("退出", self)

        show_action.triggered.connect(self.show)
        exit_action.triggered.connect(self.close)

        tray_menu.addAction(show_action)
        tray_menu.addAction(exit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._tray_icon_activated)
        self.tray_icon.show()

    @Slot(QSystemTrayIcon.ActivationReason)
    def _tray_icon_activated(self, reason):
        """处理托盘图标点击事件"""
        # 左键单击显示窗口
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.showNormal() # 显示并恢复窗口状态
            self.activateWindow() # 激活窗口

    def closeEvent(self, event):
        """重写关闭事件，实现最小化到托盘或退出的逻辑"""
        event.ignore() # 默认忽略关闭事件，由我们完全接管

        # 1. 检查是否有正在运行的子进程
        running_tasks = self.ProcessManager.get_running_tasks()
        if running_tasks:
            task_list_str = "\n - ".join(running_tasks)
            ret = QMessageBox.question(self, "确认退出?", 
                                         f"有以下任务正在运行:\n - {task_list_str}\n\n是否要终止这些任务并继续?",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if ret == QMessageBox.No:
                return # 用户取消，不做任何事

        # 2. 询问用户是最小化还是退出
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("操作确认")
        msg_box.setText("您想如何操作？")
        msg_box.setStandardButtons(QMessageBox.Cancel)
        tray_button = msg_box.addButton("最小化到托盘", QMessageBox.ActionRole)
        exit_button = msg_box.addButton("直接退出", QMessageBox.ActionRole)
        
        msg_box.exec()

        # 3. 根据用户选择执行操作
        if msg_box.clickedButton() == tray_button:
            self.hide() # 隐藏窗口
        elif msg_box.clickedButton() == exit_button:
            self.tray_icon.hide()
            self.ProcessManager.stop_all_tasks()
            QApplication.quit() # 彻底退出应用
        else:
            return # 用户点击了Cancel


    def load_cfg(self):
        # --- 加载主程序UI配置 ---
        self.ui_config_path = os.path.join(self.config_path, "UI_config.json")
        default_ui_config = {
            "theme": "dark",
            "master_autostart": True,
            "window_opacity": 1.0,
            "app_font": "Segoe UI",
            "app_font_size": 11
        }
        try:
            if not os.path.exists(self.ui_config_path):
                self.main_config = default_ui_config
                self._save_main_config()
            else:
                with open(self.ui_config_path, "r", encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # 合并默认配置，确保新添加的设置项存在
                    for key, value in default_ui_config.items():
                        if key not in loaded_config:
                            loaded_config[key] = value
                    self.main_config = loaded_config
        except (json.JSONDecodeError, IOError) as e:
            print(f"无法加载UI配置文件，将使用默认配置: {e}")
            self.main_config = default_ui_config
        
        # 启动时应用主题、透明度和字体
        self._apply_theme(self.main_config.get("theme", "dark"))
        self.setWindowOpacity(self.main_config.get("window_opacity", 1.0))
        self._apply_font()

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
        else:
            # 如果没有配置文件，允许保存以创建新文件
            self.ProcessManager.enable_save()

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

    def _apply_font(self):
        """应用全局字体"""
        font_family = self.main_config.get("app_font", "Segoe UI")
        font_size = int(self.main_config.get("app_font_size", 11)) # Ensure int
        font = QFont(font_family, font_size)
        QApplication.setFont(font)

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
                self.ProcessManager._update_app_autostart_status()
            elif key == "window_opacity":
                self.setWindowOpacity(value)

    def backend_init(self):
        """后端初始化 & 传递必要的对象"""
        self.ProcessManager.set_main_panel_config(self.main_config) # 传递主配置
        self.ProcessManager.add_obj(self,self.task_page)

    def initUI(self):
        # 1. 设置中心部件为完全透明
        central_wid = QWidget()
        central_wid.setAttribute(Qt.WA_TranslucentBackground)
        self.setCentralWidget(central_wid)
        
        # 2. 根布局，留出边距给阴影
        root_layout = QVBoxLayout(central_wid)
        root_layout.setContentsMargins(10, 10, 10, 10) 
        
        # 3. 创建实际的背景容器 (QFrame)，所有内容都放在这里
        self.main_container = QFrame()
        self.main_container.setObjectName("mainContainer") # 用于QSS
        
        # 4. 添加阴影效果
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 0)
        self.main_container.setGraphicsEffect(shadow)
        
        root_layout.addWidget(self.main_container)

        # 5. 容器内部的主布局：垂直布局，顶部是标题栏，底部是内容
        container_layout = QVBoxLayout(self.main_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # --- 自定义标题栏 ---
        self.title_bar = CustomTitleBar(self)
        self.title_bar.set_icon(self.app_icon)
        self.title_bar.set_title(self.windowTitle())
        
        # --- 内容布局：水平布局 ---
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)

        # --- 侧边栏 ---
        self.siderBar = CollapsibleListWidget()
        self.siderBar.setFont(QFont("Segoe UI", 12))
        
        icon_map = {
            "任务管理": QStyle.StandardPixmap.SP_ComputerIcon,
            "护眼助手": QStyle.StandardPixmap.SP_DesktopIcon,
            "设置": QStyle.StandardPixmap.SP_FileDialogDetailedView
        }
        for i, item_data in enumerate(self.sidebar_list):
            name = item_data["name"]
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, i)
            icon = self.style().standardIcon(icon_map.get(name, QStyle.StandardPixmap.SP_FileIcon))
            item.setIcon(icon)
            self.siderBar.addItem(item)
            
        self.siderBar.itemClicked.connect(self.onclick)

        # --- 内容区域 ---
        self.content = self.content_init()

        # --- 组装内容布局 ---
        content_layout.addWidget(self.siderBar)
        content_layout.addWidget(self.content, 1)
        
        # --- 组装容器布局 ---
        container_layout.addWidget(self.title_bar)
        container_layout.addLayout(content_layout)


    def content_init(self) -> QStackedWidget:
        content = AnimatedStackedWidget()
        for dict_obj in self.sidebar_list:
            page = dict_obj["instance"]
            content.addWidget(page)
        return content

    def onclick(self, item: QListWidgetItem) -> None:
        data =  item.data(Qt.UserRole)
        self.content.setCurrentIndex(data)

    def showEvent(self, event):
        """重写showEvent，在窗口显示时添加淡入动画"""
        target_opacity = self.main_config.get("window_opacity", 1.0)
        
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(300)
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(target_opacity)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        
        self.fade_animation.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
        
        super().showEvent(event)


