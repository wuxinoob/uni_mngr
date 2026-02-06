# -*- coding: utf-8 -*-
import subprocess
import sys
import os
import json
from typing import Optional

from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QHBoxLayout, QMenu,
    QSystemTrayIcon, QStyle, QPushButton, QListWidget,
    QListWidgetItem, QVBoxLayout, QStackedWidget, QLineEdit,
    QLayout, QFormLayout, QPlainTextEdit, QComboBox, QDialog, 
    QFileDialog, QDialogButtonBox, QSpinBox, QCheckBox, 
    QMessageBox, QMainWindow, QFrame, QGraphicsDropShadowEffect
)
from PySide6.QtCore import (
    Qt, QTimer, QPoint, QRectF, Signal, QThread, 
    QPropertyAnimation, QEasingCurve, QRect, 
    QProcess, Slot
)
from PySide6.QtGui import (
    QPainter, QColor, QAction, QPixmap, QGuiApplication,
    QIcon, QBrush, QPen, QFont, QImage, QRegion, QPalette, QMouseEvent,
    QPolygonF
)

from uni_panel_pj.core.Qt_process_manager import ProcessManager
from uni_panel_pj.ui.task_page import task_page
from uni_panel_pj.ui.settings_page import SettingsPage
from uni_panel_pj.ui.eye_care_page import EyeCarePage
from uni_panel_pj.ui.animated_stacked_widget import AnimatedStackedWidget
from uni_panel_pj.ui.collapsible_list_widget import CollapsibleListWidget
from uni_panel_pj.ui.custom_title_bar import CustomTitleBar

# --- Theme Color Definitions ---
THEME_COLORS = {
    "dark": {
        "@bg_darkest": "#233140",
        "@bg_dark":    "#2c3e50",
        "@bg_medium":  "#34495e",
        "@bg_light":   "#4a637a",
        "@text_main":  "#ecf0f1",
        "@text_button":"#ffffff",
        "@accent_blue":  "#3498db",
        "@accent_green": "#2ecc71",
        "@accent_red":   "#e74c3c",
        "@accent_orange":"#f39c12",
        "@border_color": "#34495e",
        "@accent_hover": "#4ea8e1",
        "@accent_pressed": "#2980b9"
    },
    "light": {
        "@bg_darkest": "#f5f6fa",
        "@bg_dark":    "#ffffff",
        "@bg_medium":  "#ecf0f1",
        "@bg_light":   "#dcdde1",
        "@text_main":  "#2c3e50",
        "@text_button":"#ffffff",
        "@accent_blue":  "#3498db",
        "@accent_green": "#27ae60",
        "@accent_red":   "#c0392b",
        "@accent_orange":"#d35400",
        "@border_color": "#bdc3c7",
        "@accent_hover": "#5dade2",
        "@accent_pressed": "#2980b9"
    }
}

class mainWindow(QMainWindow):
    def __init__(self, config_path: str):
        super().__init__()
        self.setWindowTitle("通用面板")
        self.resize(830, 630)
        
        # 设置无边框窗口和背景透明
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # 设置图标
        self.app_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        self.setWindowIcon(self.app_icon)

        self.config_path = config_path
        self.main_config = {}
        self.sidebar_list: list[dict] = []

        self.ProcessManager = ProcessManager()
        # 尽早设置路径
        process_config_file_path = os.path.join(self.config_path, "process_manager_config.json")
        self.ProcessManager.set_config_path(process_config_file_path)

        self.task_page = task_page(self.ProcessManager)
        self.settings_page = SettingsPage()

        self.backend_init()
        self.load_cfg()

        # EyeCarePage depends on ProcessManager status, so init it AFTER loading config
        self.eye_care_page = EyeCarePage(self.ProcessManager)

        self.sidebar_list.append({"name": "任务管理", "instance": self.task_page})
        self.sidebar_list.append({"name": "护眼助手", "instance": self.eye_care_page})
        self.sidebar_list.append({"name": "设置", "instance": self.settings_page})

        self.initUI()
        self._init_tray_icon()
        
        self.settings_page.load_settings(self.main_config)
        self.settings_page.setting_changed.connect(self._on_setting_changed)

        # 缩放相关变量
        self._resize_drag_pos = None
        self._resize_drag_edge = None

    def _init_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.app_icon)
        self.tray_icon.setToolTip("UniPanel")

        tray_menu = QMenu()
        show_action = QAction("显示", self)
        exit_action = QAction("退出", self)

        show_action.triggered.connect(self.showNormal)
        show_action.triggered.connect(self.activateWindow)
        exit_action.triggered.connect(self.close)

        tray_menu.addAction(show_action)
        tray_menu.addAction(exit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._tray_icon_activated)
        self.tray_icon.show()

    @Slot(QSystemTrayIcon.ActivationReason)
    def _tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.showNormal()
            self.activateWindow()

    def closeEvent(self, event):
        event.ignore()
        running_tasks = self.ProcessManager.get_running_tasks()
        if running_tasks:
            task_list_str = "\n - ".join(running_tasks)
            ret = QMessageBox.question(self, "确认退出?", 
                                         f"有以下任务正在运行:\n - {task_list_str}\n\n是否要终止这些任务并继续?",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if ret == QMessageBox.No:
                return

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("操作确认")
        msg_box.setText("您想如何操作？")
        msg_box.setStandardButtons(QMessageBox.Cancel)
        tray_button = msg_box.addButton("最小化到托盘", QMessageBox.ActionRole)
        exit_button = msg_box.addButton("直接退出", QMessageBox.ActionRole)
        
        msg_box.exec()

        if msg_box.clickedButton() == tray_button:
            self.hide()
        elif msg_box.clickedButton() == exit_button:
            self.tray_icon.hide()
            self.ProcessManager.stop_all_tasks()
            QApplication.quit()

    def load_cfg(self):
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
                    for key, value in default_ui_config.items():
                        if key not in loaded_config:
                            loaded_config[key] = value
                    self.main_config = loaded_config
        except (json.JSONDecodeError, IOError) as e:
            print(f"无法加载UI配置文件: {e}")
            self.main_config = default_ui_config
        
        self._apply_theme(self.main_config.get("theme", "dark"))
        self.setWindowOpacity(self.main_config.get("window_opacity", 1.0))
        self._apply_font()

        process_config_path = os.path.join(self.config_path, "process_manager_config.json")
        if os.path.exists(process_config_path):
            try:
                with open(process_config_path, "r", encoding='utf-8') as f:
                    content = f.read()
                    if content:
                        config_data = json.loads(content)
                        self.ProcessManager.load_config(config_data)
            except Exception as e:
                print(f"加载进程配置失败: {e}")
        else:
            self.ProcessManager.enable_save()

    def _save_main_config(self):
        try:
            with open(self.ui_config_path, 'w', encoding='utf-8') as f:
                json.dump(self.main_config, f, indent=4, ensure_ascii=False)
        except IOError as e:
            print(f"保存UI配置失败: {e}")
            
    def _apply_theme(self, theme_name: str):
            print(f"应用主题: {theme_name}")
            app = QApplication.instance()
            if not app: return

            if theme_name == "dark":
                self._set_dark_palette(app)
            else:
                app.setPalette(self.style().standardPalette())
                
            self._load_stylesheet("modern.qss", theme_name)

    def _set_dark_palette(self, app):
        dark_palette = QPalette()
        dark_color = QColor(44, 62, 80)
        darker_color = QColor(35, 49, 64)
        light_color = QColor(236, 240, 241)
        accent_color = QColor(52, 152, 219)
        
        dark_palette.setColor(QPalette.ColorRole.Window, darker_color)
        dark_palette.setColor(QPalette.ColorRole.WindowText, light_color)
        dark_palette.setColor(QPalette.ColorRole.Base, darker_color)
        dark_palette.setColor(QPalette.ColorRole.AlternateBase, dark_color)
        dark_palette.setColor(QPalette.ColorRole.ToolTipBase, light_color)
        dark_palette.setColor(QPalette.ColorRole.ToolTipText, light_color)
        dark_palette.setColor(QPalette.ColorRole.Text, light_color)
        dark_palette.setColor(QPalette.ColorRole.Button, dark_color)
        dark_palette.setColor(QPalette.ColorRole.ButtonText, light_color)
        dark_palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        dark_palette.setColor(QPalette.ColorRole.Link, accent_color)
        dark_palette.setColor(QPalette.ColorRole.Highlight, accent_color)
        dark_palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)
        app.setPalette(dark_palette)

    def _load_stylesheet(self, filename, theme_name):
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            style_path = os.path.join(current_dir, "styles", filename)
            
            with open(style_path, "r", encoding='utf-8') as f:
                stylesheet = f.read()
                
            # 替换颜色变量
            colors = THEME_COLORS.get(theme_name, THEME_COLORS["dark"])
            replacements = colors.copy()
            
            # --- Generate Arrow PNGs (Save to Disk) ---
            text_color_str = replacements.get("@text_main", "#ffffff")
            text_color = QColor(text_color_str)
            
            # Ensure generated directory exists
            generated_dir = os.path.join(current_dir, "styles", "generated")
            if not os.path.exists(generated_dir):
                os.makedirs(generated_dir)

            def generate_arrow_file(is_up: bool) -> str:
                size = 16
                image = QImage(size, size, QImage.Format.Format_ARGB32_Premultiplied)
                image.fill(QColor(0, 0, 0, 0))
                
                painter = QPainter(image)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                painter.setBrush(QBrush(text_color))
                painter.setPen(Qt.PenStyle.NoPen)
                
                cx, cy = size / 2, size / 2
                offset = 4
                h_offset = 3
                
                if is_up:
                    points = [
                        QPoint(cx - offset, cy + h_offset), 
                        QPoint(cx, cy - h_offset),     
                        QPoint(cx + offset, cy + h_offset)
                    ]
                else:
                    points = [
                        QPoint(cx - offset, cy - h_offset), 
                        QPoint(cx, cy + h_offset),     
                        QPoint(cx + offset, cy - h_offset)
                    ]
                    
                painter.drawPolygon(points)
                painter.end()
                
                filename = "arrow_up.png" if is_up else "arrow_down.png"
                file_path = os.path.join(generated_dir, filename)
                image.save(file_path, "PNG")
                
                # Qt stylesheets require forward slashes
                return f"url('{file_path.replace(os.sep, '/')}')"

            replacements["@arrow_up_url"] = generate_arrow_file(True)
            replacements["@arrow_down_url"] = generate_arrow_file(False)
            # ---------------------------------------------
            
            # 生成用于SVG的RGB格式颜色 (避免URL中的#号问题)
            for k, v in colors.items():
                if isinstance(v, str) and v.startswith("#"):
                    try:
                        # 解析 hex 颜色
                        hex_val = v.lstrip('#')
                        if len(hex_val) == 3:
                            hex_val = "".join([x*2 for x in hex_val])
                        r = int(hex_val[0:2], 16)
                        g = int(hex_val[2:4], 16)
                        b = int(hex_val[4:6], 16)
                        replacements[k + "_rgb"] = f"rgb({r}, {g}, {b})"
                    except Exception:
                        pass

            # 按长度降序排序键，防止部分匹配替换 (如 @text_main 替换了 @text_main_rgb 的前缀)
            sorted_keys = sorted(replacements.keys(), key=len, reverse=True)
            for key in sorted_keys:
                stylesheet = stylesheet.replace(key, replacements[key])
                
            QApplication.instance().setStyleSheet(stylesheet)
        except Exception as e:
            print(f"加载样式表失败: {e}")

    def _apply_font(self):
        font_family = self.main_config.get("app_font", "Segoe UI")
        font_size = int(self.main_config.get("app_font_size", 11))
        QApplication.setFont(QFont(font_family, font_size))

    @Slot(str, object)
    def _on_setting_changed(self, key: str, value: object):
        if key not in self.main_config or self.main_config[key] != value:
            print(f"设置项 '{key}' -> '{value}'")
            self.main_config[key] = value
            self._save_main_config()
            if key == "theme": self._apply_theme(value)
            elif key == "master_autostart": self.ProcessManager._update_app_autostart_status()
            elif key == "window_opacity": self.setWindowOpacity(value)
            elif key in ["app_font", "app_font_size"]: self._apply_font()

    def backend_init(self):
        self.ProcessManager.set_main_panel_config(self.main_config)
        self.ProcessManager.add_obj(self, self.task_page)

    def initUI(self):
        central_wid = QWidget()
        central_wid.setAttribute(Qt.WA_TranslucentBackground)
        central_wid.setMouseTracking(True)
        self.setCentralWidget(central_wid)
        
        root_layout = QVBoxLayout(central_wid)
        root_layout.setContentsMargins(10, 10, 10, 10) 
        
        self.main_container = QFrame()
        self.main_container.setObjectName("mainContainer")
        self.main_container.setMouseTracking(True)
        
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 0)
        self.main_container.setGraphicsEffect(shadow)
        
        root_layout.addWidget(self.main_container)

        container_layout = QVBoxLayout(self.main_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        self.title_bar = CustomTitleBar(self)
        self.title_bar.set_icon(self.app_icon)
        self.title_bar.set_title(self.windowTitle())
        
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)

        self.siderBar = CollapsibleListWidget()
        self.siderBar.setFont(QFont("Segoe UI", 12))
        
        icon_map = {
            "任务管理": QStyle.StandardPixmap.SP_ComputerIcon,
            "护眼助手": QStyle.StandardPixmap.SP_DesktopIcon,
            "设置": QStyle.StandardPixmap.SP_FileDialogDetailedView
        }
        for i, item_data in enumerate(self.sidebar_list):
            item = QListWidgetItem(item_data["name"])
            item.setData(Qt.UserRole, i)
            icon = self.style().standardIcon(icon_map.get(item_data["name"], QStyle.StandardPixmap.SP_FileIcon))
            item.setIcon(icon)
            self.siderBar.addItem(item)
            
        self.siderBar.itemClicked.connect(self.onclick)

        self.content = self.content_init()
        content_layout.addWidget(self.siderBar)
        content_layout.addWidget(self.content, 1)
        
        container_layout.addWidget(self.title_bar)
        container_layout.addLayout(content_layout)

    def content_init(self) -> QStackedWidget:
        content = AnimatedStackedWidget()
        for dict_obj in self.sidebar_list:
            content.addWidget(dict_obj["instance"])
        return content

    def onclick(self, item: QListWidgetItem) -> None:
        self.content.setCurrentIndex(item.data(Qt.UserRole))

    def showEvent(self, event):
        target_opacity = self.main_config.get("window_opacity", 1.0)
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(300)
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(target_opacity)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self.fade_animation.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
        super().showEvent(event)

    # --- 窗口拖拽调整大小逻辑 ---
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            if hasattr(self, '_resize_drag_edge') and self._resize_drag_edge:
                self._resize_drag_pos = event.globalPosition().toPoint()
                event.accept()
            else:
                super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        # 1. 检查是否正在拖动调整大小
        if hasattr(self, '_resize_drag_pos') and self._resize_drag_pos and self._resize_drag_edge:
            delta = event.globalPosition().toPoint() - self._resize_drag_pos
            rect = self.geometry()
            
            if 'left' in self._resize_drag_edge:
                rect.setLeft(rect.left() + delta.x())
            if 'right' in self._resize_drag_edge:
                rect.setRight(rect.right() + delta.x())
            if 'top' in self._resize_drag_edge:
                rect.setTop(rect.top() + delta.y())
            if 'bottom' in self._resize_drag_edge:
                rect.setBottom(rect.bottom() + delta.y())
            
            if rect.width() > self.minimumWidth() and rect.height() > self.minimumHeight():
                self.setGeometry(rect)
                self._resize_drag_pos = event.globalPosition().toPoint()
            
            event.accept()
            return

        # 2. 检测边缘
        pos = event.position().toPoint()
        rect = self.rect()
        edge = []
        margin = 8

        if pos.x() <= margin: edge.append('left')
        elif pos.x() >= rect.width() - margin: edge.append('right')
        if pos.y() <= margin: edge.append('top')
        elif pos.y() >= rect.height() - margin: edge.append('bottom')
            
        self._resize_drag_edge = '-'.join(edge) if edge else None
        
        if not self._resize_drag_edge:
            self.setCursor(Qt.CursorShape.ArrowCursor)
        elif self._resize_drag_edge in ['left', 'right']:
            self.setCursor(Qt.CursorShape.SizeHorCursor)
        elif self._resize_drag_edge in ['top', 'bottom']:
            self.setCursor(Qt.CursorShape.SizeVerCursor)
        elif self._resize_drag_edge in ['left-top', 'right-bottom']:
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        elif self._resize_drag_edge in ['left-bottom', 'right-top']:
            self.setCursor(Qt.CursorShape.SizeBDiagCursor)
            
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._resize_drag_pos = None
        super().mouseReleaseEvent(event)