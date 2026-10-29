#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Diagnose the CURRENT inject_text logic on the ORIGINAL backup for pid 9141.
Find the first byte divergence and which replacement causes the shift."""
import os, struct, json
import UnityPy

BACKUP = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY/CORPSE FACTORY_Data/backup_original/resources.assets"
OCC = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY/_cnwork/occurrences.json"
TRANS = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY/_cnwork/translations_full.json"

def align4(n): return (n + 3) & ~3

env = UnityPy.load(BACKUP)
occ = json.load(open(OCC, encoding="utf-8"))
trans_map = json.load(open(TRANS, encoding="utf-8"))

PID = 9141
obj = next(o for o in env.objects if o.path_id == PID)
raw = obj.get_raw_data()
print(f"pid {PID} raw_len={len(raw)}  trans_map size={len(trans_map)}")

ocs = [o for o in occ if o["pid"] == PID]
print(f"occurrences for pid {PID}: {len(ocs)}")

# Build reps exactly as 40_build.py does
reps = []
for o in ocs:
    en = o["text"]
    if en not in trans_map: continue
    zhb = trans_map[en].encode("utf-8")
    new_region = struct.pack("<i", len(zhb)) + zhb + b"\x00" * (align4(4+len(zhb)) - (4+len(zhb)))
    reps.append((o["off"], align4(o["len"]), new_region, en))

print(f"replacements built: {len(reps)}")
reps.sort(key=lambda r: r[0])

# Per-rep consistency check
print("\n--- per-rep consistency (first 20) ---")
for off, rsz, nr, en in reps[:20]:
    stored = struct.unpack_from("<i", raw, off)[0]
    exp = len(en.encode("utf-8"))
    gap_to_next = None
    # find next rep start
    nxt = [r[0] for r in reps if r[0] > off]
    if nxt:
        gap_to_next = nxt[0] - (off + align4(4+stored))
    flag = ""
    if stored != exp: flag += " STORED!=EXPECTED"
    if rsz != align4(4+stored): flag += " RSZ_MISMATCH"
    print(f"off={off} olen={o and 0} stored={stored} expected={exp} rsz={rsz} newrsz={len(nr)} gap_next_rawconsume={gap_to_next}{flag}  en={en[:30]!r}")

# Build new raw as 40_build does
new = bytearray()
cur = 0
for off, rsz, nr, en in reps:
    new += raw[cur:off]; new += nr; cur = off + rsz
new += raw[cur:]
new = bytes(new)

print(f"\noriginal len={len(raw)}  new len={len(new)}  delta={len(new)-len(raw)}")

# find first divergence
d0 = None
for i in range(min(len(raw), len(new))):
    if raw[i] != new[i]:
        d0 = i; break
print(f"first divergence at offset: {d0}")
if d0 is not None:
    a = max(0, d0-24); b = min(len(raw), d0+48)
    print("ORIGINAL around divergence:")
    for i in range(a, b, 16):
        print(f"  {i:6d}  " + " ".join(f"{x:02x}" for x in raw[i:i+16]) + "  " + "".join(chr(x) if 32<=x<127 else "." for x in raw[i:i+16]))
    print("PATCHED  around divergence:")
    for i in range(a, min(len(new), b), 16):
        print(f"  {i:6d}  " + " ".join(f"{x:02x}" for x in new[i:i+16]) + "  " + "".join(chr(x) if 32<=x<127 else "." for x in new[i:i+16]))
    # which rep is just before d0?
    prev_rep = [r for r in reps if r[0] <= d0]
    if prev_rep:
        pr = prev_rep[-1]
        print(f"last rep before divergence: off={pr[0]} (ends at {pr[0]+pr[1]})  en={pr[3][:40]!r}")
