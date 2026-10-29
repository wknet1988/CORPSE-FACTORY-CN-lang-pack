#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Combined localization builder for CORPSE FACTORY (Naninovel).
Inputs:
  translations.json  : {exact_english: chinese}
  --font-base PATH   : base CJK TTF (default C:/Windows/Fonts/simhei.ttf)
Output:
  A patched resources.assets that (a) replaces display text per the map and
  (b) swaps AveriaSerifLibre-Regular's embedded font with a CJK subset covering
  exactly the characters used in the translations.

Only strings present in the map are touched; commands/markers/other assets are
preserved. Unmodified objects are re-streamed byte-for-byte from the original.
"""
import os, sys, io, json, struct, argparse
from UnityPy import Environment

DATA = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY/CORPSE FACTORY_Data"
ASSETS = os.path.join(DATA, "resources.assets")
OCC = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY/_cnwork/occurrences.json"
FONT_TARGET = "AveriaSerifLibre-Regular"
BASE_FONT = r"C:/Windows/Fonts/simhei.ttf"

def align4(n): return (n + 3) & ~3

def build_subset(chars, base=BASE_FONT):
    from fontTools.subset import Subsetter, Options
    from fontTools.ttLib import TTFont
    font = TTFont(base)
    opts = Options()
    opts.glyph_names = False
    opts.recalc_bounds = False
    opts.drop_tables = []
    ss = Subsetter(options=opts)
    ss.populate(unicodes=sorted({ord(c) for c in chars}))
    ss.subset(font)
    buf = io.BytesIO()
    font.save(buf)
    return buf.getvalue()

def inject_text(env, trans_map):
    occ = json.load(open(OCC, encoding="utf-8"))
    by_pid = {}
    for o in occ:
        by_pid.setdefault(o["pid"], []).append(o)
    changed = 0; replaced = 0
    for obj in env.objects:
        if obj.type.name != "MonoBehaviour" or obj.path_id not in by_pid:
            continue
        ocs = by_pid[obj.path_id]
        raw = obj.get_raw_data()
        reps = []
        for o in ocs:
            en = o["text"]
            if en not in trans_map: continue
            zhb = trans_map[en].encode("utf-8")
            new_region = struct.pack("<i", len(zhb)) + zhb + b"\x00" * (align4(4+len(zhb)) - (4+len(zhb)))
            reps.append((o["off"], align4(o["len"]), new_region))
        if not reps: continue
        reps.sort(key=lambda r: r[0])
        for i in range(1, len(reps)):
            if reps[i][0] < reps[i-1][0] + reps[i-1][1]:
                raise RuntimeError(f"overlap pid {obj.path_id}")
        new = bytearray()
        cur = 0
        for off, rsz, nr in reps:
            new += raw[cur:off]; new += nr; cur = off + rsz
        new += raw[cur:]
        obj.set_raw_data(bytes(new))
        changed += 1; replaced += len(reps)
    return changed, replaced

def inject_font(env, ttf_bytes):
    done = False
    for obj in env.objects:
        if obj.type.name != "Font": continue
        raw = obj.get_raw_data()
        nl = struct.unpack_from("<i", raw, 0)[0]
        name = raw[4:4+nl].decode("utf-8","replace") if 0 < nl < 100 else ""
        if name != FONT_TARGET: continue
        tree = obj.read_typetree()
        tree["m_FontData"] = list(ttf_bytes)
        obj.save_typetree(tree)
        done = True; break
    assert done, "font target not found"
    return len(ttf_bytes)

def main(trans_path, out_dir, font_base=BASE_FONT, skip_font=False):
    trans_map = json.load(open(trans_path, encoding="utf-8"))
    # charset = exactly the characters used in the translations (+ ASCII so any
    # untranslated English residue still renders). No giant CJK baseline -> small
    # font, avoids the Unity dynamic-font atlas overflow at runtime.
    chars = set()
    for v in trans_map.values():
        chars.update(v)
    chars.update(chr(c) for c in range(0x20, 0x7F))  # ASCII

    env = Environment(ASSETS)
    c, r = inject_text(env, trans_map)
    print(f"text: {c} objects changed, {r} strings replaced")
    if not skip_font:
        ttf = build_subset(chars, font_base)
        flen = inject_font(env, ttf)
        print(f"font: embedded CJK subset TTF ({flen} bytes, {len(chars)} chars)")
    os.makedirs(out_dir, exist_ok=True)
    env.save(out_path=out_dir)
    print(f"saved -> {out_dir}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("trans", help="translations.json")
    ap.add_argument("out", help="output dir")
    ap.add_argument("--font-base", default=BASE_FONT)
    ap.add_argument("--skip-font", action="store_true")
    a = ap.parse_args()
    main(a.trans, a.out, a.font_base, a.skip_font)
