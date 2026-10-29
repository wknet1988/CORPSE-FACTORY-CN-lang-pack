# -*- coding: utf-8 -*-
"""对候选单词逐个分类：看它前面 4 个字符串是否为
   [GenericTextScriptLine, Naninovel, Elringus.Naninovel.Runtime, 8位hash]
是 → 展示文本；若是 CommandScriptLine/Naninovel.Commands → 命令名，跳过。
"""
import os, re, struct, json
from collections import defaultdict
import UnityPy

GAME = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY"
BACKUP = os.path.join(GAME, "CORPSE FACTORY_Data", "backup_original", "resources.assets")
HERE = os.path.dirname(os.path.abspath(__file__))
CJK = re.compile(r"[\u4e00-\u9fff]")
HEX8 = re.compile(r"^[0-9a-f]{8}$")

true_scripts = json.load(open(os.path.join(HERE, "true_scripts.json"), encoding="utf-8"))
pids = {t["pid"]: t["name"] for t in true_scripts}
tr = json.load(open(os.path.join(HERE, "translations_complete.json"), encoding="utf-8"))

def align4(n): return (n + 3) & ~3

def scan_lp(b, start=0, end=None):
    if end is None: end = len(b)
    out = []; i = start
    while i + 4 <= end:
        L = struct.unpack_from("<i", b, i)[0]
        if 0 <= L <= 8000 and i + 4 + L <= end:
            seg = b[i+4:i+4+L]
            if not any(c < 0x20 and c not in (9, 10, 13) for c in seg):
                try:
                    t = seg.decode("utf-8")
                    out.append((i, i + 4, t)); i = align4(i + 4 + L); continue
                except Exception:
                    pass
        i += 4
    return out

env = UnityPy.load(BACKUP)
raws = {}
for o in env.objects:
    if o.path_id in pids:
        raws[o.path_id] = o.get_raw_data()

GEN = "GenericTextScriptLine"
NS = "Naninovel"
ASM = "Elringus.Naninovel.Runtime"

# 候选：无空格、2~20 字符、字母开头、非全大写ID、非 camelCase
cand = set()
for pid, raw in raws.items():
    for pp, cp, t in scan_lp(raw):
        if not t or len(t) < 2 or len(t) > 20: continue
        if " " in t or t in tr or CJK.search(t): continue
        if not re.fullmatch(r"[A-Za-z][A-Za-z'\-]*", t): continue
        if t.isupper() and len(t) > 2: continue
        if re.match(r"^[a-z]+[A-Z]", t): continue
        cand.add(t)

print("候选词: %d" % len(cand))

def classify(pid, cp):
    """看 cp 前面 4 个字符串"""
    raw = raws[pid]
    win = scan_lp(raw, max(0, cp - 260), cp)
    # 只保留内容位置在 cp 之前的
    win = [w for w in win if w[1] <= cp]
    if len(win) < 4:
        return "?"
    a, b, c, d = win[-4][2], win[-3][2], win[-2][2], win[-1][2]
    if a == GEN and b == NS and c == ASM and HEX8.match(d):
        return "TEXT"
    if "Command" in a or b == "Naninovel.Commands":
        return "CMD"
    return "OTHER:%s|%s|%s|%s" % (a[:16], b[:12], c[:12], d[:8])

result = defaultdict(lambda: defaultdict(int))
locs = defaultdict(list)
for pid, raw in raws.items():
    for pp, cp, t in scan_lp(raw):
        if t not in cand: continue
        k = classify(pid, cp)
        result[t][k] += 1
        if k == "TEXT":
            locs[t].append((pid, cp))

texts = sorted([t for t in result if result[t].get("TEXT", 0) > 0])
print("\n判定为「展示文本」的: %d 个" % len(texts))
for t in texts:
    print("   %-16r TEXT=%-3d 其他=%s" % (t, result[t]["TEXT"],
          {k: v for k, v in result[t].items() if k != "TEXT"}))

print("\n判定为「命令名」的（跳过）:")
for t in sorted(result):
    if result[t].get("TEXT", 0) == 0 and result[t].get("CMD", 0) > 0:
        print("   %-16r CMD=%d" % (t, result[t]["CMD"]))

json.dump({"texts": texts, "locs": {t: locs[t] for t in texts}},
          open(os.path.join(HERE, "words_classified.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("\n-> words_classified.json 已写出")
