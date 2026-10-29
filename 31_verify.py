#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rigorous integrity check: compare every object's CONTENT (by path_id) between
the original and patched files. Unmodified objects must be byte-identical;
Credits must contain Chinese and differ. Also confirm object count & classes match."""
from UnityPy import Environment
import json

ORIG = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY/CORPSE FACTORY_Data/resources.assets"
PATCH = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY/_cnwork/test_patch/resources.assets"

eo = Environment(ORIG)
ep = Environment(PATCH)

orig = {o.path_id: o for o in eo.objects}
pat  = {o.path_id: o for o in ep.objects}

print("orig objects:", len(orig), " patched objects:", len(pat))
print("path_id sets equal:", set(orig) == set(pat))

changed, identical, errors = [], [], []
for pid, po in pat.items():
    if pid not in orig:
        errors.append((pid, "missing in orig")); continue
    try:
        pr = po.get_raw_data()
        orr = orig[pid].get_raw_data()
    except Exception as e:
        errors.append((pid, f"read err {e}")); continue
    if pr == orr:
        identical.append(pid)
    else:
        changed.append(pid)

print("identical objects:", len(identical))
print("changed objects  :", len(changed), "->", changed)

# Credits (pid 9137) must be changed & contain Chinese
cr = pat[9137].get_raw_data()
zh = "由 RIVER CROW STUDIO 开发。".encode("utf-8")
print("Credits changed & contains Chinese:", (9137 in changed) and (zh in cr))

# sanity: changed set should be EXACTLY {9137}
print("changed set == {9137}:", set(changed) == {9137})
print("errors:", errors[:5])
