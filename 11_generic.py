import os, struct, UnityPy

DATA = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY/CORPSE FACTORY_Data"
env = UnityPy.load(os.path.join(DATA, "resources.assets"))

def rd_name(b):
    n = struct.unpack_from("<i", b, 28)[0]
    return b[32:32+n].decode("utf-8","replace")

for obj in env.objects:
    if obj.type.name != "MonoBehaviour": continue
    raw = obj.get_raw_data()
    if len(raw) < 32 or rd_name(raw) != "Script_Act_00": continue
    b = raw
    pos = b.find(b"GenericScriptLine")
    print("GenericScriptLine at", pos)
    start = max(0, pos-200)
    for off in range(start, pos+360, 16):
        chunk = b[off:off+16]
        print(f"{off:8d}  " + " ".join(f"{c:02x}" for c in chunk) + "  " + "".join(chr(c) if 32<=c<127 else "." for c in chunk))
    break
