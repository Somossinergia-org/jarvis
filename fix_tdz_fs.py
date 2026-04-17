"""
FINAL DEFINITIVE FIX:
fsModeActive declared with 'let' in the FS3D block AFTER flyBack() uses it.
Solution: declare ALL FS3D state variables at the TOP of the script (globals section).
Then remove their re-declaration in the FS3D block.
"""
import pathlib, re, subprocess

hf = pathlib.Path("static/index.html")
h = hf.read_text(encoding="utf-8")

# ═══════════════════════════════════════════════════════
# STEP 1: Add FS3D state variables to the GLOBALS section at top
# ═══════════════════════════════════════════════════════
OLD_GLOBALS_END = "window.handGravity={x:.5,y:.5,active:false};\nwindow.jSpeaking=false;"
NEW_GLOBALS_END = """window.handGravity={x:.5,y:.5,active:false};
window.jSpeaking=false;

// ── FS3D State (declared here so flyBack/flyToNode can see them) ──
var fsModeActive=false;
var fs3DNodes=[];
var fs3DCores=[];
var fsPath3D='~';
var fsHistory3D=[];
var _fsAnimStart=0;"""

if OLD_GLOBALS_END in h:
    h = h.replace(OLD_GLOBALS_END, NEW_GLOBALS_END)
    print("STEP 1: FS3D vars declared in globals section")
else:
    print("ERROR: globals end not found")

# ═══════════════════════════════════════════════════════
# STEP 2: Remove the duplicate declarations in the FS3D block
# ═══════════════════════════════════════════════════════
# Remove the lines that redeclare them
DUPL_DECLS = [
    "let fsModeActive = false;\n",
    "let fs3DNodes    = [];   // {pts, core, ring, light, label, item, pos}\n",
    "let fs3DCores    = [];   // for raycast (like nodeCores but for FS)\n",
    "let fsPath3D     = '~';\n",
    "let fsHistory3D  = [];\n",
    "let _fsAnimStart=0;\n",
]
for d in DUPL_DECLS:
    if d in h:
        h = h.replace(d, "")
        print(f"Removed duplicate: {d.strip()}")
    else:
        # Try without trailing spaces variation
        d2 = d.rstrip()
        pass

# Also clean up the 4-space variant
for old, new in [
    ("let fsModeActive = false;\n", ""),
    ("let fs3DNodes    = [];", ""),
    ("let fs3DCores    = [];", ""),
    ("let fsPath3D     = '~';", ""),
    ("let fsHistory3D  = [];", ""),
]:
    if old in h:
        h = h.replace(old, new)
        print(f"Cleaned: {old.strip()}")

# ═══════════════════════════════════════════════════════
# STEP 3: Fix exitFSMode — the lbl_requestFrame call (which was a bug)
# ═══════════════════════════════════════════════════════
old_lbl_bug = "    if(n.labelEl){n.labelEl.style.display='';lbl_requestFrame();}"
new_lbl_fix = "    if(n.labelEl){n.labelEl.style.display='';}"
if old_lbl_bug in h:
    h = h.replace(old_lbl_bug, new_lbl_fix)
    print("STEP 3: removed lbl_requestFrame() bug call")

old_lbl_fn = "function lbl_requestFrame(){requestAnimationFrame(()=>{});}// dummy to trigger frame"
if old_lbl_fn in h:
    h = h.replace(old_lbl_fn, "")
    print("STEP 3: removed lbl_requestFrame dummy function")

# ═══════════════════════════════════════════════════════
# STEP 4: In the FS Color section, the FS_COL const is also redeclaring
#         global vars — make sure it uses the right var names
# ═══════════════════════════════════════════════════════
# FS_NODE_COLORS from old code may conflict with FS_COL
old_fn_colors = "const FS_NODE_COLORS = {"
if old_fn_colors in h:
    # find and check
    idx = h.find(old_fn_colors)
    print(f"Old FS_NODE_COLORS block at {idx} — removing")
    end = h.find("};", idx) + 2
    h = h[:idx] + h[end:]
    # also remove fsGetColor3D reference to old FS_NODE_COLORS
    h = h.replace("return FS_NODE_COLORS.", "return _fsCol_legacy_")
    print("Old FS_NODE_COLORS removed")
else:
    print("No duplicate FS_NODE_COLORS")

# Also clean old enterFSMode3D / functions that may be duplicated
old_getcolor3d = "\nfunction fsGetColor3D(item) {"
if old_getcolor3d in h:
    idx = h.find(old_getcolor3d)
    end = h.find("\n}\n", idx) + 3
    h = h[:idx] + h[end:]
    print("Removed old fsGetColor3D")

old_geticon3d = "\nfunction fsGetIcon3D(item) {"
if old_geticon3d in h:
    idx = h.find(old_geticon3d)
    end = h.find("\n}\n", idx) + 3
    h = h[:idx] + h[end:]
    print("Removed old fsGetIcon3D")

# ═══════════════════════════════════════════════════════
# STEP 5: Also clean old enterFSMode3D if duplicate
# ═══════════════════════════════════════════════════════
# Check how many times enterFSMode3D appears
count = h.count("async function enterFSMode3D(")
print(f"\nenterFSMode3D appears {count} times")
if count > 1:
    # Remove the old one (shorter/older one)
    idx1 = h.find("async function enterFSMode3D(")
    idx2 = h.find("async function enterFSMode3D(", idx1+10)
    # Keep the second one (the new complete version)
    end1 = h.find("\nasync function ", idx1+10)
    if end1 < 0:
        end1 = h.find("\nfunction ", idx1+10)
    h = h[:idx1] + h[end1+1:]
    print("Removed first (old) enterFSMode3D")

# ═══════════════════════════════════════════════════════
# SAVE & VALIDATE
# ═══════════════════════════════════════════════════════
hf.write_text(h, encoding="utf-8")
print(f"\nSaved: {len(h)} chars, {h.count(chr(10))} lines")

scripts = re.findall(r'<script(?![^>]*src)[^>]*>(.*?)</script>', h, re.DOTALL)
combined = "\n".join(scripts)
temp = pathlib.Path("_chk.js")
temp.write_text(combined, encoding="utf-8")
r = subprocess.run(["node","--check","_chk.js"], capture_output=True, text=True)
temp.unlink()
print("SYNTAX:", "PASS" if r.returncode==0 else "FAIL:\n"+r.stderr[:400])

# Final checks
checks = [
    "var fsModeActive=false;",
    "var fs3DNodes=[];",
    "var fs3DCores=[];",
    "enterFSMode3D",
    "updateFS3DLabels",
    "exitFSMode",
    "fsGoBack3D",
]
for c in checks:
    print(f"  {'OK' if c in h else 'MISSING'}: {c}")

print("\nfsModeActive count:", h.count("fsModeActive"))
print("enterFSMode3D count:", h.count("async function enterFSMode3D"))
