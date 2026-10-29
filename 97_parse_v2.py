# -*- coding: utf-8 -*-
"""复用 80_verify 的已验证解析器（23/23 通过），收集 GenericTextScriptLine 的 body 首串 = 展示文本。"""
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

LINE = [b'CommandScriptLine', b'CommentScriptLine', b'LabelScriptLine',
        b'GenericTextScriptLine', b'EmptyScriptLine']
KNOWN = {c.decode() for c in LINE}

def align4(n): return (n + 3) & ~3

class Bad(Exception): pass

def rd_i32(b, p, limit):
    if p + 4 > limit: raise Bad("i32 OOB")
    return struct.unpack_from("<i", b, p)[0], p + 4

def rd_str(b, p, limit):
    if p + 4 > limit: raise Bad("str OOB")
    n = struct.unpack_from("<i", b, p)[0]
    if n < 0 or p + 4 + n > limit: raise Bad("str body OOB")
    try:
        t = b[p+4:p+4+n].decode("utf-8")
    except Exception:
        raise Bad("not utf8")
    return t, align4(p + 4 + n)

def walk_body_collect(b, p, limit):
    """与 80_verify 的 parse_body_generic 完全一致，额外收集字符串"""
    strs = []
    while p < limit:
        if p + 4 > limit: raise Bad("body tail OOB")
        n = struct.unpack_from("<i", b, p)[0]
        if 0 <= n <= (limit - p - 4):
            chunk = b[p+4:p+4+n]
            try:
                t = chunk.decode("utf-8")
                printable = sum(1 for c in t if (32 <= ord(c) < 127) or ord(c) > 127)
                if printable >= max(1, len(t) * 0.6):
                    if n > 0:
                        strs.append((p + 4, t))
                    p = align4(p + 4 + n)
                    continue
            except Exception:
                pass
        p += 4
    return p, strs

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

def extract(raw):
    out = []
    ms = find_markers(raw)
    limit = len(raw)
    for i, p in enumerate(ms):
        nxt = ms[i+1] if i+1 < len(ms) else limit
        try:
            ln = struct.unpack_from("<i", raw, p)[0]
            if ln <= 0 or ln > 64: continue
            cls = raw[p+4:p+4+ln].decode("utf-8", "replace")
            if cls not in KNOWN: continue
            p2 = align4(p + 4 + ln)
            _, p2 = rd_str(raw, p2, limit)   # ns
            _, p2 = rd_str(raw, p2, limit)   # asm
            _, p2 = rd_i32(raw, p2, limit)   # flags
            h, p2 = rd_str(raw, p2, limit)   # linehash
            end, strs = walk_body_collect(raw, p2, nxt)
            if end != nxt: continue          # 结构不吻合，丢弃该元素
            if cls == "GenericTextScriptLine" and strs:
                out.append((h, strs[0][0], strs[0][1]))
        except Bad:
            continue
    return out

env = UnityPy.load(BACKUP)
rows = []
for o in env.objects:
    if o.path_id not in pids: continue
    raw = o.get_raw_data()
    for h, off, t in extract(raw):
        rows.append((o.path_id, h, off, t))

print("GenericTextScriptLine 文本: %d" % len(rows))
uniq = set(r[3] for r in rows)
print("唯一: %d" % len(uniq))
in_tr = [t for t in uniq if t in tr]
cn = [t for t in uniq if CJK.search(t)]
print("在译文表: %d (%.1f%%) | 含中文: %d | 两者皆非: %d"
      % (len(in_tr), 100.0*len(in_tr)/max(1,len(uniq)), len(cn),
         len([t for t in uniq if t not in tr and not CJK.search(t)])))

need = sorted([t for t in uniq if t not in tr and not CJK.search(t)], key=lambda s: (len(s), s))
print("\n**未译: %d**" % len(need))
for t in need:
    locs = [(p, o) for p, _, o, tt in rows if tt == t]
    src = sorted({pids[p] for p, _ in locs})
    print("   x%-4d %-50r %s" % (len(locs), t[:50], src[:2]))

json.dump({"rows": [{"pid": p, "hash": h, "off": o, "text": t} for p, h, o, t in rows],
           "need": need},
          open(os.path.join(HERE, "gen_text_v2.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("\n-> gen_text_v2.json")
