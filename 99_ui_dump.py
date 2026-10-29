# -*- coding: utf-8 -*-
"""把含 LOG/SKIP/AUTO/HIDE 的 UI 对象里所有可读字符串全部导出，
看清控制面板/菜单到底有哪些英文标签。"""
import os, struct, json
from collections import defaultdict
import UnityPy

GAME = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY"
BACKUP = os.path.join(GAME, "CORPSE FACTORY_Data", "backup_original", "resources.assets")
HERE = os.path.dirname(os.path.abspath(__file__))

env = UnityPy.load(BACKUP)

def scan_lp(b):
    out = []; n = len(b); i = 0
    while i + 4 <= n:
        L = struct.unpack_from("<i", b, i)[0]
        if 0 <= L <= 4000 and i + 4 + L <= n:
            seg = b[i+4:i+4+L]
            if not any(c < 0x20 and c not in (9, 10, 13) for c in seg):
                try:
                    t = seg.decode("utf-8")
                    out.append(t); i = (i + 4 + L + 3) & ~3; continue
                except Exception:
                    pass
        i += 4
    return out

# 先找所有含这些标签的对象
targets = set()
for w in [b"LOG", b"SKIP", b"AUTO", b"HIDE"]:
    pat = struct.pack("<i", len(w)) + w
    for o in env.objects:
        if o.type.name != "MonoBehaviour": continue
        try:
            if pat in o.get_raw_data():
                targets.add(o.path_id)
        except Exception:
            pass

print("含 LOG/SKIP/AUTO/HIDE 的对象: %s" % sorted(targets))
print("共 %d 个\n" % len(targets))

for pid in sorted(targets):
    obj = None
    for o in env.objects:
        if o.path_id == pid:
            obj = o; break
    raw = obj.get_raw_data()
    strs = scan_lp(raw)
    uniq = []
    seen = set()
    for s in strs:
        if not s or s in seen: continue
        seen.add(s)
        uniq.append(s)
    print("=" * 70)
    print("pid=%s  长度=%d  唯一字符串=%d" % (pid, len(raw), len(uniq)))
    print("=" * 70)
    for s in uniq[:40]:
        print("   %r" % s[:80])
    print()
