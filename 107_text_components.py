# -*- coding: utf-8 -*-
"""列出所有 Text 组件（含字体 PPtr 5209 且末尾为 m_Text）的文本，确认 UI 是否已全中文。"""
import os, struct, re
from collections import Counter
import UnityPy

GAME = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY"
DEPLOY = os.path.join(GAME, "CORPSE FACTORY_Data", "resources.assets")
CJK = re.compile(r"[\u4e00-\u9fff]")
FONT_PTR = struct.pack("<i", 5209)

env = UnityPy.load(DEPLOY)
rows = []
for o in env.objects:
    if o.type.name != "MonoBehaviour": continue
    try: raw = o.get_raw_data()
    except: continue
    if len(raw) > 600: continue
    if FONT_PTR not in raw: continue
    # 末尾的 length-prefixed 字符串 = m_Text
    n = len(raw)
    # 从后往前找：最后一个 4 字节长度前缀，使 4+len == 到末尾（含 padding）
    txt = None
    for pad in (0, 1, 2, 3):
        end = n - pad
        if end - 4 < 0: continue
        L = struct.unpack_from("<i", raw, end - 4 - 0)[0] if False else None
    # 简单法：尝试末尾若干位置
    for start in range(max(0, n - 200), n):
        if start + 4 > n: break
        L = struct.unpack_from("<i", raw, start)[0]
        if 0 < L <= 120 and start + 4 + L <= n and (n - (start + 4 + L)) < 4:
            seg = raw[start+4:start+4+L]
            if all(32 <= c or c > 127 for c in seg):
                try:
                    t = seg.decode("utf-8")
                    if t.strip():
                        txt = t
                        break
                except Exception:
                    pass
    rows.append((o.path_id, len(raw), txt))

print("Text 组件数: %d" % len(rows))
have = [r for r in rows if r[2]]
print("能读出 m_Text 的: %d" % len(have))

print("\n=== 全部文本（去重）===")
c = Counter(r[2] for r in have)
for t, n in sorted(c.items(), key=lambda kv: (-len(kv[0]), kv[0])):
    flag = "" if CJK.search(t) else "   <-- 仍为英文"
    print("   x%-3d %-28r%s" % (n, t[:28], flag))

en = [t for t in c if not CJK.search(t) and re.search(r"[A-Za-z]{2,}", t)]
print("\n仍为英文的文本: %d 种 -> %s" % (len(en), en))
