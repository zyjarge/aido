#!/usr/bin/env python3
import os
import re
from typing import Dict, List, Tuple
from rich.console import Console
from rich.prompt import Confirm

class ConfigMerger:
    def __init__(self, local_config: str, example_config: str):
        """初始化配置合并器
        
        Args:
            local_config: 本地配置文件路径
            example_config: 示例配置文件路径
        """
        self.local_config = local_config
        self.example_config = example_config
        self.console = Console()
        
    def _parse_config(self, file_path: str) -> Dict[str, Tuple[str, List[str]]]:
        """解析配置文件
        
        Returns:
            Dict[配置键: (配置值, 配置注释)]
        """
        config = {}
        current_comments = []
        
        if not os.path.exists(file_path):
            return config
            
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:  # 空行
                    current_comments = []
                    continue
                    
                if line.startswith('#'):  # 注释行
                    current_comments.append(line)
                    continue
                    
                if '=' in line:  # 配置行
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    config[key] = (value, current_comments)
                    current_comments = []
                    
        return config
        
    def _merge_configs(self) -> Tuple[List[str], List[str]]:
        """合并配置
        
        Returns:
            (合并后的配置行列表, 需要人工确认的配置键列表)
        """
        local_config = self._parse_config(self.local_config)
        example_config = self._parse_config(self.example_config)
        
        merged_lines = []
        need_confirm = []
        
        # 处理示例配置中的每一项
        for key, (example_value, example_comments) in example_config.items():
            # 添加注释
            merged_lines.extend(example_comments)
            
            if key in local_config:
                local_value, _ = local_config[key]
                if local_value != example_value:
                    # 值不同，需要确认
                    need_confirm.append(key)
                    merged_lines.append(f"# 新版本值: {key}={example_value}")
                    merged_lines.append(f"{key}={local_value}")
                else:
                    # 值相同，使用本地值
                    merged_lines.append(f"{key}={local_value}")
            else:
                # 新配置项，使用示例值
                merged_lines.append(f"{key}={example_value}")
            
            merged_lines.append('')  # 添加空行分隔
            
        # 处理本地配置中的自定义项
        for key, (local_value, local_comments) in local_config.items():
            if key not in example_config:
                merged_lines.extend(local_comments)
                merged_lines.append(f"{key}={local_value}")
                merged_lines.append('')
                
        return merged_lines, need_confirm
        
    def update_config(self) -> bool:
        """更新配置文件
        
        Returns:
            bool: 是否更新成功
        """
        try:
            # 如果本地配置不存在，直接复制示例配置
            if not os.path.exists(self.local_config):
                with open(self.example_config, 'r', encoding='utf-8') as src:
                    content = src.read()
                with open(self.local_config, 'w', encoding='utf-8') as dst:
                    dst.write(content)
                return True
                
            # 合并配置
            merged_lines, need_confirm = self._merge_configs()
            
            # 如果有需要确认的配置
            if need_confirm:
                self.console.print("\n[yellow]发现配置差异：[/yellow]")
                for key in need_confirm:
                    self.console.print(f"配置项 [cyan]{key}[/cyan] 在新版本中有更新")
                
                if not Confirm.ask("是否继续更新配置？"):
                    self.console.print("[yellow]配置更新已取消，请手动检查配置文件[/yellow]")
                    return False
            
            # 备份原配置
            backup_path = f"{self.local_config}.bak"
            if os.path.exists(self.local_config):
                with open(self.local_config, 'r', encoding='utf-8') as src:
                    with open(backup_path, 'w', encoding='utf-8') as dst:
                        dst.write(src.read())
            
            # 写入新配置
            with open(self.local_config, 'w', encoding='utf-8') as f:
                f.write('\n'.join(merged_lines))
            
            return True
            
        except Exception as e:
            self.console.print(f"[red]配置更新失败：{str(e)}[/red]")
            return False 