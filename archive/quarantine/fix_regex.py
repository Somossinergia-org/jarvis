import pathlib, sys, re

h = pathlib.Path("static/index.html").read_text(encoding="utf-8")

# The broken regex is: /.*[/\]/ inside a .replace() call
# This is invalid because / inside [] is fine but \ before ] is wrong without escape

# Find and fix the specific bad line in enterFSMode3D
bad = "const shortPath = data.path.replace(/.*[/\\]/, '') || data.path;"
good = "const shortPath = data.path.replace(/.*[\\/\\\\]/, '') || data.path;"

if bad in h:
    h = h.replace(bad, good)
    print("FIXED specific bad regex")
else:
    # Search with regex for any /.*[/\] patterns
    count = 0
    def fix_regex(m):
        global count
        count += 1
        return "data.path.split(/[\\/\\\\]/).pop() || data.path"
    
    # Pattern: data.path.replace(/.*[...broken...]/, '')
    h_new = re.sub(
        r"data\.path\.replace\(/\.\*\[.*?\]\/,\s*''\)\s*\|\|\s*data\.path",
        "data.path.split(/[\\/\\\\]/).pop() || data.path",
        h
    )
    if h_new != h:
        h = h_new
        print(f"FIXED via regex pattern ({count} occurrences)")
    else:
        # Manual search character by character
        idx = h.find("const shortPath")
        while idx > 0:
            end = h.find(";", idx)
            snippet = h[idx:end+1]
            print("Found shortPath:", repr(snippet[:100]))
            if "/.*[" in snippet:
                new_snippet = "const shortPath = data.path.split(/[\\/\\\\]/).pop() || data.path;"
                h = h[:idx] + new_snippet + h[end+1:]
                print("Fixed!")
                break
            idx = h.find("const shortPath", idx+1)

pathlib.Path("static/index.html").write_text(h, encoding="utf-8")
print("Saved:", len(h))

# Verify no remaining bad patterns
if "/.*[/" in h:
    # Find context
    idx = h.find("/.*[/")
    print("WARNING still found /.*[/ at", idx, ":", repr(h[max(0,idx-30):idx+60]))
else:
    print("OK: no bad regex patterns found")
