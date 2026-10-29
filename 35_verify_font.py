#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, struct
from UnityPy import Environment

ORIG = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY/CORPSE FACTORY_Data/resources.assets"
PATCH = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY/_cnwork/test_font/resources.assets"

eo = Environment(ORIG); ep = Environment(PATCH)
orig = {o.path_id: o for o in eo.objects}
pat  = {o.path_id: o for o in ep.objects}

print("orig objs:", len(orig), "patched objs:", len(pat), "same ids:", set(orig)==set(pat))

# 1) Font 5209 must now carry CJK TTF data
f = pat[5209]
tree = f.read_typetree()
data = bytes(tree["m_FontData"])
print("Font 5209 m_FontData len:", len(data))
print("  starts with TTF header (00010000):", data[:4] == b"\x00\x01\x00\x00")
print("  contains 'glyf' table:", b"glyf" in data)
print("  contains 'CFF ':", b"CFF " in data)
# check it's the simhei subset: does it have 你 (U+4F60)? not in raw easily; just confirm it's a valid TTF size
print("  is CJK subset (size>5MB):", len(data) > 5_000_000)

# 2) spot-check other objects are byte-identical to original (content by path_id)
checks = [9137, 9138, 9127, 778, 5209]
for pid in checks:
    orr = orig[pid].get_raw_data()
    prr = pat[pid].get_raw_data()
    print(f"  pid {pid} [{pat[pid].type.name}] identical-to-orig: {orr==prr}  (len {len(orr)}->{len(prr)})")

# 3) count how many objects differ from original
diff=0
for pid in pat:
    if pid not in orig: diff+=1; continue
    if pat[pid].get_raw_data() != orig[pid].get_raw_data():
        diff+=1
print("total objects differing from original:", diff, "(expected 1: the font)")
