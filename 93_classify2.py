# -*- coding: utf-8 -*-
"""修正版分类：候选词前面必须依次是 [GenericTextScriptLine, Naninovel, Elringus..., hash]
hash 允许 6~8 位十六进制。只有满足者才算展示文本，并给出精确 (pid, offset)。"""
import os, re, struct, json
from collections import defaultdict
import UnityPy

GAME = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY"
BACKUP = os.path.join(GAME, "CORPSE FACTORY_Data", "backup_original", "resources.assets")
HERE = os.path.dirname(os.path.abspath(__file__))
CJK = re.compile(r"[\u4e00-\u9fff]")
HASH = re.compile(r"^[0-9a-f]{6,8}$")

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

GEN, NS, ASM = "GenericTextScriptLine", "Naninovel", "Elringus.Naninovel.Runtime"

def verdict(pid, cp):
    raw = raws[pid]
    win = [w for w in scan_lp(raw, max(0, cp - 320), cp) if w[1] <= cp]
    if len(win) < 4: return None
    a, b, c, d = win[-4][2], win[-3][2], win[-2][2], win[-1][2]
    if a == GEN and b == NS and c == ASM and HASH.match(d):
        return "TEXT"
    if b == "Naninovel.Commands" or "Command" in a:
        return "CMD"
    return "?"

# 候选：脚本对象里 1~24 字符、无空格、非中文、未译
cand = set()
for pid, raw in raws.items():
    for pp, cp, t in scan_lp(raw):
        if not t or t in tr or CJK.search(t): continue
        if len(t) < 2 or len(t) > 24: continue
        if " " in t: continue
        cand.add(t)
print("候选串: %d" % len(cand))

texts, cmds, unknown = {}, {}, {}
for pid, raw in raws.items():
    for pp, cp, t in scan_lp(raw):
        if t not in cand: continue
        v = verdict(pid, cp)
        if v == "TEXT":
            texts.setdefault(t, []).append((pid, cp))
        elif v == "CMD":
            cmds[t] = cmds.get(t, 0) + 1
        else:
            unknown[t] = unknown.get(t, 0) + 1

print("\n=== 判定为展示文本：%d 个 ===" % len(texts))
for t in sorted(texts, key=lambda s: (-len(texts[s]), s)):
    locs = texts[t]
    src = sorted({pids[p] for p, _ in locs})
    print("   x%-4d %-20r %s" % (len(locs), t, src[:3]))

print("\n=== 判定为命令名（跳过）：%d 个 ===" % len(cmds))
print("   " + ", ".join("%s(%d)" % (k, v) for k, v in sorted(cmds.items(), key=lambda kv: -kv[1])[:40]))

print("\n=== 未判定（需人工看）：%d 个 ===" % len(unknown))
for t in sorted(unknown, key=lambda s: -unknown[s])[:40]:
    print("   x%-4d %r" % (unknown[t], t))

json.dump({"texts": {t: texts[t] for t in texts},
           "cmds": cmds, "unknown": unknown},
          open(os.path.join(HERE, "words_v2.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("\n-> words_v2.json")
