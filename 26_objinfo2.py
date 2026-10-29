#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, struct
from UnityPy import Environment

ASSETS = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY/CORPSE FACTORY_Data/resources.assets"
rawfile = open(ASSETS, "rb").read()
data_offset = 288416

# known byte_start values from UnityPy
targets = {
    "MainScript": 24932552,     # bsz 11637748
    "Script_Act_01": 9918240,   # bsz 6526528
    "AudioClip778": 1601936,    # bsz 88
}

for name, bs in targets.items():
    bs4 = struct.pack("<I", bs & 0xffffffff)
    bs8 = struct.pack("<Q", bs)
    print(f"\n=== target {name} byte_start={bs} ===")
    for label, pat in (("4B", bs4), ("8B", bs8)):
        start = 0
        hits = []
        while True:
            p = rawfile.find(pat, start, data_offset)
            if p < 0: break
            hits.append(p); start = p+1
        print(f"  {label} pattern hits ({len(hits)}): {hits[:6]}")
        for p in hits[:2]:
            chunk = rawfile[p-12:p+52]
            print(f"    @{p} context: {chunk.hex(' ')}")
            # interpret assuming [pid8][bs8][bsz8][type4][cls2][scr2] from p
            print(f"      pid={struct.unpack_from('<q',chunk,0)[0]} bs={struct.unpack_from('<q',chunk,8)[0]} bsz={struct.unpack_from('<q',chunk,16)[0]} type={struct.unpack_from('<i',chunk,24)[0]} cls={struct.unpack_from('<h',chunk,28)[0]} scr={struct.unpack_from('<h',chunk,30)[0]}")
