#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, struct
from UnityPy import Environment

ORIG = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY/CORPSE FACTORY_Data/resources.assets"
PATCH = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY/_cnwork/build_demo/resources.assets"

eo = Environment(ORIG); ep = Environment(PATCH)
orig = {o.path_id: o for o in eo.objects}
pat  = {o.path_id: o for o in ep.objects}
print("objects equal count/ids:", len(orig)==len(pat)==11600, set(orig)==set(pat))

# 1) Script_Act_00b (pid 9141) must contain Chinese
raw = pat[9141].get_raw_data()
print("Script_Act_00b has 尸体:", "尸体".encode("utf-8") in raw)
print("Script_Act_00b has 黑泽:", "黑泽".encode("utf-8") in raw)

# 2) Font 5209 has CJK TTF
tree = pat[5209].read_typetree()
d = bytes(tree["m_FontData"])
print("Font 5209 TTF header ok:", d[:4]==b"\x00\x01\x00\x00", "glyf:", b"glyf" in d, "size:", len(d))

# 3) Credits (9137) unchanged (not in act00b map) -> identical to orig
print("Credits identical to orig:", orig[9137].get_raw_data()==pat[9137].get_raw_data())

# 4) count diffs
diff=sum(1 for pid in pat if pid not in orig or pat[pid].get_raw_data()!=orig[pid].get_raw_data())
print("total objects differing from original:", diff, "(expected ~14: 13 scripts + font)")
