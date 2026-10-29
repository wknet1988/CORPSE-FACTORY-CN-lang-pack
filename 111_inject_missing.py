#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
111_inject_missing.py
补注入 371 条「已译但 occurrences.json 缺位置」的短句（如 Bitch. / Wait… / OK.）。

位置来自 110_find_missing.py 的逐字节槽扫描，写入 missing_locations.json。
同时重建字体子集，确保新译文用字全部覆盖。
"""
import os, sys, io, json, struct, argparse, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from UnityPy import Environment

spec = importlib.util.spec_from_file_location("bf", os.path.join(HERE, "40_build_final.py"))
bf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bf)

spec2 = importlib.util.spec_from_file_location("bui", os.path.join(HERE, "104_build_with_ui.py"))
bui = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(bui)

align4 = bf.align4
DATA = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY/CORPSE FACTORY_Data"
DEFAULT_IN = os.path.join(DATA, "resources.assets")


def main(in_path, out_dir, trans_path, loc_file="missing_locations.json"):
    trans = json.load(open(trans_path, encoding="utf-8"))
    loc = json.load(open(os.path.join(HERE, loc_file), encoding="utf-8"))

    by_pid = {}
    for en, lst in loc.items():
        for pid, off, rsz in lst:
            by_pid.setdefault(pid, []).append((off, rsz, en))

    env = Environment(in_path)
    changed = 0
    replaced = 0
    skipped = 0
    skipped_detail = []
    for obj in env.objects:
        pid = obj.path_id
        if pid not in by_pid:
            continue
        if obj.type.name != "MonoBehaviour":
            continue
        raw = obj.get_raw_data()
        reps = []
        for off, rsz, en in by_pid[pid]:
            if en not in trans:
                continue
            enb = en.encode("utf-8")
            if off + 4 > len(raw):
                skipped += 1; skipped_detail.append((pid, off, en, "oob")); continue
            L = struct.unpack_from("<i", raw, off)[0]
            if L != len(enb) or raw[off + 4:off + 4 + L] != enb:
                skipped += 1; skipped_detail.append((pid, off, en, "mismatch")); continue
            zhb = trans[en].encode("utf-8")
            nr = (struct.pack("<i", len(zhb)) + zhb
                  + b"\x00" * (align4(4 + len(zhb)) - (4 + len(zhb))))
            reps.append((off, rsz, nr, en))
        if not reps:
            continue
        reps.sort(key=lambda r: r[0])
        for i in range(1, len(reps)):
            if reps[i][0] < reps[i - 1][0] + reps[i - 1][1]:
                raise RuntimeError("overlap pid %s at rep %d" % (pid, i))
        new = bytearray()
        cur = 0
        for off, rsz, nr, en in reps:
            new += raw[cur:off]
            new += nr
            cur = off + rsz
        new += raw[cur:]
        obj.set_raw_data(bytes(new))
        changed += 1
        replaced += len(reps)

    print("short lines: %d objects changed, %d strings replaced, %d skipped"
          % (changed, replaced, skipped))
    for d in skipped_detail[:20]:
        print("   skip", d)

    # 字体：覆盖全部译文 + UI 标签用字
    chars = set()
    for v in trans.values():
        chars.update(v)
    for v in bui.UI_LABELS.values():
        chars.update(v)
    chars.update(chr(c) for c in range(0x20, 0x7F))
    ttf = bf.build_subset(chars)
    flen = bf.inject_font(env, ttf)
    print("font: %d bytes, %d chars" % (flen, len(chars)))

    os.makedirs(out_dir, exist_ok=True)
    env.save(out_path=out_dir)
    print("saved ->", out_dir)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default=DEFAULT_IN)
    ap.add_argument("--trans", default=os.path.join(HERE, "translations_complete.json"))
    ap.add_argument("--out", required=True)
    ap.add_argument("--loc", default="missing_locations.json")
    a = ap.parse_args()
    main(a.inp, a.out, a.trans, a.loc)
