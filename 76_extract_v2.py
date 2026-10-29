#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Robust re-extraction of ALL display text from CORPSE FACTORY resources.assets.

Strategy: per-offset scan of every MonoBehaviour object for length-prefixed,
printable, valid-UTF-8 strings, then filter to genuine DISPLAY text:
  * must contain a space (excludes labels/IDs like ACHIEVEMENT_01, CHOICE_AOI_A, BeginIf)
  * must not start with '@' (excludes Naninovel commands: @back, @set, @showUI...)
  * must not be a structural token (class names, Naninovel, Elringus..., 8-hex linehash)
  * must be printable (no control chars) -> excludes mis-aligned garbage
Script objects are scanned fully; we also scan all other MonoBehaviour objects
to catch credits / non-script text. Output: occurrences_v2.json + gap report.
"""
import json, struct, re, os
from UnityPy import Environment

BACKUP = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY/CORPSE FACTORY_Data/backup_original/resources.assets"
HERE = os.path.dirname(os.path.abspath(__file__))

STRUCT_EXCLUDE = {
    "Naninovel", "Elringus.Naninovel.Runtime",
    "CommandScriptLine", "CommentScriptLine", "LabelScriptLine",
    "GenericTextScriptLine", "EmptyScriptLine",
    "SetCustomVariable", "Naninovel.Commands", "Naninovel", "UnityEngine",
}
HEX8 = re.compile(r"^[0-9a-f]{8}$")

def is_display(t):
    if " " not in t:
        return False
    if t.startswith("@"):
        return False
    if t in STRUCT_EXCLUDE:
        return False
    if HEX8.match(t):
        return False
    if not any(c.isalpha() for c in t):
        return False
    return True

def scan_strings(b):
    """Yield (offset, text) for every length-prefixed printable UTF-8 string in b."""
    out = []
    n = len(b)
    i = 0
    while i + 4 <= n:
        L = struct.unpack_from("<i", b, i)[0]
        if 1 <= L <= 4000 and i + 4 + L <= n:
            seg = b[i + 4:i + 4 + L]
            # require printable (no control chars except tab/newline)
            ok = True
            for c in seg:
                if c < 0x20 and c not in (9, 10, 13):
                    ok = False; break
            if ok:
                try:
                    t = seg.decode("utf-8")
                except Exception:
                    t = None
                if t is not None and is_display(t):
                    out.append((i, t))
                    i += 4 + L
                    continue
        i += 1
    return out

def main():
    env = Environment(BACKUP)
    occ = json.load(open("occurrences.json", encoding="utf-8"))
    script_pids = set(o["pid"] for o in occ)

    new_occ = []
    script_total = 0
    other_total = 0
    for obj in env.objects:
        if obj.type.name != "MonoBehaviour":
            continue
        try:
            raw = obj.get_raw_data()
        except Exception:
            continue
        hits = scan_strings(raw)
        if obj.path_id in script_pids:
            script_total += len(hits)
        else:
            other_total += len(hits)
        for off, t in hits:
            d = {"pid": obj.path_id, "off": off, "len": len(t.encode("utf-8")), "text": t}
            if obj.path_id not in script_pids:
                d["other"] = True
            new_occ.append(d)

    json.dump(new_occ, open("occurrences_v2.json", "w", encoding="utf-8"), ensure_ascii=False)
    print(f"script pids display strings: {script_total}")
    print(f"OTHER MonoBehaviour display strings: {other_total}")
    print(f"TOTAL occurrences: {len(new_occ)}")

    tr = json.load(open("translations_complete.json", encoding="utf-8"))
    texts = [o["text"] for o in new_occ]
    uniq = sorted(set(texts))
    already = [t for t in uniq if t in tr]
    newtxt = [t for t in uniq if t not in tr]
    print(f"\nUNIQUE display strings: {len(uniq)}")
    print(f"  already translated: {len(already)}")
    print(f"  NEW (need translation): {len(newtxt)}")

    # sanity: are previously-missed strings now captured?
    checks = ["Sex can be wonderful. But it can be scary as well.",
              "My eyes fixate on Shinya",
              "Change title screen to version 0",
              "BONUS ENDING UNLOCKED! REQUIRED: Tomoe = 1 & Shinya = 1.",
              "(THIS SCENE IS INSERTED BEFORE THE OTHER UNLOCKED ENDING)"]
    print("\n--- coverage of known-missed strings ---")
    for c in checks:
        # check if any occurrence text CONTAINS c (since storage may include prefix like 'NORIKO: ')
        hit = any(c in t for t in texts)
        print(f"   {'OK ' if hit else 'MISS'} {c[:50]!r}")

    print("\n--- sample NEW strings (first 70) ---")
    for t in newtxt[:70]:
        print("   ", repr(t[:95]))

if __name__ == "__main__":
    main()
