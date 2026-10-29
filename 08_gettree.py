import os, struct, UnityPy
from UnityPy.helpers import TypeTreeGenerator

GEN = TypeTreeGenerator.TypeTreeGenerator("2020.3.0f1", "AssetStudio")
GEN.load_local_dll_folder(r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY/CORPSE FACTORY_Data/Managed")
tree = GEN.get_nodes("Elringus.Naninovel.Runtime.dll", "Naninovel.Script")
print("num nodes:", len(tree))
def walk(nodes, depth=0):
    for n in nodes:
        print("  " * depth + f"{n.m_Type} {n.m_Name} lvl={n.m_Level}")
        if hasattr(n, "children"):
            walk(n.children, depth + 1)
# try native children attr
for n in tree:
    print("NODE", n.m_Type, n.m_Name, n.m_Level, "children?", hasattr(n, "children"))
