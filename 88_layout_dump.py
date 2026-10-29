# -*- coding: utf-8 -*-
"""挖开布局：取一条已知译文在 Script_Act_01(9127) 中的位置，dump 周围字节与字符串，
确认 GenericTextScriptLine 的 body 里哪一段是展示文本。"""
import os, re, struct, json
import UnityPy

GAME = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY"
BACKUP = os.path.join(GAME, "CORPSE FACTORY_Data", "backup_original", "resources.assets")
HERE = os.path.dirname(os.path.abspath(__file__))
CJK = re.compile(r"[\u4e00-\u9fff]")

occ = json.load(open(os.path.join(HERE, "occurrences.json"), encoding="utf-8"))
tr = json.load(open(os.path.join(HERE, "translations_complete.json"), encoding="utf-8"))

# 选几条 pid=9127 的、长度中等的、已知译文的条目
cands = [o for o in occ if o["pid"] == 9127 and 40 <= len(o["text"]) <= 120 and o["text"] in tr]
print("pid=9127 已知译文条目: %d" % len(cands))

env = UnityPy.load(BACKUP)
raw = None
for o in env.objects:
    if o.path_id == 9127:
        raw = o.get_raw_data(); break
print("raw len:", len(raw))

def lp_around(b, center, back=260, fwd=420):
    out = []
    start = max(0, center - back)
    end = min(len(b), center + fwd)
    i = start
    while i + 4 <= end:
        L = struct.unpack_from("<i", b, i)[0]
        if 0 <= L <= 400 and i + 4 + L <= end:
            seg = b[i+4:i+4+L]
            if not any(c < 0x20 and c not in (9, 10, 13) for c in seg):
                try:
                    t = seg.decode("utf-8")
                    out.append((i, t)); i = (i + 4 + L + 3) & ~3; continue
                except Exception:
                    pass
        i += 4
    return out

for c in cands[:4]:
    off = c["off"]; ln = c["len"]
    print("\n" + "=" * 72)
    print("文本: %r" % c["text"][:80])
    print("off=%d len=%d line_cls=%s" % (off, ln, c.get("line_cls")))
    print("该位置原文校验: %r" % raw[off:off+ln].decode("utf-8", "replace")[:80])
    print("--- 前后字符串序列 ---")
    for p, t in lp_around(raw, off):
        mark = "  <<< 目标" if abs(p - off) < 4 else ""
        print("   %-8d %r%s" % (p, t[:90], mark))
    print("--- 原始字节（目标前 24 字节）---")
    print("   ", raw[max(0, off-24):off].hex(" "))

# 找一条很短的、可能是单词的条目
print("\n" + "=" * 72)
print("短条目（<=12 字符）在 occ 中的分布")
print("=" * 72)
short = [o for o in occ if len(o["text"]) <= 12 and re.fullmatch(r"[A-Za-z][A-Za-z' \-\?\!\.]*", o["text"])]
print("短英文条目数: %d" % len(short))
from collections import Counter
print("样本:", Counter(o["text"] for o in short).most_common(40))
