import os, struct, collections
import UnityPy

DATA = r"G:/SteamLibrary/steamapps/common/CORPSE FACTORY/CORPSE FACTORY_Data"
env = UnityPy.load(os.path.join(DATA, "resources.assets"))

def rd_str(b, off):
    n = struct.unpack_from("<i", b, off)[0]
    if n < 0 or off + 4 + n > len(b):
        return None, off + 4
    s = b[off + 4: off + 4 + n]
    end = (off + 4 + n + 3) & ~3
    return s, end

def scan(off, b):
    """dump candidate strings from a MonoBehaviour blob"""
    out = []
    p = off
    while p + 4 <= len(b):
        s, np = rd_str(b, p)
        if s is None or np <= p:
            p += 4
            continue
        out.append((p, s))
        p = np
    return out

found = collections.Counter()
samples = []
n = 0
for obj in env.objects:
    if obj.type.name != "MonoBehaviour":
        continue
    n += 1
    if n > 400:
        break
    try:
        b = obj.get_raw_data()
    except Exception as e:
        continue
    if len(b) < 40:
        continue
    name, p = rd_str(b, 28)
    if name is None:
        continue
    try:
        nm = name.decode("utf-8")
    except Exception:
        continue
    if not nm or not nm.isprintable():
        continue
    found[nm[:40]] += 1
    if len(samples) < 25:
        rest = scan(p, b)
        samples.append((nm, len(b), [(o, s[:60]) for o, s in rest[:4]]))

for k, v in found.most_common(60):
    print(f"{v:4d} {k!r}")

print("\n=== samples ===")
for nm, l, rest in samples:
    print(f"--- name={nm!r} len={l}")
    for o, s in rest:
        print(f"     @{o}: {s!r}")
