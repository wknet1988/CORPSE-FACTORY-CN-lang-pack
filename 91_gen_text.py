# -*- coding: utf-8 -*-
"""精确提取 GenericTextScriptLine 的展示文本（含单字母/单词）。
特征序列: 'GenericTextScriptLine' → 'Naninovel' → 'Elringus.Naninovel.Runtime' → hash(8hex) → TEXT
同时 dump 非脚本对象里 LOG/SKIP/AUTO/HIDE 的上下文，判断是否为 TMP 文本组件。
"""
import os, re, struct, json
from collections import defaultdict, Counter
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
        if 0 <= L <= 8000 and i + 4 + L <= n:
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

texts = defaultdict(list)   # text -> [(pid, content_pos)]
for pid, raw in raws.items():
    seq = scan_lp(raw)
    for i in range(len(seq) - 4):
        if seq[i][2] != GEN: continue
        if seq[i+1][2] != NS: continue
        if seq[i+2][2] != ASM: continue
        if not HEX8.match(seq[i+3][2]): continue
        t = seq[i+4][2]
        if not t: continue
        texts[t].append((pid, seq[i+4][1]))

print("GenericTextScriptLine 展示文本: %d 个唯一值" % len(texts))
uniq = set(texts)
in_tr = [t for t in uniq if t in tr]
not_tr = [t for t in uniq if t not in tr]
has_cn = [t for t in not_tr if CJK.search(t)]
need = [t for t in not_tr if not CJK.search(t)]
print("  已译: %d | 未译(英文): %d | 已中文: %d" % (len(in_tr), len(need), len(has_cn)))

print("\n" + "=" * 72)
print("未译展示文本（%d 条）" % len(need))
print("=" * 72)
buckets = defaultdict(list)
for t in need: buckets[min(len(t.split()), 5)].append(t)
for w in sorted(buckets):
    print("\n--- %s : %d ---" % ("%d 词" % w if w < 5 else "5+ 词", len(buckets[w])))
    for t in sorted(buckets[w], key=lambda s: (len(s), s)):
        p = sorted({pids[q] for q, _ in texts[t]})
        print("   x%-3d %-58r %s" % (len(texts[t]), t[:58], p[:2]))

json.dump({t: texts[t] for t in need},
          open(os.path.join(HERE, "need_translate.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("\n-> need_translate.json 已写出")

# ---------- UI 标签上下文 ----------
print("\n" + "=" * 72)
print("UI 标签 LOG/SKIP/AUTO/HIDE 上下文（非脚本对象）")
print("=" * 72)
for w in ["LOG", "SKIP", "AUTO", "HIDE"]:
    print("\n=== %s ===" % w)
    pat = struct.pack("<i", len(w)) + w.encode()
    shown = 0
    for o in env.objects:
        if o.type.name != "MonoBehaviour" or o.path_id in pids: continue
        r = o.get_raw_data()
        q = r.find(pat)
        if q < 0: continue
        seq = scan_lp(r[max(0, q - 220): q + 260])
        print("  pid=%s off=%d 附近:" % (o.path_id, q))
        for _pp, _cp, t in seq[:16]:
            mark = "  <<<" if t == w else ""
            print("     %r%s" % (t[:60], mark))
        shown += 1
        if shown >= 2: break
