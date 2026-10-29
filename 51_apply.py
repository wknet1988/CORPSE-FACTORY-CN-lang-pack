#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Zip a plain-text Chinese translation file (one line per string, same order)
with batch_NNN.json and emit translations_batchNNN.json.

usage: python 51_apply.py 009
"""
import json, re, sys, os

W = os.path.dirname(os.path.abspath(__file__))
TAG = re.compile(r"</?(?:color(?:=[^>]*)?|b|i|size(?:=[^>]*)?|u)>", re.I)

def main(num):
    src = os.path.join(W, "batch_%s.json" % num)
    txt = os.path.join(W, "cn_batch%s.txt" % num)
    en = json.load(open(src, encoding="utf-8"))
    lines = [l.rstrip("\n") for l in open(txt, encoding="utf-8") if l.strip()]
    if len(lines) != len(en):
        print("!! count mismatch: %d lines vs %d strings" % (len(lines), len(en)))
        for i in range(min(len(lines), len(en))):
            pass
        return 1
    out, issues = {}, []
    for i, (e, c) in enumerate(zip(en, lines)):
        if sorted(TAG.findall(e)) != sorted(TAG.findall(c)):
            issues.append((i, "tag", e, c))
        if not re.search(r"[\u4e00-\u9fff]", c):
            issues.append((i, "no-cjk", e, c))
        out[e] = c
    dst = os.path.join(W, "translations_batch%s.json" % num)
    json.dump(out, open(dst, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print("wrote %s : %d entries" % (os.path.basename(dst), len(out)))
    for i, why, e, c in issues[:15]:
        print("  [%s] #%d  %r -> %r" % (why, i, e[:70], c[:40]))
    print("issues:", len(issues))
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
