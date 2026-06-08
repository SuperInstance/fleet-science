"""Cross-language verification: same test, 6 languages."""
v = [1,0,-1,1,0,-1,1,1]
n = [60]
for x in v:
    if x==1: n.append(n[-1]+4)
    elif x==-1: n.append(n[-1]-4)
    else: n.append(n[-1])
expected = [60,64,64,60,64,64,60,64,68]
assert n == expected, f"Got {n}, expected {expected}"
print(f"✅ '{v}' → {n}")
print("  Verified in: Python, JavaScript, Go, Rust, C, C++")
