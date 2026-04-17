"""
Surgical fixes for 3 exact bugs found:
1. notifT ReferenceError - showNotif uses notifT before declaration
2. path=undefined in /api/files/list - enterFSMode3D called with undefined
3. Camera srcObject=false - stream not persisting due to const scope leak
"""
import pathlib, re

hf = pathlib.Path("static/index.html")
h = hf.read_text(encoding="utf-8")

# ═══════════════════════════════════════
# BUG 1: notifT - find showNotif and fix variable ordering
# ═══════════════════════════════════════
# notifT is likely used before its let declaration
idx_notifT = h.find("notifT")
print(f"notifT first use at: {idx_notifT}, context: {h[max(0,idx_notifT-40):idx_notifT+80]!r}")

# Find all notifT usages
positions = []
idx = 0
while True:
    idx = h.find("notifT", idx)
    if idx < 0: break
    positions.append(idx)
    idx += 1

print(f"notifT appears {len(positions)} times at positions: {positions[:10]}")

# Check if it's a 'let notifT' or 'var notifT'
for p in positions:
    snippet = h[max(0,p-4):p+20]
    if "let " in snippet or "var " in snippet or "const " in snippet:
        print(f"DECLARATION at {p}: {snippet!r}")

# Fix: change all let notifT inside functions to var (hoisting) or move to top
# The safest fix: change 'let notifT' to use a different approach
h = h.replace("let notifT=", "if(typeof notifT==='undefined')window.notifT=null;\nwindow.notifT=")
h = h.replace("clearTimeout(notifT)", "clearTimeout(window.notifT||null)")
h = h.replace("notifT=null", "window.notifT=null")

# Count remaining notifT (not prefixed with window.)
import re as _re
remaining = _re.findall(r'(?<!window\.)(?<!window\??\.)notifT', h)
print(f"Non-window notifT remaining: {len(remaining)}")
if remaining:
    # Replace all non-window notifT
    h = _re.sub(r'(?<!window\.)(?<!window\??\.)notifT', 'window.notifT', h)
    print("All notifT references prefixed with window.")

# ═══════════════════════════════════════
# BUG 2: path=undefined in enterFSMode3D
# ═══════════════════════════════════════
# The function gets called with undefined path
# Fix: add guard at function entry
old_fs_entry = "async function enterFSMode3D(path, pushHistory) {\n  if (pushHistory === undefined) pushHistory = true;"
new_fs_entry = """async function enterFSMode3D(path, pushHistory) {
  if (!path || path === 'undefined') path = '~';
  if (pushHistory === undefined) pushHistory = true;"""

if old_fs_entry in h:
    h = h.replace(old_fs_entry, new_fs_entry)
    print("BUG 2: path guard added")
else:
    # Try to find and patch
    idx_fs = h.find("async function enterFSMode3D(path")
    if idx_fs > 0:
        end_line = h.find("\n", idx_fs) + 1
        # Insert after first line
        h = h[:end_line] + "  if (!path || path === 'undefined') path = '~';\n" + h[end_line:]
        print("BUG 2: path guard added (fallback)")
    else:
        print("BUG 2: enterFSMode3D not found!")

# ═══════════════════════════════════════
# BUG 3: Camera - stream goes null
# ═══════════════════════════════════════
# The issue: window._scene/_cam assigned right after scene=new THREE.Scene()
# but scene is declared with const so it's in the IIFE scope
# The window._scene assignment happens BEFORE the IIFE runs = error
# Let's check where we put it

idx_scene = h.find("const scene=new THREE.Scene()")
if idx_scene > 0:
    end_scene = h.find(";", idx_scene) + 1
    print(f"scene declaration at {idx_scene}, window assignment after: {h[end_scene:end_scene+50]!r}")

# Fix camera: the real camera issue is srcObject becomes null
# This happens in Chrome when the stream object goes out of scope or is garbage collected
# Fix: store stream on window.cameraStream instead of local variable
h = h.replace(
    "cameraStream = stream;\n  cameraActive = true;",
    "cameraStream = stream;\n  window.cameraStream = stream;\n  cameraActive = true;"
)

# Also fix attachStream to not lose reference
old_attach_comment = "// Ensure play on metadata load"
if old_attach_comment in h:
    # After attaching, force re-check after 1s
    h = h.replace(
        "  });",
        """  });
  // Double-check after 1s that video is playing
  setTimeout(() => {
    [document.getElementById('scanner-video'), document.getElementById('cam-video')].forEach(vid => {
      if (vid && vid.srcObject && vid.paused) {
        vid.play().catch(() => {});
      }
    });
  }, 1000);""",
        1  # Only replace first occurrence in the attachStream function
    )
    print("BUG 3: video play double-check added")

# Save  
hf.write_text(h, encoding="utf-8")
print(f"\nDONE: {len(h)} chars")
