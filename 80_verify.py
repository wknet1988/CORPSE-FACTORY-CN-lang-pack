#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Structural verifier for Naninovel.Script MonoBehaviour objects.

Uses exact className byte-patterns (markers) for element boundaries, then
parses each element's common prefix (rid/i32, className/str, ns/str, asm/str,
flags/i32, linehash/str) and class-specific body, requiring the walk to land
EXACTLY on the next element's marker (or the buffer end for the last element).

A byte-shifted (corrupted) object fails: length prefixes point into garbage,
className decoding breaks, or the walk overshoots / cannot land on the marker.

Run on ORIGINAL to calibrate (must be 100% clean); then on a rebuilt file to
prove it is structurally sound.
"""
import sys, struct
import UnityPy

LINE = [b'CommandScriptLine', b'CommentScriptLine', b'LabelScriptLine',
        b'GenericTextScriptLine', b'EmptyScriptLine']
KNOWN = {c.decode() for c in LINE}

def align4(n): return (n + 3) & ~3

class Bad(Exception): pass

def rd_i32(b, p, limit):
    if p + 4 > limit: raise Bad(f"i32 OOB {p}")
    return struct.unpack_from("<i", b, p)[0], p + 4

def rd_str(b, p, limit):
    if p + 4 > limit: raise Bad(f"str len OOB {p}")
    n = struct.unpack_from("<i", b, p)[0]
    if n < 0 or p + 4 + n > limit: raise Bad(f"str body OOB n={n} at {p}")
    try:
        t = b[p+4:p+4+n].decode("utf-8")
    except Exception:
        raise Bad(f"str not utf8 at {p}")
    return t, align4(p + 4 + n)

def parse_body_generic(b, p, limit):
    # Walk the body as a flat sequence of i32 fields and length-prefixed
    # strings until we exactly reach `limit` (the next element's marker).
    # Disambiguate i32 vs string greedily: prefer string if the length
    # prefix points to a short, valid, printable UTF-8 run.
    while p < limit:
        if p + 4 > limit: raise Bad(f"body tail OOB {p}/{limit}")
        n = struct.unpack_from("<i", b, p)[0]
        candidate_str = (0 <= n <= (limit - p - 4) and (n == 0 or (p + 4 + n) <= limit))
        if candidate_str:
            chunk = b[p+4:p+4+n]
            try:
                t = chunk.decode("utf-8")
                printable = sum(1 for c in t if (32 <= ord(c) < 127) or ord(c) > 127)
                if printable >= max(1, len(t) * 0.6):
                    # treat as string
                    p = align4(p + 4 + n)
                    continue
            except Exception:
                pass
        # otherwise treat as i32
        p += 4
    return p

def find_markers(b):
    ms = []
    for c in LINE:
        pat = struct.pack("<i", len(c)) + c
        s = 0
        while True:
            p = b.find(pat, s)
            if p < 0: break
            ms.append(p); s = p + 1
    ms.sort()
    return ms

def verify_object(b):
    markers = find_markers(b)
    if not markers:
        return False, "no markers"
    limit = len(b)
    for i in range(len(markers)):
        p = markers[i]
        nxt = markers[i+1] if i+1 < len(markers) else limit
        # rid before className
        rid, _ = rd_i32(b, p-4, limit)
        ln = struct.unpack_from("<i", b, p)[0]
        if ln <= 0 or ln > 64: raise Bad(f"cls len {ln} at {p}")
        cls = b[p+4:p+4+ln].decode("utf-8", "replace")
        if cls not in KNOWN: raise Bad(f"unknown className {cls!r} at {p}")
        p2 = align4(p + 4 + ln)
        _, p2 = rd_str(b, p2, limit)   # ns
        _, p2 = rd_str(b, p2, limit)   # asm
        _, p2 = rd_i32(b, p2, limit)   # flags
        _, p2 = rd_str(b, p2, limit)   # linehash
        end = parse_body_generic(b, p2, nxt)
        if end != nxt:
            raise Bad(f"elem {i} ({cls}) body ends at {end}, expected {nxt} (delta {end-nxt})")
    return True, f"ok markers={len(markers)}"

def main(path):
    env = UnityPy.load(path)
    total = script = bad = 0
    bad_samples = []
    for obj in env.objects:
        total += 1
        if obj.type.name != "MonoBehaviour": continue
        raw = obj.get_raw_data()
        if not find_markers(raw): continue
        script += 1
        try:
            ok, info = verify_object(raw)
        except Bad as e:
            ok, info = False, str(e)
        if not ok:
            bad += 1
            if len(bad_samples) < 15:
                bad_samples.append((obj.path_id, info))
    print(f"file={path}")
    print(f"  total={total} script_objects={script} BAD={bad}")
    for pid, info in bad_samples:
        print(f"    BAD pid={pid}: {info}")

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else \
        r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY/CORPSE FACTORY_Data/backup_original/resources.assets"
    main(path)
