#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, time
from UnityPy import Environment

DATA = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY/CORPSE FACTORY_Data"
ASSETS = os.path.join(DATA, "resources.assets")
OUT = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY/_cnwork/test_noop.assets"

t0 = time.time()
env = Environment(ASSETS)
n = sum(1 for _ in env.objects)
print(f"loaded {n} objects in {time.time()-t0:.1f}s")
print("calling env.save() (no modifications)...")
t1 = time.time()
env.save(OUT)
print(f"saved in {time.time()-t1:.1f}s")
import os as _os
for f in [OUT, OUT + ".resS"]:
    if _os.path.exists(f):
        print(f"  exists: {f}  size={_os.path.getsize(f)}")
orig = _os.path.getsize(ASSETS)
print(f"original resources.assets size = {orig}")
