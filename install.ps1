# Save this file with UTF-8 with BOM encoding
$Colors = @{
    Red    = 'Red'
    Green  = 'Green'
    Yellow = 'Yellow'
    Reset  = 'White'
}

function Write-Info($message) {
    Write-Host "[INFO] $message" -ForegroundColor $Colors.Green
}

function Write-Warn($message) {
    Write-Host "[WARN] $message" -ForegroundColor $Colors.Yellow
}

function Write-Error($message) {
    Write-Host "[ERROR] $message" -ForegroundColor $Colors.Red
}

$SCRIPT_DIR = $PSScriptRoot
Set-Location $SCRIPT_DIR

function Check-Python {
    Write-Info "Checking Python environment..."
    if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
        Write-Error "Python3 is not installed"
        exit 1
    }
}

function Setup-Venv {
    Write-Info "Creating virtual environment..."
    
    try {
        # 检查是否已存在虚拟环境
        if (Test-Path "venv") {
            Write-Warn "Virtual environment already exists. Removing..."
            Remove-Item -Recurse -Force "venv"
        }
        
        # 检查 Python venv 模块
        Write-Info "Checking venv module..."
        python -c "import venv" 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Python venv module not available. Please install it first."
            exit 1
        }
        
        # 创建虚拟环境并捕获输出
        $output = python -m venv venv 2>&1
        Write-Info "Virtual environment creation output: $output"
        
        # 等待虚拟环境创建完成
        Write-Info "Waiting for virtual environment to be ready..."
        Start-Sleep -Seconds 2
        
        # 检查虚拟环境是否创建成功
        if (-not (Test-Path "$SCRIPT_DIR\venv\Scripts\python.exe")) {
            Write-Error "Virtual environment creation failed: python.exe not found in venv\Scripts"
            exit 1
        }
        
        if (-not (Test-Path "$SCRIPT_DIR\venv\Scripts\Activate.ps1")) {
            Write-Error "Virtual environment creation failed: Activate.ps1 not found in venv\Scripts"
            exit 1
        }
        
        Write-Info "Activating virtual environment..."
        & "$SCRIPT_DIR\venv\Scripts\Activate.ps1"
        
        if (-not $env:VIRTUAL_ENV) {
            Write-Error "Virtual environment activation failed!"
            exit 1
        }
        
        Write-Info "Installing dependencies..."
        # 使用完整路径调用 pip
        & "$SCRIPT_DIR\venv\Scripts\python.exe" -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple
        
        if (Test-Path "requirements.txt") {
            & "$SCRIPT_DIR\venv\Scripts\python.exe" -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
        } else {
            Write-Error "requirements.txt not found!"
            exit 1
        }
    }
    catch {
        Write-Error "An error occurred during virtual environment setup: $_"
        Write-Error $_.Exception.Message
        exit 1
    }
}

function Create-Launcher {
    $launcher = "$env:LOCALAPPDATA\Microsoft\WindowsApps\aido.ps1"
    
    Write-Info "Creating launcher script: $launcher"
    
    $launcherContent = @"
# Get real installation directory
`$AIDO_HOME = "$SCRIPT_DIR"

# Save current directory
`$CURRENT_DIR = Get-Location

# Switch to AIDO directory and activate virtual environment
Set-Location "`$AIDO_HOME"
& "`$AIDO_HOME\venv\Scripts\Activate.ps1"

# Set environment variables
`$env:AIDO_HOME = "`$AIDO_HOME"

# Execute Python script while maintaining current directory
Set-Location "`$CURRENT_DIR"
python "`$AIDO_HOME\aido.py" `$args

# Cleanup
deactivate
"@

    if ($PSVersionTable.PSVersion.Major -ge 6) {
        $launcherContent | Out-File -FilePath $launcher -Encoding utf8
    } else {
        $launcherContent | Out-File -FilePath $launcher -Encoding UTF8
    }
}

function Setup-Config {
    $config_file = Join-Path $SCRIPT_DIR ".env.local"
    
    if (-not (Test-Path $config_file)) {
        Write-Info "Creating default configuration file..."
        $configContent = @"
LOG_LEVEL=INFO
# DEEPSEEK_API_KEY=your_api_key_here
"@
        if ($PSVersionTable.PSVersion.Major -ge 6) {
            $configContent | Out-File -FilePath $config_file -Encoding utf8
        } else {
            $configContent | Out-File -FilePath $config_file -Encoding UTF8
        }
        Write-Warn "Please remember to set your DEEPSEEK_API_KEY in $config_file"
    }
    
    $acl = Get-Acl $config_file
    $acl.SetAccessRuleProtection($true, $false)
    $rule = New-Object System.Security.AccessControl.FileSystemAccessRule($env:USERNAME, "FullControl", "Allow")
    $acl.AddAccessRule($rule)
    Set-Acl $config_file $acl
}

function Main {
    Write-Info "Starting installation of aido..."
    
    Check-Python
    Setup-Venv
    Setup-Config
    Create-Launcher
    
    Write-Host "`nInstallation completed!" -ForegroundColor $Colors.Green
    Write-Host "`nInstallation information:" -ForegroundColor $Colors.Green
    Write-Host "Program directory: $SCRIPT_DIR"
    Write-Host "Virtual environment: $SCRIPT_DIR\venv"
    Write-Host "Configuration file: $SCRIPT_DIR\.env.local"
    Write-Host "Launcher script: $env:LOCALAPPDATA\Microsoft\WindowsApps\aido.ps1"
    
    Write-Host "`nUsage instructions:" -ForegroundColor $Colors.Green
    Write-Host "1. Please ensure DEEPSEEK_API_KEY is set in .env.local"
    Write-Host "2. You can now use 'aido' command in any directory"
    Write-Host "3. Example: aido 'list files in current directory'"
    
    Write-Host "`nNote:" -ForegroundColor $Colors.Yellow
    Write-Host "If you need to directly use Python environment, you can run:"
    Write-Host ". $SCRIPT_DIR\activate_venv.ps1"
}

Main
