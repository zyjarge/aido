#!/usr/bin/env python3
import os
import sys
import logging
import time
import json
import random
from openai import OpenAI
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.align import Align
from rich.text import Text
from rich.style import Style
from rich.spinner import Spinner
from prompt_toolkit import prompt
from prompt_toolkit.styles import Style as PromptStyle

class ChatSession:
    def __init__(self):
        """初始化聊天会话"""
        self.console = Console()
        self.messages = [
            {
                "role": "system",
                "content": """你是一个命令行专家，专门帮助用户解决各种命令行操作问题。请遵循以下规则：

1. 仔细理解用户的意图，确保给出的命令准确解决用户的问题
2. 返回JSON格式的响应，包含两个字段：command和explanation
3. command字段：
   - 提供准确的命令行指令
   - 如果有多个可用命令，可以提供多个JSON响应
   - 优先考虑通用性高的命令
   - 确保命令的正确性和安全性
4. explanation字段：
   - 必须使用中文解释命令的作用，除非用户明确要求使用其他语言
   - 解释要简明扼要，包含关键参数的含义
   - 如果命令有潜在风险，要说明注意事项
5. 根据用户的操作系统（Windows/MacOS/Linux）给出适合的命令
6. 确保JSON格式的正确性，不要添加额外的markdown标记"""
            }
        ]
        self.terminal_width = self.console.width
        self._init_client()
        self.thinking_messages = [
            "容我三思...",
            "让我想想...",
            "稍等我想一下...",
            "思考中...",
            "正在组织语言...",
            "让我帮你找找...",
            "正在查找最佳方案..."
        ]
        # 设置prompt_toolkit样式
        self.prompt_style = PromptStyle.from_dict({
            'prompt': 'bold #0000FF',  # 蓝色粗体
            'input': '#FFFFFF',        # 白色输入文本
        })

    def _init_client(self):
        """初始化DeepSeek API客户端"""
        api_key = os.getenv('DEEPSEEK_API_KEY')
        if not api_key:
            raise Exception("未找到 DEEPSEEK_API_KEY，请确保在 .env.local 文件中正确配置")
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com/v1"
        )

    def _format_ai_message(self, message):
        """格式化AI消息"""
        # 去除可能的markdown代码块标记
        message = message.strip()
        
        # 分离出所有的JSON块
        json_blocks = []
        current_block = ""
        lines = message.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('```'):
                if current_block:  # 结束当前块
                    json_blocks.append(current_block.strip())
                    current_block = ""
                continue
            current_block += line + "\n"
        if current_block:  # 添加最后一个块
            json_blocks.append(current_block.strip())
        
        # 创建格式化的文本
        formatted_text = Text()
        
        # 处理每个JSON块
        for i, block in enumerate(json_blocks):
            try:
                # 尝试解析JSON
                data = json.loads(block)
                command = data.get('command', '')
                explanation = data.get('explanation', '')
                
                # 如果有多个命令，添加分隔符
                if i > 0:
                    formatted_text.append("\n\n" + "="*40 + "\n\n", style="dim")
                
                # 添加格式化的内容
                formatted_text.append("【建议命令】\n", style="bold yellow")
                formatted_text.append(f"{command}\n\n", style="bold white")
                formatted_text.append("【解释】\n", style="bold yellow")
                formatted_text.append(explanation, style="white")
            except json.JSONDecodeError:
                # 如果解析失败，添加原始内容
                if block.strip():
                    formatted_text.append(block)
        
        return formatted_text if formatted_text.plain else Text(message)

    def _create_message_panel(self, content, is_user=False):
        """创建消息面板"""
        # 计算消息面板的宽度（终端宽度的70%）
        panel_width = min(int(self.terminal_width * 0.7), 100)
        
        # 设置消息的样式和对齐方式
        align = "right" if is_user else "left"
        style = Style(color="white") if is_user else Style(color="white", bgcolor="green")
        emoji = "🙎" if is_user else "😄"
        timestamp = time.strftime("%H:%M:%S")
        
        # 如果是用户消息，使用普通文本；如果是AI消息，格式化内容
        if is_user:
            text = Text(content)
            text.style = style
        else:
            text = self._format_ai_message(content)
        
        # 创建面板
        return Panel(
            Align(text, align=align),
            title=f"{emoji} {timestamp} {emoji}",
            title_align=align,
            border_style="blue" if is_user else "green",
            padding=(1, 2),
            width=panel_width
        )

    def _display_message(self, content, is_user=False):
        """显示消息"""
        panel = self._create_message_panel(content, is_user)
        # 根据是用户还是AI消息，调整显示位置
        if is_user:
            self.console.print(Align(panel, align="right"))
        else:
            self.console.print(Align(panel, align="left"))
        self.console.print("")  # 添加空行

    def _get_ai_response(self):
        """获取AI响应"""
        # 随机选择一个思考消息
        thinking_msg = random.choice(self.thinking_messages)
        spinner = Spinner("dots2", style="green")
        
        # 显示思考中的状态
        with Live(spinner, refresh_per_second=10) as live:
            live.update(Text(f"{thinking_msg}", style="bold green"))
            
            # 获取AI响应
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=self.messages,
                temperature=0.3,
                stream=False
            )
            
            return response.choices[0].message.content

    def start(self):
        """启动聊天会话"""
        try:
            self.console.clear()
            # 创建更醒目的欢迎标题
            welcome_text = Text("欢迎使用 AIDO 聊天助手！", style="bold white on blue")
            welcome_panel = Panel(
                Align(welcome_text, "center"),
                border_style="blue",
                padding=(1, 2)
            )
            self.console.print(welcome_panel)
            self.console.print("[dim]提示：按 Ctrl+C 结束对话[/dim]\n")

            while True:
                try:
                    # 使用prompt_toolkit获取用户输入
                    user_input = prompt(
                        '请输入您的问题：',
                        style=self.prompt_style,
                        multiline=False,  # 单行输入模式
                    )
                    
                    if not user_input.strip():
                        continue
                    
                    # 显示用户消息
                    self._display_message(user_input, is_user=True)
                    
                    # 更新消息历史
                    self.messages.append({"role": "user", "content": user_input})
                    
                    # 获取并显示AI响应
                    ai_message = self._get_ai_response()
                    self._display_message(ai_message)
                    self.messages.append({"role": "assistant", "content": ai_message})

                except Exception as e:
                    logging.error(f"处理消息时出错: {str(e)}")
                    error_text = Text(f"错误：{str(e)}", style="bold red")
                    self.console.print(error_text)

        except KeyboardInterrupt:
            # 处理Ctrl+C退出
            self.console.print("\n\n")
            farewell_text = Text("正在结束对话...", style="bold yellow")
            self.console.print(farewell_text)
            
            try:
                # 发送告别消息
                response = self.client.chat.completions.create(
                    model="deepseek-chat",
                    messages=self.messages + [{"role": "user", "content": "再见，谢谢你的帮助！"}],
                    temperature=0.3,
                    stream=False
                )
                farewell_msg = response.choices[0].message.content
                self._display_message(farewell_msg)
            except:
                self._display_message("感谢使用AIDO，再见！")
            sys.exit(0) 