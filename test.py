import sys
import os
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QSpinBox, 
                               QLabel, QHBoxLayout)
from PySide6.QtGui import QPainter, QPixmap, QColor, QBrush
from PySide6.QtCore import Qt, QPoint

def generate_arrow_pixmap(color_hex, is_up, filename):
    # 尺寸设为 16x16
    size = 16 
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QBrush(QColor(color_hex)))
    painter.setPen(Qt.PenStyle.NoPen)
    
    cx = size // 2
    cy = size // 2
    
    # 稍微调整一下三角形大小，让它看起来更饱满
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
    
    # --- 关键修改：直接保存为本地文件 ---
    # 这避免了 Base64 在不同 Qt 版本/环境下的解析 Bug
    pixmap.save(filename, "PNG")
    print(f"Generated icon: {os.path.abspath(filename)}")
    return filename

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # 1. 生成并保存图片文件到当前目录
    # 注意：Qt 样式表中的 url() 路径最好使用正斜杠
    arrow_up_path = generate_arrow_pixmap("#ecf0f1", True, "arrow_up_fixed.png")
    arrow_down_path = generate_arrow_pixmap("#ecf0f1", False, "arrow_down_fixed.png")

    # 2. 构建 QSS
    # 依然保留红色背景方便最后确认位置，确认无误后可删除 background-color
    qss = f"""
    QWidget {{
        background-color: #2c3e50;
        color: #ecf0f1;
        font-family: "Segoe UI";
        font-size: 14px;
    }}
    QSpinBox {{
        border: 1px solid #34495e;
        border-radius: 4px;
        padding: 5px;
        padding-right: 25px; 
        background-color: #34495e;
        min-height: 30px;
    }}
    
    /* === 按钮容器区域 === */
    QSpinBox::up-button {{
        subcontrol-origin: border;
        subcontrol-position: top right;
        width: 20px;
        height: 12px; /* 保持之前计算出的安全高度 */
        border: none;
        margin-right: 2px;
        margin-top: 2px;
        background-color: rgba(255, 0, 0, 0.3); /* 调试用红框，成功后可删除 */
    }}
    QSpinBox::down-button {{
        subcontrol-origin: border;
        subcontrol-position: bottom right;
        width: 20px;
        height: 12px;
        border: none;
        margin-right: 2px;
        margin-bottom: 2px;
        background-color: rgba(255, 0, 0, 0.3); /* 调试用红框 */
    }}

    /* === 箭头图标区域 === */
    /* 
       回归标准写法：将图片赋给 arrow 子控件。
       关键点：必须显式指定 width 和 height，否则可能不显示。
    */
    QSpinBox::up-arrow {{
        image: url({arrow_up_path});
        width: 12px;
        height: 12px;
    }}
    QSpinBox::down-arrow {{
        image: url({arrow_down_path});
        width: 12px;
        height: 12px;
    }}

    QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
        background-color: #4a637a;
    }}
    """

    w = QWidget()
    w.setWindowTitle("SpinBox Fixed (File Mode)")
    w.resize(400, 300)
    w.setStyleSheet(qss)

    layout = QVBoxLayout(w)
    
    layout.addWidget(QLabel("方案说明："))
    layout.addWidget(QLabel("已将图标保存为 arrow_up/down_fixed.png 并通过路径加载。"))
    layout.addWidget(QLabel("如果能看到箭头，说明之前是 Base64 解析的问题。"))
    
    sb = QSpinBox()
    sb.setValue(50)
    layout.addWidget(sb)

    layout.addStretch()
    w.show()
    sys.exit(app.exec())