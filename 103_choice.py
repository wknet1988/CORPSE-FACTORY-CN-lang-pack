# -*- coding: utf-8 -*-
"""检查 AddChoice 命令里的选项文本 —— 单词型选项最可能被过滤器漏掉。"""
import os, struct, json
from collections import defaultdict, Counter
import UnityPy

GAME = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY"
BACKUP = os.path.join(GAME, "CORPSE FACTORY_Data", "backup_original", "resources.assets")
HERE = os.path.dirname(os.path.abspath(__file__))
CJK = __import__("re").compile(r"[\u4e00-\u9fff]")

true_scripts = json.load(open(os.path.join(HERE, "true_scripts.json"), encoding="utf-8"))
pids = {t["pid"]: t["name"] for t in true_scripts}
tr = json.load(open(os.path.join(HERE, "translations_complete.json"), encoding="utf-8"))

env = UnityPy.load(BACKUP)
raws = {}
for o in env.objects:
    if o.path_id in pids:
        raws[o.path_id] = o.get_raw_data()

def align4(n): return (n + 3) & ~3

def scan_lp(b, start=0, end=None):
    if end is None: end = len(b)
    out = []; i = start
    while i + 4 <= end:
        L = struct.unpack_from("<i", b, i)[0]
        if 0 <= L <= 4000 and i + 4 + L <= end:
            seg = b[i+4:i+4+L]
            if not any(c < 0x20 and c not in (9, 10, 13) for c in seg):
                try:
                    t = seg.decode("utf-8")
                    out.append((i, i + 4, t)); i = align4(i + 4 + L); continue
                except Exception:
                    pass
        i += 4
    return out

pat = struct.pack("<i", len(b"AddChoice")) + b"AddChoice"
found = 0
print("=" * 76)
print("AddChoice 附近的字符串")
print("=" * 76)
for pid, raw in raws.items():
    s = 0
    while found < 12:
        q = raw.find(pat, s)
        if q < 0: break
        s = q + 1
        print("\n pid=%s (%s) @%d" % (pid, pids[pid], q))
        # 从 q 往后扫 300 字节
        for pp, cp, t in scan_lp(raw, q, min(len(raw), q + 400)):
            mark = ""
            if t not in tr and not CJK.search(t) and len(t) <= 40 and not t.startswith("@") \
               and "Naninovel" not in t and "Elringus" not in t and "Command" not in t:
                mark = "   <-- 候选未译"
            print("    %r%s" % (t[:70], mark))
        found += 1
    if found >= 12: break

print("\n" + "=" * 76)
print("全脚本中 1~3 词、全大写或首字母大写、未译、非命令的短串")
print("=" * 76)
# 用「前面不是 Naninovel.Commands」的粗略判断
cands = defaultdict(int)
for pid, raw in raws.items():
    for pp, cp, t in scan_lp(raw):
        if not t or t in tr or CJK.search(t): continue
        if len(t) < 2 or len(t) > 30: continue
        if t.startswith("@") or t.startswith("#"): continue
        if "Naninovel" in t or "Elringus" in t or "Command" in t: continue
        if not __import__("re").match(r"^[A-Za-z][A-Za-z' \-\.\?\!]*$", t): continue
        if len(t.split()) > 3: continue
        cands[t] += 1

print("候选 %d 种" % len(cands))
for t, c in sorted(cands.items(), key=lambda kv: -kv[1])[:60]:
    print("   x%-4d %r" % (c, t))
