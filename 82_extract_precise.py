# -*- coding: utf-8 -*-
"""精确提取：按 Naninovel 元素结构走，取 GenericTextScriptLine 的 body 字符串。
优点：不依赖「含空格」启发式，单词短句也能抓到；不会混入 TMP 配置键/命令名。
同时探测 UI 关键词（Continue/Settings/Quit...）在文件中的真实位置。
"""
import json, os, re, struct, sys
from collections import Counter, defaultdict
import UnityPy

GAME = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY"
DEPLOY = os.path.join(GAME, "CORPSE FACTORY_Data", "resources.assets")
BACKUP = os.path.join(GAME, "CORPSE FACTORY_Data", "backup_original", "resources.assets")
HERE = os.path.dirname(os.path.abspath(__file__))
CJK = re.compile(r"[\u4e00-\u9fff]")

LINE = [b'CommandScriptLine', b'CommentScriptLine', b'LabelScriptLine',
        b'GenericTextScriptLine', b'EmptyScriptLine']
KNOWN = {c.decode() for c in LINE}

def align4(n): return (n + 3) & ~3

class Bad(Exception): pass

def rd_i32(b, p, limit):
    if p + 4 > limit: raise Bad("i32 OOB")
    return struct.unpack_from("<i", b, p)[0], p + 4

def rd_str(b, p, limit):
    if p + 4 > limit: raise Bad("str OOB")
    n = struct.unpack_from("<i", b, p)[0]
    if n < 0 or p + 4 + n > limit: raise Bad("str body OOB")
    try:
        t = b[p+4:p+4+n].decode("utf-8")
    except Exception:
        raise Bad("str not utf8")
    return t, align4(p + 4 + n)

def walk_body(b, p, limit, collect):
    """走 body，返回结束位置；collect 为 list 时收集字符串 (off,text)"""
    while p < limit:
        if p + 4 > limit: raise Bad("body tail OOB")
        n = struct.unpack_from("<i", b, p)[0]
        ok = (0 <= n <= (limit - p - 4))
        if ok:
            chunk = b[p+4:p+4+n]
            try:
                t = chunk.decode("utf-8")
                printable = sum(1 for c in t if (32 <= ord(c) < 127) or ord(c) > 127)
                if printable >= max(1, len(t) * 0.6):
                    if collect is not None and n > 0:
                        collect.append((p + 4, t))
                    p = align4(p + 4 + n)
                    continue
            except Exception:
                pass
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

def extract_object(raw):
    """返回 [(cls, off, text)]"""
    out = []
    markers = find_markers(raw)
    if not markers:
        return out
    limit = len(raw)
    for i, p in enumerate(markers):
        nxt = markers[i+1] if i+1 < len(markers) else limit
        try:
            ln = struct.unpack_from("<i", raw, p)[0]
            cls = raw[p+4:p+4+ln].decode("utf-8", "replace")
            if cls not in KNOWN: continue
            p2 = align4(p + 4 + ln)
            _, p2 = rd_str(raw, p2, limit)   # ns
            _, p2 = rd_str(raw, p2, limit)   # asm
            _, p2 = rd_i32(raw, p2, limit)   # flags
            _, p2 = rd_str(raw, p2, limit)   # linehash
            got = []
            end = walk_body(raw, p2, nxt, got)
            if end != nxt:
                continue  # 结构不吻合，跳过该元素（避免垃圾）
            for off, t in got:
                out.append((cls, off, t))
        except Bad:
            continue
    return out

def main():
    tr = json.load(open(os.path.join(HERE, "translations_complete.json"), encoding="utf-8"))
    trkeys = set(tr.keys())
    print("译文表: %d 条" % len(trkeys))

    env = UnityPy.load(BACKUP)
    allitems = []   # (pid, cls, off, text)
    for obj in env.objects:
        if obj.type.name != "MonoBehaviour":
            continue
        raw = obj.get_raw_data()
        for cls, off, t in extract_object(raw):
            allitems.append((obj.path_id, cls, off, t))

    print("结构解析得到文本片段: %d" % len(allitems))
    bycls = Counter(c for _, c, _, _ in allitems)
    print("按元素类型: %s" % dict(bycls))

    # 只看正文行
    texts = [(pid, off, t) for pid, cls, off, t in allitems if cls == "GenericTextScriptLine"]
    uniq = {}
    for pid, off, t in texts:
        uniq.setdefault(t, []).append((pid, off))
    print("正文唯一字符串: %d" % len(uniq))

    miss = {t: v for t, v in uniq.items() if t not in trkeys and not CJK.search(t)}
    print("\n**正文里未翻译的: %d**" % len(miss))
    buckets = defaultdict(list)
    for t in miss:
        buckets[min(len(t.split()), 4)].append(t)
    for w in sorted(buckets):
        print("\n--- %s ---" % ("%d 词" % w if w < 4 else "4+ 词"))
        for t in sorted(buckets[w], key=lambda s: (len(s), s))[:60]:
            pid = miss[t][0][0]
            print("   [pid=%s] %r" % (pid, t[:100]))

    json.dump({t: miss[t] for t in miss},
              open(os.path.join(HERE, "gap_script_text.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("\n-> gap_script_text.json 已写出")

    # ---------- UI 关键词探测 ----------
    print("\n" + "=" * 72)
    print("UI 关键词在 BACKUP / DEPLOY 中的出现情况（length-prefixed 精确匹配）")
    print("=" * 72)
    words = ["Continue", "New Game", "Settings", "Quit", "Backlog", "Save", "Load",
             "Auto", "Skip", "Title", "Extras", "Gallery", "Confirm", "Cancel",
             "Yes", "No", "Close", "Resume", "Restart", "Main Menu", "Return",
             "Chapter Select", "Achievements", "Credits", "Language", "Text Speed",
             "Volume", "Fullscreen", "On", "Off"]
    for path, label in ((BACKUP, "BACKUP"), (DEPLOY, "DEPLOY")):
        data = open(path, "rb").read()
        print("\n--- %s ---" % label)
        for w in words:
            pat = struct.pack("<i", len(w.encode())) + w.encode()
            idxs = []
            s = 0
            while True:
                p = data.find(pat, s)
                if p < 0: break
                idxs.append(p); s = p + 1
            if idxs:
                print("  %-18r x%d  offs=%s" % (w, len(idxs), idxs[:4]))

if __name__ == "__main__":
    main()
