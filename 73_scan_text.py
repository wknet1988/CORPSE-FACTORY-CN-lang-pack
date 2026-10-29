#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Scan the DEPLOYED resources.assets for residual English DISPLAY text,
and enumerate object types in the BACKUP to find text-bearing sources
we may have missed beyond Naninovel.Script."""
import re, json, sys
from collections import Counter, defaultdict

PY = "C:/Users/wknet/.workbuddy/binaries/python/envs/default/Scripts/python.exe"
import UnityPy

BACKUP = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY/CORPSE FACTORY_Data/backup_original/resources.assets"
DEPLOYED = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY/CORPSE FACTORY_Data/resources.assets"

# ---------- 1) enumerate object types in backup ----------
print("=" * 70)
print("STEP 1: object types in BACKUP (text-bearing candidates)")
print("=" * 70)
env = UnityPy.load(BACKUP)
typ = Counter()
samples = defaultdict(list)
for o in env.objects:
    typ[o.type.name] += 1
    if len(samples[o.type.name]) < 3:
        samples[o.type.name].append(o.path_id)
for t, c in typ.most_common():
    print(f"  {t:35s} {c:6d}")

# text-bearing candidate types
CAND = {"Text", "TextMeshProUGUI", "TextMeshPro", "GUIText", "MonoBehaviour",
        "Sprite", "Texture2D", "Font", "Shader", "Material", "GameObject",
        "RectTransform", "Transform", "Mesh", "AudioClip", "AnimationClip"}
print("\nCANDIDATE types present:", [t for t in CAND if t in typ])

# ---------- 2) scan DEPLOYED raw bytes for English display strings ----------
print("\n" + "=" * 70)
print("STEP 2: residual English display strings in DEPLOYED file")
print("=" * 70)

with open(DEPLOYED, "rb") as f:
    data = f.read()

# find runs of printable ASCII 0x20-0x7e
runs = []
i = 0
n = len(data)
while i < n:
    if 0x20 <= data[i] <= 0x7e:
        j = i
        while j < n and 0x20 <= data[j] <= 0x7e:
            j += 1
        # also allow common punctuation that might be split
        s = data[i:j].decode("ascii", "ignore")
        if len(s) >= 4:
            runs.append(s)
        i = j
    else:
        i += 1

# heuristic: display text = has a space AND has at least 2 letters AND not pure identifier
def is_display(s):
    if " " not in s:
        return False
    letters = sum(c.isalpha() for c in s)
    if letters < 4:
        return False
    # exclude class names like GenericTextScriptLine / Elringus.Naninovel.Runtime
    if s.isidentifier():
        return False
    # exclude things with too many special chars (paths, guids)
    if s.count("/") or s.count("\\") or s.count("{") or s.count("}"):
        return False
    return True

disp = [s for s in runs if is_display(s)]
disp_uniq = sorted(set(disp), key=lambda s: -len(s))

# load translation keys to classify
tr = json.load(open("translations_complete.json", encoding="utf-8"))
occ = json.load(open("occurrences.json", encoding="utf-8"))
occ_texts = set(o["text"] for o in occ)

print(f"total ascii runs(>=4): {len(runs)}, display-candidate unique: {len(disp_uniq)}")

# classify: already-known-translation-key (should've been done) vs new
known_hit = [s for s in disp_uniq if s.strip() in tr]
new_miss = [s for s in disp_uniq if s.strip() not in tr and s not in occ_texts]
print(f"display strings that ARE in translation table (translated already): {len(known_hit)}")
print(f"display strings NOT in our extraction at all (MISSED source): {len(new_miss)}")

print("\n--- sample MISSED display strings (first 80) ---")
for s in new_miss[:80]:
    print("   ", repr(s[:90]))
