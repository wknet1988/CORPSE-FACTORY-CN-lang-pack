#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
115_deep_context.py
对指定短句，输出其前后最近的「较完整对话行」（长度>=8），用于判定词义。
"""
import os, sys, json, struct
from UnityPy import Environment

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY/CORPSE FACTORY_Data"
BASE = os.path.join(DATA, "resources.assets")

SKIP_TOKENS = {
    "Elringus.Naninovel.Runtime", "Naninovel.Commands", "UnityEngine", "UnityEngine.UI",
    "PrintText", "ModifyBackground", "ResetText", "CHAT_KOJIRO", "Naninovel.Script",
    "GenericTextScriptLine", "CommandScriptLine", "CommentScriptLine", "EmptyScriptLine",
    "LabelScriptLine", "Choice", "ChoiceState", "Character", "Background",
}


def scan_slots(raw):
    n = len(raw)
    i = 0
    out = []
    while i + 4 <= n:
        L = struct.unpack_from("<i", raw, i)[0]
        if L <= 0 or L > 6000 or i + 4 + L > n:
            i += 1
            continue
        chunk = raw[i + 4:i + 4 + L]
        try:
            t = chunk.decode("utf-8")
        except UnicodeDecodeError:
            i += 1
            continue
        if all((c >= " " or c in "\n\t\r") for c in t):
            out.append((i, (4 + L + 3) & ~3, t))
            i += (4 + L + 3) & ~3
        else:
            i += 1
    return out


def usable(t):
    if len(t) < 8:
        return False
    if t in SKIP_TOKENS:
        return False
    if t.startswith("Script_") or t.startswith("@"):
        return False
    if t.count(".") and all(ch.isalnum() or ch in "._" for ch in t):
        return False
    return any(ch.isalpha() for ch in t)


def main(words):
    loc = json.load(open(os.path.join(HERE, "missing_locations2.json"), encoding="utf-8"))
    trans = json.load(open(os.path.join(HERE, "translations_complete.json"), encoding="utf-8"))
    by_pid = {}
    for w in words:
        for pid, off, rsz in loc.get(w, []):
            by_pid.setdefault(pid, []).append((off, w))

    env = Environment(BASE)
    for obj in env.objects:
        pid = obj.path_id
        if pid not in by_pid:
            continue
        raw = obj.get_raw_data()
        slots = scan_slots(raw)
        idx = {s[0]: k for k, s in enumerate(slots)}
        for off, w in sorted(by_pid[pid]):
            k = idx.get(off)
            if k is None:
                continue
            before = []
            j = k - 1
            while j >= 0 and len(before) < 2:
                if usable(slots[j][2]):
                    before.insert(0, slots[j][2][:120])
                j -= 1
            after = []
            j = k + 1
            while j < len(slots) and len(after) < 2:
                if usable(slots[j][2]):
                    after.append(slots[j][2][:120])
                j += 1
            print("\n=== %r  pid=%s  译文=%r ===" % (w, pid, trans.get(w, "")))
            for b in before:
                print("   ... %s" % b)
            print("   >>> %s" % w)
            for a in after:
                print("   ... %s" % a)


if __name__ == "__main__":
    main(sys.argv[1:])
