# -*- coding: utf-8 -*-
"""校验菜单补丁：1) 结构 BAD 2) 英文标签是否已消失 3) 中文字形是否覆盖 4) 正文中文未回退"""
import os, struct, json, re, sys
import UnityPy
from fontTools.ttLib import TTFont
import io

GAME = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY"
HERE = os.path.dirname(os.path.abspath(__file__))
TARGET = sys.argv[1] if len(sys.argv) > 1 else os.path.join(GAME, "build_ui2", "resources.assets")
BASE = os.path.join(GAME, "build_final2", "resources.assets")

CJK = re.compile(r"[\u4e00-\u9fff]")

def scan_lp(b):
    out = []; n = len(b); i = 0
    while i + 4 <= n:
        L = struct.unpack_from("<i", b, i)[0]
        if 0 <= L <= 4000 and i + 4 + L <= n:
            seg = b[i+4:i+4+L]
            if not any(c < 0x20 and c not in (9, 10, 13) for c in seg):
                try:
                    t = seg.decode("utf-8")
                    out.append(t); i = (i + 4 + L + 3) & ~3; continue
                except Exception:
                    pass
        i += 4
    return out

ui = json.load(open(os.path.join(HERE, "ui_labels.json"), encoding="utf-8"))
labels = set(ui["labels"].keys())
SKIP = {"SetActive", "set_fontStyle", "set_text", "yyyy-MM-dd HH:mm", "{Text_Month}",
        "Text_Month", "Text_Day", "Text_Time", "{N}. {T}", "???", "H", "I", "M", "O",
        "g", "m", "1", "{", "DefaultUI"}
check = sorted(labels - SKIP)

def load(path):
    env = UnityPy.load(path)
    d = {}
    for o in env.objects:
        if o.type.name == "MonoBehaviour":
            try: d[o.path_id] = o.get_raw_data()
            except: pass
    return env, d

env, objs = load(TARGET)
print("目标: %s" % TARGET)
print("MonoBehaviour 数: %d" % len(objs))

# 1) 英文标签残留
print("\n=== 1) 英文标签是否还在 ===")
remain = []
for lb in check:
    pat = struct.pack("<i", len(lb.encode())) + lb.encode()
    c = sum(1 for r in objs.values() if pat in r)
    if c: remain.append((lb, c))
if remain:
    for lb, c in remain: print("   仍存在 %-26r x%d" % (lb, c))
else:
    print("   全部英文标签已消失 ✓")

# 2) 中文标签存在
print("\n=== 2) 中文标签抽样 ===")
zhs = ["自动", "隐藏", "记录", "跳过", "菜单", "读档", "存档", "设置", "标题", "返回",
       "提示", "关闭", "继续", "新游戏", "退出", "选项", "画廊", "结局", "确定", "是", "否",
       "画质：", "字号：", "语言：", "主音量：", "文字速度：", "分辨率："]
hit = 0
for z in zhs:
    pat = struct.pack("<i", len(z.encode())) + z.encode()
    c = sum(1 for r in objs.values() if pat in r)
    if c: hit += 1
    else: print("   缺失 %r" % z)
print("   命中 %d / %d" % (hit, len(zhs)))

# 3) 字体覆盖
print("\n=== 3) 字体 cmap 覆盖 ===")
for o in env.objects:
    if o.type.name != "Font": continue
    tree = o.read_typetree()
    name = tree.get("m_Name", "")
    data = bytes(tree.get("m_FontData") or b"")
    if name != "AveriaSerifLibre-Regular": continue
    print("   字体: %s  %d 字节" % (name, len(data)))
    f = TTFont(io.BytesIO(data))
    cmap = set()
    for t in f["cmap"].tables: cmap |= set(t.cmap.keys())
    print("   字形数: %d" % len(cmap))
    need = set()
    tr = json.load(open(os.path.join(HERE, "translations_complete.json"), encoding="utf-8"))
    for v in tr.values(): need |= {ord(c) for c in v}
    for z in zhs: need |= {ord(c) for c in z}
    miss = sorted(c for c in need if c not in cmap and c > 127)
    print("   需要 %d 个非 ASCII 字形, 缺 %d 个: %s"
          % (len([c for c in need if c > 127]), len(miss),
             ", ".join("U+%04X" % c for c in miss[:12])))

# 4) 正文中文对比基线
print("\n=== 4) 正文中文未回退（与 build_final2 对比）===")
_, base = load(BASE)
def cn_count(d):
    n = 0
    for r in d.values():
        n += len(CJK.findall(r.decode("utf-8", "ignore")))
    return n
print("   build_final2 中文字符总数: %d" % cn_count(base))
print("   目标文件中文字符总数:     %d" % cn_count(objs))
