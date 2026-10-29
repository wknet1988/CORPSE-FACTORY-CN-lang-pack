import os, struct, json, re, UnityPy

DATA = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY/CORPSE FACTORY_Data"
env = UnityPy.load(os.path.join(DATA, "resources.assets"))

LINE_CLASSES = [b"CommandScriptLine", b"CommentScriptLine", b"LabelScriptLine",
                b"GenericTextScriptLine", b"EmptyScriptLine"]
CMD_TOKENS = {"PrintText","Choice","ChoiceState","GenericText","PrintTextLines","PrintTextOr",
              "Command","Wait","HidePrinter","ShowPrinter","ClearPrinter","ResetText",
              "Naninovel","Elringus.Naninovel.Runtime","Naninovel.Commands","Naninovel.Script",
              "UnityEngine","UnityEngine.UI","CommandScriptLine","CommentScriptLine",
              "LabelScriptLine","GenericScriptLine","EmptyScriptLine","Background",
              "Character","ChoiceHandler","TextPrinter","Actor","Camera","Audio","Input",
              "LocalizationManager","ScriptManager"}
DENY = CMD_TOKENS | {c.decode() for c in LINE_CLASSES}

def fast_strings(b, start, end):
    """Walk length-prefixed strings between start..end, skipping 4-byte non-string fields."""
    i = start
    out = []
    while i + 4 <= end:
        ln = struct.unpack_from("<i", b, i)[0]
        if 0 < ln <= 100000:
            s = b[i+4:i+4+ln]
            try:
                t = s.decode("utf-8")
            except Exception:
                i += 4
                continue
            # plausibility: mostly printable
            if sum(1 for c in t if 32 <= ord(c) < 127 or ord(c) > 127) >= len(t)*0.8:
                out.append((i, i+4+ln, t))
                i = (i+4+ln+3) & ~3
                continue
        i += 4
    return out

def is_hex(t):
    return 4 <= len(t) <= 12 and all(c in "0123456789abcdefABCDEF" for c in t)

IDENT = re.compile(r"^[A-Za-z0-9_]+$")  # no spaces, no punctuation -> identifier-like

def is_display(t):
    if not t or len(t) < 2:
        return False
    if t in DENY:
        return False
    if is_hex(t):
        return False
    # reject strings with control chars / nulls (misaligned reads)
    if any(ord(c) < 0x20 for c in t):
        return False
    # reject pure identifiers (CHOICE_AOI_A, ACHIEVEMENT_11, PlaySfx, Script_Act_01, Act_Start, Black_Screen)
    if IDENT.match(t):
        return False
    # require it to look like display text: has a space, or ends with terminal punctuation, or is long with lowercase
    has_space = " " in t
    ends_term = t[-1] in ".?!:)\"'\u201d\u2026\u3002\uff01\uff1f"
    long_lower = len(t) >= 12 and any(c.islower() for c in t)
    if not (has_space or ends_term or long_lower):
        return False
    if not re.search(r"[A-Za-z]", t):
        return False
    return True

def find_elements(b):
    markers = []
    for cls in LINE_CLASSES:
        pat = struct.pack("<i", len(cls)) + cls
        start = 0
        while True:
            p = b.find(pat, start)
            if p < 0: break
            markers.append(p)
            start = p + 1
    markers.sort()
    elems = []
    for idx, m in enumerate(markers):
        end = markers[idx+1] if idx+1 < len(markers) else len(b)
        elems.append((m, end))
    return elems

results = []
for obj in env.objects:
    if obj.type.name != "MonoBehaviour":
        continue
    raw = obj.get_raw_data()
    name_field = struct.unpack_from("<i", raw, 28)[0]
    sname = raw[32:32+name_field].decode("utf-8","replace") if 0 < name_field < 200 else ""
    elems = find_elements(raw)
    if not elems:
        continue
    cls_count = sum(1 for (s,e) in elems if raw[s+4:s+4+17]==b"CommandScriptLine")
    if cls_count < 2 and not any(k in sname for k in ("Script","Credits","Title")):
        continue
    for (s, e) in elems:
        seg = raw[s:e]
        line_cls = None
        for c in LINE_CLASSES:
            if seg[:4] == struct.pack("<i", len(c)) + c:
                line_cls = c.decode(); break
        # skip label/empty
        if line_cls in ("LabelScriptLine","EmptyScriptLine"):
            continue
        for (ss, se, t) in fast_strings(seg, 0, len(seg)):
            if is_display(t):
                results.append({
                    "script": sname, "line_cls": line_cls,
                    "abs_off": s + ss, "len": se - ss, "text": t,
                })

print("prose strings found (occurrences):", len(results))
json.dump(results, open(r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY/_cnwork/extracted_text.json","w"), ensure_ascii=False)
uniq = sorted({r["text"] for r in results})
print("unique texts:", len(uniq))
open(r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY/_cnwork/unique_texts.txt","w",encoding="utf-8").write("\n".join(uniq))
from collections import Counter
print("per script:", dict(Counter(r["script"] for r in results)))
