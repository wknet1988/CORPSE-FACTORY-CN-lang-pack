#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
from UnityPy import Environment

BASE = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY/CORPSE FACTORY_Data"
ASSETS = os.path.join(BASE, "resources.assets")

env = Environment(ASSETS)

total = 0
by_class = {}
script_objs = []
for obj in env.objects:
    total += 1
    cn = obj.type.name
    by_class[cn] = by_class.get(cn, 0) + 1

print("TOTAL objects:", total)
print("=== top classes ===")
for k, v in sorted(by_class.items(), key=lambda x: -x[1])[:25]:
    print(f"  {k}: {v}")

# Find Naninovel.Script MonoBehaviours by scanning raw for the class marker
print("\n=== Scanning for Naninovel.Script ===")
found = []
for obj in env.objects:
    if obj.type.name != "MonoBehaviour":
        continue
    try:
        raw = obj.get_raw_data()
    except Exception:
        continue
    if b"Naninovel.Script" in raw[:200]:
        sf = obj.assets_file
        found.append((sf.name, obj.path_id, obj.byte_start, obj.byte_size, len(raw)))

print("Found Naninovel.Script MonoBehaviours:", len(found))
for fn, pid, bs, bsz, rl in found[:8]:
    print(f"  file={fn} pid={pid} byte_start={bs} byte_size={bsz} rawlen={rl}")

# Inspect externals / files
print("\n=== env.files ===")
print(env.files)
print("\n=== per-assets-file object counts ===")
from collections import Counter
fc = Counter()
for obj in env.objects:
    try:
        fc[obj.assets_file.name] += 1
    except Exception:
        fc["?"] += 1
for k, v in fc.items():
    print(f"  {k}: {v}")

# Check externals on the main serialized file
main = None
for obj in env.objects:
    main = obj.assets_file
    break
print("\n=== main SerializedFile attrs ===")
print("name:", main.name)
print("externals:", getattr(main, "externals", "N/A"))
print("has attributes:", [a for a in dir(main) if not a.startswith("_")][:40])
