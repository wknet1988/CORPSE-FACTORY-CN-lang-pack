import os, struct, json, re, UnityPy

DATA = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY/CORPSE FACTORY_Data"
env = UnityPy.load(os.path.join(DATA, "resources.assets"))

LINE_CLASSES = [b"CommandScriptLine", b"CommentScriptLine", b"LabelScriptLine",
                b"GenericTextScriptLine", b"EmptyScriptLine"]
CMD_TOKENS = {"PrintText","Choice","ChoiceState","GenericText","PrintTextLines","PrintTextOr",
              "Command","Wait","HidePrinter","ShowPrinter","ClearPrinter","ResetText",
              "Naninovel","Elringus.Naninovel.Runtime","Naninovel.Commands","Naninovel.Script",
              "UnityEngine","UnityEngine.UI","CommandScriptLine","CommentScriptLine",
              "LabelScriptLine","GenericTextScriptLine","EmptyScriptLine","Background",
              "Character","ChoiceHandler","TextPrinter","Actor","Camera","Audio","Input",
              "LocalizationManager","ScriptManager"}
DENY = CMD_TOKENS | {c.decode() for c in LINE_CLASSES}
IDENT = re.compile(r"^[A-Za-z0-9_]+$")

def fast_strings(b, start, end):
    i = start; out = []
    while i + 4 <= end:
        ln = struct.unpack_from("<i", b, i)[0]
        if 0 < ln <= 100000:
            s = b[i+4:i+4+ln]
            try: t = s.decode("utf-8")
            except Exception: i += 4; continue
            if sum(1 for c in t if 32 <= ord(c) < 127 or ord(c) > 127) >= len(t)*0.8:
                out.append((i, i+4+ln, t)); i = (i+4+ln+3) & ~3; continue
        i += 4
    return out

def is_hex(t): return 4 <= len(t) <= 12 and all(c in "0123456789abcdefABCDEF" for c in t)

def is_display(t):
    if not t or len(t) < 2: return False
    if t in DENY: return False
    if is_hex(t): return False
    if any(ord(c) < 0x20 for c in t): return False
    if IDENT.match(t): return False
    if t.startswith("@"): return False                 # naninovel command line
    if re.match(r"^[A-Za-z_]+=", t): return False       # assignment / var
    if ";" in t and "=" in t: return False
    has_space = " " in t
    ends_term = t[-1] in ".?!:)\"'\u201d\u2026\u3002\uff01\uff1f"
    long_lower = len(t) >= 12 and any(c.islower() for c in t)
    if not (has_space or ends_term or long_lower): return False
    if not re.search(r"[A-Za-z]", t): return False
    return True

def find_elements(b):
    markers = []
    for cls in LINE_CLASSES:
        pat = struct.pack("<i", len(cls)) + cls
        start = 0
        while True:
            p = b.find(pat, start)
            if p < 0: break
            markers.append(p); start = p + 1
    markers.sort()
    return [(markers[i], markers[i+1] if i+1 < len(markers) else len(b)) for i in range(len(markers))]

occ = []   # {pid, script, line_cls, off, len, text}
count_script = 0
for obj in env.objects:
    if obj.type.name != "MonoBehaviour": continue
    raw = obj.get_raw_data()
    nf = struct.unpack_from("<i", raw, 28)[0]
    sname = raw[32:32+nf].decode("utf-8","replace") if 0 < nf < 200 else ""
    elems = find_elements(raw)
    if not elems: continue
    cc = sum(1 for (s,e) in elems if raw[s+4:s+4+17]==b"CommandScriptLine")
    if cc < 2 and not any(k in sname for k in ("Script","Credits","Title")):
        continue
    for (s, e) in elems:
        seg = raw[s:e]
        line_cls = None
        for c in LINE_CLASSES:
            if seg[:4] == struct.pack("<i", len(c)) + c:
                line_cls = c.decode(); break
        if line_cls in ("LabelScriptLine","EmptyScriptLine"):
            continue
        for (ss, se, t) in fast_strings(seg, 0, len(seg)):
            if is_display(t):
                occ.append({"pid": obj.path_id, "script": sname, "line_cls": line_cls,
                            "off": s + ss, "len": se - ss, "text": t})
    count_script += 1

print("script objects:", count_script, "occurrences:", len(occ))
uniq = sorted({o["text"] for o in occ})
print("unique:", len(uniq))
json.dump(occ, open(r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY/_cnwork/occurrences.json","w"), ensure_ascii=False)
open(r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY/_cnwork/unique_texts.txt","w",encoding="utf-8").write("\n".join(uniq))
from collections import Counter
print(Counter(o["script"] for o in occ))
print("--- sample ---")
for o in occ[:15]: print(repr(o["text"][:60]))
