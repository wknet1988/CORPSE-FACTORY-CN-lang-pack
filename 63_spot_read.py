# -*- coding: utf-8 -*-
"""从部署文件里抽读中文文本，人工确认观感"""
import os, re
import UnityPy

GAME = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY"
DEPLOY = os.path.join(GAME, "CORPSE FACTORY_Data", "resources.assets")

CJK = re.compile(r"[\u4e00-\u9fff]")

env = UnityPy.load(DEPLOY)
lines = []
for obj in env.objects:
    if obj.type.name != "MonoBehaviour":
        continue
    try:
        data = obj.get_raw_data()
    except Exception:
        continue
    txt = data.decode("utf-8", "ignore")
    for m in re.finditer(r"[\u4e00-\u9fff][^\x00-\x08\x0b\x0c\x0e-\x1f]{6,120}", txt):
        s = m.group(0)
        if CJK.search(s) and len(s) >= 10:
            lines.append(s)

seen = set()
out = []
for s in lines:
    if s in seen:
        continue
    seen.add(s)
    out.append(s)

print("total unique Chinese strings found in deployed file: %d" % len(out))
print("\n--- 头 15 条 ---")
for s in out[:15]:
    print("  " + s)
print("\n--- 中段 10 条 ---")
mid = len(out) // 2
for s in out[mid:mid + 10]:
    print("  " + s)
print("\n--- 尾 10 条 ---")
for s in out[-10:]:
    print("  " + s)
