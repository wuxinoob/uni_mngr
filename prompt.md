# UniPanel 项目逻辑总结与开发上下文

## 1. 项目概述
本项目是一个基于 Python (PySide6) 的通用工具管理面板 (`UniPanel`)。主要功能是管理和运行外部子进程（任务），支持自定义配置、定时运行、自动重启、以及高度自定义的现代化 UI 界面。

## 2. 文件结构与核心职责

- **`main.py`**: 程序入口。
  - 处理命令行参数 (`--autostart`)。
  - 初始化 Qt 应用，设置 HighDPI 策略。
  - 应用默认主题 (`qdarktheme`)。
  - 启动主窗口。

- **`uni_panel_pj/ui/uni_panel_window.py` (`mainWindow`)**:
  - **核心容器**: 设置了 `Qt.FramelessWindowHint` (无边框) 和 `Qt.WA_TranslucentBackground` (背景透明)。
  - **布局逻辑**: 使用 `mainContainer` (QFrame) 包裹所有内容以实现圆角和四周阴影效果 (`QGraphicsDropShadowEffect`)。
  - **生命周期**: 处理配置加载 (`load_cfg`)、后端初始化 (`backend_init`)、托盘图标 (`QSystemTrayIcon`) 和关闭事件 (`closeEvent`)。
  - **全局设置响应**: 监听设置页面的信号，实时调整主题、透明度、字体和自启状态。
  - **窗口交互**: 实现了手动调整窗口大小的鼠标事件处理。

- **`uni_panel_pj/core/Qt_process_manager.py` (`ProcessManager`)**:
  - **进程管理**: 使用 `QProcess` 管理子任务，维护 `task_status` 字典。
  - **功能**: 支持定时任务 (`QTimer`)、自动重启、标准输出捕获与路由。
  - **持久化**: 负责 `process_manager_config.json` 的读写。
  - **自启逻辑**: 包含 `set_main_panel_config` 接口，根据主程序的“总开关”和各个任务的配置，调用 `os_utils` 修改注册表。

- **`uni_panel_pj/ui/settings_page.py`**:
  - 提供全局设置界面：主题切换、透明度滑块、字体选择、字号调整、开机自启总开关。
  - 发送 `setting_changed` 信号通知主窗口。

- **`uni_panel_pj/ui/task_page.py`**:
  - 任务管理界面，包含任务列表和详细配置页。
  - 使用 `HistoryLineEdit` 提供带有命令历史记录的输入框。
  - 提供任务的增删改查及控制（运行/停止/重启）。

- **`uni_panel_pj/ui/custom_title_bar.py`**:
  - 自定义标题栏，替代原生标题栏。
  - 包含图标、标题、最小化、最大化/恢复、关闭按钮。
  - 使用 `startSystemMove` 实现流畅的窗口拖动和系统分屏支持。

- **`uni_panel_pj/ui/collapsible_list_widget.py`**:
  - 带有动画效果的可折叠侧边栏。
  - 重写了 `IconOnlyDelegate`，在折叠模式下隐藏文本并强制图标居中。
  - 修复了水平滚动条问题（通过 `sizeHint` 强制返回折叠宽度）。

- **`uni_panel_pj/core/os_utils.py`**:
  - 封装 Windows 注册表操作，用于实现开机自启。

- **`uni_panel_pj/ui/styles/modern.qss`**:
  - 全局样式表。
  - 移除了硬编码的字体设置，以支持动态字体调整。
  - 定义了圆角、边框、按钮状态（运行/停止/删除）的样式。

## 3. 关键逻辑流程

### 3.1 启动流程
1. `main.py` 启动，设置 HighDPI。
2. `mainWindow` 初始化 -> `backend_init` (关联 ProcessManager) -> `load_cfg` (加载 UI 和 任务配置) -> `initUI` (构建界面) -> 初始化托盘。
3. `load_cfg` 会合并默认配置，防止因缺少配置项导致 UI 异常（如字号重置）。
4. 窗口显示时触发 `showEvent`，执行淡入动画。

### 3.2 退出/关闭流程
1. 用户点击关闭 -> 触发 `closeEvent`。
2. 检查是否有运行中的子进程 -> 弹窗提示。
3. 询问用户：最小化到托盘 OR 直接退出。
   - **最小化**: 调用 `self.hide()`。
   - **退出**: 调用 `ProcessManager.stop_all_tasks()` -> `QApplication.quit()`。

### 3.3 开机自启逻辑
- **总开关 (`SettingsPage`)**: 决定是否允许程序修改注册表。
- **任务开关 (`TaskPage`)**: 决定具体哪个任务在程序启动时运行。
- **逻辑**: `ProcessManager` 在每次任务变动或设置变动时，检查 `master_autostart`。如果为 False，移除注册表项；如果为 True，且有任一任务标记为自启，则添加注册表项。

### 3.4 动态字体应用
- 设置页面修改字体/字号 -> 发送信号。
- 主窗口接收信号 -> 保存配置 -> 调用 `_apply_font`。
- `_apply_font` 使用 `QApplication.setFont` 全局应用字体 (QSS 中已移除冲突样式)。

## 4. UI/UX 特性
- **圆角窗口**: 主窗口 20px 圆角，伴随柔和的阴影。
- **无边框**: 实现了自定义的边缘拖拽缩放和标题栏拖动。
- **动画**: 侧边栏折叠动画、页面切换动画、窗口启动淡入动画。
- **风格**: 深色现代主题，扁平化按钮，Unicode 图标。

## 5. 待办/已知注意事项
- 确保所有新添加的 UI 控件不要在 QSS 中硬编码字体大小，否则全局字体设置会失效。
- 涉及窗口几何计算时（如居中），需考虑阴影边距 (`ContentsMargins`) 的影响。
