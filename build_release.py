#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Assemble the ready-to-use (drop-in) Chinese patch package.

Pure drop-in: the archive mirrors the game directory layout, so extracting
into the game root directly overwrites the two patched files. No scripts.
Packaged with 7z -mx9.
"""
import os, shutil, subprocess

BASE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.join(BASE, "release", "pkg3")
OUT = os.path.join(BASE, "release", "CORPSE-FACTORY-CN-patch-v1.0.0.7z")
SEVEN_ZIP = r"C:/Program Files/7-Zip/7z.exe"
GAME_DATA = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY/CORPSE FACTORY_Data"

def w(path, text):
    with open(path, "w", encoding="utf-8", newline="\r\n") as f:
        f.write(text)

# ---- stage mirror layout: only the two patched files + README ----
if os.path.exists(PKG):
    shutil.rmtree(PKG)
os.makedirs(os.path.join(PKG, "CORPSE FACTORY_Data", "Managed"))

shutil.copyfile(os.path.join(GAME_DATA, "resources.assets"),
                os.path.join(PKG, "CORPSE FACTORY_Data", "resources.assets"))
shutil.copyfile(os.path.join(GAME_DATA, "Managed", "Elringus.Naninovel.Runtime.dll"),
                os.path.join(PKG, "CORPSE FACTORY_Data", "Managed", "Elringus.Naninovel.Runtime.dll"))

README_TXT = """CORPSE FACTORY 简体中文汉化补丁 v1.0.0（开箱即用版）
====================================================

本补丁已打好，普通玩家无需任何编译或 Python 环境。压缩包为 7z 格式，
请用 7-Zip / WinRAR（或 Windows 11 资源管理器）解压。

【安装方法：直接覆盖到游戏根目录】
1. 在 Steam 库右键 CORPSE FACTORY -> 属性 -> 本地文件 -> 浏览，
   打开游戏安装目录（即包含 CORPSE FACTORY_Data 文件夹的目录）。
2. 把压缩包里的 CORPSE FACTORY_Data 文件夹直接解压覆盖到该游戏根目录
   （与游戏原有的 CORPSE FACTORY_Data 同级，提示覆盖时选“全部覆盖”即可）。
3. 启动游戏，享受中文。

【还原方法】
- 建议覆盖前先自行备份原 resources.assets 与 Elringus.Naninovel.Runtime.dll。
- 若已覆盖且未备份，可在 Steam 对该游戏“验证游戏文件的完整性”恢复。

【已知说明】
- 引擎确认框按钮（Cancel / Delete / Continue）仍为英文，刻意为之
  （它们是输入动作标识符，改中文会导致按钮失效）。

【版权声明】
粉丝非商业汉化，仅含文本翻译与字体嵌入，请支持正版；使用即表示你已合法拥有该游戏。
"""

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
