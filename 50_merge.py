#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Merge every translations_*.json into translations_full.json and report coverage.

Also validates each translated pair:
  * inline rich-text tags (<color=...>, </color>, <b>, </b>, <i>, </i>, <size=...>) must match
  * translation must not be empty
  * translation must still contain Chinese characters
"""
import json, glob, re, sys, os

W = os.path.dirname(os.path.abspath(__file__))
TODO = os.path.join(W, "todo_list.json")
FULL = os.path.join(W, "translations_full.json")

TAG = re.compile(r"</?(?:color(?:=[^>]*)?|b|i|size(?:=[^>]*)?|u)>", re.I)
CJK = re.compile(r"[\u4e00-\u9fff]")

def tag_sig(s):
    return sorted(TAG.findall(s))

def main():
    todo = json.load(open(TODO, encoding="utf-8"))
    toset = set(todo)
    merged = {}
    bad = []
    sources = ["translations_act00b.json"] + sorted(
        os.path.basename(p) for p in glob.glob(os.path.join(W, "translations_batch*.json"))
    )
    for name in sources:
        p = os.path.join(W, name)
        if not os.path.exists(p):
            continue
        d = json.load(open(p, encoding="utf-8"))
        n0 = len(merged)
        for k, v in d.items():
            if not isinstance(v, str) or not v.strip():
                continue
            if tag_sig(k) != tag_sig(v):
                bad.append((name, k, v, "tag-mismatch"))
                continue
            if not CJK.search(v) and re.search(r"[A-Za-z]{3,}", k):
                bad.append((name, k, v, "no-cjk"))
            merged[k] = v
        print(f"{name:28s} {len(d):5d} entries -> +{len(merged)-n0}")

    # keep only keys that actually exist in the game
    extra = [k for k in merged if k not in toset]
    for k in extra:
        merged.pop(k, None)

    json.dump(merged, open(FULL, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    cov = len(merged)
    print(f"\nmerged usable: {cov}/{len(todo)} ({cov*100/len(todo):.1f}%)  dropped-not-in-game: {len(extra)}")
    if bad:
        print(f"\nvalidation issues: {len(bad)}")
        for name, k, v, why in bad[:20]:
            print(f"  [{why}] {name}: {k[:70]!r} -> {v[:50]!r}")
    # remaining batches
    for i in range(1, 37):
        p = os.path.join(W, "batch_%03d.json" % i)
        if not os.path.exists(p):
            continue
        b = json.load(open(p, encoding="utf-8"))
        done = sum(1 for x in b if x in merged)
        if done < len(b):
            print(f"batch_{i:03d}: {done}/{len(b)}  <-- incomplete")

if __name__ == "__main__":
    main()
