#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Probe the EXACT binary layout of Naninovel.Script strings in the ORIGINAL
resources.assets: does each string occupy 4+len bytes (tight) or
align4(4+len) bytes (4-byte padding after the bytes)?"""
import os, struct, json
import UnityPy

DATA = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY/CORPSE FACTORY_Data"
ASSETS = os.path.join(DATA, "resources.assets")
OCC = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY/_cnwork/occurrences.json"

def align4(n): return (n + 3) & ~3

env = UnityPy.load(ASSETS)
occ = json.load(open(OCC, encoding="utf-8"))

# pick a few pids with many occurrences
from collections import Counter
cnt = Counter(o["pid"] for o in occ)
top = [p for p,_ in cnt.most_common(5)]
print("top pids by occ count:", top)

def dump_region(raw, off, span, around=32):
    a = max(0, off-around); b = min(len(raw), off+span+around)
    print(f"  region off={off} span={span}  file[{a}:{b}] hex/ascii:")
    i = a
    while i < b:
        line = raw[i:i+16]
        hexs = " ".join(f"{x:02x}" for x in line)
        asc = "".join(chr(x) if 32<=x<127 else "." for x in line)
        mark = ""
        if off <= i < off+span: mark = "  <<<REPLACED REGION"
        print(f"    {i:6d}  {hexs:<48s} {asc}{mark}")
        i += 16

for pid in top:
    obj = next(o for o in env.objects if o.path_id == pid)
    raw = obj.get_raw_data()
    ocs = [o for o in occ if o["pid"] == pid]
    print(f"\n==== pid {pid}  raw_len={len(raw)}  occ={len(ocs)} ====")
    # verify each occurrence: read stored length at off, check padding hypothesis
    pad_present = 0; tight_ok = 0; ambiguous = 0
    for o in ocs[:40]:
        off = o["off"]; ln = o["len"]
        stored = struct.unpack_from("<i", raw, off)[0]
        # stored should equal the UTF-8 byte length of o["text"]
        expected = len(o["text"].encode("utf-8"))
        # bytes region tight = [off, off+4+stored)
        end_tight = off + 4 + stored
        end_aligned = align4(end_tight)
        # after tight end: what byte? if padding present, bytes [end_tight,end_aligned) should be 0x00
        pad_bytes = raw[end_tight:end_aligned]
        if len(pad_bytes) == 0:
            # already aligned
            if end_tight < len(raw):
                pad_present += 1; tight_ok += 1
            else:
                ambiguous += 1
        else:
            if pad_bytes == b"\x00" * len(pad_bytes):
                pad_present += 1
            else:
                # there are non-zero bytes where we expected padding -> tight packing likely
                tight_ok += 1
        if abs(off) < 0: pass
    print(f"  of first 40 occ: padding-consistent={pad_present}  tight-consistent={tight_ok}  ambiguous={ambiguous}")

# Dump the reported divergence point pid 9141 off 47944
print("\n\n########## DIVERGENCE PROBE pid 9141 off 47944 ##########")
obj = next((o for o in env.objects if o.path_id == 9141), None)
if obj is None:
    print("pid 9141 not found in objects")
else:
    raw = obj.get_raw_data()
    print("pid 9141 raw_len:", len(raw))
    dump_region(raw, 47944, 8, around=48)
    # show the occurrences around off 47944 in pid 9141
    p9141 = sorted([o for o in occ if o["pid"]==9141], key=lambda x:x["off"])
    print("occurrences for pid 9141 near 47944:")
    for o in p9141:
        if 47900 <= o["off"] <= 48050:
            print(f"  off={o['off']} len={o['len']} text={o['text']!r}")
