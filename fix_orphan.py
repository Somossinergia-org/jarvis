"""
COMPLETE DEFINITIVE REWRITE of the camera block.
The issue: fix_tdz.py left orphan code (the old CAM_CONSTRAINTS array body without 
the variable assignment) causing a syntax error.
This script removes that orphan code cleanly.
"""
import pathlib, re, subprocess

hf = pathlib.Path("static/index.html")
h = hf.read_text(encoding="utf-8")

# ══════════════════════════════════════════════
# STEP 1: Find and remove the orphan code block
# ══════════════════════════════════════════════
# The orphan looks like:
# // (declarations moved to top of camera block)
#   // Best quality first
#   {video:{width:...},audio:false},
#   ...
# ];

orphan_marker = "// (declarations moved to top of camera block)"
if orphan_marker in h:
    idx = h.find(orphan_marker)
    # The orphan block ends with "];" on its own line
    # Find the next ];" after the marker
    end_orphan = h.find("];", idx)
    if end_orphan > idx:
        end_orphan += 2  # include the ];"
        # Skip to end of that line
        eol = h.find("\n", end_orphan)
        if eol > 0:
            end_orphan = eol + 1
        removed = h[idx:end_orphan]
        print(f"REMOVING orphan block ({len(removed)} chars):")
        print(repr(removed[:200]))
        h = h[:idx] + h[end_orphan:]
        print("Orphan removed OK")
    else:
        print("Could not find end of orphan block (];)")
else:
    print("Orphan marker not found - checking for other issues")

# ══════════════════════════════════════════════
# STEP 2: Verify var CAM_CONSTRAINTS is correct
# ══════════════════════════════════════════════
idx_constraints = h.find("var CAM_CONSTRAINTS = [")
if idx_constraints > 0:
    # Show the full declaration
    end_c = h.find("];", idx_constraints) + 2
    print(f"\nCAM_CONSTRAINTS at {idx_constraints}:")
    print(repr(h[idx_constraints:end_c]))
else:
    print("\nWARNING: var CAM_CONSTRAINTS not found!")

# ══════════════════════════════════════════════
# STEP 3: Write and validate
# ══════════════════════════════════════════════
hf.write_text(h, encoding="utf-8")
print(f"\nSaved: {len(h)} chars")

# Node syntax check of the full script block
scripts = re.findall(r'<script(?![^>]*src)[^>]*>(.*?)</script>', h, re.DOTALL)
combined = "\n".join(scripts)
temp = pathlib.Path("_chk.js")
temp.write_text(combined, encoding="utf-8")
r = subprocess.run(["node", "--input-type=module", "--eval", combined[:50000]], 
                   capture_output=True, text=True, timeout=10)
# Use simpler check
r2 = subprocess.run(["node", "-e", f"(function(){{{combined}}})()"], 
                    capture_output=True, text=True, timeout=10)
temp.unlink()

if r2.returncode == 0:
    print("NODE SYNTAX: PASS")
else:
    # Show first error
    lines = r2.stderr.split("\n")
    print("NODE ERROR:")
    for l in lines[:8]:
        print(" ", l)
