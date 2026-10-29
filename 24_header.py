#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, struct
from UnityPy import Environment

DATA = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY/CORPSE FACTORY_Data"
ASSETS = os.path.join(DATA, "resources.assets")

env = Environment(ASSETS)
# get the SerializedFile for resources.assets
sf = None
for obj in env.objects:
    sf = obj.assets_file
    break

print("unity_version:", sf.unity_version)
print("header:", sf.header)
print("data_offset attr:", getattr(sf, "data_offset", "N/A"))
print("file_size attr:", getattr(sf, "file_size", "N/A"))
print("metadata_size attr:", getattr(sf, "metadata_size", "N/A"))
print("version (fmt):", getattr(sf, "version", "N/A"))

# header object fields
h = sf.header
print("\n-- header object fields --")
for k in dir(h):
    if not k.startswith("_"):
        try:
            v = getattr(h, k)
            if not callable(v):
                print(f"  {k}: {v}")
        except Exception as e:
            print(f"  {k}: ERR {e}")

# Try to find ObjectInfo entries in the metadata region by scanning for (byte_start, byte_size) pairs
rawfile = open(ASSETS, "rb").read()
data_offset = sf.header.data_offset
print("\nfile total:", len(rawfile), "data_offset:", data_offset, "metadata region size:", data_offset)

# Build list of (path_id, byte_start, byte_size) from env.objects
objs = []
for obj in env.objects:
    objs.append((obj.path_id, obj.byte_start, obj.byte_size))
objs.sort(key=lambda x: x[1])
print("objects:", len(objs))

# For a few objects, locate their ObjectInfo entry in metadata [0:data_offset]
def find_objinfo(pid, bs, bsz):
    # Try 8-byte and 4-byte widths for byte_start and byte_size
    candidates = []
    for bw in (4, 8):
        bs_pat = struct.pack("<%dQ" % (bw//8) if bw==8 else "<I", bs) if bw==4 else struct.pack("<Q", bs)
        bsz_pat = struct.pack("<I", bsz) if bw==4 else struct.pack("<Q", bsz)
        # search metadata region for bs_pat immediately followed by bsz_pat
        start = 0
        while True:
            p = rawfile.find(bs_pat, start, data_offset)
            if p < 0: break
            if rawfile[p+bw:p+2*bw] == bsz_pat:
                candidates.append((p, bw))
            start = p+1
    return candidates

# Test with AudioClip pid 778 (bs=1601936, bsz=88) and MainScript pid 9138 (bs=24932552, bsz=11637748)
for pid, bs, bsz in [(778,1601936,88),(9138,24932552,11637748),(9127,9918240,6526528)]:
    c = find_objinfo(pid, bs, bsz)
    print(f"pid={pid} bs={bs} bsz={bsz} -> ObjectInfo candidate offsets: {c[:5]}")
