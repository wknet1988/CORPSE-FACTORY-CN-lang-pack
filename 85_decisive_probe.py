# -*- coding: utf-8 -*-
"""决定性探针：
A) MonoBehaviour 的 typetree 是否可读？哪些含 text 字段？
B) @choice 等命令里的选项文本是否英文（未被译）
C) 部署文件里仍为英文的短标签（1~3 词、首字母大写、非标识符）
"""
import os, re, struct, json
from collections import Counter, defaultdict
import UnityPy

GAME = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY"
BACKUP = os.path.join(GAME, "CORPSE FACTORY_Data", "backup_original", "resources.assets")
DEPLOY = os.path.join(GAME, "CORPSE FACTORY_Data", "resources.assets")
HERE = os.path.dirname(os.path.abspath(__file__))
CJK = re.compile(r"[\u4e00-\u9fff]")

env = UnityPy.load(BACKUP)

print("=" * 72)
print("A) typetree 可读性")
print("=" * 72)
ok = 0; fail = 0
keysets = Counter()
text_fields = []
for o in env.objects:
    if o.type.name != "MonoBehaviour":
        continue
    try:
        tree = o.read_typetree()
        ok += 1
        ks = tuple(sorted(k for k in tree.keys() if "ext" in k.lower() or "text" in k.lower()))
        keysets[ks] += 1
        if ks:
            text_fields.append((o.path_id, ks, {k: tree[k] for k in ks}))
    except Exception:
        fail += 1
print("typetree 读取成功: %d / 失败: %d" % (ok, fail))
print("含 text 相关字段的键组合:")
for ks, c in keysets.most_common(10):
    print("   x%-5d %s" % (c, ks))
print("\n样例:")
for pid, ks, vals in text_fields[:12]:
    print("   pid=%s %s" % (pid, ks))
    for k, v in vals.items():
        sv = v if isinstance(v, str) else repr(v)
        print("       %s = %r" % (k, sv[:80]))

print("\n" + "=" * 72)
print("B) 命令里的选项/提示文本")
print("=" * 72)
data = open(BACKUP, "rb").read()
for cmd in ["@choice", "@print", "@input", "@set", "@goto", "@show", "@hide",
            "@wait", "@stop", "@if", "@else", "@endif", "@title"]:
    pat = struct.pack("<i", len(cmd)) + cmd.encode()
    c = data.count(pat)
    print("  %-10s length-prefixed 出现 %d 次" % (cmd, c))

# 抽几个 @choice 的完整字符串看看
def scan_lp(data, needle, limit=8):
    out = []
    pat = struct.pack("<i", len(needle)) + needle.encode()
    s = 0
    while len(out) < limit:
        p = data.find(pat, s)
        if p < 0: break
        # 该字符串长度
        n = struct.unpack_from("<i", data, p)[0]
        try:
            t = data[p+4:p+4+n].decode("utf-8")
            out.append(t)
        except Exception:
            pass
        s = p + 1
    return out

print("\n--- @choice 样例 ---")
for t in scan_lp(data, "@choice", 10):
    print("   %r" % t[:150])

print("\n--- 含 choice 的字符串 ---")
cnt = 0
i = 0
n = len(data)
while i + 4 <= n and cnt < 12:
    L = struct.unpack_from("<i", data, i)[0]
    if 2 <= L <= 600 and i + 4 + L <= n:
        try:
            t = data[i+4:i+4+L].decode("utf-8")
            if "choice" in t.lower() and not CJK.search(t):
                print("   off=%d %r" % (i, t[:150]))
                cnt += 1
                i = (i + 4 + L + 3) & ~3
                continue
        except Exception:
            pass
    i += 4

print("\n" + "=" * 72)
print("C) 部署文件中仍为英文的短标签（1~3 词）")
print("=" * 72)
dep = open(DEPLOY, "rb").read()
tr = json.load(open(os.path.join(HERE, "translations_complete.json"), encoding="utf-8"))
cands = Counter()
i = 0
n = len(dep)
while i + 4 <= n:
    L = struct.unpack_from("<i", dep, i)[0]
    if 2 <= L <= 40 and i + 4 + L <= n:
        try:
            t = dep[i+4:i+4+L].decode("utf-8")
        except Exception:
            i += 4; continue
        if (not CJK.search(t) and re.fullmatch(r"[A-Za-z][A-Za-z' \-\.\?\!,]*", t)
                and t.strip() and not t.startswith("@") and t not in tr):
            cands[t] += 1
            i = (i + 4 + L + 3) & ~3
            continue
    i += 4

print("候选短英文串: %d 个唯一值" % len(cands))
for t, c in sorted(cands.items(), key=lambda kv: (-kv[1], kv[0]))[:80]:
    print("   x%-3d %r" % (c, t))
