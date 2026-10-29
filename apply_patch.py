#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CORPSE FACTORY 简体中文汉化补丁 · 一键应用器
============================================
需要：你本机已拥有正版 CORPSE FACTORY (Steam)，并安装了 Python 3 + UnityPy + fonttools。

用法：
    python apply_patch.py "G:/SteamLibrary/steamapps/common/CORPSE FACTORY"

它会：
  1. 自动备份你原来的 resources.assets / Elringus.Naninovel.Runtime.dll（随时可还原）
  2. 注入简体中文文本，并嵌入自带的中文字体子集（cjk_subset.ttf）
  3. 汉化引擎内置的 3 条确认提示（覆盖 / 删除存档、返回主菜单）
  4. 做基础完整性自检

还原方法：把 <原名>.bak_patch 改回原名覆盖即可。
"""
import os, sys, shutil, struct, subprocess, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_PATH = os.path.join(HERE, "cjk_subset.ttf")
FONT_TARGET = "AveriaSerifLibre-Regular"

# 仅汉化 3 条“纯显示”确认提示；按钮标识符（Cancel/Delete/Continue）绝不可译，
# 否则会导致按钮无响应（它们同时是引擎的输入动作标识符）。
DLL_TARGETS = [
    ("Are you sure you want to overwrite save slot?",
     "确定要覆盖这个存档吗？"),
    ("Are you sure you want to delete save slot?",
     "确定要删除这个存档吗？"),
    ("Are you sure you want to quit to the title screen?\nAny unsaved game progress will be lost.",
     "确定要返回主菜单吗？\n未保存的进度将丢失。"),
]

def find_game(p):
    data = os.path.join(p, "CORPSE FACTORY_Data")
    res = os.path.join(data, "resources.assets")
    dll = os.path.join(data, "Managed", "Elringus.Naninovel.Runtime.dll")
    if not os.path.isfile(res):
        sys.exit("找不到 resources.assets：%s\n请确认传入的是游戏根目录（含 CORPSE FACTORY_Data 的那一层）。" % res)
    if not os.path.isfile(dll):
        sys.exit("找不到 DLL：%s" % dll)
    return data, res, dll

def pad_to(s, n):
    if len(s) > n:
        raise ValueError("中文过长: %r (%d>%d)" % (s, len(s), n))
    return s + " " * (n - len(s))

def patch_dll(dll):
    bak = dll + ".bak_patch"
    if not os.path.exists(bak):
        shutil.copy2(dll, bak)
        print("  已备份 DLL ->", os.path.basename(bak))
    data = bytearray(open(bak, "rb").read())
    for en, zh in DLL_TARGETS:
        n = len(en)
        zb = pad_to(zh, n).encode("utf-16-le")
        eb = en.encode("utf-16-le")
        assert len(zb) == len(eb), (len(zb), len(eb))
        c = data.count(eb)
        if c == 0:
            print("  SKIP (未找到):", en); continue
        data = data.replace(eb, zb)
        print("  PATCH DLL x%d: %r -> %r" % (c, en, zh))
    open(dll, "wb").write(data)

def inject_font(res_path, ttf_path):
    from UnityPy import Environment
    env = Environment(res_path)
    ttf = open(ttf_path, "rb").read()
    done = False
    for obj in env.objects:
        if obj.type.name != "Font":
            continue
        raw = obj.get_raw_data()
        nl = struct.unpack_from("<i", raw, 0)[0]
        name = raw[4:4 + nl].decode("utf-8", "replace") if 0 < nl < 100 else ""
        if name != FONT_TARGET:
            continue
        tree = obj.read_typetree()
        tree["m_FontData"] = list(ttf)
        obj.save_typetree(tree)
        done = True
        break
    if not done:
        raise RuntimeError("未在 assets 中找到字体对象 %s" % FONT_TARGET)
    env.save(out_path=os.path.dirname(res_path))
    print("  已嵌入中文字体 (%d 字节)" % len(ttf))

def sanity(res_path):
    from UnityPy import Environment
    env = Environment(res_path)
    n = sum(1 for _ in env.objects)
    print("  自检通过：resources.assets 可正常加载（%d 个对象）。" % n)

def main():
    ap = argparse.ArgumentParser(description="CORPSE FACTORY 简体中文汉化补丁一键应用器")
    ap.add_argument("game", help="游戏根目录，例如 G:/SteamLibrary/steamapps/common/CORPSE FACTORY")
    a = ap.parse_args()

    try:
        import UnityPy  # noqa
    except ImportError:
        sys.exit("缺少依赖。请先运行：pip install UnityPy fonttools")

    data, res, dll = find_game(a.game)

    # 1) 备份原始文件
    res_bak = res + ".bak_patch"
    if not os.path.exists(res_bak):
        shutil.copy2(res, res_bak)
        print("已备份 resources.assets ->", os.path.basename(res_bak))

    # 2) 文本注入（调用 40_build_final.py，仅文本，字体稍后单独嵌入）
    out = os.path.join(HERE, "build_out")
    build = os.path.join(HERE, "40_build_final.py")
    if not os.path.isfile(build):
        sys.exit("缺少 40_build_final.py，请确认本补丁包完整。")
    print(">>> 步骤 1/3：注入简体中文文本 ...")
    r = subprocess.run([sys.executable, build, "--in", res, "--out", out, "--skip-font"])
    if r.returncode != 0:
        sys.exit("文本注入失败，请检查上方报错。")
    patched = os.path.join(out, "resources.assets")
    if not os.path.isfile(patched):
        sys.exit("注入后未生成 resources.assets。")

    # 3) 嵌入中文字体
    print(">>> 步骤 2/3：嵌入中文字体 ...")
    if not os.path.isfile(FONT_PATH):
        sys.exit("缺少 cjk_subset.ttf，请确认本补丁包完整。")
    inject_font(patched, FONT_PATH)

    # 4) 写回游戏目录（保留同名 .resS 不动）
    shutil.copy2(patched, res)
    print("  已写入汉化 resources.assets ->", res)

    # 5) 汉化引擎确认提示（DLL）
    print(">>> 步骤 3/3：汉化引擎内置确认提示 ...")
    patch_dll(dll)

    # 6) 自检
    print(">>> 完整性自检 ...")
    sanity(res)

    print("\n✅ 汉化完成！启动游戏即可看到简体中文。")
    print("   如需还原：将 resources.assets.bak_patch 与")
    print("   Elringus.Naninovel.Runtime.dll.bak_patch 改回原名覆盖即可。")

if __name__ == "__main__":
    main()
