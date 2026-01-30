# -*- coding: utf-8 -*-
import sys
import os
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def manage_app_autostart(enabled: bool):
    """
    配置主程序自身的开机自启动（仅支持Windows）。
    如果启用，程序将在用户登录时以 --autostart 参数启动。

    :param enabled: True 表示设置为开机启动，False 表示移除。
    """
    if sys.platform != 'win32':
        logging.warning(f"开机启动功能目前只支持 Windows。")
        return

    import winreg

    # App的唯一标识，用于注册表值名称
    app_name = "UniPanel" # 单一的启动项名称
    
    # 获取Python解释器路径和主脚本路径
    python_exe = sys.executable
    # sys.argv[0] 在打包后可能不准确，使用 __file__ 会更稳健
    # 但在此脚本执行环境下，假定 main.py 是入口
    main_script_path = os.path.abspath(sys.argv[0])

    # 构建要在注册表中写入的命令
    # --autostart 是我们约定的命令行参数，用于告知程序是自启动的
    command = f'"{python_exe}" "{main_script_path}" --autostart'

    # 注册表路径
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"

    try:
        # 打开注册表项
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS) as key:
            if enabled:
                # 设置开机启动
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, command)
                logging.info(f"已设置 UniPanel 开机自启。")
            else:
                # 移除开机启动
                try:
                    winreg.DeleteValue(key, app_name)
                    logging.info(f"已移除 UniPanel 开机自启。")
                except FileNotFoundError:
                    # 如果值不存在，说明之前未设置，忽略即可
                    logging.info(f"UniPanel 未设置过开机自启，无需移除。")

    except Exception as e:
        logging.error(f"操作注册表失败: {e}")
