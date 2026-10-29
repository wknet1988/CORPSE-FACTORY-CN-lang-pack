# -*- coding: utf-8 -*-
"""1) 列出 122 条「已提取但未译」的文本
2) 用结构校验（80_verify 同款）筛出真正的 Naninovel 脚本对象 pid
3) 只在这些对象里扫全部字符串（含单词），列出未译项
"""
import os, re, struct, json
from collections import Counter, defaultdict
import UnityPy

GAME = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY"
BACKUP = os.path.join(GAME, "CORPSE FACTORY_Data", "backup_original", "resources.assets")
HERE = os.path.dirname(os.path.abspath(__file__))
CJK = re.compile(r"[\u4e00-\u9fff]")

tr = json.load(open(os.path.join(HERE, "translations_complete.json"), encoding="utf-8"))
occ = json.load(open(os.path.join(HERE, "occurrences.json"), encoding="utf-8"))
uniq = set(o["text"] for o in occ)
miss = sorted([t for t in uniq if t not in tr], key=lambda s: (len(s), s))
print("=" * 72)
print("1) 已提取但未译的 %d 条" % len(miss))
print("=" * 72)
for t in miss:
    print("   %r" % t[:110])

# ---------- 2) 真脚本对象 ----------
LINE = [b'CommandScriptLine', b'CommentScriptLine', b'LabelScriptLine',
        b'GenericTextScriptLine', b'EmptyScriptLine']
KNOWN = {c.decode() for c in LINE}
def align4(n): return (n + 3) & ~3
class Bad(Exception): pass

def rd_i32(b, p, limit):
    if p + 4 > limit: raise Bad("i32")
    return struct.unpack_from("<i", b, p)[0], p + 4

def rd_str(b, p, limit):
    if p + 4 > limit: raise Bad("str")
    n = struct.unpack_from("<i", b, p)[0]
    if n < 0 or p + 4 + n > limit: raise Bad("str body")
    try:
        t = b[p+4:p+4+n].decode("utf-8")
    except Exception:
        raise Bad("utf8")
    return t, align4(p + 4 + n)

def walk_body(b, p, limit):
    while p < limit:
        if p + 4 > limit: raise Bad("tail")
        n = struct.unpack_from("<i", b, p)[0]
        if 0 <= n <= (limit - p - 4):
            try:
                t = b[p+4:p+4+n].decode("utf-8")
                pr = sum(1 for c in t if (32 <= ord(c) < 127) or ord(c) > 127)
                if pr >= max(1, len(t) * 0.6):
                    p = align4(p + 4 + n); continue
            except Exception:
                pass
        p += 4
    return p

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

def verify(raw):
    markers = find_markers(raw)
    if not markers: return False, 0
    limit = len(raw)
    for i, p in enumerate(markers):
        nxt = markers[i+1] if i+1 < len(markers) else limit
        try:
            ln = struct.unpack_from("<i", raw, p)[0]
            if ln <= 0 or ln > 64: return False, 0
            cls = raw[p+4:p+4+ln].decode("utf-8", "replace")
            if cls not in KNOWN: return False, 0
            p2 = align4(p + 4 + ln)
            _, p2 = rd_str(raw, p2, limit)
            _, p2 = rd_str(raw, p2, limit)
            _, p2 = rd_i32(raw, p2, limit)
            _, p2 = rd_str(raw, p2, limit)
            end = walk_body(raw, p2, nxt)
            if end != nxt: return False, 0
        except Bad:
            return False, 0
    return True, len(markers)

env = UnityPy.load(BACKUP)
true_pids = []
for o in env.objects:
    if o.type.name != "MonoBehaviour": continue
    raw = o.get_raw_data()
    ok, n = verify(raw)
    if ok and n >= 2:
        # 取对象名
        try:
            nf = struct.unpack_from("<i", raw, 28)[0]
            name = raw[32:32+nf].decode("utf-8", "replace") if 0 < nf < 200 else ""
        except Exception:
            name = ""
        true_pids.append((o.path_id, name, n, len(raw)))

print("\n" + "=" * 72)
print("2) 真脚本对象: %d 个" % len(true_pids))
print("=" * 72)
for pid, name, n, sz in true_pids:
    print("   pid=%-6s name=%-28r markers=%-4d size=%d" % (pid, name[:28], n, sz))

json.dump([{"pid": p, "name": n, "markers": m, "size": s} for p, n, m, s in true_pids],
          open(os.path.join(HERE, "true_scripts.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

# ---------- 3) 只在这些对象里扫 ----------
print("\n" + "=" * 72)
print("3) 真脚本对象内未译文本（含单词）")
print("=" * 72)
DENY = {"Naninovel", "Elringus.Naninovel.Runtime", "Naninovel.Commands", "Naninovel.Script",
        "CommandScriptLine", "CommentScriptLine", "LabelScriptLine", "GenericTextScriptLine",
        "EmptyScriptLine", "UnityEngine", "Assembly-CSharp"}
HEX8 = re.compile(r"^[0-9a-fA-F]{8}$")

def scan_lp(b):
    out = []; n = len(b); i = 0
    while i + 4 <= n:
        L = struct.unpack_from("<i", b, i)[0]
        if 1 <= L <= 3000 and i + 4 + L <= n:
            seg = b[i+4:i+4+L]
            if not any(c < 0x20 and c not in (9, 10, 13) for c in seg):
                try:
                    t = seg.decode("utf-8")
                    out.append((i + 4, t)); i = align4(i + 4 + L); continue
                except Exception:
                    pass
        i += 4
    return out

res = defaultdict(list)
for pid, name, n, sz in true_pids:
    raw = env.objects_by_pid[pid].get_raw_data() if hasattr(env, "objects_by_pid") else None
    if raw is None:
        for o in env.objects:
            if o.path_id == pid:
                raw = o.get_raw_data(); break
    for off, t in scan_lp(raw):
        if t in tr or CJK.search(t): continue
        if t in DENY or t.startswith("@") or t.startswith("#"): continue
        if HEX8.match(t): continue
        if not re.search(r"[A-Za-z]", t): continue
        if re.search(r"(UnityEngine|Naninovel|Elringus|\.dll|\.assets|\.resS)", t): continue
        res[t].append((pid, off))

print("未译唯一文本: %d" % len(res))
buckets = defaultdict(list)
for t in res: buckets[min(len(t.split()), 4)].append(t)
for w in sorted(buckets):
    print("\n--- %s : %d ---" % ("%d 词" % w if w < 4 else "4+ 词", len(buckets[w])))
    for t in sorted(buckets[w], key=lambda s: (len(s), s))[:80]:
        print("   %r  pids=%s" % (t[:100], sorted({p for p, _ in res[t]})[:3]))

json.dump({t: res[t] for t in res},
          open(os.path.join(HERE, "gap_true_scripts.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
