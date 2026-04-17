import pathlib, re

f = pathlib.Path("server.py")
c = f.read_text(encoding="utf-8")

# Fix the broken backslash in the /api/files/list endpoint
# The problem line is: clean = path.replace("/", "\")
bad = 'clean = path.replace("/", "\\")'
good = 'clean = path.replace("/", chr(92))'
if bad in c:
    c = c.replace(bad, good)
    print("Fixed backslash replace")
else:
    # Try alternative fix
    bad2 = 'clean = path.replace("/", chr(92))'
    if bad2 in c:
        print("Already fixed")
    else:
        # Brute-force: replace the whole files/list endpoint cleanly
        print("Doing full endpoint rewrite...")

# Also fix str(item).replace("\\", "/") lines that might be broken
c = c.replace('str(item).replace("\\\\", "/")', 'str(item).replace(chr(92), "/")')
c = c.replace('str(p).replace("\\\\", "/")', 'str(p).replace(chr(92), "/")')
c = c.replace('str(p.parent).replace("\\\\", "/")', 'str(p.parent).replace(chr(92), "/")')
c = c.replace('raw = req.get("path", "").replace("/", "\\\\")', 'raw = req.get("path", "").replace("/", chr(92))')
c = c.replace('path.replace("/", "\\\\")', 'path.replace("/", chr(92))')

f.write_text(c, encoding="utf-8")

# Verify syntax
import subprocess
result = subprocess.run(["py", "-3.12", "-m", "py_compile", "server.py"], capture_output=True, text=True)
if result.returncode == 0:
    print("server.py syntax OK!")
else:
    print("SYNTAX ERROR:", result.stderr)
    # Show problem area
    for line_info in result.stderr.split("\n"):
        if "line" in line_info.lower():
            print(line_info)
