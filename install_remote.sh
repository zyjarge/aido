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

# 检查系统类型
check_system() {
    info "检查系统环境..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
    elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        error "Windows 用户请使用 PowerShell 运行 install.bat"
        exit 1
    else
        error "不支持的操作系统: $OSTYPE"
        exit 1
    fi
}

# 检查必要的命令
check_requirements() {
    info "检查必要的命令..."
    local commands=("git" "python3" "pip3")
    
    for cmd in "${commands[@]}"; do
        if ! command -v $cmd &> /dev/null; then
            error "$cmd 未安装"
            case $cmd in
                "git")
                    if [[ "$OS" == "macos" ]]; then
                        warn "请运行: brew install git"
                    else
                        warn "请运行: sudo apt-get install git"
                    fi
                    ;;
                "python3"|"pip3")
                    if [[ "$OS" == "macos" ]]; then
                        warn "请运行: brew install python3"
                    else
                        warn "请运行: sudo apt-get install python3 python3-pip"
                    fi
                    ;;
            esac
            exit 1
        fi
    done
}

# 克隆仓库
clone_repo() {
    info "克隆 AIDO 仓库..."
    local install_dir="$HOME/.aido"
    
    if [ -d "$install_dir" ]; then
        warn "目录已存在: $install_dir"
        warn "正在备份旧文件..."
        mv "$install_dir" "${install_dir}.bak.$(date +%Y%m%d_%H%M%S)"
    fi
    
    git clone https://github.com/zyjarge/aido.git "$install_dir"
    if [ $? -ne 0 ]; then
        error "克隆仓库失败"
        exit 1
    fi
    
    cd "$install_dir"
}

# 主安装流程
main() {
    info "开始安装 AIDO..."
    
    # 检查系统
    check_system
    
    # 检查依赖
    check_requirements
    
    # 克隆仓库
    clone_repo
    
    # 运行本地安装脚本
    info "运行安装脚本..."
    if [[ "$OS" == "macos" || "$OS" == "linux" ]]; then
        chmod +x install.sh
        ./install.sh
    fi
    
    # 安装完成
    echo -e "\n${GREEN}AIDO 安装完成！${NC}"
    echo -e "\n${GREEN}使用说明：${NC}"
    echo "1. 编辑 ~/.aido/.env.local 文件，设置你的 DEEPSEEK_API_KEY"
    echo "2. 运行 'aido \"你的命令\"' 开始使用"
    echo "3. 示例: aido \"查看当前目录下的文件\""
}

# 执行安装
main 