#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Find which objects reference each Font via PPtr (int32 fileID=0 + int64 pathID)."""
import os, struct
from UnityPy import Environment

DATA = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY/CORPSE FACTORY_Data"
env = Environment(os.path.join(DATA, "resources.assets"))

FONTS = {5209:"AveriaSerifLibre-Regular",5210:"PermanentMarker-Regular",5211:"Roboto-Regular",
         5212:"AveriaSerifLibre-BoldItalic",5213:"AveriaSerifLibre-Bold",
         5214:"AveriaSerifLibre-Light",5215:"LiberationSans"}

# Build PPtr patterns: fileID(4 bytes 0) + pathID(8 bytes int64)
patterns = {pid: (b"\x00\x00\x00\x00" + struct.pack("<q", pid)) for pid in FONTS}

# also count reverse: any object whose raw contains the pattern
refs = {pid: [] for pid in FONTS}
name_by_pid = {}
for obj in env.objects:
    name_by_pid[obj.path_id] = obj.type.name
    raw = obj.get_raw_data()
    for pid, pat in patterns.items():
        idx = 0
        found = False
        while True:
            p = raw.find(pat, idx)
            if p < 0: break
            found = True
            idx = p + 1
        if found:
            refs[pid].append(obj.path_id)

for pid in FONTS:
    refs[pid].sort()
    print(f"{FONTS[pid]} (pid {pid}): referenced by {len(refs[pid])} objects")
    # show a few referers with their type
    shown = 0
    for rpid in refs[pid]:
        print(f"    -> pid {rpid} [{name_by_pid.get(rpid,'?')}]")
        shown += 1
        if shown >= 12: 
            print("    ... (more)"); break

# Also: find Text components directly (class Text) and their font
print("\n=== Text components and their referenced font (pathID) ===")
cnt=0
for obj in env.objects:
    if obj.type.name != "Text":
        continue
    raw = obj.get_raw_data()
    # m_Font is a PPtr; scan for font path_ids as int64 preceded by fileID 0
    for pid in FONTS:
        pat = b"\x00\x00\x00\x00" + struct.pack("<q", pid)
        if pat in raw:
            print(f"  Text pid={obj.path_id} uses font pid={pid} ({FONTS[pid]})")
            cnt+=1
            break
    if cnt>30: print("... (truncated)"); break
print(f"Text components referencing known fonts: {cnt}")
