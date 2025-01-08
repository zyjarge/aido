#!/bin/bash

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 打印带颜色的信息
info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 检查 Python 环境
check_python() {
    info "检查 Python 环境..."
    if ! command -v python3 &> /dev/null; then
        error "Python3 未安装"
        exit 1
    fi
}

# 创建并激活虚拟环境
setup_venv() {
    info "创建虚拟环境..."
    python3 -m venv venv
    
    # 创建激活脚本的包装器
    cat > activate_venv.sh << 'EOL'
#!/bin/bash
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source "$SCRIPT_DIR/venv/bin/activate"
EOL
    chmod +x activate_venv.sh
    
    # 激活虚拟环境
    source venv/bin/activate
    
    info "安装依赖..."
    pip install --upgrade pip
    pip install -r requirements.txt
}

# 创建启动器脚本
create_launcher() {
    local launcher="/usr/local/bin/aido"
    
    info "创建启动器脚本: $launcher"
    
    # 创建启动器
    cat > "$launcher.tmp" << EOL
#!/bin/bash

# 获取真实的安装目录
AIDO_HOME="$SCRIPT_DIR"

# 保存当前目录
CURRENT_DIR="\$(pwd)"

# 切换到 AIDO 目录并激活虚拟环境
cd "\$AIDO_HOME"
source "\$AIDO_HOME/venv/bin/activate"

# 设置环境变量
export AIDO_HOME="\$AIDO_HOME"

# 执行 Python 脚本，并保持在当前目录
cd "\$CURRENT_DIR"
python "\$AIDO_HOME/aido.py" "\$@"

# 清理
deactivate
EOL

    # 使用 sudo 移动文件并设置权限
    sudo mv "$launcher.tmp" "$launcher"
    sudo chmod +x "$launcher"
}

# 检查配置文件
setup_config() {
    local config_file="$SCRIPT_DIR/.env.local"
    
    if [ ! -f "$config_file" ]; then
        info "创建默认配置文件..."
        echo "LOG_LEVEL=INFO" > "$config_file"
        echo "# DEEPSEEK_API_KEY=your_api_key_here" >> "$config_file"
        warn "请记得在 $config_file 中设置你的 DEEPSEEK_API_KEY"
    fi
    
    # 设置配置文件权限
    chmod 600 "$config_file"
}

# 主安装流程
main() {
    info "开始安装 aido..."
    
    # 检查 Python
    check_python
    
    # 设置虚拟环境
    setup_venv
    
    # 设置配置文件
    setup_config
    
    # 创建启动器
    create_launcher
    
    # 安装完成，显示信息
    echo -e "\n${GREEN}安装完成！${NC}"
    echo -e "\n${GREEN}安装信息：${NC}"
    echo "程序目录: $SCRIPT_DIR"
    echo "虚拟环境: $SCRIPT_DIR/venv"
    echo "配置文件: $SCRIPT_DIR/.env.local"
    echo "启动脚本: /usr/local/bin/aido"
    
    echo -e "\n${GREEN}使用说明：${NC}"
    echo "1. 请确保在 .env.local 中设置了 DEEPSEEK_API_KEY"
    echo "2. 现在可以在任何目录使用 'aido' 命令了"
    echo "3. 示例: aido '查看当前目录下的文件'"
    
    # 提示激活虚拟环境（如果需要直接使用 Python 环境）
    echo -e "\n${YELLOW}提示：${NC}"
    echo "如果需要直接使用 Python 环境，可以运行："
    echo "source $SCRIPT_DIR/activate_venv.sh"
}

# 执行安装
main 