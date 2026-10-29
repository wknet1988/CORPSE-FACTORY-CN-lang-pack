import os, collections
import UnityPy

DATA = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY/CORPSE FACTORY_Data"
env = UnityPy.load(os.path.join(DATA, "resources.assets"))

# Unity version
for f in env.files.values():
    print("unity version:", getattr(f, "version", None))
    print("typetree in file:", getattr(f, "typetree", None) is not None)

cnt = collections.Counter()
samples = {}
for obj in env.objects:
    if obj.type.name != "MonoBehaviour":
        continue
    st = obj.serialized_type
    nodes = getattr(st, "nodes", None)
    key = "?"
    if nodes:
        # first node is class name
        key = getattr(nodes[0], "m_Name", "?") if hasattr(nodes[0], "m_Name") else str(nodes[0])
    else:
        try:
            scr = obj.read_typetree() and None
        except Exception:
            pass
        key = "NO_TYPETREE"
    cnt[key] += 1
    samples.setdefault(key, obj.path_id)

for k, v in cnt.most_common(40):
    print(f"{v:6d}  {k}")
