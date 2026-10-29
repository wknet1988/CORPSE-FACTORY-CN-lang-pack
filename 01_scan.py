import os, sys, collections
import UnityPy

DATA = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY/CORPSE FACTORY_Data"
target = os.path.join(DATA, "resources.assets")

env = UnityPy.load(target)
print("files:", list(env.files.keys()))
cnt = collections.Counter()
for obj in env.objects:
    cnt[obj.type.name] += 1
for k, v in cnt.most_common():
    print(f"{k:20s} {v}")

print("\n=== TextAsset ===")
for obj in env.objects:
    if obj.type.name == "TextAsset":
        try:
            d = obj.read()
            name = getattr(d, "m_Name", None) or getattr(d, "name", "?")
            raw = d.raw_data if hasattr(d, "raw_data") else b""
            script = getattr(d, "m_Script", None)
            print(f"{name!r:60s} class={obj.type.name} len={len(raw) if raw else len(script or '')}")
        except Exception as e:
            print("ERR", obj.path_id, e)
