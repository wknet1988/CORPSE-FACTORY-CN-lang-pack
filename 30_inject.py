#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Injection engine for CORPSE FACTORY (Naninovel).
Replaces display-text strings inside Naninovel.Script MonoBehaviour objects,
using a translation map {exact_english: chinese}. Only strings present in the
map are modified; everything else (commands, markers, resS assets) is preserved.

Uses UnityPy set_raw_data() so the (SerializeReference-heavy) script objects are
written back as raw bytes -- no re-serialization, no corruption.
"""
import os, json, struct
from UnityPy import Environment

BASE = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY/CORPSE FACTORY_Data"
ASSETS = os.path.join(BASE, "resources.assets")
OCC = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY/_cnwork/occurrences.json"
SCRIPT_NAMES = None  # None => use all monobehaviours that contain script markers (from occ)

def align4(n):
    return (n + 3) & ~3

def build_replacer(trans_map):
    occ = json.load(open(OCC, encoding="utf-8"))

    # group occurrences by pid
    by_pid = {}
    for o in occ:
        by_pid.setdefault(o["pid"], []).append(o)

    env = Environment(ASSETS)
    total_replaced = 0
    objs_changed = 0

    for obj in env.objects:
        if obj.path_id not in by_pid:
            continue
        if obj.type.name != "MonoBehaviour":
            continue
        ocs = by_pid[obj.path_id]
        raw = obj.get_raw_data()

        # build list of replacements for strings present in the map
        reps = []
        for o in ocs:
            en = o["text"]
            if en not in trans_map:
                continue
            zh = trans_map[en]
            zhb = zh.encode("utf-8")
            new_total = 4 + len(zhb)
            new_padded = align4(new_total)
            new_region = struct.pack("<i", len(zhb)) + zhb + b"\x00" * (new_padded - new_total)
            region_size = align4(o["len"])  # original occupied bytes (len includes 4-byte prefix)
            reps.append((o["off"], region_size, new_region, en))

        if not reps:
            continue

        reps.sort(key=lambda r: r[0])
        # sanity: regions must not overlap
        for i in range(1, len(reps)):
            if reps[i][0] < reps[i-1][0] + reps[i-1][1]:
                raise RuntimeError(f"overlap at pid {obj.path_id}: {reps[i-1]} {reps[i]}")

        new = bytearray()
        cursor = 0
        for off, region_size, new_region, en in reps:
            new += raw[cursor:off]
            new += new_region
            cursor = off + region_size
        new += raw[cursor:]

        obj.set_raw_data(bytes(new))
        objs_changed += 1
        total_replaced += len(reps)
        print(f"  patched pid={obj.path_id} script={ocs[0]['script']} replaced={len(reps)} new_len={len(new)} old_len={len(raw)}")

    print(f"\nObjects changed: {objs_changed}  total strings replaced: {total_replaced}")
    return env, objs_changed

def main(trans_map, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    env, n = build_replacer(trans_map)
    if n == 0:
        print("Nothing to replace (translation map empty / no matches).")
        return
    env.save(out_path=out_dir)
    print(f"Saved patched file(s) to: {out_dir}")

if __name__ == "__main__":
    import sys
    tmap = json.load(open(sys.argv[1], encoding="utf-8")) if len(sys.argv) > 1 else {}
    out = sys.argv[2] if len(sys.argv) > 2 else r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY/_cnwork/test_patch"
    main(tmap, out)
