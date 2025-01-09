@echo off
setlocal enabledelayedexpansion

:: 颜色定义
set "GREEN=[32m"
set "YELLOW=[33m"
set "RED=[31m"
set "NC=[0m"

:: 获取脚本所在目录的绝对路径
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

:: 打印带颜色的信息函数
:info
echo %GREEN%[INFO]%NC% %*
exit /b

:warn
echo %YELLOW%[WARN]%NC% %*
exit /b

:error
echo %RED%[ERROR]%NC% %*
exit /b

:: 检查 Python 环境
:check_python
call :info "检查 Python 环境..."
python --version >nul 2>&1
if errorlevel 1 (
    call :error "Python 未安装"
    exit /b 1
)
exit /b 0

:: 创建并激活虚拟环境
:setup_venv
call :info "创建虚拟环境..."
python -m venv venv

:: 创建激活脚本的包装器
echo @echo off > activate_venv.bat
echo set "SCRIPT_DIR=%%~dp0" >> activate_venv.bat
echo call "%%SCRIPT_DIR%%venv\Scripts\activate.bat" >> activate_venv.bat

:: 激活虚拟环境
call venv\Scripts\activate.bat

call :info "安装依赖..."
python -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
exit /b 0

:: 创建启动器脚本
:create_launcher
set "launcher=%USERPROFILE%\AppData\Local\Microsoft\WindowsApps\aido.bat"
call :info "创建启动器脚本: %launcher%"

:: 创建启动器
(
    echo @echo off
    echo :: 获取真实的安装目录
    echo set "AIDO_HOME=%SCRIPT_DIR%"
    echo.
    echo :: 保存当前目录
    echo set "CURRENT_DIR=%%CD%%"
    echo.
    echo :: 切换到 AIDO 目录并激活虚拟环境
    echo cd /d "%%AIDO_HOME%%"
    echo call "%%AIDO_HOME%%venv\Scripts\activate.bat"
    echo.
    echo :: 设置环境变量
    echo set "AIDO_HOME=%%AIDO_HOME%%"
    echo.
    echo :: 执行 Python 脚本，并保持在当前目录
    echo cd /d "%%CURRENT_DIR%%"
    echo python "%%AIDO_HOME%%aido.py" %%*
    echo.
    echo :: 清理
    echo deactivate
) > "%launcher%"
exit /b 0

:: 检查配置文件
:setup_config
set "config_file=%SCRIPT_DIR%.env.local"

if not exist "%config_file%" (
    call :info "创建默认配置文件..."
    echo LOG_LEVEL=INFO> "%config_file%"
    echo # DEEPSEEK_API_KEY=your_api_key_here>> "%config_file%"
    call :warn "请记得在 %config_file% 中设置你的 DEEPSEEK_API_KEY"
)
exit /b 0

:: 主安装流程
:main
call :info "开始安装 aido..."

:: 检查 Python
call :check_python
if errorlevel 1 exit /b 1

:: 设置虚拟环境
call :setup_venv
if errorlevel 1 exit /b 1

:: 设置配置文件
call :setup_config
if errorlevel 1 exit /b 1

:: 创建启动器
call :create_launcher
if errorlevel 1 exit /b 1

:: 安装完成，显示信息
echo.
echo %GREEN%安装完成！%NC%
echo.
echo %GREEN%安装信息：%NC%
echo 程序目录: %SCRIPT_DIR%
echo 虚拟环境: %SCRIPT_DIR%venv
echo 配置文件: %SCRIPT_DIR%.env.local
echo 启动脚本: %USERPROFILE%\AppData\Local\Microsoft\WindowsApps\aido.bat
echo.
echo %GREEN%使用说明：%NC%
echo 1. 请确保在 .env.local 中设置了 DEEPSEEK_API_KEY
echo 2. 现在可以在任何目录使用 'aido' 命令了
echo 3. 示例: aido "查看当前目录下的文件"
echo.
echo %YELLOW%提示：%NC%
echo 如果需要直接使用 Python 环境，可以运行：
echo call %SCRIPT_DIR%activate_venv.bat

exit /b 0

:: 执行安装
call :main 