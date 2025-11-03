import sys
import json
import io
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QHBoxLayout, QMenu,
    QSystemTrayIcon, QStyle
)
from PySide6.QtCore import Qt, QTimer, QPoint, QRectF, Signal, QThread, QPropertyAnimation, QEasingCurve, QBuffer, QRect
from PySide6.QtGui import (
    QPainter, QColor, QAction, QPixmap, QGuiApplication,
    QIcon, QBrush, QPen, QFont, QImage, QRegion
)
from PIL import Image

# ====================================================================
# 全局常量
# ====================================================================
AVAILABLE_FONTS = ["Segoe UI", "Arial", "Verdana", "Tahoma", "Trebuchet MS", "Georgia"]

# ====================================================================
# 主题定义
# ====================================================================
THEMES = {
    "Dark": {
        "background_normal": QColor(0, 0, 0, 180),
        "background_locked": QColor(0, 0, 0, 50),
        "text": QColor("white"),
        "text_style": "font-weight: normal;",
        "font_family": "Segoe UI",
        "icon": QColor("#E0E0E0"),
        "icon_locked": QColor("white"),
        "menu_background": QColor("#2E2E2E"),
        "menu_text": QColor("#F0F0F0"),
        "menu_border": QColor("#424242"),
        "menu_selected_background": QColor("#505050"),
        "menu_separator": QColor("#424242"),
        "menu_disabled_text": QColor("#707070"),
    },
    "Light": {
        "background_normal": QColor(255, 255, 255, 200),
        "background_locked": QColor(255, 255, 255, 80),
        "text": QColor("black"),
        "text_style": "font-weight: normal;",
        "font_family": "Segoe UI",
        "icon": QColor("#333333"),
        "icon_locked": QColor("black"),
        "menu_background": QColor("#FFFFFF"),
        "menu_text": QColor("#000000"),
        "menu_border": QColor("#E0E0E0"),
        "menu_selected_background": QColor("#F0F0F0"),
        "menu_separator": QColor("#E0E0E0"),
        "menu_disabled_text": QColor("#A0A0A0"),
    },
    "Aqua": {
        "background_normal": QColor(10, 132, 143, 210),
        "background_locked": QColor(10, 132, 143, 80),
        "text": QColor("white"),
        "text_style": "font-weight: normal;",
        "font_family": "Verdana",
        "icon": QColor("#C8F0F0"),
        "icon_locked": QColor("white"),
        "menu_background": QColor("#0A6B74"),
        "menu_text": QColor("#FFFFFF"),
        "menu_border": QColor("#0F8A97"),
        "menu_selected_background": QColor("#13A2B1"),
        "menu_separator": QColor("#0F8A97"),
        "menu_disabled_text": QColor("#88C5CA"),
    },
    "Minimal": {
        "background_normal": QColor(0, 0, 0, 1),
        "background_locked": QColor(0, 0, 0, 1),
        "text": QColor("white"),
        "text_style": "font-weight: bold;",
        "font_family": "Arial",
        "icon": QColor("#E0E0E0"),
        "icon_locked": QColor("white"),
        "menu_background": QColor("#2E2E2E"),
        "menu_text": QColor("#F0F0F0"),
        "menu_border": QColor("#424242"),
        "menu_selected_background": QColor("#505050"),
        "menu_separator": QColor("#424242"),
        "menu_disabled_text": QColor("#707070"),
    }
}

# ====================================================================
# 默认配置
# ====================================================================
DEFAULT_CONFIG = {
    "work_minutes": 25,
    "rest_minutes": 5,
    "window_width": 220,
    "window_height": 40,
    "theme": "Dark",
    "font_family": None, # 默认为None，将使用主题自带字体
    "image_path": None,
    "rest_image_opacity": 0.8,
    "fade_duration": 1000,
    "rest_image_gamma": 1.5,
}

# ====================================================================
# 热重载监听线程
# ====================================================================
class CommandListenerThread(QThread):
    commandReceived = Signal(str)
    def run(self):
        print("[IPC Listener]: Command listener started.", flush=True)
        for line in sys.stdin:
            command = line.strip()
            if command:
                self.commandReceived.emit(command)

# ====================================================================
# 锁定图标窗口
# ====================================================================
class LockIconWidget(QWidget):
    toggled = Signal(bool)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_locked = False
        self.theme_colors = THEMES["Dark"]
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(30, 40)

    def set_locked_state(self, is_locked):
        self.is_locked = is_locked
        self.update()

    def set_theme(self, theme):
        self.theme_colors = theme
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 1))
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen()
        pen.setWidth(2)
        if self.is_locked:
            pen.setColor(self.theme_colors["icon_locked"])
            painter.setBrush(Qt.BrushStyle.NoBrush) # 空心
        else:
            pen.setColor(self.theme_colors["icon"])
            painter.setBrush(self.theme_colors["icon"]) # 实心
        painter.setPen(pen)
        center_x, center_y = 15, self.height() / 2
        radius = 8
        painter.drawEllipse(QPoint(center_x, center_y), radius, radius)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggled.emit(not self.is_locked)

# ====================================================================
# 休息图片窗口
# ====================================================================
class RestImageWidget(QWidget):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.setup_ui()
        self.setup_animation()

    def setup_ui(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool | Qt.WindowType.WindowTransparentForInput)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowOpacity(0.0)

    def setup_animation(self):
        self.animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(self.config["fade_duration"])
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(self.config["rest_image_opacity"])
        self.animation.finished.connect(self.on_animation_finished)

    def fade_in(self):
        self.animation.setDirection(QPropertyAnimation.Direction.Forward)
        self.showFullScreen()
        self.animation.start()

    def fade_out(self):
        self.animation.setDirection(QPropertyAnimation.Direction.Backward)
        self.animation.start()

    def on_animation_finished(self):
        if self.animation.direction() == QPropertyAnimation.Direction.Backward:
            self.hide()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if not self.config["image_path"]:
            painter.fillRect(self.rect(), QColor(30, 30, 30))
            return
        try:
            # 1. 获取真实的物理像素尺寸并立即转换为整数
            pixel_ratio = self.devicePixelRatioF()
            physical_width = int(self.width() * pixel_ratio)
            physical_height = int(self.height() * pixel_ratio)

            # 2. PIL 读取图像
            pil_image = Image.open(self.config["image_path"]).convert("RGBA")
            
            # 3. 计算保持比例缩放后的新尺寸 (使用整数物理尺寸)
            img_ratio = pil_image.width / pil_image.height
            screen_ratio = physical_width / physical_height
            if img_ratio > screen_ratio:
                new_height = physical_height
                new_width = int(new_height * img_ratio)
            else:
                new_width = physical_width
                new_height = int(new_width / img_ratio)

            # 4. PIL 高质量缩放
            resized_image = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # 5. PIL 伽马校正
            gamma = self.config.get("rest_image_gamma", 1.0)
            if gamma != 1.0:
                gamma_lut = [pow(i / 255.0, gamma) * 255 for i in range(256)]
                r, g, b, a = resized_image.split()
                r = r.point(gamma_lut); g = g.point(gamma_lut); b = b.point(gamma_lut)
                processed_image = Image.merge('RGBA', (r, g, b, a))
            else:
                processed_image = resized_image

            # 6. 转换回 Qt 对象
            data = processed_image.tobytes("raw", "RGBA")
            q_image = QImage(data, processed_image.width, processed_image.height, QImage.Format.Format_RGBA8888)
            final_pixmap = QPixmap.fromImage(q_image)
            final_pixmap.setDevicePixelRatio(pixel_ratio)

            # 7. 最终绘制：只使用整数计算和 QRect
            crop_x = (new_width - physical_width) // 2
            crop_y = (new_height - physical_height) // 2
            source_rect = QRect(crop_x, crop_y, physical_width, physical_height)
            painter.drawPixmap(self.rect(), final_pixmap, source_rect)

        except Exception as e:
            print(f"[EyeCareApp]: Error during PIL image processing: {e}", flush=True)
            painter.fillRect(self.rect(), QColor(30, 30, 30))

# ====================================================================
# 主计时器窗口
# ====================================================================
class EyeCareTimerWidget(QWidget):
    def __init__(self, config=None):
        super().__init__()
        self.config = DEFAULT_CONFIG.copy()
        if config:
            self.config.update(config)
        self.base_config = self.config.copy()
        self.scale_factor = 1.0
        self.is_locked = False
        self.is_paused = False
        self.state = "work"
        self.work_seconds = self.config["work_minutes"] * 60
        self.rest_seconds = self.config["rest_minutes"] * 60
        self.time_left = self.work_seconds
        self.rest_widget = RestImageWidget(self.config)
        self.lock_widget = LockIconWidget()
        self.setup_ui()
        self.apply_theme(self.config["theme"])
        self.setup_timer()
        self.create_tray_icon()
        self.setup_ipc_listener()
        self.old_pos = None
        self.lock_widget.toggled.connect(self.toggle_lock)

    def setup_ui(self):
        self.base_flags = (Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setWindowFlags(self.base_flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setGeometry(100, 100, self.config["window_width"], self.config["window_height"])
        self.time_label = QLabel(self)
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, self.lock_widget.width() + 5, 0)
        layout.addWidget(self.time_label)
        self.update_label()

    def setup_timer(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)
        self.timer.start(1000)

    def setup_ipc_listener(self):
        if sys.stdin and hasattr(sys.stdin, 'fileno'):
            try:
                sys.stdin.fileno()
                self.listener = CommandListenerThread(self)
                self.listener.commandReceived.connect(self.handle_command)
                self.listener.start()
            except io.UnsupportedOperation:
                self.log_message("IPC listener disabled: stdin is not a valid stream.")
        else:
            self.log_message("IPC listener disabled: No stdin detected.")

    def wheelEvent(self, event):
        if self.is_locked: return
        delta = event.angleDelta().y()
        self.scale_factor *= 1.1 if delta > 0 else 0.9
        self.scale_factor = max(0.5, min(3.0, self.scale_factor))
        self.apply_scale()

    def resizeEvent(self, event):
        lock_pos = self.pos() + QPoint(self.width() - self.lock_widget.width() - 5, (self.height() - self.lock_widget.height()) / 2)
        self.lock_widget.move(lock_pos)
        self.layout().setContentsMargins(10, 0, self.lock_widget.width() + 5, 0)
        self.lock_widget.raise_()
        super().resizeEvent(event)

    def moveEvent(self, event):
        lock_pos = self.pos() + QPoint(self.width() - self.lock_widget.width() - 5, (self.height() - self.lock_widget.height()) / 2)
        self.lock_widget.move(lock_pos)
        self.lock_widget.raise_()
        super().moveEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        bg_color = self.config.get("background_locked" if self.is_locked else "background_normal")
        painter.setBrush(QBrush(bg_color))
        painter.setPen(QPen(Qt.PenStyle.NoPen))
        painter.drawRoundedRect(self.rect(), 10, 10)

    def contextMenuEvent(self, event):
        if self.is_locked: return
        self.lock_widget.raise_()
        self.create_menu().exec(event.globalPos())
        

    def mousePressEvent(self, event):
        if self.is_locked: return
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = event.globalPosition().toPoint()
            self.lock_widget.raise_()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self.old_pos and not self.is_locked:
            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self.old_pos = None

    def showEvent(self, event):
        self.lock_widget.show()
        self.lock_widget.raise_()
        super().showEvent(event)

    def hideEvent(self, event):
        self.lock_widget.hide()
        super().hideEvent(event)

    def log_message(self, message):
        output = f"[EyeCareApp]: {message}"
        print(output, flush=True)

    def update_timer(self):
        if self.is_paused: return
        self.time_left -= 1
        if self.time_left < 0:
            if self.state == "work": self.start_rest()
            else: self.start_work()
        self.update_label()

    def start_work(self):
        self.log_message("State changed to: Work")
        self.state = "work"
        self.time_left = self.base_config["work_minutes"] * 60
        self.rest_widget.fade_out()
        self.update_label()

    def start_rest(self):
        self.log_message("State changed to: Rest")
        self.state = "rest"
        self.time_left = self.base_config["rest_minutes"] * 60
        self.rest_widget.fade_in()
        self.update_label()
        self.raise_()
        self.lock_widget.raise_()
    def extend_work_time(self):
        self.log_message("Work time extended by 5 minutes.")
        if self.state == "rest":
            self.state = "work"
            self.rest_widget.fade_out()
        self.time_left = (self.time_left if self.state == 'work' else 0) + 5 * 60
        self.update_label()

    def reset_timer(self):
        self.log_message("Timer reset.")
        if self.state == "work": self.time_left = self.base_config["work_minutes"] * 60
        else: self.time_left = self.base_config["rest_minutes"] * 60
        self.update_label()

    def set_time(self, seconds):
        if isinstance(seconds, int) and seconds >= 0:
            self.log_message(f"Time set externally to {seconds} seconds.")
            self.time_left = seconds
            self.update_label()

    def handle_command(self, command_str):
        self.log_message(f"Received IPC command: {command_str}")
        try:
            cmd_data = json.loads(command_str)
            command = cmd_data.get("command")
            value = cmd_data.get("value")
            if command == "set_theme" and value in THEMES: self.set_theme(value)
            elif command == "set_font" and value in AVAILABLE_FONTS: self.set_font(value)
            elif command == "set_time" and isinstance(value, int): self.set_time(value)
        except Exception as e:
            self.log_message(f"Error processing IPC command: {e}")

    def apply_scale(self):
        new_width = self.base_config["window_width"] * self.scale_factor
        new_height = self.base_config["window_height"] * self.scale_factor
        self.resize(int(new_width), int(new_height))
        self.apply_theme(self.config["theme"])

    def set_theme(self, name):
        if name in THEMES:
            self.log_message(f"Setting theme to: {name}")
            self.config["theme"] = name
            self.config["font_family"] = None
            self.apply_theme(name)
        else:
            self.log_message(f"Error: Theme '{name}' not found.")

    def set_font(self, font_name):
        if font_name in AVAILABLE_FONTS:
            self.log_message(f"Setting font to: {font_name}")
            self.config["font_family"] = font_name
            self.apply_theme(self.config["theme"])

    def apply_theme(self, name):
        theme = THEMES[name]
        self.config.update(theme)
        font_family = self.config["font_family"] or theme["font_family"]
        base_font_size = 14
        new_font_size = int(base_font_size * self.scale_factor)
        font_style = theme.get("text_style", "font-weight: normal;")
        self.time_label.setStyleSheet(f"color: {theme['text'].name()}; font-size: {new_font_size}px; {font_style} font-family: '{font_family}';")
        self.lock_widget.set_theme(theme)
        self.update()

    def update_label(self):
        mins, secs = divmod(self.time_left, 60)
        time_str = f"{int(mins):02d}:{int(secs):02d}"
        prefix = "Paused" if self.is_paused else ("Work" if self.state == "work" else "Rest")
        self.time_label.setText(f"{prefix}: {time_str}")

    def create_menu(self):
        menu = QMenu(self)
        theme = THEMES[self.config.get("theme", "Dark")]
        qss = f"""            QMenu {{                 background-color: {theme['menu_background'].name()};                 color: {theme['menu_text'].name()};                 border: 1px solid {theme['menu_border'].name()};                 border-radius: 5px; padding: 5px;             }}            QMenu::item {{ padding: 8px 25px 8px 20px; border-radius: 4px; }}            QMenu::item:selected {{ background-color: {theme['menu_selected_background'].name()}; }}            QMenu::item:disabled {{ color: {theme['menu_disabled_text'].name()}; }}            QMenu::separator {{ height: 1px; background-color: {theme['menu_separator'].name()}; margin: 5px 0px; }}        """
        menu.setStyleSheet(qss)
        extend_action = QAction("延长5分钟工作", self, triggered=self.extend_work_time)
        actions = [extend_action, QAction("立即休息", self, triggered=self.start_rest), QAction("立即工作", self, triggered=self.start_work), QAction("重置计时", self, triggered=self.reset_timer)]
        menu.addActions(actions)
        menu.addSeparator()
        theme_menu = menu.addMenu("主题")
        for theme_name in THEMES:
            action = QAction(theme_name, self, checkable=True)
            action.setChecked(theme_name == self.config["theme"])
            action.triggered.connect(lambda checked=False, name=theme_name: self.set_theme(name))
            theme_menu.addAction(action)

        font_menu = menu.addMenu("字体")
        current_font = self.config["font_family"] or theme["font_family"]
        for font_name in AVAILABLE_FONTS:
            action = QAction(font_name, self, checkable=True)
            action.setChecked(font_name == current_font)
            action.triggered.connect(lambda checked=False, name=font_name: self.set_font(name))
            font_menu.addAction(action)
        menu.addSeparator()
        menu.addAction(QAction("解锁" if self.is_locked else "锁定", self, triggered=lambda: self.toggle_lock(not self.is_locked)))
        menu.addSeparator()
        menu.addAction(QAction("退出", self, triggered=self.close_app))
        return menu

    def toggle_lock(self, is_locked):
        self.is_locked = is_locked
        self.lock_widget.set_locked_state(is_locked)
        self.log_message(f"Window {'locked' if is_locked else 'unlocked'}.")
        if self.is_locked:
            self.setWindowFlags(self.base_flags | Qt.WindowType.WindowTransparentForInput)
        else:
            self.setWindowFlags(self.base_flags)
        self.show()
        self.lock_widget.raise_()

    def create_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        icon = self.style().standardIcon(QStyle.StandardPixmap.SP_DesktopIcon)
        self.tray_icon.setIcon(icon)
        self.tray_icon.setContextMenu(self.create_menu())
        self.tray_icon.show()
        self.tray_icon.setToolTip("护眼助手")
        self.tray_icon.contextMenu().aboutToShow.connect(lambda: self.tray_icon.setContextMenu(self.create_menu()))

    def close_app(self):
        self.log_message("Application closing.")
        if hasattr(self, 'listener') and self.listener.isRunning():
            self.listener.quit()
        self.rest_widget.close()
        self.lock_widget.close()
        self.close()
        QApplication.instance().quit()

# ====================================================================
# 主程序入口
# ====================================================================
def run_app(config=None):
    if QApplication.instance() is None:
        app = QApplication(sys.argv)
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    else:
        app = QApplication.instance()

    main_widget = EyeCareTimerWidget(config)
    main_widget.show()
    
    # 仅当作为主脚本运行时，才执行app.exec()
    if __name__ == "__main__":
        sys.exit(app.exec())
    return main_widget

if __name__ == "__main__":
    custom_config = {
        "work_minutes": 0.2,
        "rest_minutes": 0.2,
        "window_width": 140,
        "image_path": r"D:\documentation\图片\pixiv\58145566_p0.png"
    }
    run_app(custom_config)