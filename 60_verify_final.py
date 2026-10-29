# -*- coding: utf-8 -*-
"""终局校验：已部署 resources.assets vs translations_full.json vs 原版备份
用法: <UnityPy解释器> 60_verify_final.py
"""
import io, json, os, re, sys, random
import UnityPy

BASE = os.path.dirname(os.path.abspath(__file__))
GAME = os.path.dirname(BASE)
DEPLOY = os.path.join(GAME, "CORPSE FACTORY_Data", "resources.assets")
ORIG = os.path.join(GAME, "CORPSE FACTORY_Data", "backup_original", "resources.assets")
FULL = os.path.join(BASE, "translations_full.json")

CJK = re.compile(r"[\u4e00-\u9fff]")
TAG = re.compile(r"</?(?:color(?:=[^>]*)?|b|i|size(?:=[^>]*)?|u)>", re.I)
# 常见英文单词（用于残留检测，排除专名/缩写）
EN_WORD = re.compile(r"\b(?:the|and|you|your|that|this|with|have|from|what|was|were|are|his|her|she|they|not|but|for|all|just|like|know|can|will|would|about|there|their|been|when|then|them|than|into|out|get|got|him|how|now|one|two|only|some|more|very|said|did|does|here|why|who|because|before|after|should|could|think|want|need|going|make|take|see|come|back|down|over|again|never|always|something|nothing|everything|anyone|someone)\b", re.I)
# 繁体字（高频简繁差异字，仅作误用抽查）
TRAD = set("屍體們這個來說時會發現實對開關問題點數學國語話語錄後從裡邊處麼樣東頭條經過應該還將於與為並讓給帶給們個")


def load(path):
    env = UnityPy.load(path)
    return env


def get_scripts(env):
    out = []
    for obj in env.objects:
        if obj.type.name != "MonoBehaviour":
            continue
        try:
            d = obj.read()
            name = getattr(d, "m_Name", "") or ""
        except Exception:
            continue
        if "Script" in str(getattr(obj, "type", "")):
            pass
        out.append((obj, d, name))
    return out


def main():
    trans = json.load(open(FULL, encoding="utf-8"))
    print("translations_full.json entries: %d" % len(trans))

    # 只取真正的中文译文（有 CJK 的）
    zh = {k: v for k, v in trans.items() if CJK.search(v or "")}
    print("entries containing CJK: %d" % len(zh))

    # ---------- 已部署文件 ----------
    env = load(DEPLOY)
    n_obj = len(env.objects)
    print("\n[DEPLOY] %s" % DEPLOY)
    print("  size: %d bytes" % os.path.getsize(DEPLOY))
    print("  objects: %d  %s" % (n_obj, "OK" if n_obj == 11600 else "<-- MISMATCH (expect 11600)"))

    raw_blob = b""
    script_objs = 0
    for obj in env.objects:
        if obj.type.name != "MonoBehaviour":
            continue
        try:
            data = obj.get_raw_data()
        except Exception:
            continue
        if b"Naninovel" in data or b"m_Script" in data:
            pass
        raw_blob += data
        script_objs += 1

    # 按对象粒度找 Naninovel Script
    naninovel = []
    for obj in env.objects:
        if obj.type.name != "MonoBehaviour":
            continue
        try:
            d = obj.read()
        except Exception:
            continue
        if d.__class__.__name__ == "Script":
            naninovel.append(d)
    print("  Naninovel.Script objects: %d" % len(naninovel))

    # 直接对整份二进制做抽样命中检测（最可靠）
    blob = open(DEPLOY, "rb").read()
    print("  file read: %d bytes" % len(blob))

    # ---------- 抽样命中 ----------
    keys = list(zh.keys())
    random.seed(20261029)
    sample = random.sample(keys, min(80, len(keys)))
    hit = miss = 0
    miss_samples = []
    for k in sample:
        v = zh[k]
        if v.encode("utf-8") in blob:
            hit += 1
        else:
            miss += 1
            if len(miss_samples) < 5:
                miss_samples.append((k[:50], v[:50]))
    print("\n[SAMPLE] %d/%d hit  (miss %d)" % (hit, len(sample), miss))
    for a, b in miss_samples:
        print("   MISS en=%r zh=%r" % (a, b))

    # ---------- 全量命中（较慢但彻底） ----------
    print("\n[FULL SWEEP] checking all %d entries..." % len(zh))
    full_hit = 0
    full_miss = []
    for k, v in zh.items():
        if v.encode("utf-8") in blob:
            full_hit += 1
        else:
            full_miss.append((k, v))
    print("  hit %d / %d  (%.2f%%)" % (full_hit, len(zh), 100.0 * full_hit / max(1, len(zh))))
    if full_miss:
        print("  missing %d entries:" % len(full_miss))
        for k, v in full_miss[:20]:
            print("    en=%r" % k[:70])
            print("    zh=%r" % v[:70])

    # ---------- 英文残留 ----------
    # 在 Naninovel.Script 的文本里找未被替换的英文叙述
    print("\n[RESIDUE] scanning Naninovel scripts for untranslated English prose...")
    residue = []
    for d in naninovel:
        try:
            raw = d.get_raw_data()
        except Exception:
            continue
        text = raw.decode("utf-8", "ignore")
        # 提取形如普通句子的英文段
        for m in re.finditer(r"[A-Za-z][A-Za-z ,.'\"!?;:\-]{40,}", text):
            seg = m.group(0).strip()
            words = EN_WORD.findall(seg)
            if len(words) >= 5:
                residue.append(seg[:90])
    residue = list(dict.fromkeys(residue))
    print("  suspicious English runs: %d" % len(residue))
    for r in residue[:12]:
        print("    %r" % r)

    # ---------- 繁体误用 ----------
    print("\n[TRAD] scanning deployed text for traditional-only chars...")
    bad = {}
    for d in naninovel:
        try:
            raw = d.get_raw_data()
        except Exception:
            continue
        text = raw.decode("utf-8", "ignore")
        for ch in text:
            if ch in TRAD:
                bad[ch] = bad.get(ch, 0) + 1
    print("  traditional hits: %s" % (bad if bad else "none"))

    # ---------- 与原版差异 ----------
    print("\n[DIFF vs ORIGINAL]")
    env_o = load(ORIG)
    print("  original objects: %d" % len(env_o.objects))
    diff = 0
    diff_names = []
    for a, b in zip(env.objects, env_o.objects):
        try:
            ra = a.get_raw_data()
            rb = b.get_raw_data()
        except Exception:
            continue
        if ra != rb:
            diff += 1
            if len(diff_names) < 25:
                try:
                    diff_names.append("%s/%s" % (a.type.name, getattr(a.read(), "m_Name", "")))
                except Exception:
                    diff_names.append(a.type.name)
    print("  objects differing: %d" % diff)
    for n in diff_names:
        print("    %s" % n)

    # ---------- 字体 ----------
    print("\n[FONT]")
    for obj in env.objects:
        if obj.type.name != "MonoBehaviour":
            continue
        try:
            d = obj.read()
        except Exception:
            continue
        if d.__class__.__name__ == "Font":
            fd = getattr(d, "m_FontData", b"") or b""
            if len(fd) > 10000:
                print("  font '%s' data: %d bytes" % (getattr(d, "m_Name", "?"), len(fd)))
                try:
                    from fontTools.ttLib import TTFont
                    f = TTFont(io.BytesIO(fd))
                    cmap = set()
                    for t in f["cmap"].tables:
                        cmap |= set(t.cmap.keys())
                    print("  glyph cmap size: %d" % len(cmap))
                    need = set()
                    for v in zh.values():
                        for ch in v:
                            if ord(ch) > 127:
                                need.add(ord(ch))
                    missing = sorted(need - cmap)
                    print("  non-ascii used: %d | missing from font: %d" % (len(need), len(missing)))
                    if missing:
                        print("  missing codepoints: %s" % ", ".join("U+%04X" % c for c in missing[:20]))
                except Exception as e:
                    print("  font parse error: %s" % e)


if __name__ == "__main__":
    main()
