#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
114_context.py
对指定的短句，输出它在脚本对象里出现位置的前后相邻文本槽，用于判断词义。
用法: <python> 114_context.py "Lie." "Fire."
"""
import os, sys, json, struct
from UnityPy import Environment

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY/CORPSE FACTORY_Data"
BASE = os.path.join(DATA, "resources.assets")


def align4(n):
    return (n + 3) & ~3


def scan_slots(raw):
    n = len(raw)
    i = 0
    out = []
    while i + 4 <= n:
        L = struct.unpack_from("<i", raw, i)[0]
        if L <= 0 or L > 6000 or i + 4 + L > n:
            i += 1
            continue
        chunk = raw[i + 4:i + 4 + L]
        try:
            t = chunk.decode("utf-8")
        except UnicodeDecodeError:
            i += 1
            continue
        if all((c >= " " or c in "\n\t\r") for c in t):
            out.append((i, (4 + L + 3) & ~3, t))
            i += (4 + L + 3) & ~3
        else:
            i += 1
    return out


def main(words):
    loc = json.load(open(os.path.join(HERE, "missing_locations2.json"), encoding="utf-8"))
    trans = json.load(open(os.path.join(HERE, "translations_complete.json"), encoding="utf-8"))
    by_pid = {}
    for w in words:
        for pid, off, rsz in loc.get(w, []):
            by_pid.setdefault(pid, []).append((off, w))
    if not by_pid:
        print("无匹配")
        return

    env = Environment(BASE)
    for obj in env.objects:
        pid = obj.path_id
        if pid not in by_pid:
            continue
        raw = obj.get_raw_data()
        slots = scan_slots(raw)
        idx = {s[0]: k for k, s in enumerate(slots)}
        for off, w in sorted(by_pid[pid]):
            k = idx.get(off)
            print("\n=== %r  pid=%s  slot#%s ===" % (w, pid, k))
            if k is None:
                print("   (槽索引未找到)")
                continue
            for j in range(max(0, k - 2), min(len(slots), k + 3)):
                mark = ">>" if j == k else "  "
                print("   %s %r" % (mark, slots[j][2][:110]))
            print("   译文: %r" % trans.get(w, ""))


if __name__ == "__main__":
    main(sys.argv[1:])
