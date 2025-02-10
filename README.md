# AIDO - AI-Powered Command Line Assistant

AIDO 是一个基于 AI 的命令行助手，它可以将自然语言转换为命令行指令。

## 开发动机

在日常开发过程中，我们经常需要：
- 在浏览器中打开 AI 网站查询命令
- 在不同窗口间切换复制粘贴
- 重复查询一些常用但不容易记住的命令
- 部分灵感来自于 [《AI帮你赢：人人都能用的AI方法论》](https://book.douban.com/subject/37152637/)

AIDO 直接集成在终端中，让你可以：
- 直接在终端中用自然语言获取命令
- 自动复制命令到剪贴板
- 获取命令的中文解释
- 支持单轮查询和多轮对话两种模式
- 减少在不同窗口间切换的时间

## 安装方法

### 前置要求
- Python 3.8 或更高版本
- Git（用于克隆仓库）
- 支持的 API 服务之一：
  - [DeepSeek](https://platform.deepseek.com/)
  - [SiliconFlow](https://docs.siliconflow.cn/)
- curl（用于安装脚本）

### 快速安装（推荐）

使用以下命令一键安装：

```bash
# MacOS/Linux
curl -fsSL https://raw.githubusercontent.com/zyjarge/aido/master/install.sh | bash

# Windows (在管理员权限的 PowerShell 中运行)
Set-ExecutionPolicy RemoteSigned -Scope Process
iwr -useb https://raw.githubusercontent.com/zyjarge/aido/master/install.ps1 | iex
```

安装脚本会自动完成以下操作：
- 检查 Python 环境
- 创建虚拟环境
- 安装所需依赖（使用清华大学镜像源加速）
- 创建配置文件
- 设置启动器

安装完成后，你需要：
1. 编辑 `.env.local` 文件，配置以下信息：
   - `BASE_URL`: API 服务地址
   - `MODEL_NAME`: 使用的模型名称
   - `API_KEY`: API 密钥
2. 现在可以在任何目录使用 `aido` 命令了

## 配置说明

在 `.env.local` 文件中可以配置：

### DeepSeek API 配置示例
```bash
BASE_URL=https://api.deepseek.com/v1
MODEL_NAME=deepseek-chat
API_KEY=your_api_key_here
```

### SiliconFlow API 配置示例
```bash
BASE_URL=https://api.siliconflow.com/v1
MODEL_NAME=chatglm3-6b
API_KEY=your_api_key_here
```

### 其他配置
```bash
# 日志级别：DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL=CRITICAL
```

## 支持的 API 服务

AIDO 目前支持以下 API 服务：

### 1. DeepSeek API
- 官网：https://platform.deepseek.com
- 特点：稳定性好，响应速度快
- 默认模型：deepseek-chat

### 2. SiliconFlow API
- 官网：https://docs.siliconflow.cn
- 特点：支持模型多，本地部署快
- 可用模型：
  - chatglm3-6b
  - qwen-7b-chat
  - baichuan2-13b
  等

## 使用方法

AIDO 支持两种使用模式：

### 1. 单轮查询模式
适合快速查询单个命令：
```bash
# 直接跟随查询内容
aido 查看系统内存使用情况
aido 如何查找大文件
aido 统计当前目录下的文件数量
```

### 2. 多轮对话模式
适合需要连续交互或复杂问题：
```bash
# 直接启动，进入交互模式
aido
```
- 使用 `>>>` 提示符输入问题
- 支持连续对话，保持上下文
- 按 Ctrl+C 结束对话

### 使用示例

1. 单轮查询示例：
```bash
# 系统信息查询
aido 显示系统内存使用情况
aido 查看CPU使用率最高的进程

# 文件操作
aido 查找当前目录下所有的jpg文件
aido 查找大于100MB的文件

# 网络操作
aido 测试与google.com的连接延迟
aido 查看本机IP地址
```

2. 多轮对话示例：
```bash
$ aido
欢迎使用 AIDO 聊天助手！
>>> 如何压缩文件？
【建议命令】tar -czf archive.tar.gz files/
【解释】使用tar命令压缩文件，-c创建新档案，-z使用gzip压缩，-f指定档案文件名

>>> 如何解压这个文件？
【建议命令】tar -xzf archive.tar.gz
【解释】解压tar.gz文件，-x表示解压，-z使用gzip解压，-f指定要解压的文件
```

### 特点
- 支持单轮查询和多轮对话两种模式
- 命令会自动复制到剪贴板
- 提供命令的中文解释
- 支持复杂的命令组合
- 适配 MacOS/Linux/Windows 环境
- 优雅的界面展示
- 智能的上下文理解

## 注意事项

1. 需要有效的 DeepSeek API key
2. 建议在执行命令前仔细检查 AI 生成的命令
3. 某些命令可能需要 root/管理员权限
4. Windows 环境下部分命令可能不适用
5. 在多轮对话模式中，可以随时使用 Ctrl+C 优雅退出

## 贡献

欢迎提交 Issue 和 Pull Request！

## 卸载方法

如果你想卸载 AIDO，可以按照以下步骤操作：

```bash
# 运行卸载命令
rm -f ~/.local/bin/aido && rm -rf ~/aido
```

3. 清理环境变量（可选）：
- 如果你不再需要 `~/.local/bin` 目录用于其他程序，可以从 PATH 中移除：
- 编辑 `~/.bashrc` 或 `~/.zshrc`，删除以下行：
```bash
export PATH="$HOME/.local/bin:$PATH"
```
- 然后重新加载配置：
```bash
source ~/.bashrc  # 或 source ~/.zshrc
```

卸载完成后，所有 AIDO 相关的文件和配置都会被清除。如果你之后想重新安装，可以重新运行安装命令。

## 许可证

MIT License 