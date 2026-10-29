# -*- coding: utf-8 -*-
"""用「linehash(8位hex) 后紧跟的字符串 = 展示文本」这一精确特征，
在 23 个真脚本对象里找出所有未译展示文本（含单词短句）。"""
import os, re, struct, json
from collections import defaultdict, Counter
import UnityPy

GAME = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY"
BACKUP = os.path.join(GAME, "CORPSE FACTORY_Data", "backup_original", "resources.assets")
HERE = os.path.dirname(os.path.abspath(__file__))
CJK = re.compile(r"[\u4e00-\u9fff]")
HEX8 = re.compile(r"^[0-9a-f]{8}$")

true_scripts = json.load(open(os.path.join(HERE, "true_scripts.json"), encoding="utf-8"))
pids = [t["pid"] for t in true_scripts]
names = {t["pid"]: t["name"] for t in true_scripts}
tr = json.load(open(os.path.join(HERE, "translations_complete.json"), encoding="utf-8"))

def align4(n): return (n + 3) & ~3

def scan_lp(b):
    """返回 [(prefix_pos, content_pos, text)]"""
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
print("载入脚本对象: %d" % len(raws))

hits = defaultdict(list)      # text -> [(pid, content_pos)]
total_pairs = 0
for pid, raw in raws.items():
    seq = scan_lp(raw)
    for idx in range(len(seq) - 1):
        _pp, _cp, cur = seq[idx]
        _pp2, cp2, nxt = seq[idx + 1]
        if not HEX8.match(cur):
            continue
        if not nxt:
            continue
        total_pairs += 1
        if nxt in tr or CJK.search(nxt):
            continue
        hits[nxt].append((pid, cp2))

print("hash→文本 配对总数: %d" % total_pairs)
print("**未译展示文本: %d 个唯一值**\n" % len(hits))

buckets = defaultdict(list)
for t in hits:
    buckets[min(len(t.split()), 5)].append(t)
for w in sorted(buckets):
    print("--- %s : %d ---" % ("%d 词" % w if w < 5 else "5+ 词", len(buckets[w])))
    for t in sorted(buckets[w], key=lambda s: (len(s), s))[:90]:
        p = sorted({x[0] for x in hits[t]})
        print("   %-52r %s" % (t[:52], [names.get(q, q) for q in p][:2]))
    print()

json.dump({t: hits[t] for t in hits},
          open(os.path.join(HERE, "gap_display.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("-> gap_display.json 已写出")

# 同时统计「已译/未译」比例，验证该特征是否可信
allpairs = 0
known = 0
for pid, raw in raws.items():
    seq = scan_lp(raw)
    for idx in range(len(seq) - 1):
        if not HEX8.match(seq[idx][2]):
            continue
        nxt = seq[idx + 1][2]
        if not nxt:
            continue
        allpairs += 1
        if nxt in tr or CJK.search(nxt):
            known += 1
print("\n可信度: 配对 %d 中已译/已中文 %d (%.1f%%)" % (allpairs, known, 100.0 * known / max(1, allpairs)))
