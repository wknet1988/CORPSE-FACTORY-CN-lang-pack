# -*- coding: utf-8 -*-
"""以 linehash 为锚点，正向定位全部展示文本槽。
hash 是长度前缀的 8 位小写十六进制串，特征极强，不会失步。
text 槽 = align4(hash 结束位置) 处的 length-prefixed 字符串。
"""
import os, re, struct, json
from collections import defaultdict, Counter
import UnityPy

GAME = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY"
BACKUP = os.path.join(GAME, "CORPSE FACTORY_Data", "backup_original", "resources.assets")
HERE = os.path.dirname(os.path.abspath(__file__))
CJK = re.compile(r"[\u4e00-\u9fff]")

true_scripts = json.load(open(os.path.join(HERE, "true_scripts.json"), encoding="utf-8"))
pids = {t["pid"]: t["name"] for t in true_scripts}
tr = json.load(open(os.path.join(HERE, "translations_complete.json"), encoding="utf-8"))

def align4(n): return (n + 3) & ~3

HEXSET = set(b"0123456789abcdef")

def find_hashes(b):
    """返回 [(prefix_pos, hash_str, end_pos)]"""
    out = []
    n = len(b)
    i = 0
    while i + 12 <= n:
        L = struct.unpack_from("<i", b, i)[0]
        if 6 <= L <= 8 and i + 4 + L <= n:
            seg = b[i+4:i+4+L]
            if all(c in HEXSET for c in seg):
                out.append((i, seg.decode(), i + 4 + L))
                i += 4 + L
                continue
        i += 1
    return out

def read_text_at(b, p):
    if p + 4 > len(b): return None
    n = struct.unpack_from("<i", b, p)[0]
    if n <= 0 or n > 4000 or p + 4 + n > len(b): return None
    seg = b[p+4:p+4+n]
    if any(c < 0x20 and c not in (9, 10, 13) for c in seg): return None
    try:
        return seg.decode("utf-8")
    except Exception:
        return None

env = UnityPy.load(BACKUP)
raws = {}
for o in env.objects:
    if o.path_id in pids:
        raws[o.path_id] = o.get_raw_data()

slots = []       # (pid, prefix_pos, text)
for pid, raw in raws.items():
    for hp, hs, hend in find_hashes(raw):
        tp = align4(hend)
        t = read_text_at(raw, tp)
        if t is None: continue
        if not t: continue
        slots.append((pid, tp, t))

print("定位到文本槽: %d" % len(slots))
uniq = set(t for _, _, t in slots)
print("唯一文本: %d" % len(uniq))
in_tr = [t for t in uniq if t in tr]
cn = [t for t in uniq if CJK.search(t)]
print("  在译文表: %d (%.1f%%) | 已含中文: %d" % (len(in_tr), 100.0*len(in_tr)/max(1,len(uniq)), len(cn)))

need = sorted([t for t in uniq if t not in tr and not CJK.search(t)], key=lambda s: (len(s), s))
print("\n**未译: %d**" % len(need))
byw = defaultdict(list)
for t in need: byw[min(len(t.split()), 5)].append(t)
for w in sorted(byw):
    print("\n--- %s : %d ---" % ("%d 词" % w if w < 5 else "5+ 词", len(byw[w])))
    for t in byw[w][:60]:
        locs = [(p, o) for p, o, tt in slots if tt == t]
        src = sorted({pids[p] for p, _ in locs})
        print("   x%-4d %-46r %s" % (len(locs), t[:46], src[:2]))

json.dump({"slots": [{"pid": p, "off": o, "text": t} for p, o, t in slots],
           "need": need},
          open(os.path.join(HERE, "text_slots.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("\n-> text_slots.json")
