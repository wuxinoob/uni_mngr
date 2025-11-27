import sys
from PySide6.QtWidgets import (QApplication, QDialog, QWidget, QVBoxLayout, 
                               QFormLayout, QLineEdit, QPushButton, QHBoxLayout, 
                               QSpinBox, QDialogButtonBox, QFileDialog, QLabel)
from PySide6.QtCore import Qt

class TaskConfigDialog(QDialog):
    """
    任务配置模态窗口
    功能：
    1. 以字典形式初始化配置
    2. 提供文件选择框选择运行程序
    3. 设置定时任务和超时时间
    4. 返回修改后的配置字典
    """
    def __init__(self, config: dict = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("任务配置")
        self.resize(450, 300)
        
        # 如果没有传入配置，使用空字典
        self.current_config = config if config else {}
        
        self.setup_ui()
        self.load_config_to_ui()

    def setup_ui(self):
        # 主布局
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # 表单布局
        form_layout = QFormLayout()
        
        # 1. 任务名称
        self.le_task_name = QLineEdit()
        self.le_task_name.setPlaceholderText("请输入任务唯一标识名")
        form_layout.addRow("任务名称:", self.le_task_name)

        # 2. 运行程序 (带文件选择按钮)
        path_layout = QHBoxLayout()
        self.le_task_cmd = QLineEdit()
        self.le_task_cmd.setPlaceholderText("可执行文件路径")
        self.btn_browse = QPushButton("浏览...")
        self.btn_browse.clicked.connect(self.open_file_dialog)
        
        path_layout.addWidget(self.le_task_cmd)
        path_layout.addWidget(self.btn_browse)
        form_layout.addRow("运行程序:", path_layout)

        # 3. 运行参数
        self.le_cmd_args = QLineEdit()
        self.le_cmd_args.setPlaceholderText("例如: --port 8080 (空格分隔)")
        form_layout.addRow("运行参数:", self.le_cmd_args)

        # 4. 定时时间 (Interval)
        # 假设为循环执行间隔，0表示不循环/单次运行
        self.sb_interval = QSpinBox()
        self.sb_interval.setRange(0, 86400) # 最大一天
        self.sb_interval.setSuffix(" 秒")
        self.sb_interval.setSpecialValueText("无 (单次运行)") # 值为0时显示文本
        form_layout.addRow("定时/循环间隔:", self.sb_interval)

        # 5. 最大运行时间 (Timeout)
        # 0 表示不限制
        self.sb_timeout = QSpinBox()
        self.sb_timeout.setRange(0, 86400)
        self.sb_timeout.setSuffix(" 秒")
        self.sb_timeout.setSpecialValueText("不限制")
        form_layout.addRow("最大运行时间:", self.sb_timeout)

        main_layout.addLayout(form_layout)

        # 底部按钮区 (确认/取消)
        # QDialogButtonBox 自动处理不同操作系统的按钮顺序
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept) # 点击OK触发 accept()
        self.button_box.rejected.connect(self.reject) # 点击Cancel触发 reject()
        main_layout.addWidget(self.button_box)

    def open_file_dialog(self):
        """打开文件选择器"""
        file_path, _ = QFileDialog.getOpenFileName(self, "选择运行程序", "", "Executables (*.exe *.py *.sh *.bat);;All Files (*)")
        if file_path:
            self.le_task_cmd.setText(file_path)

    def load_config_to_ui(self):
        """将传入的字典数据填充到UI控件中"""
        self.le_task_name.setText(self.current_config.get("name", ""))
        self.le_task_cmd.setText(self.current_config.get("command", ""))
        self.le_cmd_args.setText(self.current_config.get("args", ""))
        self.sb_interval.setValue(int(self.current_config.get("interval", 0)))
        self.sb_timeout.setValue(int(self.current_config.get("timeout", 0)))

    def get_config(self) -> dict:
        """获取UI上的最新数据，返回字典"""
        return {
            "name": self.le_task_name.text().strip(),
            "command": self.le_task_cmd.text().strip(),
            "args": self.le_cmd_args.text().strip(),
            "interval": self.sb_interval.value(),
            "timeout": self.sb_timeout.value()
        }

# ==========================================
# 使用示例 (模拟主程序调用)
# ==========================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 模拟一个旧配置
    old_config = {
        "name": "DataProcessor",
        "command": "python.exe",
        "args": "main.py --verbose",
        "interval": 60,  # 60秒跑一次
        "timeout": 0     # 不限制
    }

    # 1. 创建对话框实例
    dialog = TaskConfigDialog(config=old_config)
    
    # 2. 模态显示 (exec 会阻塞直到窗口关闭)
    result = dialog.exec()
    
    # 3. 判断用户点击的是"确认"还是"取消"
    if result == QDialog.Accepted:
        new_config = dialog.get_config()
        print("用户点击了保存:")
        print(new_config)
    else:
        print("用户取消了操作")

    sys.exit()