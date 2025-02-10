#!/bin/bash

# 设置工作目录
cd /Users/zhangyong/workspace/aido

# 检查用户是否提供了版本号
if [ -n "$1" ]; then
  new_version="$1"
  echo "使用用户指定的版本号: $new_version"
else
  # 读取当前版本号
  current_version=$(cat VERSION)
  echo "当前版本号: $current_version"

  # 自动增加版本号（假设是增加补丁版本号）
  IFS='.' read -r -a version_parts <<< "$current_version"
  version_parts[2]=$((version_parts[2] + 1))
  new_version="${version_parts[0]}.${version_parts[1]}.${version_parts[2]}"
  echo "新版本号: $new_version"
fi

# 更新版本文件
echo $new_version > VERSION

# 提交更改
git add VERSION
git commit -m "Bump version to $new_version"

# 创建Git标签
git tag -a "$new_version" -m "Release version $new_version"

# 推送到远程仓库
git push origin master
git push origin "$new_version"

echo "版本 $new_version 已成功推送到远程仓库" 