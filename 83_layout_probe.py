# -*- coding: utf-8 -*-
"""布局探针：
1) 打印若干 GenericTextScriptLine 段内的全部字符串（找哪一个是展示文本）
2) 定位 UI 关键词（Continue/Settings/Skip...）属于哪个对象、周围上下文是什么
"""
import json, os, re, struct
import UnityPy

GAME = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY"
BACKUP = os.path.join(GAME, "CORPSE FACTORY_Data", "backup_original", "resources.assets")

LINE_CLASSES = [b"CommandScriptLine", b"CommentScriptLine", b"LabelScriptLine",
                b"GenericTextScriptLine", b"EmptyScriptLine"]

def fast_strings(b, start, end, minlen=1):
    i = start; out = []
    while i + 4 <= end:
        ln = struct.unpack_from("<i", b, i)[0]
        if 0 < ln <= 100000 and i + 4 + ln <= end:
            s = b[i+4:i+4+ln]
            try:
                t = s.decode("utf-8")
            except Exception:
                i += 4; continue
            if sum(1 for c in t if 32 <= ord(c) < 127 or ord(c) > 127) >= len(t) * 0.8:
                out.append((i, i + 4 + ln, t)); i = (i + 4 + ln + 3) & ~3; continue
        i += 4
    return out

def find_elements(b):
    markers = []
    for cls in LINE_CLASSES:
        pat = struct.pack("<i", len(cls)) + cls
        st = 0
        while True:
            p = b.find(pat, st)
            if p < 0: break
            markers.append(p); st = p + 1
    markers.sort()
    return [(markers[i], markers[i+1] if i+1 < len(markers) else len(b)) for i in range(len(markers))]

env = UnityPy.load(BACKUP)
objs = {}
for obj in env.objects:
    if obj.type.name != "MonoBehaviour":
        continue
    try:
        objs[obj.path_id] = obj.get_raw_data()
    except Exception:
        pass
print("MonoBehaviour objects loaded: %d" % len(objs))

# ---------- 1) GenericTextScriptLine 段内字符串布局 ----------
print("\n" + "=" * 72)
print("1) GenericTextScriptLine 段内字符串布局（前 12 段）")
print("=" * 72)
shown = 0
for pid, raw in objs.items():
    if shown >= 12: break
    elems = find_elements(raw)
    if not elems: continue
    for (s, e) in elems:
        if shown >= 12: break
        seg = raw[s:e]
        if seg[:4] != struct.pack("<i", len(b"GenericTextScriptLine")) + b"GenericTextScriptLine":
            continue
        strs = fast_strings(seg, 0, len(seg))
        # 过滤掉结构串
        keep = [(o, t) for o, _e, t in strs if t not in
                ("GenericTextScriptLine", "Naninovel", "Elringus.Naninovel.Runtime",
                 "Naninovel.ScriptLines", "Naninovel.Commands")]
        print("  pid=%s seglen=%d  strings=%d" % (pid, len(seg), len(keep)))
        for o, t in keep[:8]:
            print("      off+%-5d %r" % (o, t[:90]))
        shown += 1

# ---------- 2) UI 关键词归属 ----------
print("\n" + "=" * 72)
print("2) UI 关键词归属对象与上下文")
print("=" * 72)
words = ["Continue", "Settings", "Skip", "Cancel", "Title", "Fullscreen", "Quit",
         "Backlog", "Save", "Load", "New Game", "Main Menu", "Yes", "No"]
for w in words:
    pat = struct.pack("<i", len(w.encode())) + w.encode()
    owners = []
    for pid, raw in objs.items():
        p = raw.find(pat)
        if p >= 0:
            owners.append((pid, p))
    if not owners:
        print("\n  %-12r 未在任何 MonoBehaviour 中" % w)
        continue
    print("\n  %-12r 出现于 %d 个对象: %s" % (w, len(owners), owners[:6]))
    pid, p = owners[0]
    raw = objs[pid]
    ctx = raw[max(0, p - 90): p + len(w) + 120]
    # 打印上下文里所有可读字符串
    near = fast_strings(raw, max(0, p - 400), min(len(raw), p + 400))
    print("     附近字符串:")
    for o, _e, t in near[:14]:
        mark = "  <<<" if t == w else ""
        print("       +%-5d %r%s" % (o - max(0, p - 400), t[:80], mark))
