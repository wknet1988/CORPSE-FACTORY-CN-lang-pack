#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
110_find_missing.py
定位 todo_list 中「已译但 occurrences.json 里没有位置」的 371 条文本。

方法：遍历 MonoBehaviour 对象，扫描其 raw data 中所有
「<int32 长度><UTF-8 内容>」形式的字符串槽，收集槽文本，
再与目标集合求交。
"""
import os, sys, json, struct
from UnityPy import Environment

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY/CORPSE FACTORY_Data/resources.assets"

def load(p):
    return json.load(open(os.path.join(HERE, p), encoding="utf-8"))

def scan_slots(raw):
    """产出 (off, consumed_len, text) —— 槽起点、原槽消耗字节数、文本"""
    n = len(raw)
    i = 0
    out = []
    while i + 4 <= n:
        L = struct.unpack_from("<i", raw, i)[0]
        if L <= 0 or L > 4000 or i + 4 + L > n:
            i += 1
            continue
        chunk = raw[i+4:i+4+L]
        try:
            t = chunk.decode("utf-8")
        except UnicodeDecodeError:
            i += 1
            continue
        # 必须全是可打印字符或常见控制符
        if all((c >= " " or c in "\n\t\r") for c in t):
            out.append((i, (4 + L + 3) & ~3, t))
            i += (4 + L + 3) & ~3
        else:
            i += 1
    return out

def main():
    todo = load("todo_list.json")
    occ = load("occurrences.json")
    trans = load("translations_complete.json")
    occt = set(o["text"] for o in occ)
    targets = [t for t in todo if t not in occt and t in trans]
    tset = set(targets)
    print("目标条数: %d" % len(targets))

    env = Environment(BASE)
    found = {}   # text -> list of (pid, off, rsz)
    objcount = 0
    for obj in env.objects:
        if obj.type.name != "MonoBehaviour":
            continue
        try:
            raw = obj.get_raw_data()
        except Exception:
            continue
        if len(raw) < 16 or len(raw) > 4_000_000:
            continue
        objcount += 1
        for off, rsz, t in scan_slots(raw):
            if t in tset:
                found.setdefault(t, []).append((obj.path_id, off, rsz))
    print("扫描 MonoBehaviour: %d" % objcount)
    hit = len(found)
    print("命中不同文本: %d / %d" % (hit, len(targets)))
    tot = sum(len(v) for v in found.values())
    print("命中槽位总数: %d" % tot)

    miss = [t for t in targets if t not in found]
    print("未命中: %d" % len(miss))
    for t in miss[:40]:
        print("   MISS %r" % t[:100])

    print("\n--- 命中样本（前 50 条，含出现次数）---")
    for t in sorted(found, key=lambda x: (len(x), x))[:50]:
        print("   x%-2d %r" % (len(found[t]), t[:90]))

    json.dump({t: v for t, v in found.items()},
              open(os.path.join(HERE, "missing_locations.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("\n已写出 missing_locations.json")

if __name__ == "__main__":
    main()
