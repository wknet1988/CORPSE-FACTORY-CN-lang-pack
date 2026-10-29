import os, struct, UnityPy

DATA = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY/CORPSE FACTORY_Data"
env = UnityPy.load(os.path.join(DATA, "resources.assets"))

def rd_name(b):
    n = struct.unpack_from("<i", b, 28)[0]
    return b[32:32+n].decode("utf-8","replace")

for obj in env.objects:
    if obj.type.name != "MonoBehaviour": continue
    raw = obj.get_raw_data()
    if len(raw) < 32: continue
    if rd_name(raw) != "Script_Act_00": continue
    b = raw
    # find first '@back' style text occurrence
    idx = b.find(b"@back")
    print("found @back at", idx)
    # dump 120 bytes before
    start = max(0, idx-120)
    print("hex before text:")
    for off in range(start, idx+60, 16):
        chunk = b[off:off+16]
        print(f"{off:8d}  " + " ".join(f"{c:02x}" for c in chunk) + "  " + "".join(chr(c) if 32<=c<127 else "." for c in chunk))
    break
