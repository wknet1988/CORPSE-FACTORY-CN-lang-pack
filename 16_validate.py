import os, struct, shutil, UnityPy

SRC = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY/CORPSE FACTORY_Data/resources.assets"
TMP = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY/_cnwork/test_resources.assets"
shutil.copy(SRC, TMP)
orig_size = os.path.getsize(TMP)
print("orig size", orig_size)

env = UnityPy.load(TMP)

# Cache ALL objects' raw data so save() preserves them
for obj in env.objects:
    _ = obj.get_raw_data()

# find target string
needle = b"Start rain over 2 seconds"
target_obj = None
target_off = None
target_old_span = None
for obj in env.objects:
    if obj.type.name != "MonoBehaviour": continue
    raw = obj.get_raw_data()
    idx = raw.find(needle)
    if idx < 0: continue
    ln = struct.unpack_from("<i", raw, idx-4)[0]
    target_obj = obj
    target_off = idx - 4
    target_old_span = (4 + ln + 3) & ~3
    break

assert target_obj is not None
cn = "测试雨持续两秒".encode("utf-8")
new_span = struct.pack("<i", len(cn)) + cn
new_span += b"\x00" * (((4+len(cn)+3)&~3) - (4+len(cn)))
raw = target_obj.get_raw_data()
new_raw = raw[:target_off] + new_span + raw[target_off+target_old_span:]
target_obj.set_raw_data(new_raw)
print("raw", len(raw), "->", len(new_raw), "old span", target_old_span, "new span", len(new_span))

env.save(out_path=r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY/_cnwork")
new_size = os.path.getsize(TMP)
print("saved size", new_size, "(orig", orig_size, ")")
assert abs(new_size - (orig_size - (target_old_span - len(new_span)))) <= 4, "size delta unexpected"

# verify
data = open(TMP, "rb").read()
cn_full = b"\xe6\xb5\x8b\xe9\x9b\xa8\xe6\x8c\x81\xe7\xbb\xad\xe4\xb8\xa4\xe7\xa7\x92"
print("CN present:", cn_full in data, "| old present:", needle in data)
assert cn_full in data and needle not in data
print("VALIDATE OK")
