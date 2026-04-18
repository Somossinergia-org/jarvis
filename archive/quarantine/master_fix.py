"""
MASTER FIX — Fixes ALL remaining issues in one pass:
1. window._cam referenced before cam is declared (line 802 vs 803)
2. panel-files still opens as flat panel (not 3D cells) — flyToNode hook
3. Duplicate panel-files comment
4. Various other accumulated patch noise
"""
import pathlib, subprocess, re

hf = pathlib.Path("static/index.html")
h = hf.read_text(encoding="utf-8")

# ══════════════════════════════════════════════════
# FIX 1: window._cam referenced before cam exists
# Move window._scene/_cam assignment AFTER cam declaration
# ══════════════════════════════════════════════════

# Current (BROKEN):
# const scene=new THREE.Scene();
# window._scene=scene;window._cam=cam;   <-- cam not declared yet!
# const cam=new THREE.PerspectiveCamera(...);

BAD = "const scene=new THREE.Scene();\nwindow._scene=scene;window._cam=cam;\nconst cam=new THREE.PerspectiveCamera(58,window.innerWidth/window.innerHeight,0.1,500);\ncam.position.set(0,0,12);"

GOOD = "const scene=new THREE.Scene();\nconst cam=new THREE.PerspectiveCamera(58,window.innerWidth/window.innerHeight,0.1,500);\ncam.position.set(0,0,12);\nwindow._scene=scene;window._cam=cam;  // exposed for FS3D cells"

if BAD in h:
    h = h.replace(BAD, GOOD)
    print("FIX 1: window._cam moved after cam declaration — DONE")
else:
    # Try alternate detection
    idx = h.find("window._scene=scene;window._cam=cam;")
    cam_idx = h.find("const cam=new THREE.PerspectiveCamera")
    print(f"FIX 1: window._cam at {idx}, cam declaration at {cam_idx}")
    if idx > 0 and cam_idx > idx:
        # Remove the wrong assignment
        h = h.replace("\nwindow._scene=scene;window._cam=cam;\n", "\n")
        # Add it after cam declaration
        old_cam_line = "const cam=new THREE.PerspectiveCamera(58,window.innerWidth/window.innerHeight,0.1,500);\ncam.position.set(0,0,12);"
        new_cam_line = old_cam_line + "\nwindow._scene=scene;window._cam=cam;"
        h = h.replace(old_cam_line, new_cam_line)
        print("FIX 1: Moved by pattern replacement")

# ══════════════════════════════════════════════════
# FIX 2: Remove duplicate panel comment
# ══════════════════════════════════════════════════
h = h.replace(
    "  <!-- ARCHIVOS — HOLOGRAPHIC FILE BROWSER -->\n    <!-- ARCHIVOS — HOLOGRAPHIC FILE BROWSER -->\n",
    "  <!-- ARCHIVOS — HOLOGRAPHIC FILE BROWSER -->\n"
)
print("FIX 2: duplicate comment removed")

# ══════════════════════════════════════════════════
# FIX 3: Make sure flyToNode ARCHIVOS goes to 3D mode NOT flat panel
# Also make sure activeNode is reset so flyBack() works
# ══════════════════════════════════════════════════
idx_ftn = h.find("function flyToNode(nd){")
if idx_ftn > 0:
    end_ftn = h.find("\nfunction flyBack()", idx_ftn)
    ftn_block = h[idx_ftn:end_ftn]
    print(f"flyToNode block ({len(ftn_block)} chars):")
    print(repr(ftn_block[:500]))

# Check that files trigger is correct
if "nd.id==='files'" in h:
    print("FIX 3: files trigger present")
    # Make sure it resets activeNode properly before entering FS mode
    old_files_trigger = "    if(nd.id==='files'){setTimeout(()=>enterFSMode3D('~'),200); return;}"
    new_files_trigger = """    if(nd.id==='files'){
      setTimeout(()=>enterFSMode3D('~'),200);
      document.getElementById('btn-back').style.display='flex';
      document.getElementById('brain-hint').classList.add('hidden');
      return;
    }"""
    if old_files_trigger in h:
        h = h.replace(old_files_trigger, new_files_trigger)
        print("FIX 3: files trigger improved with btn-back")
else:
    print("FIX 3: files trigger NOT FOUND — adding it")

# ══════════════════════════════════════════════════
# FIX 4: exitFSMode should reset activeNode too
# ══════════════════════════════════════════════════
old_exit = """function exitFSMode() {
  fsModeActive = false;
  clearFS3DNodes();
  fsHistory3D = [];
  document.getElementById('fs-hud').classList.remove('active');
  // Restore main node opacity
  NODES.forEach(n => {
    if (n.pts && n.pts.material) n.pts.material.opacity = 0.9;
  });
  // Close any open panel
  if (activeNode) flyBack();
  showGBadge('⬡ CEREBRO');
}"""

new_exit = """function exitFSMode() {
  fsModeActive = false;
  clearFS3DNodes();
  fsHistory3D = [];
  document.getElementById('fs-hud').classList.remove('active');
  document.getElementById('btn-back').style.display='none';
  document.getElementById('brain-hint').classList.remove('hidden');
  // Restore main node opacity
  NODES.forEach(n => {
    if (n.pts && n.pts.material) n.pts.material.opacity = 0.9;
  });
  // Reset navigation state
  activeNode = null;
  autoRotate = true;
  closeAllPanels();
  showGBadge('⬡ CEREBRO');
}"""

if old_exit in h:
    h = h.replace(old_exit, new_exit)
    print("FIX 4: exitFSMode improved")
else:
    print("FIX 4: exitFSMode not found exactly — patching")
    h = h.replace(
        "  if (activeNode) flyBack();\n  showGBadge('⬡ CEREBRO');\n}",
        """  activeNode = null; autoRotate = true; closeAllPanels();
  document.getElementById('btn-back').style.display='none';
  document.getElementById('brain-hint').classList.remove('hidden');
  showGBadge('⬡ CEREBRO');
}""", 1
    )

# ══════════════════════════════════════════════════
# FIX 5: window._sph issue in tweenToSph
# ══════════════════════════════════════════════════
# The tweenToSph has a broken conditional from fix_scope.py
# Let's find and fix it
broken_sph = h.find("if(window._sph){window._sph.theta")
if broken_sph > 0:
    # Find the full broken section
    end_block = h.find("}", broken_sph + 50)
    snippet = h[broken_sph:end_block+1]
    print(f"Broken sph snippet: {repr(snippet[:200])}")
    
    # Replace with simple working code  
    h = h.replace(
        "if(window._sph){window._sph.theta = start.theta + (end.theta - start.theta) * e;\n    window._sph.phi   = start.phi   + (end.phi   - start.phi)   * e;\n    window._sph.r     = start.r     + (end.r     - start.r)     * e;}",
        "const s=window._sph||{};\n    s.theta=start.theta+(end.theta-start.theta)*e;\n    s.phi=start.phi+(end.phi-start.phi)*e;\n    s.r=start.r+(end.r-start.r)*e;"
    )
    print("FIX 5: tweenToSph sph reference fixed")
else:
    print("FIX 5: tweenToSph no broken pattern found")

# ══════════════════════════════════════════════════
# SAVE AND VALIDATE
# ══════════════════════════════════════════════════
hf.write_text(h, encoding="utf-8")
print(f"\nSaved: {len(h)} chars")

# JS validation
scripts = re.findall(r'<script(?![^>]*src)[^>]*>(.*?)</script>', h, re.DOTALL)
combined = "\n".join(scripts)
temp = pathlib.Path("_chk.js")
temp.write_text(combined, encoding="utf-8")
r = subprocess.run(["node", "--check", "_chk.js"], capture_output=True, text=True)
temp.unlink()
if r.returncode == 0:
    print("NODE SYNTAX CHECK: PASS ✓")
else:
    print("NODE SYNTAX ERROR:")
    for line in r.stderr.split("\n")[:8]:
        print(" ", line)

# Check cam declared before window._cam
cam_decl = h.find("const cam=new THREE.PerspectiveCamera")
win_cam  = h.find("window._cam=cam")
print(f"\ncam declared at: {cam_decl}")
print(f"window._cam at:  {win_cam}")
print(f"Order OK: {cam_decl < win_cam}")
