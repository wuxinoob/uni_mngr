@echo off
setlocal enabledelayedexpansion

:: =============================================================================
:: 配置区 - 请根据需要修改
:: =============================================================================
:: 为计划任务设置一个唯一的名称，避免与其他任务冲突
set "TaskName=MyStartExeStartup"
:: 需要开机启动的程序文件名
set "TargetFileName=main.exe"


:: =============================================================================
:: 脚本主体 - 请勿修改下方内容
:: =============================================================================

:: 获取当前脚本所在的文件夹路径
set "CurrentFolder=%~dp0"
:: 移除路径末尾的反斜杠，以规范化路径
if "%CurrentFolder:~-1%"=="\" set "CurrentFolder=%CurrentFolder:~0,-1%"
set "TargetFullPath=%CurrentFolder%\%TargetFileName%"

:: --- 检查管理员权限 ---
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo.
    echo [提示] 当前非管理员权限，正在尝试以管理员身份重新运行...
    echo.
    
    :: 使用PowerShell尝试以管理员身份重启脚本
    powershell -Command "Start-Process -FilePath '%~f0' -Verb RunAs" >nul 2>&1
    if !errorlevel! neq 0 (
        :: PowerShell方法失败，尝试使用VBScript
        echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
        echo UAC.ShellExecute "%~f0", "", "", "runas", 1 >> "%temp%\getadmin.vbs"
        "%temp%\getadmin.vbs"
        del "%temp%\getadmin.vbs"
    )
    exit
)

:menu
cls
echo =================================================================
echo  开机启动和Windows Defender排除项管理脚本
echo =================================================================
echo.
echo  当前文件夹: %CurrentFolder%
echo  目标启动程序: %TargetFileName%
echo.
echo -----------------------------------------------------------------
echo  请选择要执行的操作:
echo -----------------------------------------------------------------
echo.
echo  [ Windows Defender 排除项管理 ]
echo    1. 添加当前文件夹到 Windows Defender 排除列表
echo    2. 从 Windows Defender 排除列表移除当前文件夹
echo.
echo  [ 开机启动项管理 (%TargetFileName%) ]
echo    3. 设置开机以管理员身份自启动
echo    4. 取消开机自启动
echo.
echo  [ 状态检查 ]
echo    5. 查看当前状态
echo.
echo  [ 其他 ]
echo    6. 退出
echo.
echo -----------------------------------------------------------------

set /p "choice=请输入选项数字并按回车: "

if "%choice%"=="1" goto addExclusion
if "%choice%"=="2" goto removeExclusion
if "%choice%"=="3" goto addStartup
if "%choice%"=="4" goto removeStartup
if "%choice%"=="5" goto checkStatus
if "%choice%"=="6" goto :eof
echo.
echo [错误] 无效的输入，请重新输入。
pause
goto menu

:addExclusion
echo.
echo --- 正在尝试添加 Windows Defender 排除项... ---
powershell -NoProfile -ExecutionPolicy Bypass -Command "Add-MpPreference -ExclusionPath '%CurrentFolder%'"
if !errorlevel! equ 0 (
    echo.
    echo [成功] 已将文件夹 "%CurrentFolder%" 添加到 Windows Defender 排除列表。
) else (
    echo.
    echo [失败] 无法自动添加排除项。可能是由于权限问题或安全策略限制。
    echo [提示] 将为您打开 Windows 安全中心，请手动添加排除项。
    echo        路径 -> 病毒和威胁防护 -> "病毒和威胁防护"设置 -> 管理设置 -> 添加或删除排除项。
    pause
    start ms-settings:windowsdefender
)
echo.
pause
goto menu

:removeExclusion
echo.
echo --- 正在尝试移除 Windows Defender 排除项... ---
powershell -NoProfile -ExecutionPolicy Bypass -Command "Remove-MpPreference -ExclusionPath '%CurrentFolder%'"
if !errorlevel! equ 0 (
    echo.
    echo [成功] 已从 Windows Defender 排除列表移除文件夹 "%CurrentFolder%"。
) else (
    echo.
    echo [失败] 无法自动移除排除项或该路径原本就不在排除列表中。
    echo [提示] 将为您打开 Windows 安全中心，请手动检查并移除。
    echo        路径 -> 病毒和威胁防护 -> "病毒和威胁防护"设置 -> 管理设置 -> 添加或删除排除项。
    pause
    start ms-settings:windowsdefender
)
echo.
pause
goto menu

:addStartup
echo.
if not exist "%TargetFullPath%" (
    echo [错误] 在当前目录下未找到 "%TargetFileName%" 文件，无法创建启动项。
    pause
    goto menu
)
echo --- 正在尝试创建开机启动任务... ---
pause
:: 优先使用PowerShell创建计划任务，功能更全面
powershell -NoProfile -ExecutionPolicy Bypass -Command "$Action = New-ScheduledTaskAction -Execute '%TargetFullPath%' -WorkingDirectory '%CurrentFolder%'; $Trigger = New-ScheduledTaskTrigger -AtLogOn; $Principal = New-ScheduledTaskPrincipal -GroupId 'BUILTIN\Administrators' -RunLevel Highest; $Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Seconds 0); Register-ScheduledTask -TaskName '%TaskName%' -Action $Action -Trigger $Trigger -Principal $Principal -Settings $Settings -Description '以管理员身份启动 %TargetFileName%' -Force"
if !errorlevel! equ 0 (
    echo.
    echo [成功] 已创建计划任务 "%TaskName%"。
    echo        - 启动程序: "%TargetFileName%"
    echo        - 起始位置: "%CurrentFolder%"
    echo        - 运行方式: 用户登录时，以最高权限(管理员)运行
    echo        - 运行时间: 无限制
    pause
) else (
    echo [提示] PowerShell 方法失败，正在尝试使用传统的 schtasks 命令...
    pause
    :: PowerShell失败后的备用方案
    schtasks /create /tn "%TaskName%" /tr "\"%TargetFullPath%\"" /sc onlogon /rl highest /f
    if !errorlevel! equ 0 (
        echo.
        echo [成功] 已通过 schtasks 创建计划任务 "%TaskName%"。
        echo        注意：schtasks 无法直接设置工作目录和取消时间限制，但通常不影响程序运行。
    ) else (
        echo.
        echo [失败] 两种自动设置开机启动的方法均失败。
        echo [提示] 将为您打开任务计划程序，请手动创建。
        echo        操作步骤:
        echo        1. 打开 "任务计划程序" -> 点击 "创建任务..."
        echo        2. [常规] 选项卡: 名称填写 "%TaskName%", 勾选 "使用最高权限运行"。
        echo        3. [触发器] 选项卡: 点击 "新建...", 开始任务选择 "登录时"。
        echo        4. [操作] 选项卡: 点击 "新建...", 程序或脚本填写 "%TargetFullPath%", 起始于(可选)填写 "%CurrentFolder%"。
        echo        5. [设置] 选项卡: 取消勾选 "如果运行时间超过以下值，则停止任务"。
        echo        6. 点击 "确定" 保存。
        pause
        taskschd.msc
    )
)
echo.
pause
goto menu

:removeStartup
echo.
echo --- 正在尝试删除开机启动任务... ---
:: 优先使用PowerShell删除
powershell -NoProfile -ExecutionPolicy Bypass -Command "Unregister-ScheduledTask -TaskName '%TaskName%' -Confirm:$false"
if !errorlevel! equ 0 (
    echo.
    echo [成功] 已删除名为 "%TaskName%" 的计划任务。
) else (
    echo [提示] PowerShell 方法失败，正在尝试使用传统的 schtasks 命令...
    :: PowerShell失败后的备用方案
    schtasks /delete /tn "%TaskName%" /f
    if !errorlevel! equ 0 (
        echo.
        echo [成功] 已通过 schtasks 删除名为 "%TaskName%" 的计划任务。
    ) else (
        echo.
        echo [失败] 无法自动删除计划任务，或该任务不存在。
        echo [提示] 将为您打开任务计划程序，请手动检查并删除。
        pause
        taskschd.msc
    )
)
echo.
pause
goto menu

:checkStatus
echo.
echo --- 正在检查当前状态... ---
echo.
echo [ Windows Defender 排除项检查 ]
powershell -NoProfile -ExecutionPolicy Bypass -Command "$exclusions = Get-MpPreference; if ($exclusions.ExclusionPath -contains '%CurrentFolder%') { Write-Host '状态: 当前文件夹已在排除列表中。' -ForegroundColor Green } else { Write-Host '状态: 当前文件夹不在排除列表中。' -ForegroundColor Yellow }"
echo.
echo [ 开机启动任务检查 ]
schtasks /query /tn "%TaskName%" >nul 2>&1
if !errorlevel! equ 0 (
    echo 状态: 找到名为 "%TaskName%" 的开机启动任务。
    echo ------------------ 任务详细信息 ------------------
    schtasks /query /tn "%TaskName%" /fo list /v
    echo ----------------------------------------------------
) else (
    echo 状态: 未找到名为 "%TaskName%" 的开机启动任务。
)
echo.
pause
goto menu