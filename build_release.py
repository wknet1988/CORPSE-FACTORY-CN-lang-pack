#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Assemble the ready-to-use (drop-in) Chinese patch package.

Layout mirrors the game directory so extracting into the game root
directly overwrites the two patched files. Packaged with 7z -mx9.
"""
import os, shutil, subprocess

BASE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.join(BASE, "release", "pkg2")
OUT = os.path.join(BASE, "release", "CORPSE-FACTORY-CN-patch-v1.0.0.7z")
SEVEN_ZIP = r"C:/Program Files/7-Zip/7z.exe"
GAME_DATA = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY/CORPSE FACTORY_Data"

def w(path, text):
    with open(path, "w", encoding="utf-8", newline="\r\n") as f:
        f.write(text)

# ---- stage mirror layout ----
if os.path.exists(PKG):
    shutil.rmtree(PKG)
os.makedirs(os.path.join(PKG, "CORPSE FACTORY_Data", "Managed"))
os.makedirs(os.path.join(PKG, "source"))

shutil.copyfile(os.path.join(GAME_DATA, "resources.assets"),
                os.path.join(PKG, "CORPSE FACTORY_Data", "resources.assets"))
shutil.copyfile(os.path.join(GAME_DATA, "Managed", "Elringus.Naninovel.Runtime.dll"),
                os.path.join(PKG, "CORPSE FACTORY_Data", "Managed", "Elringus.Naninovel.Runtime.dll"))

SRC_FILES = [
    "apply_patch.py", "40_build_final.py", "76_extract_v2.py", "77_add_translations.py",
    "78_patch_dll.py", "80_verify.py", "55_merge_complete.py",
    "translations_complete.json", "occurrences.json", "occurrences_v2.json",
    "cjk_subset.ttf", "PATCH_README.md",
]
for fn in SRC_FILES:
    shutil.copyfile(os.path.join(BASE, fn), os.path.join(PKG, "source", fn))

INSTALL_BAT = r"""@echo off
setlocal EnableDelayedExpansion
set "PKG=%~dp0"
set "SRC=%PKG%CORPSE FACTORY_Data"
if not exist "%SRC%\resources.assets" (
  echo 未找到补丁文件（CORPSE FACTORY_Data\resources.assets）。
  echo 请确认本 install.bat 与 CORPSE FACTORY_Data 文件夹在一起。
  pause & exit /b 1
)

:: 定位游戏根目录：向上查找 CORPSE FACTORY.exe
set "ROOT="
for %%D in ("%PKG%." "%PKG%.." "%PKG%..\.." "%PKG%..\..\.." "%PKG%..\..\..\..") do (
  if exist "%%~fD\CORPSE FACTORY.exe" ( set "ROOT=%%~fD" & goto :found )
)
:found
if not defined ROOT (
  echo 未自动找到游戏目录。请输入 CORPSE FACTORY 游戏根目录
  echo （即包含 CORPSE FACTORY.exe 与 CORPSE FACTORY_Data 的文件夹）：
  set /p "GAME=游戏根目录> "
  if defined GAME set "ROOT=!GAME!"
)
if not defined ROOT ( echo 已取消。 & pause & exit /b 1 )
if not exist "!ROOT!\CORPSE FACTORY_Data\resources.assets" (
  echo 目录似乎不正确：!ROOT! 内没有 CORPSE FACTORY_Data\resources.assets
  pause & exit /b 1
)

set "DST=!ROOT!\CORPSE FACTORY_Data"
:: 若补丁已解压进游戏目录（SRC==DST），文件应已就位，无需再复制
if /I "%SRC%"=="%DST%" (
  echo 检测到补丁已在游戏目录内，文件应已就位。
  echo 如需还原原版，请在 Steam 对该游戏“验证游戏文件的完整性”。
  pause & exit /b 0
)

echo 正在备份原文件...
if not exist "!DST!\resources.assets.bak" copy /Y "!DST!\resources.assets" "!DST!\resources.assets.bak" >nul
if not exist "!DST!\Managed\Elringus.Naninovel.Runtime.dll.bak" copy /Y "!DST!\Managed\Elringus.Naninovel.Runtime.dll" "!DST!\Managed\Elringus.Naninovel.Runtime.dll.bak" >nul

echo 正在应用汉化补丁...
copy /Y "%SRC%\resources.assets" "!DST!\resources.assets" >nul
if not exist "!DST!\Managed" mkdir "!DST!\Managed"
copy /Y "%SRC%\Managed\Elringus.Naninovel.Runtime.dll" "!DST!\Managed\Elringus.Naninovel.Runtime.dll" >nul

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

本补丁已打好，普通玩家无需任何编译或 Python 环境。压缩包为 7z 格式，
请用 7-Zip / WinRAR（或 Windows 11 资源管理器）解压。

【使用方法】
方式一（推荐，带自动备份）：
1. 把压缩包解压到任意文件夹（如桌面）。
2. 进入解压出的文件夹，双击 install.bat。
3. 若脚本没自动找到游戏，按提示输入游戏根目录
   （即包含 CORPSE FACTORY.exe 与 CORPSE FACTORY_Data 的文件夹），
   它会自动备份原文件并覆盖汉化文件。
4. 启动游戏，享受中文。

方式二（直接覆盖）：
1. 在 Steam 库右键 CORPSE FACTORY -> 属性 -> 本地文件 -> 浏览，打开游戏根目录。
2. 把压缩包里的 CORPSE FACTORY_Data 文件夹直接解压覆盖到该游戏根目录
   （提示覆盖时选“全部覆盖”即可）。
3. 启动游戏。（建议覆盖前先自行备份原 resources.assets 与 Elringus.Naninovel.Runtime.dll）

【还原方法】
方式一产生的备份：把 CORPSE FACTORY_Data\resources.assets.bak 与
CORPSE FACTORY_Data\Managed\Elringus.Naninovel.Runtime.dll.bak
去掉 .bak 后缀覆盖回去即可。
若用方式二且未备份，可在 Steam 对该游戏“验证游戏文件的完整性”恢复。

【压缩包内容】
- CORPSE FACTORY_Data\resources.assets                  ：已注入简体中文并内嵌中文字体
- CORPSE FACTORY_Data\Managed\Elringus.Naninovel.Runtime.dll ：已汉化确认提示
- install.bat             ：一键安装（自动备份 + 复制）
- README.txt             ：本说明
- source\                ：汉化工程源码与翻译表（无需使用）

【已知说明】
- 引擎确认框按钮（Cancel / Delete / Continue）仍为英文，刻意为之
  （它们是输入动作标识符，改中文会导致按钮失效）。

【版权声明】
粉丝非商业汉化，仅含文本翻译与字体嵌入，请支持正版；使用即表示你已合法拥有该游戏。
"""

w(os.path.join(PKG, "install.bat"), INSTALL_BAT)
w(os.path.join(PKG, "README.txt"), README_TXT)

# ---- package with 7z -mx9 ----
if os.path.exists(OUT):
    os.remove(OUT)
cmd = [SEVEN_ZIP, "a", "-mx9", "-mmt=on", "-t7z", OUT, "."]
print("running:", " ".join(cmd))
r = subprocess.run(cmd, cwd=PKG, capture_output=True, text=True)
print(r.stdout[-1500:] if len(r.stdout) > 1500 else r.stdout)
if r.returncode != 0:
    print("STDERR:", r.stderr[-1500:])
    raise SystemExit("7z failed: " + str(r.returncode))

print("created:", OUT)
print("size:", os.path.getsize(OUT), "bytes")
