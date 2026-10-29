import os, struct
import UnityPy

DATA = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY/CORPSE FACTORY_Data"
env = UnityPy.load(os.path.join(DATA, "resources.assets"))

def rd_str(b, off):
    n = struct.unpack_from("<i", b, off)[0]
    if n < 0 or off + 4 + n > len(b):
        return None, off + 4
    return b[off + 4: off + 4 + n], (off + 4 + n + 3) & ~3

for obj in env.objects:
    if obj.type.name != "MonoBehaviour":
        continue
    b = obj.get_raw_data()
    if len(b) < 32:
        continue
    name, p = rd_str(b, 28)
    if name is None:
        continue
    try:
        nm = name.decode("utf-8")
    except Exception:
        continue
    if nm not in ("Credits", "ShowPauseUI_2", "Script_Act_00"):
        continue
    print("=" * 70)
    print("path_id", obj.path_id, "bytesize", obj.byte_size, "name", nm)
    print("header:", b[:min(p, 64)].hex(" "))
    tail = b[p:p + 400]
    print("after name @", p, ":", tail[:200].hex(" "))
    print("as text:", tail[:200])
    # find first printable-ish region
    import re
    m = None
    for mm in re.finditer(rb"[ -~\n]{40,}", b[p:]):
        m = mm
        break
    if m:
        print("FIRST TEXT @", p + m.start(), ":", b[p + m.start(): p + m.start() + 600])
