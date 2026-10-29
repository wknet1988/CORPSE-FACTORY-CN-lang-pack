#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Investigate fonts and Naninovel text rendering setup.
Goal: find which Font the dialogue printer uses, and assess CJK coverage."""
import os, struct
from UnityPy import Environment

DATA = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY/CORPSE FACTORY_Data"
env = Environment(os.path.join(DATA, "resources.assets"))

print("=== Font assets (names + font data size) ===")
for obj in env.objects:
    if obj.type.name != "Font":
        continue
    raw = obj.get_raw_data()
    # Font MonoBehaviour: m_Name (string), then fields, m_FontData (array: int32 len + bytes)
    # name is near start. Find first ascii name.
    # read m_Name length-prefixed near offset 0
    nl = struct.unpack_from("<i", raw, 0)[0]
    name = raw[4:4+nl].decode("utf-8","replace") if 0 < nl < 100 else "?"
    # font data is a ByteArray; locate it by scanning for a big byte array
    # Typically m_FontData appears as int32 length = size of TTF
    print(f"  pid={obj.path_id} name={name!r} rawlen={len(raw)}")

print("\n=== MonoBehaviours whose name hints at Naninovel/Printer/Config/UI ===")
import re
hits = 0
for obj in env.objects:
    if obj.type.name != "MonoBehaviour":
        continue
    raw = obj.get_raw_data()
    nl = struct.unpack_from("<i", raw, 28)[0]
    sname = raw[32:32+nl].decode("utf-8","replace") if 0 < nl < 200 else ""
    if re.search(r"Naninovel|Printer|Config|Engine|Dialog|Text|UI|Localiz|Font", sname, re.I):
        # collect referenced Font path_ids
        print(f"  pid={obj.path_id} script={sname!r} rawlen={len(raw)}")
        hits += 1
        if hits > 40: 
            print("  ... (truncated)"); break

print(f"\nTotal hinted MonoBehaviours: {hits}")
