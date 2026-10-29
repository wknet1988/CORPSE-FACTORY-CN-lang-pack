# -*- coding: utf-8 -*-
"""对比 ui_labels 里的 pid 在补丁前后是否替换成功，并定位残留英文标签所在的对象类型。"""
import os, struct, json
from collections import defaultdict
import UnityPy

GAME = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY"
HERE = os.path.dirname(os.path.abspath(__file__))
BEFORE = os.path.join(GAME, "build_final2", "resources.assets")
AFTER = os.path.join(GAME, "build_ui2", "resources.assets")

ui = json.load(open(os.path.join(HERE, "ui_labels.json"), encoding="utf-8"))
rows = ui["rows"]

def load(path):
    env = UnityPy.load(path)
    d = {}
    for o in env.objects:
        if o.type.name == "MonoBehaviour":
            try: d[o.path_id] = o.get_raw_data()
            except: pass
    return env, d

envB, B = load(BEFORE)
envA, A = load(AFTER)

print("=== 1) 目标对象替换情况（抽 12 个）===")
ok = 0; bad = []
for r in rows:
    pid = r["pid"]; lbs = r["labels"]
    if not lbs: continue
    b = B.get(pid); a = A.get(pid)
    if b is None or a is None: continue
    changed = False
    for lb in lbs:
        pat = struct.pack("<i", len(lb.encode())) + lb.encode()
        if pat in b and pat not in a:
            changed = True
    if changed: ok += 1
    else: bad.append((pid, lbs))
print("已替换对象: %d | 未替换: %d" % (ok, len(bad)))
for pid, lbs in bad[:15]:
    print("   未替换 pid=%s labels=%s" % (pid, lbs))

print("\n=== 2) 残留英文标签所在对象 ===")
words = ["HIDE", "LOG", "SKIP", "AUTO", "MENU", "SAVE", "LOAD", "SETTINGS", "TITLE", "TIPS"]
for w in words:
    pat = struct.pack("<i", len(w)) + w.encode()
    owners = [pid for pid, r in A.items() if pat in r]
    print("\n  %r 仍在 %d 个对象: %s" % (w, len(owners), owners[:8]))
    for pid in owners[:2]:
        raw = A[pid]
        # 列出该对象的全部字符串
        strs = []; i = 0; n = len(raw)
        while i + 4 <= n:
            L = struct.unpack_from("<i", raw, i)[0]
            if 0 <= L <= 300 and i + 4 + L <= n:
                seg = raw[i+4:i+4+L]
                if not any(c < 0x20 and c not in (9, 10, 13) for c in seg):
                    try:
                        t = seg.decode("utf-8")
                        strs.append(t); i = (i + 4 + L + 3) & ~3; continue
                    except Exception:
                        pass
            i += 4
        print("    pid=%s len=%d 字符串=%s" % (pid, len(raw), strs[:10]))
