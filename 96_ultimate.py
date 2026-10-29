# -*- coding: utf-8 -*-
"""终极诊断：1) typetree 能否读 Script？ 2) 'Q' 附近的原始字节到底长什么样"""
import os, struct, json
import UnityPy

GAME = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY"
BACKUP = os.path.join(GAME, "CORPSE FACTORY_Data", "backup_original", "resources.assets")

env = UnityPy.load(BACKUP)
target = None
for o in env.objects:
    if o.path_id == 9127:
        target = o
        break

print("对象类型:", target.type.name, "| path_id:", target.path_id)
raw = target.get_raw_data()
print("raw 长度:", len(raw))

print("\n=== typetree 尝试 ===")
try:
    tree = target.read_typetree()
    print("成功，顶层键:", list(tree.keys())[:20])
    for k in list(tree.keys())[:10]:
        v = tree[k]
        print("   %s : %s" % (k, type(v).__name__))
except Exception as e:
    print("失败:", type(e).__name__, e)

print("\n=== read() 尝试 ===")
try:
    d = target.read()
    print("类:", d.__class__.__name__)
    attrs = [a for a in dir(d) if not a.startswith("_")][:25]
    print("属性:", attrs)
except Exception as e:
    print("失败:", type(e).__name__, e)

print("\n=== 'Q'(off=94620 附近) 原始字节 ===")
# 找到单字符 'Q' 的长度前缀
pat = struct.pack("<i", 1) + b"Q"
p = raw.find(pat)
print("首次出现 prefix 位置:", p)
start = max(0, p - 120)
seg = raw[start:p + 60]
print("hex:")
for i in range(0, len(seg), 16):
    chunk = seg[i:i+16]
    hexs = " ".join("%02x" % c for c in chunk)
    asci = "".join(chr(c) if 32 <= c < 127 else "." for c in chunk)
    print("  %08x  %-47s  %s" % (start + i, hexs, asci))

print("\n=== 该位置向前解析 ===")
# 尝试从 p-120 开始按 str 走
q = start
for _ in range(12):
    if q + 4 > len(raw): break
    n = struct.unpack_from("<i", raw, q)[0]
    if 0 <= n <= 200 and q + 4 + n <= len(raw):
        try:
            t = raw[q+4:q+4+n].decode("utf-8")
            print("  @%d len=%d %r" % (q, n, t[:60]))
            q = (q + 4 + n + 3) & ~3
            continue
        except Exception:
            pass
    print("  @%d i32=%d (非字符串)" % (q, n))
    q += 4
