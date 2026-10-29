#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Characterize the DEPLOYED (corrupt) resources.assets vs ORIGINAL backup.
Is pid 9141 translated? Where does it first diverge? Object count ok?"""
import os, struct
import UnityPy

DEPLOYED = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY/CORPSE FACTORY_Data/resources.assets"
ORIGINAL = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY/CORPSE FACTORY_Data/backup_original/resources.assets"

def info(path):
    env = UnityPy.load(path)
    objs = list(env.objects)
    n = len(objs)
    types = {}
    for o in objs:
        types[o.type.name] = types.get(o.type.name,0)+1
    return env, n, types

print("Loading ORIGINAL...")
eo, no, to = info(ORIGINAL)
print(f"  original objects={no}")
print("Loading DEPLOYED...")
ed, nd, td = info(DEPLOYED)
print(f"  deployed objects={nd}")

# find pid 9141 in both
def get_raw(env, pid):
    for o in env.objects:
        if o.path_id == pid:
            return o.get_raw_data()
    return None

for pid in (9141, 9138, 9127):
    ro = get_raw(eo, pid); rd = get_raw(ed, pid)
    if ro is None or rd is None:
        print(f"pid {pid}: missing (orig={'Y' if ro else 'N'} deploy={'Y' if rd else 'N'})"); continue
    print(f"\npid {pid}: orig_len={len(ro)} deploy_len={len(rd)} delta={len(rd)-len(ro)}")
    # first divergence
    d0=None
    for i in range(min(len(ro),len(rd))):
        if ro[i]!=rd[i]:
            d0=i; break
    if d0 is None:
        print("  IDENTICAL (no change)"); continue
    print(f"  first divergence at {d0}")
    a=max(0,d0-20); b=min(len(ro),d0+40)
    print("  ORIG :", " ".join(f"{x:02x}" for x in ro[a:b]))
    print("  DEPLOY:", " ".join(f"{x:02x}" for x in rd[a:b]))
    # Is there Chinese in deployed around divergence?
    seg = rd[max(0,d0-30):d0+60]
    try:
        txt = seg.decode("utf-8","replace")
    except: txt=""
    has_cjk = any(0x4e00<=ord(c)<=0x9fff for c in txt)
    print("  deployed segment has CJK:", has_cjk)
