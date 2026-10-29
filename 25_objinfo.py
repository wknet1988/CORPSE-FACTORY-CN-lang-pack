#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, struct
from UnityPy import Environment

ASSETS = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY/CORPSE FACTORY_Data/resources.assets"
rawfile = open(ASSETS, "rb").read()
data_offset = 288416

env = Environment(ASSETS)
# get known (path_id, byte_start, byte_size)
known = {}
for obj in env.objects:
    known[obj.path_id] = (obj.byte_start, obj.byte_size)

def dump_around_pid(pid):
    bs, bsz = known[pid]
    print(f"\n=== pid={pid}  byte_start={bs} byte_size={bsz} ===")
    # search path_id as 4-byte and 8-byte in metadata region
    for w in (4, 8):
        fmt = "<I" if w==4 else "<Q"
        pat = struct.pack(fmt, pid)
        start = 0
        while True:
            p = rawfile.find(pat, start, data_offset)
            if p < 0: break
            chunk = rawfile[p:p+48]
            print(f"  PID@{p} (width {w}) next 48 bytes:")
            print("   ", chunk.hex(" "))
            # Try to read plausible fields
            print("    u32 after pid:", struct.unpack_from("<I", chunk, w)[0],
                  " u32+4:", struct.unpack_from("<I", chunk, w+4)[0],
                  " u32+8:", struct.unpack_from("<I", chunk, w+8)[0])
            start = p+1

for pid in [778, 9138, 9127]:
    dump_around_pid(pid)
