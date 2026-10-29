# -*- coding: utf-8 -*-
"""正向逐元素解析（唯一可靠方式）。
元素结构: [i32 len][className][ns][asm][i32 flags][hash] + body
GenericTextScriptLine 的 body 第一个字符串 = 展示文本。
用「body首串命中译文表的比例」自校验解析是否正确。
"""
import os, re, struct, json
from collections import defaultdict
import UnityPy

GAME = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY"
BACKUP = os.path.join(GAME, "CORPSE FACTORY_Data", "backup_original", "resources.assets")
HERE = os.path.dirname(os.path.abspath(__file__))
CJK = re.compile(r"[\u4e00-\u9fff]")

true_scripts = json.load(open(os.path.join(HERE, "true_scripts.json"), encoding="utf-8"))
pids = {t["pid"]: t["name"] for t in true_scripts}
tr = json.load(open(os.path.join(HERE, "translations_complete.json"), encoding="utf-8"))

LINE = [b"CommandScriptLine", b"CommentScriptLine", b"LabelScriptLine",
        b"GenericTextScriptLine", b"EmptyScriptLine"]

def align4(n): return (n + 3) & ~3

def find_markers(b):
    ms = []
    for c in LINE:
        pat = struct.pack("<i", len(c)) + c
        s = 0
        while True:
            p = b.find(pat, s)
            if p < 0: break
            ms.append(p); s = p + 1
    ms.sort()
    return ms

def rd_i32(b, p):
    return struct.unpack_from("<i", b, p)[0], p + 4

def rd_str(b, p):
    n = struct.unpack_from("<i", b, p)[0]
    if n < 0 or p + 4 + n > len(b): return None, None
    try:
        t = b[p+4:p+4+n].decode("utf-8")
    except Exception:
        return None, None
    return t, align4(p + 4 + n)

def parse_object(raw):
    """返回 [(cls, hash, text, body_off)]"""
    out = []
    ms = find_markers(raw)
    for i, p in enumerate(ms):
        end = ms[i+1] if i+1 < len(ms) else len(raw)
        try:
            ln = struct.unpack_from("<i", raw, p)[0]
            if ln <= 0 or ln > 64: continue
            cls = raw[p+4:p+4+ln].decode("utf-8", "replace")
            p2 = align4(p + 4 + ln)
            ns, p2 = rd_str(raw, p2)
            if ns is None: continue
            asm, p2 = rd_str(raw, p2)
            if asm is None: continue
            flags, p2 = rd_i32(raw, p2)
            h, p2 = rd_str(raw, p2)
            if h is None: continue
            text = ""
            if p2 + 4 <= end:
                n = struct.unpack_from("<i", raw, p2)[0]
                if 0 < n <= (end - p2 - 4):
                    try:
                        text = raw[p2+4:p2+4+n].decode("utf-8")
                    except Exception:
                        text = ""
            out.append((cls, h, text, p2))
        except Exception:
            continue
    return out

env = UnityPy.load(BACKUP)
allrows = []
for o in env.objects:
    if o.path_id not in pids: continue
    raw = o.get_raw_data()
    for cls, h, text, boff in parse_object(raw):
        allrows.append((o.path_id, cls, h, text, boff))

from collections import Counter
print("解析元素总数: %d" % len(allrows))
print("按类型:", dict(Counter(c for _, c, _, _, _ in allrows)))

gen = [(pid, h, t, bo) for pid, cls, h, t, bo in allrows if cls == "GenericTextScriptLine"]
print("\nGenericTextScriptLine: %d" % len(gen))
uniq = set(t for _, _, t, _ in gen if t)
in_tr = [t for t in uniq if t in tr]
cn = [t for t in uniq if CJK.search(t)]
print("唯一展示文本: %d | 在译文表中: %d (%.1f%%) | 含中文: %d"
      % (len(uniq), len(in_tr), 100.0 * len(in_tr) / max(1, len(uniq)), len(cn)))

need = sorted([t for t in uniq if t not in tr and not CJK.search(t)], key=lambda s: (len(s), s))
print("\n**未译展示文本: %d**" % len(need))
for t in need:
    locs = [(pid, bo) for pid, _, tt, bo in gen if tt == t]
    src = sorted({pids[p] for p, _ in locs})
    print("   x%-4d %-46r %s" % (len(locs), t[:46], src[:3]))

json.dump({"rows": [{"pid": p, "hash": h, "text": t, "off": bo} for p, _, h, t, bo in gen],
           "need": need},
          open(os.path.join(HERE, "gen_parsed.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("\n-> gen_parsed.json")
