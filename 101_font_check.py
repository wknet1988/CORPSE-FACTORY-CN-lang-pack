# -*- coding: utf-8 -*-
"""检查 UI Text 对象引用的字体 pid，判断翻译后中文能否显示。"""
import os, struct, json
import UnityPy

GAME = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY"
BACKUP = os.path.join(GAME, "CORPSE FACTORY_Data", "backup_original", "resources.assets")
HERE = os.path.dirname(os.path.abspath(__file__))

FONTS = {5209: "AveriaSerifLibre-Regular(已换SimHei)", 5210: "PermanentMarker-Regular",
         5211: "Roboto-Regular", 5212: "AveriaSerifLibre-BoldItalic",
         5213: "AveriaSerifLibre-Bold", 5214: "AveriaSerifLibre-Light",
         5215: "LiberationSans"}

env = UnityPy.load(BACKUP)
ui = json.load(open(os.path.join(HERE, "ui_labels.json"), encoding="utf-8"))
pids = [r["pid"] for r in ui["rows"]]
print("待检查 UI 对象: %d" % len(pids))

objs = {}
for o in env.objects:
    if o.path_id in pids:
        objs[o.path_id] = o.get_raw_data()

from collections import Counter
hit = Counter()
nofont = []
for pid, raw in objs.items():
    found = []
    for fpid, fname in FONTS.items():
        pat = struct.pack("<i", fpid)
        if pat in raw:
            found.append(fpid)
    if found:
        for f in found: hit[f] += 1
    else:
        nofont.append(pid)

print("\n字体引用统计（在 UI 对象原始字节里出现的 pid）:")
for f, c in hit.most_common():
    print("   pid=%-5d %-32s 出现于 %d 个对象" % (f, FONTS[f], c))
print("\n未检出字体 pid 的对象: %d 个 %s" % (len(nofont), nofont[:10]))

# 详细看 3 个对象：把 i32 值全列出来，找 PPtr(fileID,pathID) 对
print("\n=== 详细：3 个 UI 对象的 i32 序列 ===")
for pid in pids[:3]:
    raw = objs[pid]
    print("\n pid=%s len=%d" % (pid, len(raw)))
    # 打印可读字符串 + 其后 8 字节（可能是 PPtr）
    i = 0
    n = len(raw)
    while i + 4 <= n:
        L = struct.unpack_from("<i", raw, i)[0]
        if 0 <= L <= 300 and i + 4 + L <= n:
            seg = raw[i+4:i+4+L]
            if not any(c < 0x20 and c not in (9, 10, 13) for c in seg):
                try:
                    t = seg.decode("utf-8")
                    nxt = (i + 4 + L + 3) & ~3
                    tail = raw[nxt:nxt+8]
                    vals = struct.unpack("<ii", tail) if len(tail) == 8 else ()
                    print("    @%-4d str %-24r  后8字节=%s" % (i, t[:24], vals))
                    i = nxt
                    continue
                except Exception:
                    pass
        i += 4
