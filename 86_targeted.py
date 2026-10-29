# -*- coding: utf-8 -*-
"""精确定位两类缺口：
A) 脚本对象内、仍未翻译的短文本（含单词）
B) 非脚本对象内的 UI 标签（LOG/SKIP/AUTO/HIDE 等）及其上下文归属
"""
import os, re, struct, json
from collections import Counter, defaultdict
import UnityPy

GAME = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY"
BACKUP = os.path.join(GAME, "CORPSE FACTORY_Data", "backup_original", "resources.assets")
HERE = os.path.dirname(os.path.abspath(__file__))
CJK = re.compile(r"[\u4e00-\u9fff]")

DENY = {
    "Naninovel", "Elringus.Naninovel.Runtime", "Naninovel.Commands", "Naninovel.Script",
    "CommandScriptLine", "CommentScriptLine", "LabelScriptLine", "GenericTextScriptLine",
    "EmptyScriptLine", "PrintText", "GenericText", "ResetText", "Wait", "Goto", "Stop",
    "HidePrinter", "ShowPrinter", "ClearPrinter", "AddChoice", "ChoiceHandler",
    "SetCustomVariable", "ModifyCharacter", "ModifyBackground", "ModifyTextPrinter",
    "HideActors", "ShowActors", "PlayBgm", "StopBgm", "PlaySfx", "StopSfx",
    "PlayVoice", "StopVoice", "HideUI", "ShowUI", "AppendLineBreak", "UnityEngine",
    "Assembly-CSharp", "MainScript", "resources.assets", "resources.assets.resS",
    "resources.resource", "Background", "Character", "Audio", "Camera", "TextPrinter",
}
HEX8 = re.compile(r"^[0-9a-fA-F]{8}$")
UPPER_ID = re.compile(r"^[A-Z][A-Z0-9_]*$")

def scan_lp(b):
    out = []
    n = len(b); i = 0
    while i + 4 <= n:
        L = struct.unpack_from("<i", b, i)[0]
        if 1 <= L <= 3000 and i + 4 + L <= n:
            seg = b[i+4:i+4+L]
            bad = False
            for c in seg:
                if c < 0x20 and c not in (9, 10, 13):
                    bad = True; break
            if not bad:
                try:
                    t = seg.decode("utf-8")
                except Exception:
                    t = None
                if t is not None:
                    out.append((i + 4, i + 4 + L, t))
                    i = (i + 4 + L + 3) & ~3
                    continue
        i += 4
    return out

env = UnityPy.load(BACKUP)
occ = json.load(open(os.path.join(HERE, "occurrences.json"), encoding="utf-8"))
script_pids = set(o["pid"] for o in occ)
tr = json.load(open(os.path.join(HERE, "translations_complete.json"), encoding="utf-8"))
print("脚本对象 pid 数: %d | 译文表: %d" % (len(script_pids), len(tr)))

def usable(t):
    if not t.strip(): return False
    if t in DENY: return False
    if t.startswith("@"): return False
    if t.startswith("#"): return False
    if HEX8.match(t): return False
    if UPPER_ID.match(t) and len(t) > 3: return False
    if not re.search(r"[A-Za-z]", t): return False
    if re.search(r"\.(png|jpg|wav|mp3|ogg|mat|asset|prefab|shader|ttf|otf|anim|controller|json|txt|bytes|resS|assets|dll|exe)$", t, re.I): return False
    if re.search(r"(UnityEngine|Naninovel|Elringus)", t): return False
    if "/" in t or "\\" in t: return False
    return True

# ---------- A. 脚本对象内的未译短文本 ----------
print("\n" + "=" * 72)
print("A) 脚本对象内仍未翻译的文本（含单词）")
print("=" * 72)
script_hits = defaultdict(list)   # text -> [(pid, off)]
for o in env.objects:
    if o.type.name != "MonoBehaviour" or o.path_id not in script_pids:
        continue
    raw = o.get_raw_data()
    for a, b, t in scan_lp(raw):
        if t in tr: continue
        if CJK.search(t): continue
        if not usable(t): continue
        script_hits[t].append((o.path_id, a))

print("未译唯一文本: %d" % len(script_hits))
buckets = defaultdict(list)
for t in script_hits:
    buckets[min(len(t.split()), 5)].append(t)
for w in sorted(buckets):
    label = "%d 词" % w if w < 5 else "5+ 词"
    print("\n--- %s : %d ---" % (label, len(buckets[w])))
    for t in sorted(buckets[w], key=lambda s: (len(s), s))[:70]:
        print("   %r" % t[:110])

json.dump({t: script_hits[t] for t in script_hits},
          open(os.path.join(HERE, "gap_A_script.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

# ---------- B. 非脚本对象的 UI 标签 ----------
print("\n" + "=" * 72)
print("B) 非脚本对象内的 UI 标签候选")
print("=" * 72)
ui_hits = defaultdict(list)
for o in env.objects:
    if o.type.name != "MonoBehaviour" or o.path_id in script_pids:
        continue
    raw = o.get_raw_data()
    for a, b, t in scan_lp(raw):
        if t in tr: continue
        if CJK.search(t): continue
        if not usable(t): continue
        # UI 标签特征：1~4 词、字母开头、无数字串、长度 <= 40
        if len(t) > 40: continue
        if len(t.split()) > 4: continue
        if not re.match(r"^[A-Za-z]", t): continue
        ui_hits[t].append((o.path_id, a))

print("UI 候选: %d 个唯一值" % len(ui_hits))
for t, locs in sorted(ui_hits.items(), key=lambda kv: -len(kv[1])):
    pids = sorted({p for p, _ in locs})
    print("   x%-4d %-28r pids=%s" % (len(locs), t, pids[:5]))

json.dump({t: ui_hits[t] for t in ui_hits},
          open(os.path.join(HERE, "gap_B_ui.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

# ---------- C. LOG/SKIP/AUTO/HIDE 上下文 ----------
print("\n" + "=" * 72)
print("C) 控制面板标签 LOG/SKIP/AUTO/HIDE 的归属与上下文")
print("=" * 72)
for w in ["LOG", "SKIP", "AUTO", "HIDE"]:
    print("\n=== %s ===" % w)
    pat = struct.pack("<i", len(w)) + w.encode()
    found = 0
    for o in env.objects:
        if o.type.name != "MonoBehaviour":
            continue
        raw = o.get_raw_data()
        p = 0
        while True:
            q = raw.find(pat, p)
            if q < 0: break
            p = q + 1
            # 上下文：前后各 3 个字符串
            before = scan_lp(raw[max(0, q - 300): q])
            after = scan_lp(raw[q: min(len(raw), q + 300)])
            bs = [x[2] for x in before][-4:]
            afs = [x[2] for x in after][:4]
            print("  pid=%s off=%d  前=%s  后=%s" % (o.path_id, q, bs, afs))
            found += 1
            if found >= 6: break
        if found >= 6: break
