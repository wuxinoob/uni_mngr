from PySide6.QtWidgets import QLineEdit
from PySide6.QtCore import Qt

class HistoryLineEdit(QLineEdit):
    """
    一个 QLineEdit 的子类，增加了命令历史记录功能。
    通过上下箭头键可以遍历输入过的历史命令。
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.history = []
        self.history_index = -1
        self.temp_text = "" # 用于暂存用户在浏览历史前输入的文本

    def add_to_history(self, command: str):
        """将一个新命令添加到历史记录中"""
        if not command or (self.history and self.history[-1] == command):
            return # 避免添加空命令或重复的连续命令
        self.history.append(command)
        self.history_index = len(self.history) # 重置索引到末尾之后

    def keyPressEvent(self, event):
        """重写按键事件处理器，以处理上下箭头键"""
        key = event.key()

        if key == Qt.Key.Key_Up:
            if self.history_index == len(self.history):
                # 第一次按上键时，保存当前行内的文本
                self.temp_text = self.text()

            if self.history_index > 0:
                self.history_index -= 1
                self.setText(self.history[self.history_index])
            event.accept()

        elif key == Qt.Key.Key_Down:
            if self.history_index < len(self.history) - 1:
                self.history_index += 1
                self.setText(self.history[self.history_index])
            else:
                # 按下键超过历史记录范围时，恢复之前暂存的文本
                self.history_index = len(self.history)
                self.setText(self.temp_text)
            event.accept()
            
        else:
            # 对于其他按键，调用父类的默认行为
            super().keyPressEvent(event)
