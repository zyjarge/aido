#!/usr/bin/env python3
import os
import sys
import json
import logging
import clipboard
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text
from chat_session import ChatSession

console = Console()

# 表情符号常量
INFO = "ℹ️ "
WARNING = "🚷"

def get_env_file_path():
    """获取环境文件的路径"""
    aido_home = os.environ.get('AIDO_HOME')
    if not aido_home:
        aido_home = os.path.dirname(os.path.abspath(__file__))
    
    env_file = os.path.join(aido_home, '.env.local')
    
    if not os.path.exists(env_file):
        logging.warning(f"配置文件不存在: {env_file}")
        with open(env_file, 'w') as f:
            f.write('# API服务配置\n')
            f.write('# DeepSeek API配置示例：\n')
            f.write('BASE_URL=https://api.deepseek.com/v1\n')
            f.write('MODEL_NAME=deepseek-chat\n')
            f.write('API_KEY=your_api_key_here\n\n')
            f.write('# SiliconFlow API配置示例：\n')
            f.write('# BASE_URL=https://api.siliconflow.com/v1\n')
            f.write('# MODEL_NAME=chatglm3-6b\n')
            f.write('# API_KEY=your_api_key_here\n\n')
            f.write('# 日志级别\n')
            f.write('LOG_LEVEL=CRITICAL\n')
        logging.warning(f"已创建默认配置文件，请设置你的 API 配置")
    
    return env_file

def load_env_config():
    """加载环境配置"""
    env_path = get_env_file_path()
    if os.path.exists(env_path):
        load_dotenv(env_path, override=True)
        return True
    return False

def setup_logging(level=None):
    """配置日志"""
    default_level = os.getenv('LOG_LEVEL', 'CRITICAL').upper()
    try:
        level = getattr(logging, default_level) if level is None else level
    except AttributeError:
        level = logging.CRITICAL
    
    logging.basicConfig(
        format='%(asctime)s - %(levelname)s - %(message)s',
        level=level,
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def handle_single_query(query):
    """处理单次查询"""
    chat = ChatSession()
    
    # 显示用户查询
    chat._display_message(query, is_user=True)
    
    # 添加用户查询到消息历史
    chat.messages.append({"role": "user", "content": query})
    
    # 获取AI响应
    response = chat._get_ai_response()
    
    # 尝试解析JSON并提取命令
    try:
        data = json.loads(response.strip())
        command = data.get('command', '')
        
        # 复制命令到剪贴板
        try:
            clipboard.copy(command)
            console.print(f"\n{INFO} [green]命令已复制到剪贴板[/green]")
        except Exception as e:
            logging.warning(f"复制到剪贴板失败: {str(e)}")
            console.print(f"\n{WARNING} [yellow]复制到剪贴板失败[/yellow]")
    except:
        pass
    
    # 显示AI响应
    chat._display_message(response)

def main():
    """主程序入口"""
    # 设置日志
    setup_logging()
    
    # 加载环境配置
    if not load_env_config():
        console.print("[bold red]错误：无法加载配置文件[/bold red]")
        return 1
    
    try:
        # 检查是否有命令行参数
        if len(sys.argv) > 1:
            # 单轮对话模式
            query = ' '.join(sys.argv[1:])
            handle_single_query(query)
        else:
            # 多轮对话模式
            chat_session = ChatSession()
            chat_session.start()
            
    except Exception as e:
        logging.error(f"程序运行错误: {str(e)}")
        console.print(f"[bold red]错误：{str(e)}[/bold red]")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
