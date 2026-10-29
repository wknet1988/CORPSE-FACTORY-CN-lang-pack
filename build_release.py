#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Assemble the ready-to-use (drop-in) Chinese patch package and zip it."""
import os, zipfile

BASE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.join(BASE, "release", "pkg")
OUT = os.path.join(BASE, "release", "CORPSE-FACTORY-CN-patch-v1.0.0.zip")

def w(path, text):
    # write with Windows CRLF line endings
    with open(path, "w", encoding="utf-8", newline="\r\n") as f:
        f.write(text)

INSTALL_BAT = r"""@echo off
setlocal EnableDelayedExpansion
set "PKG=%~dp0"
set "DATA="

if exist "%PKG%CORPSE FACTORY_Data\resources.assets" (
  set "DATA=%PKG%CORPSE FACTORY_Data"
)
if not defined DATA (
  if exist "%PKG%..\CORPSE FACTORY_Data\resources.assets" (
    set "DATA=%PKG%..\CORPSE FACTORY_Data"
  )
)
if not defined DATA (
  echo 未自动找到游戏目录。请把补丁解压到游戏根目录，
  echo 或在此输入游戏根目录路径（即包含 CORPSE FACTORY_Data 的文件夹）：
  set /p "GAME=游戏根目录> "
  if defined GAME set "DATA=!GAME!\CORPSE FACTORY_Data"
)
if not defined DATA (
  echo 无法定位游戏目录，安装已取消。
  pause
  exit /b 1
)
if not exist "!DATA!\resources.assets" (
  echo 目录似乎不正确：!DATA! 内没有 resources.assets
  pause
  exit /b 1
)

echo 正在备份原有文件...
if not exist "!DATA!\resources.assets.bak" copy /Y "!DATA!\resources.assets" "!DATA!\resources.assets.bak" >nul
if not exist "!DATA!\Managed\Elringus.Naninovel.Runtime.dll.bak" copy /Y "!DATA!\Managed\Elringus.Naninovel.Runtime.dll" "!DATA!\Managed\Elringus.Naninovel.Runtime.dll.bak" >nul

echo 正在应用汉化补丁...
copy /Y "%PKG%resources.assets" "!DATA!\resources.assets" >nul
if not exist "!DATA!\Managed" mkdir "!DATA!\Managed"
copy /Y "%PKG%Elringus.Naninovel.Runtime.dll" "!DATA!\Managed\Elringus.Naninovel.Runtime.dll" >nul

echo.
echo ============================================
echo  汉化补丁已应用完成！
echo  原文件已备份为 .bak（可随时还原）。
echo  现在启动游戏即可体验中文。
echo ============================================
echo.
pause
"""

README_TXT = """CORPSE FACTORY 简体中文汉化补丁 v1.0.0（开箱即用版）
====================================================

本补丁已打好，普通玩家无需任何编译或 Python 环境，直接按下面步骤即可游玩中文版。

【使用方法】
1. 在 Steam 库里右键 CORPSE FACTORY -> 属性 -> 本地文件 -> 浏览，打开游戏安装目录
   （即包含 “CORPSE FACTORY_Data” 文件夹的那个目录）。
2. 把本压缩包里的全部内容解压到该游戏根目录（与 CORPSE FACTORY_Data 同级）。
3. 双击运行 install.bat，按提示完成（会自动备份原文件，再把汉化文件复制进去）。
4. 启动游戏，享受中文。

【还原方法】
若想恢复英文原版：把游戏目录里的
  CORPSE FACTORY_Data\resources.assets.bak
  CORPSE FACTORY_Data\Managed\Elringus.Naninovel.Runtime.dll.bak
去掉 .bak 后缀，覆盖回去即可。

【包含的文件】
- resources.assets        ：已注入简体中文剧情/UI 文本，并内嵌中文字体
- Elringus.Naninovel.Runtime.dll ：已汉化“覆盖存档/删除存档/返回主菜单”确认提示
- install.bat             ：一键安装（自动备份 + 复制）
- source\                 ：汉化工程源码与翻译表（供有兴趣的玩家自行重建/核对，无需使用）

【已知说明】
- 引擎内置确认框的按钮文字（Cancel / Delete / Continue）仍为英文。
  这是刻意的：它们是游戏输入动作的标识符，改成中文会导致按钮失效，故保留英文。
- 本补丁基于你自己的正版游戏副本打制，不替换任何你已有的其他游戏文件。
- 请使用对应版本的游戏；若游戏更新导致文件不匹配，请还原 .bak 后再行处理。

【版权声明】
本补丁为粉丝非商业汉化作品，仅包含文本翻译与字体嵌入，不含有游戏程序的逆向代码。
请支持正版。使用本补丁即表示你已合法拥有该游戏。
"""

w(os.path.join(PKG, "install.bat"), INSTALL_BAT)
w(os.path.join(PKG, "README.txt"), README_TXT)

# Build the zip (store paths relative to PKG)
if os.path.exists(OUT):
    os.remove(OUT)
with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
    for root, dirs, files in os.walk(PKG):
        for fn in sorted(files):
            full = os.path.join(root, fn)
            rel = os.path.relpath(full, PKG)
            z.write(full, rel)

print("created:", OUT)
print("size:", os.path.getsize(OUT), "bytes")
for info in zipfile.ZipFile(OUT).infolist():
    print("  ", info.filename, info.file_size)
