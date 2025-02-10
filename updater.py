#!/usr/bin/env python3
import os
import sys
import json
import time
import shutil
import logging
import tempfile
import requests
from typing import Optional, Dict, Tuple
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.markdown import Markdown
from config_merger import ConfigMerger
from datetime import datetime

class UpdateManager:
    def __init__(self):
        """初始化更新管理器"""
        self.console = Console()
        self.logger = logging.getLogger(__name__)
        self.aido_home = os.environ.get('AIDO_HOME') or os.path.dirname(os.path.abspath(__file__))
        self.check_file = os.path.join(self.aido_home, '.last_check')
        self.current_version = self._get_current_version()
        self.github_api = "https://api.github.com/repos/zyjarge/aido"
        self.check_interval = 24 * 60 * 60  # 24小时的秒数
        self.github_api_url = "https://api.github.com/repos/zyjarge/aido/releases/latest"  # 需要替换为实际的仓库地址

    def _get_current_version(self) -> str:
        """获取当前版本"""
        version_file = os.path.join(self.aido_home, 'VERSION')
        try:
            with open(version_file, 'r') as f:
                return f.read().strip()
        except FileNotFoundError:
            return "v0.0.0"

    def should_check_update(self) -> bool:
        """检查是否需要更新"""
        # 如果没有检查记录，需要检查
        if not os.path.exists(self.check_file):
            return True

        try:
            with open(self.check_file, 'r') as f:
                last_check = float(f.read().strip())
            # 24小时检查一次
            return time.time() - last_check > self.check_interval
        except:
            return True

    def _update_check_time(self):
        """更新检查时间"""
        with open(self.check_file, 'w') as f:
            f.write(str(time.time()))

    def get_latest_version(self) -> Optional[Dict]:
        """获取最新版本信息"""
        try:
            response = requests.get(self.github_api_url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return {
                    'version': data['tag_name'],
                    'description': data['body'],
                    'download_url': data['zipball_url']
                }
        except Exception as e:
            self.logger.warning(f"获取最新版本信息失败: {e}")
        return None

    def download_update(self, url: str, target_dir: str) -> bool:
        """下载更新"""
        try:
            with Progress() as progress:
                task = progress.add_task("[cyan]下载更新...", total=None)
                
                response = requests.get(url, stream=True)
                total = int(response.headers.get('content-length', 0))
                progress.update(task, total=total)
                
                # 下载到临时文件
                with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            tmp_file.write(chunk)
                            progress.update(task, advance=len(chunk))
                
                # 解压更新
                shutil.unpack_archive(tmp_file.name, target_dir)
                os.unlink(tmp_file.name)
                return True
        except Exception as e:
            self.logger.error(f"下载更新失败: {e}")
            return False

    def backup_current_version(self) -> Optional[str]:
        """备份当前版本"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_dir = os.path.join(self.aido_home, f"backup_{timestamp}")
            shutil.copytree(self.aido_home, backup_dir, ignore=shutil.ignore_patterns('backup_*', '.git', '__pycache__', '*.pyc'))
            return backup_dir
        except Exception as e:
            self.logger.error(f"备份失败: {e}")
            return None

    def update_config(self, new_version_dir: str) -> bool:
        """更新配置文件"""
        try:
            local_config = os.path.join(self.aido_home, '.env.local')
            example_config = os.path.join(new_version_dir, '.env.local.example')
            
            merger = ConfigMerger(local_config, example_config)
            return merger.update_config()
        except Exception as e:
            self.logger.error(f"更新配置文件失败: {e}")
            return False

    def apply_update(self, new_version_dir: str) -> bool:
        """应用更新"""
        try:
            # 复制新文件
            for item in os.listdir(new_version_dir):
                source = os.path.join(new_version_dir, item)
                target = os.path.join(self.aido_home, item)
                
                if item == '.env.local.example':  # 跳过示例配置文件
                    continue
                    
                if os.path.isdir(source):
                    shutil.copytree(source, target, dirs_exist_ok=True)
                else:
                    shutil.copy2(source, target)
            
            return True
        except Exception as e:
            self.logger.error(f"应用更新失败: {e}")
            return False

    def check_update(self) -> Tuple[bool, str]:
        """检查更新
        
        Returns:
            (是否有更新, 提示信息)
        """
        if not self.should_check_update():
            return False, ""

        self._update_check_time()
        latest = self.get_latest_version()
        
        if not latest:
            return False, "检查更新失败"
            
        if latest['version'] <= self.current_version:
            return False, f"当前版本 {self.current_version} 已是最新"
            
        return True, f"""发现新版本！
当前版本：{self.current_version}
最新版本：{latest['version']}

更新内容：
{latest['description']}"""

    def update(self) -> bool:
        """执行更新"""
        try:
            # 获取最新版本信息
            latest = self.get_latest_version()
            if not latest:
                return False

            # 创建临时目录
            with tempfile.TemporaryDirectory() as temp_dir:
                # 下载更新
                if not self.download_update(latest['download_url'], temp_dir):
                    return False

                # 备份当前版本
                backup_dir = self.backup_current_version()
                if not backup_dir:
                    return False

                # 更新配置文件
                if not self.update_config(temp_dir):
                    return False

                # 应用更新
                if not self.apply_update(temp_dir):
                    # 如果更新失败，尝试恢复备份
                    self.logger.warning("更新失败，正在恢复备份...")
                    shutil.rmtree(self.aido_home)
                    shutil.copytree(backup_dir, self.aido_home)
                    return False

            self.console.print("[green]更新完成！[/green]")
            return True

        except Exception as e:
            self.logger.error(f"更新失败: {e}")
            return False

    def _get_last_check_time(self):
        """获取上次检查更新的时间"""
        if os.path.exists(self.check_file):
            with open(self.check_file, 'r') as f:
                return float(f.read().strip())
        return 0
        
    def _update_last_check_time(self):
        """更新检查时间"""
        with open(self.check_file, 'w') as f:
            f.write(str(time.time()))
            
    def _create_backup(self):
        """创建带时间戳的备份"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = f"aido.bak_{timestamp}"
        shutil.copytree(self.aido_home, backup_dir, ignore=shutil.ignore_patterns('*.bak_*'))
        return backup_dir
        
    def _clean_old_backups(self):
        """清理所有旧的备份"""
        current_dir = os.path.dirname(self.aido_home)
        for item in os.listdir(current_dir):
            if item.startswith('aido.bak_'):
                backup_path = os.path.join(current_dir, item)
                shutil.rmtree(backup_path)
                
    def perform_update(self, latest_version):
        """执行更新操作"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
        ) as progress:
            # 1. 创建备份
            backup_task = progress.add_task("[cyan]创建备份...", total=1)
            backup_dir = self._create_backup()
            progress.update(backup_task, completed=1)
            
            # 2. 下载新版本
            download_task = progress.add_task("[cyan]下载新版本...", total=1)
            # TODO: 实现下载逻辑
            progress.update(download_task, completed=1)
            
            # 3. 安装新版本
            install_task = progress.add_task("[cyan]安装新版本...", total=1)
            # TODO: 实现安装逻辑
            progress.update(install_task, completed=1)
            
            # 4. 合并配置
            config_task = progress.add_task("[cyan]合并配置文件...", total=1)
            # TODO: 实现配置合并逻辑
            progress.update(config_task, completed=1)
            
        return True
        
    def confirm_update(self, changelog):
        """显示更新日志并确认更新"""
        self.console.print("\n[yellow]发现新版本！以下是更新内容：[/yellow]")
        self.console.print(Markdown(changelog))
        
        response = input("\n是否要进行更新？(y/n): ")
        return response.lower() == 'y'
        
    def confirm_success(self):
        """确认更新成功"""
        response = input("\n新版本测试是否成功？(y/n): ")
        if response.lower() == 'y':
            self._clean_old_backups()
            return True
        return False 