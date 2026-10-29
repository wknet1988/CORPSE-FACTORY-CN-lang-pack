# -*- coding: utf-8 -*-
"""检查部署文件是否仍依赖外部 resources.assets.resS（流式资源）"""
import os
import UnityPy

GAME = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY"
DEPLOY = os.path.join(GAME, "CORPSE FACTORY_Data", "resources.assets")
ORIG = os.path.join(GAME, "CORPSE FACTORY_Data", "backup_original", "resources.assets")

def scan(path, label):
    print("=== %s ===" % label)
    print("  size: %d" % os.path.getsize(path))
    env = UnityPy.load(path)
    ext = 0
    stream_objs = 0
    stream_bytes = 0
    samples = []
    for obj in env.objects:
        try:
            tree = obj.read_typetree()
        except Exception:
            continue
        if not isinstance(tree, dict):
            continue
        sd = tree.get("m_StreamData")
        if isinstance(sd, dict):
            p = sd.get("path") or ""
            size = sd.get("size") or 0
            if p:
                stream_objs += 1
                stream_bytes += size
                if len(samples) < 6:
                    samples.append((obj.type.name, obj.path_id, p, size))
        if "m_ExternalResources" in tree:
            ext += 1
    print("  objects with m_StreamData.path: %d" % stream_objs)
    print("  total streamed bytes referenced: %d (%.2f MB)" % (stream_bytes, stream_bytes / 1048576.0))
    print("  objects with m_ExternalResources: %d" % ext)
    for s in samples:
        print("    %s pid=%s path=%r size=%d" % s)
    return stream_objs, stream_bytes

a = scan(ORIG, "ORIGINAL")
print()
b = scan(DEPLOY, "DEPLOYED")

print("\n=== CONCLUSION ===")
if b[0] > 0:
    print("部署文件仍引用外部流式资源 %d 个（约 %.1f MB）" % (b[0], b[1] / 1048576.0))
    print("=> .resS 仍然必需，**不能**重命名为 .bak，否则音频/纹理丢失。")
else:
    print("部署文件无外部流式引用，.resS 可安全移除。")
