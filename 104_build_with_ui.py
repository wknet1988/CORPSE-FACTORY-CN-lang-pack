# -*- coding: utf-8 -*-
"""在 40_build_final 基础上增加「菜单/提示标签」替换，并重建含新字的字体子集。

用法:
  <python> 104_build_with_ui.py --out <输出目录>
"""
import os, sys, io, json, struct, argparse
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from UnityPy import Environment
import importlib.util

spec = importlib.util.spec_from_file_location("bf", os.path.join(HERE, "40_build_final.py"))
bf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bf)

DATA = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY/CORPSE FACTORY_Data"
DEFAULT_IN = os.path.join(DATA, "backup_original", "resources.assets")

# 菜单/提示标签译文（只列确认是显示文本的）
UI_LABELS = {
    "AUTO": "自动",
    "HIDE": "隐藏",
    "LOG": "记录",
    "SKIP": "跳过",
    "MENU": "菜单",
    "LOAD": "读档",
    "SAVE": "存档",
    "SETTINGS": "设置",
    "TITLE": "标题",
    "RETURN": "返回",
    "TIPS": "提示",
    "CLOSE": "关闭",
    "CREDITS": "制作人员",
    "CONTINUE": "继续",
    "NEW GAME": "新游戏",
    "EXIT": "退出",
    "OPTIONS": "选项",
    "QUICK SAVE": "快速存档",
    "QUICK LOAD": "快速读档",
    "GALLERY": "画廊",
    "CG GALLERY": "CG 画廊",
    "ENDINGS": "结局",
    "SUBMIT": "确定",
    "YES": "是",
    "NO": "否",
    "BASIC": "基础",
    "TEXT": "文本",
    "SOUND": "声音",
    "CROW FACTORY": "乌鸦工厂",
    "BUY SOUNDTRACK": "购买原声带",
    "EXTERNAL SCRIPTS": "外部脚本",
    "Select a script to play": "选择要播放的脚本",
    "Graphics:": "画质：",
    "Auto delay:": "自动延迟：",
    "Effects volume:": "音效音量：",
    "Font size:": "字号：",
    "Font:": "字体：",
    "Language:": "语言：",
    "Master volume:": "主音量：",
    "Message speed:": "文字速度：",
    "Music volume:": "音乐音量：",
    "Voice language:": "语音语言：",
    "Voice volume:": "语音音量：",
    "Resolution:": "分辨率：",
    "Screen mode:": "屏幕模式：",
    "Skip mode:": "快进模式：",
    "Preview": "预览",
    "Rollback": "回滚",
    "File {N} - {D}": "存档 {N} - {D}",
    # 制作人员页表头 / 初始默认值
    "Staff": "制作团队",
    "Cast": "配音",
    "WEDNESDAY": "星期三",
    "Morning": "早晨",
    "Kojiro": "小次郎",
    # Cast 页角色名
    "Emi Katsuno": "胜野惠美",
    "Kenji Ogawa": "小川健二",
    "Tomoe Watanabe": "渡边智惠",
    "Junpei Matsumoto": "松本纯平",
}
# 明确不动的东西
SKIP = {"SetActive", "set_fontStyle", "set_text", "yyyy-MM-dd HH:mm",
        "{Text_Month}", "Text_Month", "Text_Day", "Text_Time", "{N}. {T}",
        "???", "H", "I", "M", "O", "g", "m", "1", "{", "DefaultUI"}


def align4(n): return (n + 3) & ~3


def patch_ui_labels(env, ui_rows, max_size=600):
    """在小体量 UI 对象（Text 组件 / UnityEvent 项）里替换标签字面量，
    替换该对象内**全部**出现位置（m_Text 与事件参数可能各存一份）。"""
    changed = 0
    replaced = 0
    details = []
    for obj in env.objects:
        if obj.type.name != "MonoBehaviour":
            continue
        try:
            raw = obj.get_raw_data()
        except Exception:
            continue
        if len(raw) > max_size:
            continue
        reps = []
        for lb, new in UI_LABELS.items():
            enb = lb.encode("utf-8")
            pat = struct.pack("<i", len(enb)) + enb
            rsz = align4(4 + len(enb))
            start = 0
            while True:
                p = raw.find(pat, start)
                if p < 0:
                    break
                start = p + 1
                if p + rsz > len(raw):
                    continue
                newb = new.encode("utf-8")
                new_region = (struct.pack("<i", len(newb)) + newb
                              + b"\x00" * (align4(4 + len(newb)) - (4 + len(newb))))
                reps.append((p, rsz, new_region, lb, new))
        if not reps:
            continue
        reps.sort(key=lambda r: r[0])
        # 去重叠
        kept = []
        last_end = -1
        for r in reps:
            if r[0] < last_end:
                continue
            kept.append(r)
            last_end = r[0] + r[1]
        newraw = bytearray()
        cur = 0
        for p, rsz, nr, lb, new in kept:
            newraw += raw[cur:p]
            newraw += nr
            cur = p + rsz
            details.append((obj.path_id, lb, new))
        newraw += raw[cur:]
        obj.set_raw_data(bytes(newraw))
        changed += 1
        replaced += len(kept)

    print("UI 标签: %d 个对象, %d 处替换" % (changed, replaced))
    return replaced, details


def main(out_dir, in_path, trans_path, skip_font=False, skip_text=False):
    trans_map = json.load(open(trans_path, encoding="utf-8"))
    ui = json.load(open(os.path.join(HERE, "ui_labels.json"), encoding="utf-8"))

    chars = set()
    for v in trans_map.values():
        chars.update(v)
    for en, zh in UI_LABELS.items():
        chars.update(zh)
    chars.update(chr(c) for c in range(0x20, 0x7F))

    env = Environment(in_path)
    if skip_text:
        print("skip-text: 保留输入文件已有正文译文，只打菜单标签补丁")
    else:
        c, r, s = bf.inject_text(env, trans_map)
    nrep, details = patch_ui_labels(env, ui["rows"])

    if not skip_font:
        ttf = bf.build_subset(chars)
        flen = bf.inject_font(env, ttf)
        print("font: 子集 %d 字节, %d 字" % (flen, len(chars)))

    os.makedirs(out_dir, exist_ok=True)
    env.save(out_path=out_dir)
    print("saved -> %s" % out_dir)

    json.dump([{"pid": p, "en": e, "zh": z} for p, e, z in details],
              open(os.path.join(HERE, "ui_patched.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default=DEFAULT_IN)
    ap.add_argument("--trans", default=os.path.join(HERE, "translations_complete.json"))
    ap.add_argument("--out", required=True)
    ap.add_argument("--skip-font", action="store_true")
    ap.add_argument("--skip-text", action="store_true")
    a = ap.parse_args()
    main(a.out, a.inp, a.trans, a.skip_font, a.skip_text)
