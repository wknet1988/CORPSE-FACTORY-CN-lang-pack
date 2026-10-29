#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, struct
from UnityPy import Environment

DATA = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY/CORPSE FACTORY_Data"
ASSETS = os.path.join(DATA, "resources.assets")
RES = ASSETS + ".resS"

rawfile = open(ASSETS, "rb").read()
ress = open(RES, "rb").read()
print("=== first 64 bytes of resources.assets (hex) ===")
print(rawfile[:64].hex(" "))

env = Environment(ASSETS)

def loc_check(pid_target, label):
    for obj in env.objects:
        if obj.path_id != pid_target:
            continue
        bs, bsz = obj.byte_start, obj.byte_size
        raw = obj.get_raw_data()
        in_main = rawfile[bs:bs+bsz] == raw
        in_resS = ress[bs:bs+bsz] == raw if bs+bsz <= len(ress) else False
        print(f"\n[{label}] pid={pid_target} byte_start={bs} byte_size={bsz}")
        print(f"  matches main resources.assets bytes: {in_main}")
        print(f"  matches resS bytes:                 {in_resS}")
        print(f"  raw[0:16] hex: {raw[:16].hex(' ')}")
        return

loc_check(9127, "Script_Act_01")
loc_check(9138, "MainScript")
loc_check(778,  "AudioClip sample")
loc_check(5209, "Font sample")  # font path_ids 5209-5215 from summary
