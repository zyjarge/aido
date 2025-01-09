#!/usr/bin/env python3
import os
import sys
import json
import logging
import subprocess
from dotenv import load_dotenv
from openai import OpenAI
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich import print as rprint
import clipboard

console = Console()

# 表情符号常量
BOY = "👦"
ROBOT = "🤖"
INFO = "ℹ️ "
WARNING = "🚷"
ERROR = "❌"

def get_env_file_path():
    """获取环境文件的路径"""
    # 优先使用环境变量中的 AIDO_HOME
    aido_home = os.environ.get('AIDO_HOME')
    if not aido_home:
        # 如果环境变量未设置，使用脚本所在目录
        aido_home = os.path.dirname(os.path.abspath(__file__))
    
    env_file = os.path.join(aido_home, '.env.local')
    
    if not os.path.exists(env_file):
        logging.warning(f"配置文件不存在: {env_file}")
        # 创建默认配置
        with open(env_file, 'w') as f:
            f.write('LOG_LEVEL=INFO\n')
            f.write('# DEEPSEEK_API_KEY=your_api_key_here\n')
        logging.warning(f"已创建默认配置文件，请设置你的 API key")
    
    return env_file

def load_env_config():
    """加载环境配置"""
    env_path = get_env_file_path()
    if os.path.exists(env_path):
        load_dotenv(env_path, override=True)
        return True
    return False

def print_user_message(message):
    # 创建一个面板来展示用户请求
    panel = Panel(
        message,
        title=f"{BOY} 用户请求",
        title_align="left",
        border_style="blue",
        padding=(1, 2),
        expand=False
    )
    console.print("\n", panel)

def clean_command(command):
    """清理命令中的 markdown 语法和命令前缀"""
    # 移除代码块标记
    command = command.strip('`')
    
    # 移除语言标识
    if command.startswith(('bash:', 'zsh:', 'shell:')):
        command = command.split(':', 1)[1]
    
    # 移除多行代码块
    if command.startswith(('```', '~~~')):
        lines = command.split('\n')
        if len(lines) > 2:
            command = '\n'.join(lines[1:-1])
    
    # 移除命令前缀
    if command.startswith(('zsh ', '/bin/zsh ', 'bash ', '/bin/bash ')):
        command = ' '.join(command.split()[1:])
    
    return command.strip()

def print_ai_response(command, explanation=None):
    # 清理命令中的 markdown 语法
    clean_cmd = clean_command(command)
    
    # 复制到剪贴板
    try:
        clipboard.copy(clean_cmd)
        clipboard_status = f"{INFO} [green]命令已复制到剪贴板[/green]"
    except Exception as e:
        logging.warning(f"复制到剪贴板失败: {str(e)}")
        clipboard_status = f"{WARNING} [yellow]复制到剪贴板失败[/yellow]"
    
    # 创建命令部分的面板
    command_panel = Panel(
        Syntax(clean_cmd, "bash", theme="monokai", word_wrap=True),
        title=f"{ROBOT} AI建议命令",
        title_align="left",
        border_style="green",
        padding=(1, 2),
        expand=False
    )
    
    # 创建解释部分的面板（如果有）
    if explanation:
        explanation_panel = Panel(
            explanation,
            title=f"{ROBOT} 命令解释",
            title_align="left",
            border_style="blue",
            padding=(1, 2),
            expand=False
        )
        
        # 打印两个面板
        console.print("\n")
        console.print(command_panel)
        console.print("\n")
        console.print(explanation_panel)
    else:
        # 如果没有解释，只打印命令面板
        console.print("\n")
        console.print(command_panel)
    
    # 打印状态信息
    console.print("\n")
    console.print(clipboard_status)
    console.print(f"{INFO} [dim]提示：命令已经复制到剪贴板，可以直接粘贴使用[/dim]")

# 配置日志
def setup_logging(level=None):
    # 加载环境配置
    load_env_config()
    
    # 从环境变量获取日志级别
    default_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    
    # 如果没有指定level参数，使用环境变量中的设置
    if level is None:
        try:
            level = getattr(logging, default_level)
        except AttributeError:
            print(f"警告：无效的日志级别 {default_level}，使用 INFO")
            level = logging.INFO
    
    logging.basicConfig(
        format='%(asctime)s - %(levelname)s - %(message)s',
        level=level,
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    logging.debug(f"日志级别设置为: {logging.getLevelName(level)}")

def clean_json_string(text):
    """清理 API 返回的 JSON 字符串，移除 markdown 代码块标记"""
    # 移除开头的 ```json 或 ``` 标记
    if text.startswith('```'):
        # 找到第一个换行符
        first_newline = text.find('\n')
        if first_newline != -1:
            text = text[first_newline + 1:]
    
    # 移除结尾的 ``` 标记
    if text.rstrip().endswith('```'):
        text = text.rstrip()[:-3]
    
    return text.strip()

def get_command_suggestion(query):
    logging.debug(f"开始处理查询: {query}")
    
    # 每次执行都重新加载环境配置
    load_env_config()
    
    # 获取 API key
    api_key = os.getenv('DEEPSEEK_API_KEY')
    
    if not api_key:
        error_msg = "未找到 DEEPSEEK_API_KEY，请确保在 .env.local 文件中正确配置"
        logging.error(error_msg)
        raise Exception(error_msg)
    
    # 初始化 OpenAI 客户端
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com/v1"  # DeepSeek API 基础 URL
    )
    
    prompt = f"""将以下操作转换为命令：
    {query}
    
    要求：
    1. 返回格式为 JSON，包含两个字段：
       - command: 可执行的命令文本
       - explanation: 对命令的简短解释
    2. command 字段：
       - 不要添加任何markdown标记、代码块或其他格式
       - 不要添加命令提示符或shell前缀
       - 如果有多个命令，每行一个
    3. explanation 字段：
       - 用中文简明扼要地解释命令的作用
       - 如果有特殊参数，简单说明其含义
    4. 如果明确平台信息，请直接给出该平台的指令，如果没有平台信息，请给出通用的指令或者按平台分别给出。"""
    
    try:
        logging.debug("发送请求到 DeepSeek API")
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "system",
                    "content": "你是一个命令行专家。返回JSON格式的响应，包含命令(command)和解释(explanation)。"
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            stream=False
        )
        
        result = response.choices[0].message.content.strip()
        logging.debug(f"API 响应原始数据: {result}")
        
        # 清理 JSON 字符串
        cleaned_result = clean_json_string(result)
        logging.debug(f"清理后的 JSON 数据: {cleaned_result}")
        
        # 解析 JSON 响应
        try:
            parsed = json.loads(cleaned_result)
            if isinstance(parsed, dict) and 'command' in parsed:
                command = parsed.get('command', '').strip()
                explanation = parsed.get('explanation', '').strip()
                if not command:
                    raise ValueError("命令内容为空")
                return command, explanation
            else:
                # 如果返回的 JSON 格式不正确，尝试从整个响应中提取命令
                logging.warning("JSON 格式不符合预期，尝试提取命令")
                return result, None
        except json.JSONDecodeError as e:
            logging.warning(f"JSON 解析失败: {e}, 尝试直接返回响应内容")
            # 如果解析失败，假设返回的只是命令
            return result, None
            
    except Exception as e:
        logging.error(f"API 调用失败: {str(e)}")
        raise

def main():
    # 解析命令行参数
    debug_mode = '--debug' in sys.argv
    if debug_mode:
        sys.argv.remove('--debug')
        setup_logging(logging.DEBUG)
    else:
        setup_logging()  # 使用环境变量中的配置
    
    if len(sys.argv) < 2:
        console.print(f"\n{ERROR} [bold red]错误：参数不足[/bold red]")
        console.print(f"{INFO} 用法: aido [--debug] <你想执行的操作>")
        sys.exit(1)
    
    query = ' '.join(sys.argv[1:])
    logging.info(f"处理用户请求: {query}")
    
    # 打印用户请求
    print_user_message(query)
    
    try:
        command, explanation = get_command_suggestion(query)
        logging.info("获取到命令建议")
        logging.debug(f"命令: {command}")
        logging.debug(f"解释: {explanation}")
        # 打印 AI 响应
        print_ai_response(command, explanation)
        
    except Exception as e:
        console.print(f"\n{ERROR} [bold red]错误：{str(e)}[/bold red]")
        sys.exit(1)

if __name__ == "__main__":
    main()
