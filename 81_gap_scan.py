# -*- coding: utf-8 -*-
"""缺口扫描：1) 单词/短语级未译文本  2) UI 组件(m_Text/m_text)里的英文
对 DEPLOYED 与 BACKUP 同时扫描，输出差异，定位漏译来源。
"""
import json, os, re, struct, sys
from collections import Counter, defaultdict
import UnityPy

GAME = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY"
DEPLOY = os.path.join(GAME, "CORPSE FACTORY_Data", "resources.assets")
BACKUP = os.path.join(GAME, "CORPSE FACTORY_Data", "backup_original", "resources.assets")
HERE = os.path.dirname(os.path.abspath(__file__))

CJK = re.compile(r"[\u4e00-\u9fff]")
STRUCT = {
    "Naninovel", "Elringus.Naninovel.Runtime", "CommandScriptLine", "CommentScriptLine",
    "LabelScriptLine", "GenericTextScriptLine", "EmptyScriptLine", "SetCustomVariable",
    "Naninovel.Commands", "UnityEngine", "System.Collections.Generic.List`1",
}
HEX8 = re.compile(r"^[0-9a-f]{8}$")
# 明显的标识符/资源名/变量
IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_.\-]*$")
ASSET_EXT = re.compile(r"\.(png|jpg|wav|mp3|ogg|mat|asset|prefab|unity|shader|ttf|otf|anim|controller|json|txt|bytes|resS|assets)$", re.I)

def scan_strings(b, minlen=1, maxlen=4000):
    """length-prefixed printable utf-8 strings"""
    out = []
    n = len(b); i = 0
    while i + 4 <= n:
        L = struct.unpack_from("<i", b, i)[0]
        if minlen <= L <= maxlen and i + 4 + L <= n:
            seg = b[i + 4:i + 4 + L]
            ok = True
            for c in seg:
                if c < 0x20 and c not in (9, 10, 13):
                    ok = False; break
            if ok:
                try:
                    t = seg.decode("utf-8")
                except Exception:
                    t = None
                if t is not None:
                    out.append((i, t))
                    i += 4 + L
                    continue
        i += 1
    return out

def load_typetrees(path, label):
    """返回 {pid: {'name':..., 'm_Text':..., 'm_text':...}}"""
    env = UnityPy.load(path)
    res = {}
    types = Counter()
    for obj in env.objects:
        types[obj.type.name] += 1
    print("[%s] object types: %s" % (label, dict(types.most_common(12))))
    return env, types

def main():
    tr = json.load(open(os.path.join(HERE, "translations_complete.json"), encoding="utf-8"))
    print("translations_complete.json: %d entries" % len(tr))
    trkeys = set(tr.keys())

    # ---------- A. UI 组件文本 ----------
    print("\n" + "=" * 72)
    print("A. UI 组件 m_Text / m_text 扫描")
    print("=" * 72)
    env = UnityPy.load(BACKUP)
    ui_hits = []
    for obj in env.objects:
        if obj.type.name != "MonoBehaviour":
            continue
        try:
            tree = obj.read_typetree()
        except Exception:
            continue
        if not isinstance(tree, dict):
            continue
        for k in ("m_Text", "m_text", "m_CachedText", "text"):
            v = tree.get(k)
            if isinstance(v, str) and v.strip():
                ui_hits.append((obj.path_id, k, v))
                break
    print("含文本字段的 MonoBehaviour: %d" % len(ui_hits))
    en_ui = [(p, k, v) for p, k, v in ui_hits if not CJK.search(v) and re.search(r"[A-Za-z]{2,}", v)]
    print("其中仍为英文的: %d" % len(en_ui))
    seen = set()
    for p, k, v in en_ui:
        if v in seen: continue
        seen.add(v)
        print("   pid=%s %s %r  [已译:%s]" % (p, k, v[:70], "Y" if v in trkeys else "N"))

    # ---------- B. 全部 MonoBehaviour 长度前缀字符串 ----------
    print("\n" + "=" * 72)
    print("B. BACKUP 中所有 length-prefixed 字符串（无空格要求）")
    print("=" * 72)
    occ = json.load(open(os.path.join(HERE, "occurrences.json"), encoding="utf-8"))
    script_pids = set(o["pid"] for o in occ)

    allstr = defaultdict(list)   # text -> [(pid, off)]
    for obj in env.objects:
        if obj.type.name != "MonoBehaviour":
            continue
        try:
            raw = obj.get_raw_data()
        except Exception:
            continue
        for off, t in scan_strings(raw, 1, 4000):
            allstr[t].append((obj.path_id, off))

    print("唯一字符串总数: %d" % len(allstr))

    def is_candidate(t):
        if t in STRUCT: return False
        if t.startswith("@"): return False       # Naninovel 命令
        if t.startswith("#"): return False       # 标签
        if HEX8.match(t): return False
        if ASSET_EXT.search(t): return False
        if not re.search(r"[A-Za-z]", t): return False
        if len(t) > 200: return False
        # 纯标识符且全大写/驼峰且无空格，多半是 key
        if IDENT.match(t) and ("_" in t or t.isupper() or re.search(r"[a-z][A-Z]", t)):
            return False
        return True

    cands = {t: v for t, v in allstr.items() if is_candidate(t)}
    print("过滤后候选文本: %d" % len(cands))

    untranslated = {t: v for t, v in cands.items() if t not in trkeys and not CJK.search(t)}
    print("**未在译文表中且无中文的: %d**" % len(untranslated))

    # 按词数分桶
    buckets = defaultdict(list)
    for t in untranslated:
        w = len(t.split())
        buckets[min(w, 5)].append(t)
    for w in sorted(buckets):
        label = "%d 词" % w if w < 5 else "5+ 词"
        print("\n--- %s : %d 条 ---" % (label, len(buckets[w])))
        for t in sorted(buckets[w], key=len)[:40]:
            pid = untranslated[t][0][0]
            where = "脚本" if pid in script_pids else "非脚本"
            print("   [%s pid=%s] %r" % (where, pid, t[:80]))

    json.dump({t: untranslated[t] for t in untranslated},
              open(os.path.join(HERE, "gap_untranslated.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("\n-> 已写出 gap_untranslated.json")

if __name__ == "__main__":
    main()
