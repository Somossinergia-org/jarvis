"""
ROOT CAUSE FIX: camRetries TDZ error.
Move all camera variable declarations BEFORE the camera functions.
"""
import pathlib

hf = pathlib.Path("static/index.html")
h = hf.read_text(encoding="utf-8")

# The issue: camRetries, camWatchdog, CAM_CONSTRAINTS are declared INSIDE
# the camera manager block but AFTER restartCamera function references them.
# Fix: Declare them at the TOP of the camera block BEFORE any function.

CAM_BLOCK_START = "// ══════════════════════════════════════════════════\n// CAMERA MANAGER — BULLETPROOF, NEVER FAILS\n// ══════════════════════════════════════════════════"

NEW_CAM_BLOCK_START = """// ══════════════════════════════════════════════════
// CAMERA MANAGER — BULLETPROOF, NEVER FAILS
// ══════════════════════════════════════════════════
// Declare ALL camera variables first (before any function) to avoid TDZ
var camRetries = 0;
var camWatchdog = null;
var CAM_CONSTRAINTS = [
  {video:{width:{ideal:1280},height:{ideal:720},facingMode:'user'},audio:false},
  {video:{width:{ideal:640},height:{ideal:480},facingMode:'user'},audio:false},
  {video:{width:{ideal:320},height:{ideal:240}},audio:false},
  {video:true, audio:false},
];"""

if CAM_BLOCK_START in h:
    h = h.replace(CAM_BLOCK_START, NEW_CAM_BLOCK_START)
    print("Camera block header replaced with var declarations")
else:
    print("ERROR: Camera block header not found")

# Now remove the DUPLICATE declarations that come after (let camRetries=0 etc)
h = h.replace("let camRetries = 0;\nlet camWatchdog = null;\nconst CAM_CONSTRAINTS = [", 
               "// (declarations moved to top of camera block)")

# Also remove old multiline const CAM_CONSTRAINTS if it appears
import re
h = re.sub(
    r"// \(declarations moved to top of camera block\)\s*\n"
    r"  \{video:\{width:\{ideal:1280\}.*?\},\s*\{video:true, audio:false\},\s*\];",
    "// (declarations already at top)",
    h, flags=re.DOTALL
)

pathlib.Path("static/index.html").write_text(h, encoding="utf-8")
print(f"Saved: {len(h)} chars")

# Verify
print("camRetries TDZ fixed:", "var camRetries = 0;" in h)
print("CAM_CONSTRAINTS var:", "var CAM_CONSTRAINTS = [" in h)
