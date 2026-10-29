#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Final, robust localization builder for CORPSE FACTORY (Naninovel).

Key robustness features vs. earlier versions:
  * Reads the REAL stored length prefix at each occurrence offset to compute the
    consumed byte span (align4(4+stored_len)). Does NOT trust o["len"].
  * Sanity-checks that the bytes actually stored at `off` equal the English
    string (utf-8 byte length), and skips (with a warning) any occurrence whose
    stored bytes disagree -- this prevents byte-shift corruption.
  * Re-base logic handles size changes between original and new strings.

Inputs:
  --input   pristine resources.assets to patch (default: backup_original)
  --trans   translations {en: zh}  (default: translations_complete.json)
  --out     output directory
  --skip-font  only patch text (no embedded CJK font)
"""
import os, sys, io, json, struct, argparse
from UnityPy import Environment

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY/CORPSE FACTORY_Data"
DEFAULT_IN = os.path.join(DATA, "backup_original", "resources.assets")
DEFAULT_TRANS = os.path.join(HERE, "translations_complete.json")
FONT_TARGET = "AveriaSerifLibre-Regular"
BASE_FONT = r"C:/Windows/Fonts/simhei.ttf"

def align4(n): return (n + 3) & ~3

def build_subset(chars, base=BASE_FONT):
    from fontTools.subset import Subsetter, Options
    from fontTools.ttLib import TTFont
    font = TTFont(base)
    opts = Options(); opts.glyph_names = False; opts.recalc_bounds = False; opts.drop_tables = []
    ss = Subsetter(options=opts)
    ss.populate(unicodes=sorted({ord(c) for c in chars}))
    ss.subset(font)
    buf = io.BytesIO(); font.save(buf)
    return buf.getvalue()

def inject_text(env, trans_map):
    occ = json.load(open(os.path.join(HERE, "occurrences.json"), encoding="utf-8"))
    by_pid = {}
    for o in occ:
        by_pid.setdefault(o["pid"], []).append(o)
    changed = 0; replaced = 0; skipped = 0
    for obj in env.objects:
        if obj.type.name != "MonoBehaviour" or obj.path_id not in by_pid:
            continue
        ocs = by_pid[obj.path_id]
        raw = obj.get_raw_data()
        reps = []
        for o in ocs:
            en = o["text"]
            if en not in trans_map:
                continue
            off = o["off"]
            if off + 4 > len(raw):
                skipped += 1; continue
            stored = struct.unpack_from("<i", raw, off)[0]
            exp = len(en.encode("utf-8"))
            if stored != exp:
                # stored bytes don't match the expected English text -> skip, do
                # not corrupt. (Occurrence may be stale or a false positive.)
                skipped += 1; continue
            zhb = trans_map[en].encode("utf-8")
            new_region = (struct.pack("<i", len(zhb)) + zhb
                          + b"\x00" * (align4(4 + len(zhb)) - (4 + len(zhb))))
            # consume exactly the original aligned region size:
            rsz = align4(4 + stored)
            reps.append((off, rsz, new_region))
        if not reps:
            continue
        reps.sort(key=lambda r: r[0])
        for i in range(1, len(reps)):
            if reps[i][0] < reps[i-1][0] + reps[i-1][1]:
                raise RuntimeError(f"overlap pid {obj.path_id} at rep {i}")
        new = bytearray()
        cur = 0
        for off, rsz, nr in reps:
            new += raw[cur:off]; new += nr; cur = off + rsz
        new += raw[cur:]
        obj.set_raw_data(bytes(new))
        changed += 1; replaced += len(reps)
    print(f"text: {changed} objects changed, {replaced} strings replaced, {skipped} skipped")
    return changed, replaced, skipped

def inject_font(env, ttf_bytes):
    done = False
    for obj in env.objects:
        if obj.type.name != "Font":
            continue
        raw = obj.get_raw_data()
        nl = struct.unpack_from("<i", raw, 0)[0]
        name = raw[4:4+nl].decode("utf-8", "replace") if 0 < nl < 100 else ""
        if name != FONT_TARGET:
            continue
        tree = obj.read_typetree()
        tree["m_FontData"] = list(ttf_bytes)
        obj.save_typetree(tree)
        done = True; break
    assert done, "font target not found"
    return len(ttf_bytes)

def main(in_path, trans_path, out_dir, skip_font=False):
    trans_map = json.load(open(trans_path, encoding="utf-8"))
    chars = set()
    for v in trans_map.values():
        chars.update(v)
    chars.update(chr(c) for c in range(0x20, 0x7F))
    env = Environment(in_path)
    c, r, s = inject_text(env, trans_map)
    if not skip_font:
        ttf = build_subset(chars)
        flen = inject_font(env, ttf)
        print(f"font: embedded CJK subset ({flen} bytes, {len(chars)} chars)")
    os.makedirs(out_dir, exist_ok=True)
    env.save(out_path=out_dir)
    print(f"saved -> {out_dir}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default=DEFAULT_IN)
    ap.add_argument("--trans", default=DEFAULT_TRANS)
    ap.add_argument("--out", required=True)
    ap.add_argument("--skip-font", action="store_true")
    a = ap.parse_args()
    main(a.inp, a.trans, a.out, a.skip_font)
