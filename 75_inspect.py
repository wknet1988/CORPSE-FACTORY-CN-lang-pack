#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Inspect how specific strings are stored in the DEPLOYED file, and
cross-reference occurrences.json to understand why some translated strings
weren't replaced and some weren't extracted at all."""
import json, struct
import UnityPy

DEPLOYED = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY/CORPSE FACTORY_Data/resources.assets"
BACKUP   = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY/CORPSE FACTORY_Data/backup_original/resources.assets"
occ = json.load(open("occurrences.json", encoding="utf-8"))

probes = [
    "BONUS ENDING UNLOCKED! REQUIRED: Tomoe = 1 & Shinya = 1.",
    "Sex can be wonderful. But it can be scary as well.",
    "Change title screen to version 0",
    "My eyes fixate on Shinya",
]

# map offset->pid
env = UnityPy.load(DEPLOYED)
omap = []
for o in env.objects:
    omap.append((o.byte_start, o.byte_start + o.byte_size, o.path_id, o.type.name))
omap.sort()

def pid_of(off):
    for s, e, pid, t in omap:
        if s <= off < e:
            return pid, t
    return None, None

def dump_around(data, pos, label):
    print(f"\n### {label}")
    print(f"    file offset {pos}  pid/type={pid_of(pos)}")
    a = max(0, pos - 16)
    b = min(len(data), pos + 80)
    for i in range(a, b, 16):
        seg = data[i:i+16]
        print("    %8d  %s  %s" % (i, " ".join("%02x" % x for x in seg),
              "".join(chr(x) if 32 <= x < 127 else "." for x in seg)))
    # show the int32 just before the string (possible length prefix)
    pre = data[pos-4:pos]
    if len(pre) == 4:
        L = struct.unpack_from("<i", pre)[0]
        print(f"    -> 4 bytes before string = {L} (0x{L:x})  (as length prefix? bytes-after={L})")

with open(DEPLOYED, "rb") as f:
    dep = f.read()
with open(BACKUP, "rb") as f:
    bak = f.read()

for p in probes:
    pb = p.encode("utf-8")
    for data, name in [(dep, "DEPLOYED"), (bak, "BACKUP")]:
        idx = data.find(pb)
        if idx >= 0:
            dump_around(data, idx, f"[{name}] {p[:40]!r}")
            # cross-ref occurrences
            matches = [o for o in occ if o["text"] == p]
            print(f"    occurrences.json matches: {len(matches)}",
                  [(m["pid"], m["off"], m["len"]) for m in matches[:5]])
            break
    else:
        print(f"\n### [{p[:40]!r}] NOT FOUND in either file")
