#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
112_verify_short.py
校验短句补注入结果：
  1) 369 条目标短句是否仍以「完整槽」形式存在（长度前缀 + 原文）
  2) 结构完整性（对象数）
  3) 抽查 Bitch. / Wait… / OK. 的实际落地
"""
import os, sys, json, struct
from UnityPy import Environment

HERE = os.path.dirname(os.path.abspath(__file__))
PATH = sys.argv[1] if len(sys.argv) > 1 else r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY/build_short/resources.assets"


def main():
    data = open(PATH, "rb").read()
    print("file: %s (%d bytes)" % (PATH, len(data)))

    loc = json.load(open(os.path.join(HERE, "missing_locations.json"), encoding="utf-8"))
    trans = json.load(open(os.path.join(HERE, "translations_complete.json"), encoding="utf-8"))

    still = []
    gone = 0
    for en in loc:
        if en not in trans:
            continue
        enb = en.encode("utf-8")
        pat = struct.pack("<i", len(enb)) + enb
        c = data.count(pat)
        if c:
            still.append((en, c))
        else:
            gone += 1
    print("短句已消失: %d / %d" % (gone, gone + len(still)))
    if still:
        print("仍残留 %d 条:" % len(still))
        for en, c in sorted(still, key=lambda x: -x[1])[:30]:
            print("   x%-2d %r" % (c, en[:70]))

    # 译文落地抽查
    print("\n--- 译文落地抽查 ---")
    for en in ["Bitch.", "Wait…", "OK.", "Shit.", "“Ah…”", "Fire.", "No!"]:
        if en not in trans:
            print("   %-12r (无译文)" % en); continue
        zh = trans[en]
        zhb = zh.encode("utf-8")
        zp = struct.pack("<i", len(zhb)) + zhb
        print("   %-12r -> %-12r  原文槽残留=%d  译文槽=%d"
              % (en, zh, data.count(struct.pack("<i", len(en.encode("utf-8"))) + en.encode("utf-8")),
                 data.count(zp)))

    env = Environment(PATH)
    print("\nobjects: %d" % len(env.objects))


if __name__ == "__main__":
    main()
