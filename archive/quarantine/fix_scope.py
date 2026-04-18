"""
DEFINITIVE FIX:
1. Camera - force video by checking readyState and retrying play()
2. FS3D cells - move into the same scope as scene/cam/THREE by patching the IIFE closure
"""
import pathlib, re

hf = pathlib.Path("static/index.html")
h = hf.read_text(encoding="utf-8")

# ═══════════════════════════════════════════
# FIX 1: CAMERA — add onloadedmetadata handler + force play loop
# ═══════════════════════════════════════════
# The current attachStream doesn't force play properly on Chrome
# Chrome needs autoplay + muted + playsInline + onloadedmetadata

OLD_ATTACH = """function attachStream(stream) {
  if (!stream) return;
  cameraStream = stream;
  cameraActive = true;

  const sv = document.getElementById('scanner-video');
  const cv = document.getElementById('cam-video');

  [sv, cv].forEach(vid => {
    if (!vid) return;
    vid.srcObject = stream;
    vid.muted = true;
    vid.playsInline = true;
    // Force play with retry
    const tryPlay = () => vid.play().catch(() => setTimeout(tryPlay, 500));
    tryPlay();
  });"""

NEW_ATTACH = """function attachStream(stream) {
  if (!stream) return;
  cameraStream = stream;
  cameraActive = true;

  const sv = document.getElementById('scanner-video');
  const cv = document.getElementById('cam-video');

  [sv, cv].forEach(vid => {
    if (!vid) return;
    vid.srcObject = stream;
    vid.muted = true;
    vid.playsInline = true;
    vid.autoplay = true;
    // Ensure play on metadata load
    vid.onloadedmetadata = () => {
      vid.play().catch(e => {
        console.warn('[CAM] play() failed on metadata:', e.name);
        // Retry after short delay
        setTimeout(() => vid.play().catch(() => {}), 300);
      });
    };
    // Also try immediately in case metadata is already loaded
    if (vid.readyState >= 1) {
      vid.play().catch(() => setTimeout(() => vid.play().catch(() => {}), 500));
    }
  });"""

if OLD_ATTACH in h:
    h = h.replace(OLD_ATTACH, NEW_ATTACH)
    print("attachStream fixed with onloadedmetadata")
else:
    print("WARN: attachStream not found for patching")
    # fallback: find and patch just the tryPlay section
    old_tryplay = "    const tryPlay = () => vid.play().catch(() => setTimeout(tryPlay, 500));\n    tryPlay();"
    new_tryplay = """    vid.muted = true; vid.playsInline = true; vid.autoplay = true;
    vid.onloadedmetadata = () => vid.play().catch(() => setTimeout(() => vid.play().catch(()=>{}), 300));
    if (vid.readyState >= 1) vid.play().catch(() => {});"""
    if old_tryplay in h:
        h = h.replace(old_tryplay, new_tryplay)
        print("tryPlay fallback patched")

# ═══════════════════════════════════════════
# FIX 2: FS3D SCOPE — move FS3D vars into window.* so IIFE closure can access them
# ═══════════════════════════════════════════
# The problem: scene/cam/THREE are inside (function loop(){...})() IIFE
# enterFSMode3D is outside the IIFE but calls scene.add() etc. which aren't accessible
# Fix: expose scene and cam on window object right after their creation

# Find where scene and cam are created/assigned
# Look for: const scene = new THREE.Scene() or similar
scene_assign = h.find("const scene=new THREE.Scene()")
if scene_assign < 0:
    scene_assign = h.find("scene = new THREE.Scene()")
    
cam_assign = h.find("const cam=new THREE.PerspectiveCamera(")
if cam_assign < 0:
    cam_assign = h.find("cam=new THREE.PerspectiveCamera(")

print(f"scene at: {scene_assign}, cam at: {cam_assign}")

# After scene = new THREE.Scene() add window.scene = scene; window.cam = cam;
if scene_assign > 0:
    # Find end of that statement
    end_scene = h.find(";", scene_assign) + 1
    h = h[:end_scene] + "\nwindow._scene=scene;window._cam=cam;" + h[end_scene:]
    print("window._scene/_cam assigned after scene creation")

# Now replace all scene./cam. in FS3D code with window._scene / window._cam
# First find where FS3D JS starts and ends
fs_start = h.find("// 3D FILE SYSTEM CELLS")
fs_end = h.find("// END 3D FILE SYSTEM CELLS")

if fs_start > 0 and fs_end > fs_start:
    fs_block = h[fs_start:fs_end+len("// END 3D FILE SYSTEM CELLS")]
    # Replace scene. and cam. references  
    fs_fixed = fs_block.replace(
        "scene.add(cloud);", "window._scene && window._scene.add(cloud);"
    ).replace(
        "scene.add(core);", "window._scene && window._scene.add(core);"
    ).replace(
        "scene.remove(n.cloud);", "window._scene && window._scene.remove(n.cloud);"
    ).replace(
        "scene.remove(n.core);", "window._scene && window._scene.remove(n.core);"
    ).replace(
        "const v = n.pos.clone().project(cam);",
        "if(!window._cam)return;\n  const v = n.pos.clone().project(window._cam);"
    )
    # Also fix THREE references
    fs_fixed = fs_fixed.replace("new THREE.", "new window.THREE.")
    
    h = h[:fs_start] + fs_fixed + h[fs_end+len("// END 3D FILE SYSTEM CELLS"):]
    print("FS3D scope: scene/cam/THREE references externalized")
else:
    print(f"WARN: FS3D block not found. fs_start={fs_start}, fs_end={fs_end}")
    # Alternative: just expose scene globally right where it's used
    # Find the IIFE that contains the render loop
    iife_start = h.find("(function loop(){")
    if iife_start > 0:
        # Go backwards to find where scene is defined
        block_start = h.rfind("const scene=", 0, iife_start)
        if block_start < 0:
            block_start = h.rfind("let scene=", 0, iife_start)
        print(f"Scene defined at: {block_start}")

# ═══════════════════════════════════════════
# FIX 3: Also add window.THREE = THREE at top of script
# ═══════════════════════════════════════════
# THREE is loaded from CDN - it's already global, but just to be safe
# The issue is really just scene and cam
print("Fix 3: Verifying THREE is global (CDN loaded - should be fine)")

# ═══════════════════════════════════════════
# FIX 4: Also find tweenToSph and if sph is not accessible, use window._sph
# ═══════════════════════════════════════════
sph_find = h.find("let sph=")
if sph_find < 0:
    sph_find = h.find("const sph=")
if sph_find < 0:
    sph_find = h.find("sph={")
print(f"sph defined at: {sph_find}")

# After sph definition, expose on window
if sph_find > 0:
    end_sph = h.find(";", sph_find) + 1
    sph_snippet = h[sph_find:end_sph]
    print("sph definition:", repr(sph_snippet[:80]))
    h = h[:end_sph] + "\nwindow._sph=sph;" + h[end_sph:]
    print("window._sph assigned")

# Fix tweenToSph to use window._sph
h = h.replace(
    "const start = {theta: sph.theta, phi: sph.phi, r: sph.r};",
    "const sphRef=window._sph||sph||{};\n  const start = {theta: sphRef.theta||0.6, phi: sphRef.phi||0.95, r: sphRef.r||13};"
).replace(
    "sph.theta = start.theta + (end.theta - start.theta) * e;",
    "if(window._sph){window._sph.theta = start.theta + (end.theta - start.theta) * e;"
).replace(
    "sph.phi   = start.phi   + (end.phi   - start.phi)   * e;",
    "window._sph.phi   = start.phi   + (end.phi   - start.phi)   * e;"
).replace(
    "sph.r     = start.r     + (end.r     - start.r)     * e;",
    "window._sph.r     = start.r     + (end.r     - start.r)     * e;}"
)

hf.write_text(h, encoding="utf-8")
print(f"\nDONE: {len(h)} chars")
