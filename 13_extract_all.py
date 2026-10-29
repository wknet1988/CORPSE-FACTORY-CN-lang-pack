import os, struct, json, re, UnityPy

DATA = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY/CORPSE FACTORY_Data"
env = UnityPy.load(os.path.join(DATA, "resources.assets"))

def rd_str(b, off):
    if off + 4 > len(b):
        return None, off + 4
    n = struct.unpack_from("<i", b, off)[0]
    if n < 0 or off + 4 + n > len(b):
        return None, off + 4
    s = b[off + 4: off + 4 + n]
    end = (off + 4 + n + 3) & ~3
    return s, end

def rd_i32(b, off):
    return struct.unpack_from("<i", b, off)[0], off + 4

def looks_script(b):
    if len(b) < 40:
        return -1
    n = struct.unpack_from("<i", b, 28)[0]
    if n <= 0 or 28 + 4 + n > len(b):
        return -1
    # name starts at 32
    # count int at offset (32+n) aligned
    name_end = 32 + n
    cnt_off = (name_end + 3) & ~3
    if cnt_off + 4 > len(b):
        return -1
    cnt = struct.unpack_from("<i", b, cnt_off)[0]
    if cnt <= 0 or cnt > 200000:
        return -1
    # check next cnt*4 bytes are 0,1,2,... ascending
    p = cnt_off + 4
    if p + cnt * 4 > len(b):
        return -1
    for i in range(min(cnt, 30)):
        v = struct.unpack_from("<i", b, p + i * 4)[0]
        if v != i:
            return -1
    return cnt_off  # where count lives

def parse_script(name, b):
    cnt_off = looks_script(b)
    cnt = struct.unpack_from("<i", b, cnt_off)[0]
    p = cnt_off + 4 + cnt * 4  # skip lineIndex array
    lines = []
    for li in range(cnt):
        rid, p = rd_i32(b, p)
        cls, p = rd_str(b, p)
        if cls is None:
            break
        ns, p = rd_str(b, p)
        asm, p = rd_str(b, p)
        flags, p = rd_i32(b, p)
        linehash, p = rd_str(b, p)
        if cls is None:
            break
        cls = cls.decode("utf-8", "replace")
        linehash = linehash.decode("utf-8", "replace") if linehash else ""
        # body
        body = {"className": cls}
        if cls == "CommandScriptLine":
            crid, p = rd_i32(b, p)
            ccls, p = rd_str(b, p)
            cns, p = rd_str(b, p)
            casm, p = rd_str(b, p)
            cflags, p = rd_i32(b, p)
            cid, p = rd_str(b, p)
            body["cmd"] = ccls.decode("utf-8","replace") if ccls else ""
            # gather remaining strings in this element until next element (RID pattern)
            # We'll just collect all subsequent length-prefixed strings until we hit next element start.
            # Heuristic: next element starts with an int32 RID that is NOT a plausible string length (>= some small) 
            # Instead, scan strings until alignment with next "className" marker. Too complex; just capture until next rid.
        lines.append((li, rid, cls, linehash, body))
    return lines

scripts = {}
for obj in env.objects:
    if obj.type.name != "MonoBehaviour":
        continue
    raw = obj.get_raw_data()
    c = looks_script(raw)
    if c < 0:
        continue
    nn = struct.unpack_from("<i", raw, 28)[0]
    name = raw[32:32+nn].decode("utf-8","replace")
    lines = parse_script(name, raw)
    scripts[name] = (obj.path_id, len(raw), lines)
    print(f"{name:24s} path_id={obj.path_id} bytes={len(raw)} lines={len(lines)}")

print("TOTAL scripts:", len(scripts))
json.dump({k: {"path_id": v[0], "bytes": v[1], "linecount": len(v[2])} for k,v in scripts.items()},
          open(r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY/_cnwork/scripts_index.json","w"), ensure_ascii=False, indent=1)
