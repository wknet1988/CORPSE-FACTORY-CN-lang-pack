# -*- coding: utf-8 -*-
"""1) 定位 pid=9127 里单字母 'Q' 的上下文（排除字符表噪音）
2) 枚举 23 个脚本对象中「无空格/无结尾标点/2~14 字符」的未译候选"""
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

def scan_lp(b):
    out = []; n = len(b); i = 0
    while i + 4 <= n:
        L = struct.unpack_from("<i", b, i)[0]
        if 0 <= L <= 6000 and i + 4 + L <= n:
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

raw = raws[9127]
print("=" * 72)
print("1) pid=9127 中 'Q' 的上下文")
print("=" * 72)
pat = struct.pack("<i", 1) + b"Q"
cnt = 0
s = 0
while cnt < 3:
    p = raw.find(pat, s)
    if p < 0: break
    s = p + 1
    seq = scan_lp(raw[max(0, p - 400): p + 400])
    print("\n  off=%d 附近字符串:" % p)
    for pp, cp, t in seq[:22]:
        mark = " <<<" if t == "Q" else ""
        print("     %r%s" % (t[:60], mark))
    cnt += 1

print("\n" + "=" * 72)
print("2) 无空格、无结尾标点、2~14 字符的未译候选")
print("=" * 72)
DENY = {"Naninovel", "Elringus.Naninovel.Runtime", "Naninovel.Commands", "Naninovel.Script",
        "CommandScriptLine", "CommentScriptLine", "LabelScriptLine", "GenericTextScriptLine",
        "EmptyScriptLine", "UnityEngine", "Assembly-CSharp", "MainScript"}
TERM = ".?!:)\"'”’…。！？"

cands = defaultdict(list)
for pid, r in raws.items():
    for pp, cp, t in scan_lp(r):
        if not t or t in tr or CJK.search(t): continue
        if len(t) < 2 or len(t) > 14: continue
        if " " in t: continue
        if t[-1] in TERM: continue
        if t in DENY or t.startswith("@") or t.startswith("#"): continue
        if HEX8.match(t): continue
        if not re.fullmatch(r"[A-Za-z][A-Za-z\-']*", t): continue
        if t.isupper() and len(t) > 2: continue       # 角色ID
        if re.match(r"^[a-z]+[A-Z]", t): continue     # camelCase
        cands[t].append((pid, cp))

print("候选: %d 个唯一值" % len(cands))
for t, locs in sorted(cands.items(), key=lambda kv: -len(kv[1])):
    print("   x%-4d %-18r %s" % (len(locs), t, sorted({pids[p] for p, _ in locs})[:3]))

json.dump({t: cands[t] for t in cands},
          open(os.path.join(HERE, "gap_words.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("\n-> gap_words.json 已写出")
