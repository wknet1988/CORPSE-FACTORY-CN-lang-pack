# -*- coding: utf-8 -*-
"""1) 枚举 resources.assets 全部对象类型
2) 导出所有 TextAsset 的 m_Name 与内容片段（找 Naninovel managed text）
3) 修正后的 GenericTextScriptLine 布局探针
"""
import os, re, struct
from collections import Counter
import UnityPy

GAME = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY"
BACKUP = os.path.join(GAME, "CORPSE FACTORY_Data", "backup_original", "resources.assets")
HERE = os.path.dirname(os.path.abspath(__file__))
CJK = re.compile(r"[\u4e00-\u9fff]")

env = UnityPy.load(BACKUP)

print("=" * 72)
print("1) 对象类型统计")
print("=" * 72)
typ = Counter()
for o in env.objects:
    typ[o.type.name] += 1
for t, c in typ.most_common():
    print("  %-28s %6d" % (t, c))

print("\n" + "=" * 72)
print("2) TextAsset 清单（名称 + 内容特征）")
print("=" * 72)
ta = []
for o in env.objects:
    if o.type.name != "TextAsset":
        continue
    try:
        d = o.read()
        name = getattr(d, "m_Name", "?")
        script = getattr(d, "m_Script", None)
        if isinstance(script, str):
            body = script
        elif isinstance(script, (bytes, bytearray)):
            body = bytes(script).decode("utf-8", "replace")
        else:
            body = str(script)
    except Exception as e:
        print("  pid=%s read error %s" % (o.path_id, e))
        continue
    ta.append((o.path_id, name, body))

print("TextAsset 总数: %d" % len(ta))
for pid, name, body in ta:
    has_cn = bool(CJK.search(body))
    print("  pid=%-6s %-32s len=%-7d 中文=%s" % (pid, name[:32], len(body), "Y" if has_cn else "N"))

print("\n" + "=" * 72)
print("3) 含英文 UI 关键词的 TextAsset 内容预览")
print("=" * 72)
KEY = ["Save", "Load", "Quit", "Backlog", "Settings", "Continue", "Auto", "Skip",
       "Title", "New Game", "Menu", "Yes", "No", "Cancel", "Return", "Chapter"]
for pid, name, body in ta:
    hits = [k for k in KEY if k in body]
    if not hits:
        continue
    print("\n--- pid=%s name=%r len=%d 关键词=%s ---" % (pid, name, len(body), hits))
    lines = body.splitlines()
    print("    行数=%d" % len(lines))
    for ln in lines[:25]:
        print("      " + ln[:100])
    if len(lines) > 25:
        print("      ... 省略 %d 行" % (len(lines) - 25))

# 保存全部 TextAsset 以便后续处理
import json
json.dump([{"pid": p, "name": n, "body": b} for p, n, b in ta],
          open(os.path.join(HERE, "textassets.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("\n-> textassets.json 已写出（%d 个）" % len(ta))

print("\n" + "=" * 72)
print("4) GenericTextScriptLine 段内字符串布局（修正版）")
print("=" * 72)
LINE_CLASSES = [b"CommandScriptLine", b"CommentScriptLine", b"LabelScriptLine",
                b"GenericTextScriptLine", b"EmptyScriptLine"]
GEN = struct.pack("<i", len(b"GenericTextScriptLine")) + b"GenericTextScriptLine"

def fast_strings(b, start, end):
    i = start; out = []
    while i + 4 <= end:
        ln = struct.unpack_from("<i", b, i)[0]
        if 0 < ln <= 100000 and i + 4 + ln <= end:
            try:
                t = b[i+4:i+4+ln].decode("utf-8")
            except Exception:
                i += 4; continue
            if sum(1 for c in t if 32 <= ord(c) < 127 or ord(c) > 127) >= len(t) * 0.8:
                out.append((i, i+4+ln, t)); i = (i+4+ln+3) & ~3; continue
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

shown = 0
for o in env.objects:
    if shown >= 10 or o.type.name != "MonoBehaviour":
        continue
    try:
        raw = o.get_raw_data()
    except Exception:
        continue
    for (s, e) in find_elements(raw):
        if shown >= 10:
            break
        if raw[s:s+len(GEN)] != GEN:
            continue
        seg = raw[s:e]
        strs = [(off, t) for off, _e, t in fast_strings(seg, 0, len(seg))
                if t not in ("GenericTextScriptLine", "Naninovel",
                             "Elringus.Naninovel.Runtime", "Naninovel.ScriptLines")]
        print("  pid=%s seglen=%d strings=%d" % (o.path_id, len(seg), len(strs)))
        for off, t in strs[:7]:
            print("      +%-5d %r" % (off, t[:95]))
        shown += 1
