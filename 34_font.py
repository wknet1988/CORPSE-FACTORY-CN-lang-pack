#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Replace a Font asset's embedded TTF (m_FontData) with a CJK subset font.
Targets AveriaSerifLibre-Regular (pid 5209) -- the most-referenced font, used by
the dialogue printer and most UI. Uses read_typetree/save_typetree so the Font
structure is re-serialized correctly (Font is a standard Unity type)."""
import os, struct
from UnityPy import Environment

DATA = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY/CORPSE FACTORY_Data"
ASSETS = os.path.join(DATA, "resources.assets")
SUBSET = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY/_cnwork/cjk_subset.ttf"
TARGET_NAME = "AveriaSerifLibre-Regular"

def main(out_dir, subset_path=SUBSET, target=TARGET_NAME):
    ttf = open(subset_path, "rb").read()
    print(f"subset font size: {len(ttf)} bytes")
    env = Environment(ASSETS)
    done = False
    for obj in env.objects:
        if obj.type.name != "Font":
            continue
        raw = obj.get_raw_data()
        nl = struct.unpack_from("<i", raw, 0)[0]
        name = raw[4:4+nl].decode("utf-8","replace") if 0 < nl < 100 else ""
        if name != target:
            continue
        print(f"found target Font pid={obj.path_id} name={name!r}")
        tree = obj.read_typetree()
        assert "m_FontData" in tree, f"no m_FontData in typetree keys: {list(tree.keys())}"
        old_len = len(tree["m_FontData"])
        tree["m_FontData"] = list(ttf)
        obj.save_typetree(tree)
        print(f"  replaced m_FontData: {old_len} -> {len(ttf)} bytes")
        done = True
        break
    assert done, "target font not found"
    os.makedirs(out_dir, exist_ok=True)
    env.save(out_path=out_dir)
    print(f"saved to {out_dir}")

if __name__ == "__main__":
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY/_cnwork/test_font"
    main(out)
