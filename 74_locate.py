#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Locate residual real English display strings in the DEPLOYED file:
which path_id/object-type contains each, so we know the real scope of
missed translation sources."""
import re, json
import UnityPy

DEPLOYED = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY/CORPSE FACTORY_Data/resources.assets"

env = UnityPy.load(DEPLOYED)

# build offset -> (pid, type) map
objs = []
for o in env.objects:
    try:
        bs = o.byte_start
        sz = o.byte_size
    except Exception:
        continue
    objs.append((bs, bs + sz, o.path_id, o.type.name))
objs.sort()

def find_obj(off):
    for s, e, pid, t in objs:
        if s <= off < e:
            return pid, t
    return None, None

with open(DEPLOYED, "rb") as f:
    data = f.read()

# extract display-ish strings
def is_real_display(s):
    if " " not in s:
        return False
    if sum(c.isalpha() for c in s) < 6:
        return False
    if s.isidentifier():
        return False
    # exclusions
    if s.startswith("Lorem ipsum") or "Lorem ipsum" in s:
        return False
    if "Version=0.0.0.0" in s and "Culture=" in s:
        return False
    if "Arimo" in s or "Liberation is a trademark" in s or "Steve Matteson" in s:
        return False
    if s.count("/") or s.count("\\"):
        return False
    if s.count("{") or s.count("}"):
        return False
    # must contain at least one lowercase word of length>=3 (natural English)
    if not re.search(r"[a-z]{3,}", s):
        return False
    return True

# find candidate strings and their location
from collections import defaultdict, Counter
by_pid = Counter()
by_type = Counter()
by_pid_examples = defaultdict(list)
positions = []

i = 0
n = len(data)
while i < n:
    if 0x20 <= data[i] <= 0x7e:
        j = i
        while j < n and 0x20 <= data[j] <= 0x7e:
            j += 1
        s = data[i:j].decode("ascii", "ignore")
        if len(s) >= 6 and is_real_display(s):
            pid, t = find_obj(i)
            if pid is not None:
                by_pid[pid] += 1
                by_type[t] += 1
                if len(by_pid_examples[pid]) < 3:
                    by_pid_examples[pid].append(s[:80])
        i = j
    else:
        i += 1

print("REAL display strings found (after exclusions):")
print("by object TYPE:")
for t, c in by_type.most_common():
    print(f"   {t:30s} {c}")
print("\nby path_id (top 30):")
for pid, c in by_pid.most_common(30):
    print(f"   pid={pid:8d}  count={c:4d}  examples={by_pid_examples[pid][:2]}")
print(f"\ntotal pids containing real display text: {len(by_pid)}")
print(f"total real display string occurrences: {sum(by_pid.values())}")
