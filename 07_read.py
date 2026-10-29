import os, struct, json, UnityPy
from UnityPy.helpers import TypeTreeGenerator

GEN = TypeTreeGenerator.TypeTreeGenerator("2020.3.0f1")
DATA = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY/CORPSE FACTORY_Data"
env = UnityPy.load(os.path.join(DATA, "resources.assets"))

# 1) gather MonoScript classes
mono_tree = GEN.get_nodes_up("UnityEngine.CoreModule.dll", "UnityEngine.MonoScript")
print("MonoScript tree nodes:", len(mono_tree))

script_class = {}  # path_id -> (assembly, fullclass)
for obj in env.objects:
    if obj.type.name != "MonoScript":
        continue
    try:
        obj.serialized_type.nodes = mono_tree
        d = obj.read_typetree()
        asm = d.get("m_AssemblyName") or d.get("m_AssemblyNameRaw") or ""
        ns = d.get("m_Namespace") or ""
        cls = d.get("m_ClassName") or ""
        full = (ns + "." + cls) if ns else cls
        script_class[obj.path_id] = (asm, full)
    except Exception as e:
        pass
print("MonoScripts read:", len(script_class))

tree_cache = {}
def tree_for(asm, full):
    k = (asm, full)
    if k not in tree_cache:
        tree_cache[k] = GEN.get_nodes_up(asm, full)
    return tree_cache[k]

def mb_name(path_id):
    return script_class.get(path_id)

# 2) read MonoBehaviours, focusing on Naninovel.Script
seen = 0
for obj in env.objects:
    if obj.type.name != "MonoBehaviour":
        continue
    raw = obj.get_raw_data()
    # m_Script PPtr at offset 16 (fileID int32) / 20 (pathID int64)
    script_pid = struct.unpack_from("<q", raw, 20)[0]
    info = mb_name(script_pid)
    if info is None:
        continue
    asm, full = info
    if full != "Naninovel.Script":
        continue
    try:
        obj.serialized_type.nodes = tree_for(asm, full)
        d = obj.read_typetree()
    except Exception as e:
        print("read err", obj.path_id, e)
        continue
    print("=== Naninovel.Script path_id", obj.path_id, "name", d.get("m_Name"))
    keys = list(d.keys())
    print("top keys:", [k for k in keys if k != "m_Script"])
    # Try to find the Text/lines
    for k in keys:
        v = d[k]
        if isinstance(v, str) and len(v) > 40:
            print(f"  [{k}] str len={len(v)}: {v[:200]!r}")
        if isinstance(v, list) and len(v) > 3:
            print(f"  [{k}] list len={len(v)} first item type={type(v[0]).__name__}")
            if isinstance(v[0], dict):
                print("    item keys:", list(v[0].keys())[:20])
    seen += 1
    if seen >= 2:
        break
