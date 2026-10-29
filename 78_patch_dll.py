#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Patch Naninovel engine confirmation-message strings inside Elringus.Naninovel.Runtime.dll
so the save/load/title prompts show Chinese.

These strings are NOT in resources.assets; they are UTF-16LE literals in the DLL's
#US (user string) heap. We replace them IN PLACE, keeping the exact same character
count (each UTF-16 char = 2 bytes for both ASCII and BMP Chinese), padding the rest
with spaces. Because the byte length is identical, the length prefix and all metadata
offsets stay valid -> the assembly remains loadable.

IMPORTANT (learned the hard way): only translate the three *display* confirmation
messages below. DO NOT translate the button labels "Cancel"/"Delete"/"Continue" -- they
also appear inside an input/navigation identifier list ("Submit.Cancel.Delete.Continue")
that the engine uses to map keyboard/gamepad input to UI actions. Changing those breaks
button input ("buttons don't respond"). Likewise never touch any string that looks like
an identifier/enumeration/list of action names.

We always read from the pristine backup and re-apply all replacements in one pass, so
the result is deterministic regardless of any prior partial patch.
"""
import os, shutil, sys

DLL = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY/CORPSE FACTORY_Data/Managed/Elringus.Naninovel.Runtime.dll"
BAK = DLL + ".bak_patch"

# (full_original_string, chinese_replacement_padded_to_same_length)
# Each replacement keeps the SAME number of UTF-16 chars; remainder padded with spaces.
# ONLY the 3 confirmation MESSAGES (pure display text). Button labels are intentionally
# left untouched (they double as input-action identifiers).
TARGETS = [
    ("Are you sure you want to overwrite save slot?",
     "确定要覆盖这个存档吗？"),                       # 11 -> pad to 45
    ("Are you sure you want to delete save slot?",
     "确定要删除这个存档吗？"),                        # 11 -> pad to 42
    ("Are you sure you want to quit to the title screen?\nAny unsaved game progress will be lost.",
     "确定要返回主菜单吗？\n未保存的进度将丢失。"), # 22 -> pad to 90
]

def pad_to(s, n):
    if len(s) > n:
        raise ValueError("chinese too long: %r (%d > %d)" % (s, len(s), n))
    return s + " " * (n - len(s))

def main():
    if not os.path.exists(BAK):
        print("backup missing:", BAK); sys.exit(1)
    data = bytearray(open(BAK, "rb").read())   # always start from pristine backup
    report = []
    for en, zh in TARGETS:
        n = len(en)
        zh_padded = pad_to(zh, n)
        enb = en.encode("utf-16-le")
        zb = zh_padded.encode("utf-16-le")
        assert len(zb) == len(enb), (len(zb), len(enb))
        cnt = data.count(enb)
        if cnt == 0:
            report.append("SKIP  %r: not found" % en)
            continue
        data = data.replace(enb, zb)
        report.append("PATCH %dx %r -> %r (len %d)" % (cnt, en, zh_padded, n))
    open(DLL, "wb").write(data)
    print("\n".join(report))
    print("written DLL size:", len(data), "(backup size:", os.path.getsize(BAK), ")")

if __name__ == "__main__":
    main()
