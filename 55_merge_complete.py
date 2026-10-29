#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Merge ALL translation sources into one complete map that covers 100% of
display text (including main-story dialogue in translations_act00b.json)."""
import json, glob, os

HERE = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY/_cnwork"
sources = ["translations_full.json", "translations_act00b.json", "trans_credits.json"]
sources += sorted(glob.glob(os.path.join(HERE, "translations_batch*.json")))

merged = {}
order = []
for f in sources:
    p = f if os.path.isabs(f) else os.path.join(HERE, f)
    try:
        d = json.load(open(p, encoding="utf-8"))
    except Exception as e:
        print("skip", f, repr(e)[:50]); continue
    if not isinstance(d, dict):
        print("skip (not dict)", f); continue
    added = 0
    for k, v in d.items():
        if isinstance(v, str) and v.strip():
            if k not in merged:
                order.append(k)
            merged[k] = v
            added += 1
    print(f"  {os.path.basename(f):30s} keys={len(d)} added={added}")

out = {k: merged[k] for k in order}
json.dump(out, open(os.path.join(HERE, "translations_complete.json"), "w"),
          ensure_ascii=False, indent=0)
print("TOTAL unique keys:", len(out))

# coverage vs occurrences
occ = json.load(open(os.path.join(HERE, "occurrences.json"), encoding="utf-8"))
occt = set(o["text"] for o in occ)
hit = sum(1 for t in occt if t in out)
print(f"unique occ texts={len(occt)} covered={hit} missing={len(occt)-hit}")
for m in [t for t in occt if t not in out][:30]:
    print("   MISSING:", repr(m)[:70])
