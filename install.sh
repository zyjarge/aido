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

# 设置安装目录
INSTALL_DIR="$HOME/aido"
REPO_URL="https://github.com/zyjarge/aido.git"

# 检查依赖
check_dependencies() {
    info "检查依赖..."
    local missing_deps=()
    local need_apt_update=false
    
    if ! command -v git &> /dev/null; then
        missing_deps+=("git")
        need_apt_update=true
    fi
    
    if ! command -v python3 &> /dev/null; then
        missing_deps+=("python3")
        need_apt_update=true
    fi

    # 检查 python3-venv
    if ! python3 -c "import venv" &> /dev/null; then
        missing_deps+=("python3-venv")
        need_apt_update=true
    fi
    
    # 如果有缺失的依赖
    if [ ${#missing_deps[@]} -ne 0 ]; then
        if [ -f "/etc/debian_version" ] || [ -f "/etc/lsb-release" ]; then
            # Debian/Ubuntu 系统
            warn "以下依赖未安装: ${missing_deps[*]}"
            info "尝试自动安装依赖..."
            
            if [ "$need_apt_update" = true ]; then
                if ! sudo apt-get update; then
                    error "更新软件源失败，请手动安装依赖"
                    exit 1
                fi
            fi
            
            if ! sudo apt-get install -y "${missing_deps[@]}"; then
                error "安装依赖失败，请手动安装：${missing_deps[*]}"
                exit 1
            fi
        else
            # 其他系统
            error "以下依赖未安装: ${missing_deps[*]}"
            error "请先安装这些依赖后再运行安装脚本"
            exit 1
        fi
    fi
}

# 准备用户目录
prepare_user_dirs() {
    info "准备用户目录..."
    
    # 创建 ~/.local 和 ~/.local/bin 目录（如果不存在）
    mkdir -p "$HOME/.local/bin"
    
    # 确保目录权限正确
    chmod 755 "$HOME/.local"
    chmod 755 "$HOME/.local/bin"
    
    # 检查目录是否创建成功
    if [ ! -d "$HOME/.local/bin" ]; then
        error "无法创建必要的目录结构"
        exit 1
    fi
}

# 准备安装目录
prepare_install_dir() {
    info "准备安装目录..."
    # 如果存在旧的安装，先清理
    if [ -L "$HOME/.local/bin/aido" ]; then
        info "清理旧的安装..."
        rm -f "$HOME/.local/bin/aido"
    fi
    
    if [ -d "$INSTALL_DIR" ]; then
        warn "目录 $INSTALL_DIR 已存在，将备份为 ${INSTALL_DIR}.bak"
        mv "$INSTALL_DIR" "${INSTALL_DIR}.bak"
    fi
    
    info "克隆项目仓库..."
    if ! git clone "$REPO_URL" "$INSTALL_DIR"; then
        error "克隆仓库失败"
        exit 1
    fi
    
    cd "$INSTALL_DIR" || exit 1
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
    # 检查网络连接
    if ping -c 1 pypi.tuna.tsinghua.edu.cn &> /dev/null; then
        PIP_MIRROR="-i https://pypi.tuna.tsinghua.edu.cn/simple"
    else
        warn "无法连接到清华镜像源，将使用默认源"
        PIP_MIRROR=""
    fi
    
    pip install --upgrade pip $PIP_MIRROR
    pip install -r requirements.txt $PIP_MIRROR
}

# 创建启动器脚本
create_launcher() {
    local bin_dir="$HOME/.local/bin"
    local launcher="$bin_dir/aido"
    
    # 检查目录权限
    if [ ! -w "$HOME/.local" ] || ([ -d "$bin_dir" ] && [ ! -w "$bin_dir" ]); then
        error "没有写入 ~/.local/bin 的权限"
        exit 1
    fi
    
    info "创建启动器脚本: $launcher"
    
    # 创建 bin 目录（如果不存在）
    mkdir -p "$bin_dir"
    
    # 创建启动器
    cat > "$launcher" << EOL
#!/bin/bash

# 获取真实的安装目录
AIDO_HOME="$INSTALL_DIR"

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

    # 设置执行权限
    chmod +x "$launcher"
    
    # 检查 PATH 中是否包含 ~/.local/bin
    if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
        warn "请将 ~/.local/bin 添加到你的 PATH 环境变量中"
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.zshrc"
    fi
}

# 检查配置文件
setup_config() {
    local config_file="$INSTALL_DIR/.env.local"
    
    if [ ! -f "$config_file" ]; then
        info "创建默认配置文件..."
        cat > "$config_file" << EOL
# API服务配置
# DeepSeek API配置示例：
BASE_URL=https://api.deepseek.com/v1
MODEL_NAME=deepseek-chat
API_KEY=your_api_key_here

# SiliconFlow API配置示例：
# BASE_URL=https://api.siliconflow.com/v1
# MODEL_NAME=chatglm3-6b
# API_KEY=your_api_key_here

# 日志级别：DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL=CRITICAL
EOL
        warn "请记得在 $config_file 中设置你的 API 配置"
    fi
    
    # 设置配置文件权限
    chmod 600 "$config_file"
}

# 主安装流程
main() {
    info "开始安装 aido..."
    
    # 检查依赖
    check_dependencies
    
    # 准备用户目录
    prepare_user_dirs
    
    # 准备安装目录
    prepare_install_dir
    
    # 设置虚拟环境
    setup_venv
    
    # 设置配置文件
    setup_config
    
    # 创建启动器
    create_launcher
    
    # 安装完成，显示信息
    echo -e "\n${GREEN}安装完成！${NC}"
    echo -e "\n${GREEN}安装信息：${NC}"
    echo "程序目录: $INSTALL_DIR"
    echo "虚拟环境: $INSTALL_DIR/venv"
    echo "配置文件: $INSTALL_DIR/.env.local"
    echo "启动脚本: $HOME/.local/bin/aido"
    
    echo -e "\n${GREEN}使用说明：${NC}"
    echo "1. 请在 .env.local 中配置以下信息："
    echo "   - BASE_URL: API服务地址"
    echo "   - MODEL_NAME: 使用的模型名称"
    echo "   - API_KEY: API密钥"
    echo "2. 如果命令 'aido' 无法运行，请重新打开终端或运行："
    echo "   source ~/.bashrc 或 source ~/.zshrc"
    echo "3. 现在可以在任何目录使用 'aido' 命令了"
    echo "4. 示例: aido '查看当前目录下的文件'"
    
    # 提示激活虚拟环境（如果需要直接使用 Python 环境）
    echo -e "\n${YELLOW}提示：${NC}"
    echo "如果需要直接使用 Python 环境，可以运行："
    echo "source $INSTALL_DIR/activate_venv.sh"
}

# 执行安装
main 