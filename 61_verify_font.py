# -*- coding: utf-8 -*-
"""字体专项校验：pid 5209 是否已内嵌中文字集，覆盖译文全部用字"""
import io, json, os, sys
import UnityPy
from fontTools.ttLib import TTFont

BASE = os.path.dirname(os.path.abspath(__file__))
GAME = os.path.dirname(BASE)
DEPLOY = os.path.join(GAME, "CORPSE FACTORY_Data", "resources.assets")
ORIG = os.path.join(GAME, "CORPSE FACTORY_Data", "backup_original", "resources.assets")
FULL = os.path.join(BASE, "translations_full.json")

CJK = __import__("re").compile(r"[\u4e00-\u9fff]")

def font_obj(path):
    env = UnityPy.load(path)
    for obj in env.objects:
        if obj.type.name == "Font":
            tree = obj.read_typetree()
            yield obj, tree

print("=== DEPLOY fonts ===")
dep = {}
for obj, tree in font_obj(DEPLOY):
    name = tree.get("m_Name", "?")
    data = bytes(tree.get("m_FontData") or b"")
    print("  pid %s  name=%s  m_FontData=%d bytes" % (obj.path_id, name, len(data)))
    dep[name] = (obj.path_id, data)

print("\n=== ORIGINAL fonts ===")
for obj, tree in font_obj(ORIG):
    name = tree.get("m_Name", "?")
    data = bytes(tree.get("m_FontData") or b"")
    print("  pid %s  name=%s  m_FontData=%d bytes" % (obj.path_id, name, len(data)))

# 找最大的那份（嵌入的中文字体）
cand = max(dep.items(), key=lambda kv: len(kv[1][1]))
name, (pid, data) = cand
print("\n=== ANALYZE %s (pid %s) ===" % (name, pid))
print("  size: %d bytes" % len(data))
print("  TTF magic ok: %s" % (data[:4] == b"\x00\x01\x00\x00"))
print("  has glyf: %s | has CFF: %s" % (b"glyf" in data, b"CFF " in data))

f = TTFont(io.BytesIO(data))
cmap = set()
for t in f["cmap"].tables:
    cmap |= set(t.cmap.keys())
print("  cmap glyph count: %d" % len(cmap))
print("  font name: %s" % (f["name"].getDebugName(4) or f["name"].getDebugName(1)))

trans = json.load(open(FULL, encoding="utf-8"))
zh = {k: v for k, v in trans.items() if CJK.search(v or "")}
need = {}
for k, v in zh.items():
    for ch in v:
        if ord(ch) > 127:
            need[ord(ch)] = need.get(ord(ch), 0) + 1

missing = {c: n for c, n in need.items() if c not in cmap}
print("\n  distinct non-ascii chars used: %d" % len(need))
print("  missing from font: %d" % len(missing))
if missing:
    for c, n in sorted(missing.items()):
        try:
            print("    U+%04X  %r  x%d" % (c, chr(c), n))
        except Exception:
            print("    U+%04X  ?  x%d" % (c, n))

# 检查常见标点是否在
for ch in "，。！？；：、“”‘’（）《》…—·":
    print("  punct %r in cmap: %s" % (ch, ord(ch) in cmap))
