#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, struct
from UnityPy import Environment

DATA = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY/CORPSE FACTORY_Data"
ASSETS = os.path.join(DATA, "resources.assets")
RES = ASSETS + ".resS"

rawfile = open(ASSETS, "rb").read()
resS_size = os.path.getsize(RES)
print("resources.assets size:", len(rawfile))
print("resS size:", resS_size)

# Parse header
import io
r = io.BytesIO(rawfile)
metadataSize, fileSize, version, dataOffset = struct.unpack_from("<iQII", r.read(20))
r.read(4)  # endianness + reserved
print(f"metadataSize={metadataSize} fileSize={fileSize} version(fmt)={version} dataOffset={dataOffset}")

env = Environment(ASSETS)

# Script name set
SCRIPT_NAMES = {"MainScript","Script_Act_00","Script_Act_00a","Script_Act_00b","Script_Act_01",
"Script_Act_01a","Script_Act_01b","Script_Act_01c","Script_Act_01d","Script_Act_01e","Script_Act_02",
"Script_Act_02a","Script_Act_02b","Script_Act_03","Script_Act_03a","Script_Act_Endings","Script_Act_Special",
"Script_Start","Credits","TitleScript","Platform_Buttons","ShowPauseUI_2","HidePauseMenu","InputConfiguration"}

script_objs = []
audio_objs = []
for obj in env.objects:
    cn = obj.type.name
    if cn == "MonoBehaviour":
        raw = obj.get_raw_data()
        nf = struct.unpack_from("<i", raw, 28)[0]
        sname = raw[32:32+nf].decode("utf-8","replace") if 0 < nf < 200 else ""
        if sname in SCRIPT_NAMES:
            script_objs.append((obj.path_id, obj.byte_start, obj.byte_size, sname, len(raw)))
    elif cn == "AudioClip":
        audio_objs.append((obj.path_id, obj.byte_start, obj.byte_size))

print(f"\nScript objects found: {len(script_objs)}")
tot = 0
for pid, bs, bsz, sname, rl in sorted(script_objs, key=lambda x: x[1]):
    in_main = (dataOffset <= bs and bs + bsz <= fileSize)
    print(f"  {sname:16s} pid={pid:6d} byte_start={bs:>10d} byte_size={bsz:>9d} rawlen={rl:>9d} in_main={in_main}")
    tot += bsz
print(f"  total script byte_size sum = {tot}  (resS={resS_size})")

print(f"\nAudioClip sample (first 5):")
for pid, bs, bsz in audio_objs[:5]:
    in_main = (dataOffset <= bs and bs + bsz <= fileSize)
    print(f"  pid={pid:6d} byte_start={bs:>10d} byte_size={bsz:>9d} in_main={in_main}")

# What's the max byte_start among ALL objects, and how many exceed fileSize?
maxbs = 0; exceed = 0; total = 0
for obj in env.objects:
    bs = obj.byte_start; bsz = obj.byte_size
    maxbs = max(maxbs, bs)
    if bs > fileSize: exceed += 1
    total += 1
print(f"\nmax byte_start={maxbs}  objects_exceeding_fileSize={exceed} / {total}")
print("dataOffset+metadata check: metadata region ends at", dataOffset, "object data starts there")
