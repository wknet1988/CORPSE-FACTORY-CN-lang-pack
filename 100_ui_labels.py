# -*- coding: utf-8 -*-
"""导出所有含 set_text 的 UI 对象及其标签字面量 —— 完整的菜单/提示标签清单。"""
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
                    out.append((i, i + 4, t)); i = (i + 4 + L + 3) & ~3; continue
                except Exception:
                    pass
        i += 4
    return out

rows = []
for o in env.objects:
    if o.type.name != "MonoBehaviour": continue
    raw = o.get_raw_data()
    if b"set_text" not in raw and b"set_" not in raw: continue
    if len(raw) > 1200: continue          # 只看小的 UIEvent 对象
    strs = [t for _p, _c, t in scan_lp(raw) if t]
    if "set_text" not in strs: continue
    # 标签 = set_text 之前那个既不是路径也不是类名的字符串
    labels = []
    for s in strs:
        if s in ("set_text",) or s.startswith("UnityEngine") or s.startswith("DefaultUI"):
            continue
        if "." in s and "/" not in s and s[0].isupper() and s.count(".") >= 1 and " " not in s:
            continue   # ControlPanel.Hide 这类键
        labels.append(s)
    rows.append((o.path_id, len(raw), strs, labels))

print("含 set_text 的小 UI 对象: %d\n" % len(rows))

# 汇总标签
from collections import Counter
cnt = Counter()
detail = defaultdict(list)
for pid, sz, strs, labels in rows:
    for lb in labels:
        cnt[lb] += 1
        detail[lb].append(pid)

print("=== 全部标签字面量（%d 种）===" % len(cnt))
for lb, c in sorted(cnt.items(), key=lambda kv: (-kv[1], kv[0])):
    print("   x%-4d %-32r pids=%s" % (c, lb[:32], detail[lb][:4]))

print("\n=== 键 → 标签 对应关系（样本 40 个）===")
for pid, sz, strs, labels in rows[:40]:
    key = [s for s in strs if "." in s and "UnityEngine" not in s and " " not in s]
    print("   pid=%-6s key=%-28r labels=%s" % (pid, (key[0] if key else "?"), labels))

json.dump({"rows": [{"pid": p, "size": s, "strs": st, "labels": lb} for p, s, st, lb in rows],
           "labels": {k: v for k, v in detail.items()}},
          open(os.path.join(HERE, "ui_labels.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("\n-> ui_labels.json")
