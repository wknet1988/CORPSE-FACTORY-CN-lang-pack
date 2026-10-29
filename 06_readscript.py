import os, json, UnityPy
from UnityPy.helpers import TypeTreeGenerator

GEN = TypeTreeGenerator.TypeTreeGenerator("2020.3.0f1")

DATA = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY/CORPSE FACTORY_Data"
env = UnityPy.load(os.path.join(DATA, "resources.assets"))

cache = {}
def get_tree(obj):
    sc = obj.script  # MonoScript object
    asm = sc.m_AssemblyName
    ns = sc.m_Namespace or ""
    cls = sc.m_ClassName
    full = (ns + "." + cls) if ns else cls
    key = (asm, full)
    if key not in cache:
        try:
            cache[key] = GEN.get_nodes_up(asm, full)
        except Exception as e:
            return None
    return cache[key]

count = 0
for obj in env.objects:
    if obj.type.name != "MonoBehaviour":
        continue
    tree = obj.serialized_type.nodes
    if tree:
        continue
    name = None
    try:
        t = get_tree(obj)
        if t is None:
            continue
        obj.serialized_type.nodes = t
        data = obj.read_typetree()
        # find name
        name = data.get("m_Name")
        if name in ("Script_Act_00", "Credits", "MainScript"):
            print("NAME", name, "keys:", list(data.keys())[:20])
            print(json.dumps(data, ensure_ascii=False)[:1500])
            count += 1
            if count >= 3:
                break
    except Exception as e:
        print("ERR", repr(e))
        continue
