# UniPanel 项目逻辑总结与开发上下文

## 1. 项目概述
本项目是一个基于 Python (PySide6) 的通用工具管理面板 (`UniPanel`)。主要功能是管理和运行外部子进程（任务），支持自定义配置、定时运行、自动重启、以及高度自定义的现代化 UI 界面。包含一个核心子工具“护眼助手”，展示了与主面板的深度集成能力。

## 2. 文件结构与核心职责

- **`main.py`**: 程序入口。
  - 处理命令行参数 (`--autostart`)。
  - 初始化 Qt 应用，设置 HighDPI 策略。
  - 应用默认主题 (`qdarktheme`)。
  - 启动主窗口。

- **`uni_panel_pj/ui/uni_panel_window.py` (`mainWindow`)**:
  - **核心容器**: 设置了 `Qt.FramelessWindowHint` (无边框) 和 `Qt.WA_TranslucentBackground` (背景透明)。
  - **布局逻辑**: 使用 `mainContainer` (QFrame) 包裹所有内容以实现 20px 圆角和四周阴影效果 (`QGraphicsDropShadowEffect`)。
  - **生命周期**: 
    - `__init__`: 初始化 `ProcessManager`，设置配置路径，实例化各个页面（TaskPage, EyeCarePage, SettingsPage）。
    - `backend_init`: 将主配置传递给 `ProcessManager`。
    - `load_cfg`: 加载 UI 配置（合并默认值）和 ProcessManager 配置。如果 PM 配置不存在，启用保存以允许创建。
    - `initUI`: 构建界面，集成自定义标题栏和侧边栏。
    - `closeEvent`: 处理退出逻辑（最小化/退出确认）。
  - **全局设置响应**: 监听设置页面的信号，实时调整主题、透明度、字体和自启状态。
  - **窗口交互**: 实现了手动调整窗口大小的鼠标事件处理。

- **`uni_panel_pj/core/Qt_process_manager.py` (`ProcessManager`)**:
  - **进程管理**: 使用 `QProcess` 管理子任务，维护 `task_status` 字典。
  - **功能**: 支持定时任务 (`QTimer`)、自动重启、标准输出捕获与路由（支持隐藏任务的控制台输出）。
  - **持久化**: 负责 `process_manager_config.json` 的读写。
    - **安全机制**: 引入 `_save_enabled` 标志，防止在初始化阶段（仅加载了部分默认任务时）意外覆盖旧的配置文件。
  - **自启逻辑**: 包含 `set_main_panel_config` 接口，根据主程序的“总开关”和各个任务的配置，调用 `os_utils` 修改注册表。

- **`uni_panel_pj/ui/settings_page.py`**:
  - 提供全局设置界面：主题切换、透明度滑块、字体选择、字号调整、开机自启总开关。
  - 发送 `setting_changed` 信号通知主窗口。

- **`uni_panel_pj/ui/task_page.py`**:
  - 任务管理界面，包含任务列表和详细配置页。
  - 使用 `HistoryLineEdit` 提供带有命令历史记录的输入框。
  - 提供任务的增删改查及控制（运行/停止/重启）。

- **`uni_panel_pj/ui/eye_care_page.py` (`EyeCarePage`)**:
  - **职责**: “护眼助手”子工具的配置与控制面板。
  - **集成**: 
    - 初始化时检查/添加 "EyeCare" 任务到 `ProcessManager`。
    - 从 `config.json` 读取配置更新 UI。
    - UI 变动时，通过 `ProcessManager.write_to_process` (stdin) 发送 JSON 指令给子进程实现热更新。
    - 同时使用“读取-更新-写入”模式保存配置到 `config.json`，确保不覆盖子进程维护的位置信息。

- **`uni_panel_pj/subtools/eye_care/eye_care.py`**:
  - **独立进程**: 一个 PySide6 应用程序，运行护眼倒计时。
  - **功能**: 
    - 倒计时窗口（支持拖拽、滚轮缩放）。
    - 休息时全屏显示图片（支持透明度、淡入淡出）。
    - 锁定模式。
  - **配置**: 自身维护 `config.json`，支持记住窗口位置（拖拽结束后保存）。
  - **IPC**: 监听 `stdin`，接收主面板发来的 JSON 指令动态更新配置。

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
  - 定义了 20px 圆角、边框、按钮状态（运行/停止/删除）的样式。

## 3. 关键逻辑流程

### 3.1 启动流程
1. `main.py` 启动，设置 HighDPI。
2. `mainWindow` 初始化:
   - 创建 `ProcessManager` 并立即设置 config path。
   - 初始化 `TaskPage`, `EyeCarePage`, `SettingsPage`。
     - `EyeCarePage` 初始化时向 PM 添加任务，但此时 PM 的保存功能尚未启用（`_save_enabled=False`），防止覆盖。
   - `backend_init`: 传递主配置给 PM。
   - `load_cfg`: 加载主配置（合并默认值），加载 PM 任务配置。
     - 加载完成后，启用 PM 保存 (`_save_enabled=True`)。
     - 如果 PM 配置文件不存在，显式调用 `enable_save()`。
   - `initUI`: 构建界面。
3. 窗口显示时触发 `showEvent`，执行淡入动画。

### 3.2 EyeCare 集成流程
1. **启动**: 用户在面板点击启动 -> PM 启动 `eye_care.py` 子进程。
2. **配置同步**: 
   - `EyeCarePage` 启动时从 `config.json` 读取配置。
   - 用户修改 UI -> `EyeCarePage` 发送 JSON 到子进程 stdin -> 子进程 `handle_command` 更新运行时状态。
   - `EyeCarePage` 将新配置合并写入 `config.json`。
3. **位置记忆**: 
   - 用户拖拽子进程窗口 -> 子进程 `mouseReleaseEvent` -> 更新内存配置 -> 写入 `config.json`。
   - 下次启动，子进程读取 `config.json` 恢复位置。

### 3.3 退出/关闭流程
1. 用户点击关闭 -> 触发 `closeEvent`。
2. 检查是否有运行中的子进程 -> 弹窗提示。
3. 询问用户：最小化到托盘 OR 直接退出。
   - **最小化**: 调用 `self.hide()`。
   - **退出**: 调用 `ProcessManager.stop_all_tasks()` -> `QApplication.quit()`。

## 4. UI/UX 特性
- **圆角窗口**: 主窗口 20px 圆角，伴随柔和的阴影。
- **无边框**: 实现了自定义的边缘拖拽缩放和标题栏拖动。
- **动画**: 侧边栏折叠动画、页面切换动画、窗口启动淡入动画。
- **风格**: 深色现代主题，扁平化按钮，Unicode 图标。
- **字体**: 支持动态调整全局字体和字号。

## 5. 待办/已知注意事项
- `ProcessManager` 解析参数时使用简单的空格分割，不支持带空格的路径。建议改进为 `shlex` 解析。
- `EyeCare` 子进程依赖 `Pillow` 库。
- 确保所有新添加的 UI 控件不要在 QSS 中硬编码字体大小。