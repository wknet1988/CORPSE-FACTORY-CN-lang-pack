# -*- coding: utf-8 -*-
"""对每个候选词：找到它前面最近的 className 标记，从该标记正向解析，
判断这个词是否是 GenericTextScriptLine 的 text 字段。"""
import os, struct, json
from collections import defaultdict
import UnityPy

GAME = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY"
BACKUP = os.path.join(GAME, "CORPSE FACTORY_Data", "backup_original", "resources.assets")
HERE = os.path.dirname(os.path.abspath(__file__))

LINE = [b'CommandScriptLine', b'CommentScriptLine', b'LabelScriptLine',
        b'GenericTextScriptLine', b'EmptyScriptLine']
MARKS = [(c, struct.pack("<i", len(c)) + c) for c in LINE]

true_scripts = json.load(open(os.path.join(HERE, "true_scripts.json"), encoding="utf-8"))
pids = {t["pid"]: t["name"] for t in true_scripts}

env = UnityPy.load(BACKUP)
raws = {}
for o in env.objects:
    if o.path_id in pids:
        raws[o.path_id] = o.get_raw_data()

def align4(n): return (n + 3) & ~3

def rd_str(b, p):
    if p + 4 > len(b): return None, None
    n = struct.unpack_from("<i", b, p)[0]
    if n < 0 or p + 4 + n > len(b): return None, None
    try:
        return b[p+4:p+4+n].decode("utf-8"), align4(p + 4 + n)
    except Exception:
        return None, None

def analyze(pid, raw, word_prefix):
    """word_prefix = 词的 i32 长度前缀位置"""
    # 找前面最近的 className 标记
    best = None
    for cls, pat in MARKS:
        s = 0
        while True:
            q = raw.rfind(pat, 0, word_prefix)
            if q < 0: break
            if best is None or q > best[0]:
                best = (q, cls)
            break
    if best is None:
        return None
    p, cls = best
    cls_name = cls.decode()
    # 从 p 解析
    ln = struct.unpack_from("<i", raw, p)[0]
    q = align4(p + 4 + ln)
    ns, q = rd_str(raw, q)
    asm, q = rd_str(raw, q)
    if ns is None or asm is None: return (cls_name, "解析失败")
    flags = struct.unpack_from("<i", raw, q)[0]; q += 4
    h, q = rd_str(raw, q)
    if h is None: return (cls_name, "hash失败")
    text, q2 = rd_str(raw, q)
    is_text_field = (q == word_prefix)
    return (cls_name, "text字段=%s" % ("是" if is_text_field else "否"), "hash=%r" % h,
            "text=%r" % (text[:30] if text else None))

words = ["Thud", "Rain", "Zipper", "Morgue", "Stairwell", "Office", "Library",
         "Sick", "Award", "Revelation", "Flashback", "Perish", "Violence",
         "Terminus", "Submitted", "Unlock", "none", "Start"]

print("=" * 76)
print("候选词归属判定")
print("=" * 76)
for w in words:
    pat = struct.pack("<i", len(w)) + w.encode()
    found = 0
    verdicts = defaultdict(int)
    samples = []
    for pid, raw in raws.items():
        s = 0
        while found < 200:
            q = raw.find(pat, s)
            if q < 0: break
            s = q + 1
            r = analyze(pid, raw, q)
            if r:
                verdicts[r[0] + "/" + r[1]] += 1
                if len(samples) < 2:
                    samples.append((pids[pid], r))
            found += 1
    print("\n%-14r 出现 %d 次" % (w, found))
    for k, c in sorted(verdicts.items(), key=lambda kv: -kv[1]):
        print("    %-40s x%d" % (k, c))
    for s in samples:
        print("    样本:", s)
