import os, struct, UnityPy
from UnityPy.helpers import TypeTreeGenerator

GEN = TypeTreeGenerator.TypeTreeGenerator("2020.3.0f1", "AssetStudio")
GEN.load_local_dll_folder(r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY/CORPSE FACTORY_Data/Managed")
tree = GEN.get_nodes_up("Elringus.Naninovel.Runtime.dll", "Naninovel.Script")

DATA = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY/CORPSE FACTORY_Data"
env = UnityPy.load(os.path.join(DATA, "resources.assets"))

def rd_name(b):
    n = struct.unpack_from("<i", b, 28)[0]
    return b[32:32+n].decode("utf-8", "replace")

target = "Script_Act_00"
for obj in env.objects:
    if obj.type.name != "MonoBehaviour":
        continue
    raw = obj.get_raw_data()
    if len(raw) < 32:
        continue
    name = rd_name(raw)
    if name != target:
        continue
    try:
        d = obj.read_typetree(nodes=[tree])
    except Exception as e:
        print("read err", e); continue
    print("keys:", list(d.keys()))
    lines = d.get("lines", [])
    print("num lines:", len(lines))
    # inspect first line structure & types
    for i, ln in enumerate(lines[:12]):
        print(i, type(ln), ln if not isinstance(ln, dict) else {k: (type(v).__name__, (v[:40] if isinstance(v,(str,list)) else v)) for k,v in ln.items()})
    # show text field of first few
    break
