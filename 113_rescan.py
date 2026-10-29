#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
113_rescan.py
重新定位 371 条短句：不再逐字节扫槽，改为对每个对象直接搜索
「<int32 字节长度><UTF-8 原文>」这一精确模式，因此不受对象体积限制。
对每个命中位置校验其消耗区间不越界、且与其它命中不重叠。
"""
import os, sys, json, struct
from UnityPy import Environment

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY/CORPSE FACTORY_Data"
BASE = os.path.join(DATA, "resources.assets")


def align4(n):
    return (n + 3) & ~3


def load(p):
    return json.load(open(os.path.join(HERE, p), encoding="utf-8"))


def main():
    todo = load("todo_list.json")
    occ = load("occurrences.json")
    trans = load("translations_complete.json")
    occt = set(o["text"] for o in occ)
    targets = [t for t in todo if t not in occt and t in trans]
    tset = set(targets)
    print("目标条数: %d" % len(targets))

    # 预编译每个目标的 pattern
    pats = {}
    for t in targets:
        b = t.encode("utf-8")
        pats[t] = struct.pack("<i", len(b)) + b

    env = Environment(BASE)
    found = {}
    obj_sizes = []
    n_obj = 0
    for obj in env.objects:
        if obj.type.name != "MonoBehaviour":
            continue
        try:
            raw = obj.get_raw_data()
        except Exception:
            continue
        if len(raw) < 16:
            continue
        n_obj += 1
        obj_sizes.append((len(raw), obj.path_id))
        hits = []
        for t, pat in pats.items():
            start = 0
            while True:
                p = raw.find(pat, start)
                if p < 0:
                    break
                rsz = align4(4 + len(pat) - 4)
                if p + rsz <= len(raw):
                    hits.append((p, rsz, t))
                start = p + 1
        if not hits:
            continue
        hits.sort()
        # 丢弃互相重叠的命中（保留先出现的）
        clean = []
        for h in hits:
            if clean and h[0] < clean[-1][0] + clean[-1][1]:
                continue
            clean.append(h)
        for p, rsz, t in clean:
            found.setdefault(t, []).append((obj.path_id, p, rsz))

    print("扫描 MonoBehaviour: %d" % n_obj)
    obj_sizes.sort(reverse=True)
    print("最大 5 个对象: %s" % [(s, p) for s, p in obj_sizes[:5]])

    hit = len(found)
    print("命中不同文本: %d / %d" % (hit, len(targets)))
    print("命中槽位总数: %d" % sum(len(v) for v in found.values()))
    miss = [t for t in targets if t not in found]
    print("未命中: %d" % len(miss))
    for t in miss[:30]:
        print("   MISS %r" % t[:90])

    json.dump(found, open(os.path.join(HERE, "missing_locations2.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("已写出 missing_locations2.json")


if __name__ == "__main__":
    main()
