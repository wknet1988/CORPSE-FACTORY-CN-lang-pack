# -*- coding: utf-8 -*-
"""看几个低出现次数的疑似单词展示文本，其前后字节到底是什么。
若确认是展示文本，就能拿到精确 offset 做定点替换。"""
import os, struct, json
import UnityPy

GAME = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY"
BACKUP = os.path.join(GAME, "CORPSE FACTORY_Data", "backup_original", "resources.assets")
HERE = os.path.dirname(os.path.abspath(__file__))

true_scripts = json.load(open(os.path.join(HERE, "true_scripts.json"), encoding="utf-8"))
pids = {t["pid"]: t["name"] for t in true_scripts}

env = UnityPy.load(BACKUP)
raws = {}
for o in env.objects:
    if o.path_id in pids:
        raws[o.path_id] = o.get_raw_data()

def align4(n): return (n + 3) & ~3

def show(pid, raw, p, word):
    """从 p-140 开始按 str/i32 混合走，打印到 word 之后"""
    start = max(0, p - 140)
    q = start
    print("  --- 从 %d 开始 ---" % start)
    for _ in range(14):
        if q + 4 > len(raw): break
        n = struct.unpack_from("<i", raw, q)[0]
        if 0 <= n <= 200 and q + 4 + n <= len(raw):
            try:
                t = raw[q+4:q+4+n].decode("utf-8")
                ok = all(32 <= ord(c) < 127 or ord(c) > 127 for c in t)
                if ok:
                    mark = "   <<< 目标" if q + 4 == p else ""
                    print("    @%-8d str len=%-3d %r%s" % (q, n, t[:60], mark))
                    q = align4(q + 4 + n)
                    if q + 4 > p + 4 + len(word): break
                    continue
            except Exception:
                pass
        print("    @%-8d i32=%d" % (q, n))
        q += 4

for word in ["Thud", "Rain", "Morgue", "Zipper", "Stairwell"]:
    pat = struct.pack("<i", len(word)) + word.encode()
    print("\n" + "=" * 70)
    print("WORD %r" % word)
    print("=" * 70)
    shown = 0
    for pid, raw in raws.items():
        s = 0
        while shown < 3:
            q = raw.find(pat, s)
            if q < 0: break
            s = q + 1
            print(" pid=%s (%s) prefix_off=%d" % (pid, pids[pid], q))
            show(pid, raw, q + 4, word)
            shown += 1
        if shown >= 3: break
