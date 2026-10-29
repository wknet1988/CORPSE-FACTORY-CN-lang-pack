import os, json, UnityPy
from UnityPy.helpers import TypeTreeGenerator

GEN = TypeTreeGenerator.TypeTreeGenerator("2020.3.0f1")
GEN.load_local_dll_folder(r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY/CORPSE FACTORY_Data/Managed")

# generate nodes for Naninovel.Script
try:
    nodes = GEN.get_nodes("Elringus.Naninovel.Runtime", "Naninovel.Script")
    GEN.fill_serialized_type(nodes)
    print(json.dumps(nodes, ensure_ascii=False, indent=1)[:4000])
except Exception as e:
    print("Script err:", repr(e))
    try:
        n = GEN.get_nodes_up("Elringus.Naninovel.Runtime", "Naninovel.Script")
        print(json.dumps(n, ensure_ascii=False, indent=1)[:4000])
    except Exception as e2:
        print("err2", e2)
