"""
JARVIS FINAL ARCHITECTURAL FIX:
1. Chat → hidden drawer (not covering brain)
2. File system → 3D floating cells in brain space (not a flat panel)
"""
import pathlib, re

hf = pathlib.Path("static/index.html")
h = hf.read_text(encoding="utf-8")

# ══════════════════════════════════════════════
# 1. FIX CHAT CSS — hide messages by default
# ══════════════════════════════════════════════

OLD_CHAT_CSS = """/* ── CHAT OVERLAY ─────────────────────────── */
#chat-overlay{
  position:fixed;bottom:0;left:50%;transform:translateX(-50%);
  width:min(720px,92vw);z-index:30;display:flex;flex-direction:column;
  max-height:55vh;pointer-events:none;
}
#chat-messages{
  flex:1;overflow-y:auto;padding:10px 14px;display:flex;flex-direction:column;gap:8px;
  scrollbar-width:thin;scrollbar-color:rgba(0,212,255,.1) transparent;pointer-events:auto;
}"""

NEW_CHAT_CSS = """/* ── CHAT DRAWER (hidden by default, slide in from right) ── */
#chat-overlay{
  position:fixed;bottom:0;left:50%;transform:translateX(-50%);
  width:min(720px,92vw);z-index:30;display:flex;flex-direction:column;
  pointer-events:none;
}
#chat-messages{
  flex:1;overflow-y:auto;padding:10px 14px;display:flex;flex-direction:column;gap:8px;
  scrollbar-width:thin;scrollbar-color:rgba(0,212,255,.1) transparent;pointer-events:auto;
  max-height:0;overflow:hidden;transition:max-height .4s ease;
}
#chat-messages.open{max-height:42vh;}"""

if OLD_CHAT_CSS in h:
    h = h.replace(OLD_CHAT_CSS, NEW_CHAT_CSS)
    print("Chat CSS updated")
else:
    # fallback: patch just the max-height line
    h = h.replace(
        "position:fixed;bottom:0;left:50%;transform:translateX(-50%);\n  width:min(720px,92vw);z-index:30;display:flex;flex-direction:column;\n  max-height:55vh;pointer-events:none;",
        "position:fixed;bottom:0;left:50%;transform:translateX(-50%);\n  width:min(720px,92vw);z-index:30;display:flex;flex-direction:column;\n  pointer-events:none;"
    )
    h = h.replace(
        "flex:1;overflow-y:auto;padding:10px 14px;display:flex;flex-direction:column;gap:8px;\n  scrollbar-width:thin;scrollbar-color:rgba(0,212,255,.1) transparent;pointer-events:auto;",
        "max-height:0;overflow:hidden;transition:max-height .4s ease;flex:1;overflow-y:auto;padding:10px 14px;display:flex;flex-direction:column;gap:8px;\n  scrollbar-width:thin;scrollbar-color:rgba(0,212,255,.1) transparent;pointer-events:auto;"
    )
    print("Chat CSS patched (fallback)")

# ══════════════════════════════════════════════
# 2. ADD CHAT TOGGLE BUTTON FUNCTIONALITY
# ══════════════════════════════════════════════
# Find the sendMessage function and add chat toggle
CHAT_TOGGLE_JS = """
// ── CHAT VISIBILITY CONTROL ────────────────────
let chatOpen = false;
function toggleChatDrawer(show) {
  const msgs = document.getElementById('chat-messages');
  if (!msgs) return;
  if (show === undefined) chatOpen = !chatOpen;
  else chatOpen = show;
  if (chatOpen) {
    msgs.classList.add('open');
    msgs.scrollTop = msgs.scrollHeight;
  } else {
    msgs.classList.remove('open');
  }
}
// Auto-close chat after 8s of inactivity
let chatAutoClose = null;
function chatActivity() {
  toggleChatDrawer(true);
  if (chatAutoClose) clearTimeout(chatAutoClose);
  chatAutoClose = setTimeout(() => toggleChatDrawer(false), 8000);
}
// End Chat Visibility Control
"""

insert_pos = h.find("// End File Browser")
if insert_pos < 0:
    insert_pos = h.rfind("startAuth();")
if insert_pos > 0:
    h = h[:insert_pos] + CHAT_TOGGLE_JS + "\n" + h[insert_pos:]
    print("Chat toggle JS added")

# ══════════════════════════════════════════════
# 3. PATCH sendMessage TO SHOW CHAT + AUTO-HIDE
# ══════════════════════════════════════════════
# Find where messages are appended and add chatActivity()
old_append = "msgs.scrollTop=msgs.scrollHeight;"
new_append = "msgs.scrollTop=msgs.scrollHeight;chatActivity();"
if old_append in h and new_append not in h:
    h = h.replace(old_append, new_append)
    print("scrollTop → chatActivity() patched")

# ══════════════════════════════════════════════
# 4. ADD CSS FOR 3D FILE CELLS HUD
# ══════════════════════════════════════════════
FS_3D_CSS = """
/* ── 3D FILE SYSTEM HUD ───────────────────── */
#fs-hud{
  position:fixed;top:56px;left:50%;transform:translateX(-50%);
  z-index:150;display:none;align-items:center;gap:10px;
  background:rgba(2,8,16,.9);border:1px solid rgba(0,212,255,.2);
  border-radius:12px;padding:8px 18px;backdrop-filter:blur(20px);
  font-family:'Share Tech Mono',monospace;font-size:9px;color:var(--txd);
  letter-spacing:1px;max-width:90vw;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;
}
#fs-hud.active{display:flex;}
#fs-hud-path{color:var(--c);flex:1;overflow:hidden;text-overflow:ellipsis;}
#fs-hud-back{color:var(--gold);cursor:pointer;padding:2px 10px;border:1px solid rgba(255,215,0,.2);border-radius:6px;flex-shrink:0;transition:all .2s;}
#fs-hud-back:hover{border-color:var(--gold);background:rgba(255,215,0,.08);}
#fs-hud-close{color:var(--r);cursor:pointer;padding:2px 8px;border:1px solid rgba(255,51,85,.2);border-radius:6px;flex-shrink:0;}
#fs-hud-count{color:var(--txd);font-size:8px;flex-shrink:0;}
"""
h = h.replace("</style>", FS_3D_CSS + "</style>", 1)
print("FS 3D HUD CSS added")

# ══════════════════════════════════════════════
# 5. ADD FS HUD HTML ELEMENT
# ══════════════════════════════════════════════
FS_HUD_HTML = """
  <!-- FS 3D HUD -->
  <div id="fs-hud">
    <span style="color:var(--gold);flex-shrink:0;">📁</span>
    <span id="fs-hud-path">~</span>
    <span id="fs-hud-count"></span>
    <span id="fs-hud-back" onclick="fsGoBack3D()">← ATRÁS</span>
    <span id="fs-hud-close" onclick="exitFSMode()">✕</span>
  </div>

"""

# Insert after the div#main-ui opening
main_ui_pos = h.find('<div id="main-ui">')
if main_ui_pos > 0:
    # Find end of that div opening tag
    end_tag = h.find('>', main_ui_pos) + 1
    h = h[:end_tag] + FS_HUD_HTML + h[end_tag:]
    print("FS HUD HTML added")

# ══════════════════════════════════════════════
# 6. 3D FILE SYSTEM CELLS JAVASCRIPT
# ══════════════════════════════════════════════
FS_3D_JS = """
// ══════════════════════════════════════════════════════
// 3D FILE SYSTEM CELLS — Floating nodes in brain space
// ══════════════════════════════════════════════════════
let fsModeActive = false;
let fs3DNodes = [];       // {mesh, particles, label, item}
let fs3DHovered = null;
let fsPath3D = '~';
let fsHistory3D = [];
const FS_CENTER = new THREE.Vector3(0, 0, 0);

const FS_NODE_COLORS = {
  dir:    0xffd700,
  code:   0x00ff88,
  img:    0x9955ff,
  audio:  0x00d4ff,
  video:  0xffb300,
  archive:0xff9955,
  exec:   0xff3355,
  doc:    0x88aaff,
  default:0x446688,
};

function fsGetColor3D(item) {
  if (item.is_dir) return FS_NODE_COLORS.dir;
  const ext = '.' + item.name.split('.').pop().toLowerCase();
  if (['.js','.ts','.py','.html','.css','.json','.sh','.bat'].includes(ext)) return FS_NODE_COLORS.code;
  if (['.jpg','.jpeg','.png','.gif','.svg','.webp'].includes(ext)) return FS_NODE_COLORS.img;
  if (['.mp3','.wav','.flac','.aac','.ogg'].includes(ext)) return FS_NODE_COLORS.audio;
  if (['.mp4','.mkv','.avi','.mov','.wmv'].includes(ext)) return FS_NODE_COLORS.video;
  if (['.zip','.rar','.7z','.tar','.gz'].includes(ext)) return FS_NODE_COLORS.archive;
  if (['.exe','.msi','.dll'].includes(ext)) return FS_NODE_COLORS.exec;
  if (['.txt','.md','.pdf','.doc','.docx','.xls','.xlsx'].includes(ext)) return FS_NODE_COLORS.doc;
  return FS_NODE_COLORS.default;
}

function fsGetIcon3D(item) {
  if (item.is_dir) return '📁';
  const ext = '.' + item.name.split('.').pop().toLowerCase();
  const m = {'.py':'🐍','.js':'⚡','.html':'🌐','.css':'🎨','.json':'📋',
    '.jpg':'🖼️','.png':'🖼️','.mp3':'🎵','.mp4':'🎬',
    '.zip':'📦','.exe':'⚙️','.pdf':'📕','.txt':'📝','.md':'📝'};
  return m[ext] || '📄';
}

async function enterFSMode3D(path, pushHistory) {
  if (pushHistory === undefined) pushHistory = true;

  // Show HUD
  document.getElementById('fs-hud').classList.add('active');

  // Load dir contents
  let data;
  try {
    const r = await fetch('/api/files/list?path=' + encodeURIComponent(path));
    data = await r.json();
    if (data.error) { showNotif('ERROR', data.error, 'var(--r)'); return; }
  } catch(e) { showNotif('ERROR', '' + e, 'var(--r)'); return; }

  if (pushHistory && fsPath3D !== data.path) fsHistory3D.push(fsPath3D);
  fsPath3D = data.path;

  // Update HUD
  const shortPath = data.path.replace(/.*[/\\]/, '') || data.path;
  document.getElementById('fs-hud-path').textContent = data.path;
  document.getElementById('fs-hud-count').textContent =
    data.items.filter(i => i.is_dir).length + '📁 ' +
    data.items.filter(i => !i.is_dir).length + '📄';
  document.getElementById('fs-hud-back').style.opacity = fsHistory3D.length ? '1' : '0.3';

  fsModeActive = true;

  // Clear existing FS nodes
  clearFS3DNodes();

  // Dim main brain nodes
  NODES.forEach(n => {
    if (n._cloud && n._cloud.material) {
      n._cloud.material.opacity = 0.12;
    }
  });

  // Build new 3D cells
  const items = data.items.slice(0, 24); // max 24 cells on screen
  const total = items.length;

  items.forEach((item, i) => {
    const col = fsGetColor3D(item);
    const isDir = item.is_dir;

    // Fibonacci sphere distribution
    const goldenAngle = Math.PI * (3 - Math.sqrt(5));
    const y = 1 - (i / (total - 1 || 1)) * 2;
    const radius = Math.sqrt(1 - y * y);
    const theta = goldenAngle * i;
    const r = isDir ? 4.5 : 3.5;

    const pos = new THREE.Vector3(
      Math.cos(theta) * radius * r,
      y * r * 0.9,
      Math.sin(theta) * radius * r
    );

    // Particle cloud (like main nodes)
    const pCount = isDir ? 200 : 80;
    const pSize  = isDir ? 0.07 : 0.04;
    const spread = isDir ? 0.55 : 0.35;

    const geo = new THREE.BufferGeometry();
    const pos3 = new Float32Array(pCount * 3);
    const col3 = new Float32Array(pCount * 3);
    const r3 = (col >> 16 & 0xff) / 255;
    const g3 = (col >> 8  & 0xff) / 255;
    const b3 = (col & 0xff) / 255;
    for (let j = 0; j < pCount; j++) {
      const a = Math.random() * Math.PI * 2;
      const b = Math.random() * Math.PI;
      const rr = spread * (0.3 + Math.cbrt(Math.random()));
      pos3[j*3]   = pos.x + rr * Math.sin(b) * Math.cos(a);
      pos3[j*3+1] = pos.y + rr * Math.sin(b) * Math.sin(a);
      pos3[j*3+2] = pos.z + rr * Math.cos(b);
      col3[j*3]   = r3; col3[j*3+1] = g3; col3[j*3+2] = b3;
    }
    geo.setAttribute('position', new THREE.BufferAttribute(pos3, 3));
    geo.setAttribute('color',    new THREE.BufferAttribute(col3, 3));

    const mat = new THREE.PointsMaterial({
      size: pSize, vertexColors: true, transparent: true, opacity: 0,
      blending: THREE.AdditiveBlending, depthWrite: false,
    });
    const cloud = new THREE.Points(geo, mat);
    scene.add(cloud);

    // Core sphere
    const coreGeo = new THREE.SphereGeometry(isDir ? 0.18 : 0.10, 16, 16);
    const coreMat = new THREE.MeshBasicMaterial({ color: col, transparent: true, opacity: 0 });
    const core = new THREE.Mesh(coreGeo, coreMat);
    core.position.copy(pos);
    scene.add(core);

    // HTML label
    const lbl = document.createElement('div');
    lbl.className = 'nlabel';
    lbl.style.borderColor = '#' + col.toString(16).padStart(6, '0') + '66';
    lbl.style.color = '#' + col.toString(16).padStart(6, '0');
    lbl.style.background = 'rgba(2,8,16,.85)';
    lbl.style.fontSize = '7px';
    lbl.style.letterSpacing = '1px';
    lbl.style.padding = '3px 10px';
    lbl.innerHTML = fsGetIcon3D(item) + ' ' + item.name.substring(0, 18);
    lbl.onclick = () => onFSNodeClick(item);
    document.getElementById('node-labels').appendChild(lbl);

    const nodeObj = { cloud, core, label: lbl, item, pos, col };
    fs3DNodes.push(nodeObj);

    // Animate in
    let t = 0;
    const delay = i * 35;
    setTimeout(() => {
      const anim = () => {
        t = Math.min(t + 0.04, 1);
        const ease = 1 - Math.pow(1 - t, 3);
        mat.opacity = ease * 0.9;
        coreMat.opacity = ease * 0.85;
        lbl.style.opacity = ease;
        if (!lbl.classList.contains('vis')) lbl.classList.add('vis');
        if (t < 1) requestAnimationFrame(anim);
      };
      requestAnimationFrame(anim);
    }, delay);
  });

  // Camera: move to overview position for FS
  tweenToSph(0.6, 0.95, 13, 800);

  showGBadge('📁 ' + (shortPath || 'RAÍZ'));
}

function onFSNodeClick(item) {
  if (item.is_dir) {
    enterFSMode3D(item.path);
  } else {
    // Open file via API
    fetch('/api/files/open', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({path: item.path})
    }).then(r => r.json()).then(d => {
      showGBadge('📂 ' + item.name);
    }).catch(e => showNotif('ERROR', '' + e, 'var(--r)'));
  }
}

function fsGoBack3D() {
  if (!fsHistory3D.length) return;
  const prev = fsHistory3D.pop();
  enterFSMode3D(prev, false);
}

function clearFS3DNodes() {
  fs3DNodes.forEach(n => {
    scene.remove(n.cloud);
    scene.remove(n.core);
    n.cloud.geometry.dispose();
    n.cloud.material.dispose();
    n.core.geometry.dispose();
    n.core.material.dispose();
    n.label.remove();
  });
  fs3DNodes = [];
}

function exitFSMode() {
  fsModeActive = false;
  clearFS3DNodes();
  fsHistory3D = [];
  document.getElementById('fs-hud').classList.remove('active');
  // Restore main node opacity
  NODES.forEach(n => {
    if (n._cloud && n._cloud.material) n._cloud.material.opacity = 0.9;
  });
  // Close any open panel
  if (activeNode) flyBack();
  showGBadge('⬡ CEREBRO');
}

// Helper: smooth camera tween to spherical coords
function tweenToSph(theta, phi, r, ms) {
  const start = {theta: sph.theta, phi: sph.phi, r: sph.r};
  const end = {theta, phi, r};
  const t0 = performance.now();
  function step(now) {
    const t = Math.min((now - t0) / (ms || 600), 1);
    const e = 1 - Math.pow(1 - t, 3);
    sph.theta = start.theta + (end.theta - start.theta) * e;
    sph.phi   = start.phi   + (end.phi   - start.phi)   * e;
    sph.r     = start.r     + (end.r     - start.r)     * e;
    if (t < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

// FS node label update in render loop (like main nodes)
function updateFS3DLabels() {
  if (!fs3DNodes.length) return;
  fs3DNodes.forEach(n => {
    const v = n.pos.clone().project(cam);
    const x = (v.x * 0.5 + 0.5) * window.innerWidth;
    const y = (-v.y * 0.5 + 0.5) * window.innerHeight;
    n.label.style.left = x + 'px';
    n.label.style.top  = y + 'px';
    n.label.style.opacity = v.z < 1 ? '1' : '0';
  });
}
// END 3D FILE SYSTEM CELLS
"""

# Insert before "startAuth();"
insert_pos2 = h.rfind("startAuth();")
if insert_pos2 > 0:
    h = h[:insert_pos2] + FS_3D_JS + "\n" + h[insert_pos2:]
    print("FS 3D JS added")
else:
    print("ERROR: startAuth not found for FS insertion")

# ══════════════════════════════════════════════
# 7. HOOK FS MODE INTO flyToNode FOR files node
# ══════════════════════════════════════════════
# Replace the flat panel trigger with 3D mode
old_trigger = "    if(nd.id==='files'){fbHistory=[];fbDepth=0;setTimeout(()=>fbLoad('~',false),200);}"
new_trigger = "    if(nd.id==='files'){setTimeout(()=>enterFSMode3D('~'),200); return;}"

if old_trigger in h:
    h = h.replace(old_trigger, new_trigger, 1)
    print("flyToNode → enterFSMode3D hooked")
else:
    # Try adding it after memory trigger
    h = h.replace(
        "if(nd.id==='memory')loadMemory();",
        "if(nd.id==='memory')loadMemory();\n    if(nd.id==='files'){setTimeout(()=>enterFSMode3D('~'),200);return;}"
    )
    print("flyToNode → enterFSMode3D hooked (fallback)")

# ══════════════════════════════════════════════
# 8. CALL updateFS3DLabels IN RENDER LOOP
# ══════════════════════════════════════════════
old_render_tail = "updateNodeLabels();"
new_render_tail = "updateNodeLabels();updateFS3DLabels();"
if old_render_tail in h and new_render_tail not in h:
    h = h.replace(old_render_tail, new_render_tail, 1)
    print("render loop: updateFS3DLabels() added")

# ══════════════════════════════════════════════
# 9. STORE _cloud ref ON NODES for opacity control
# ══════════════════════════════════════════════
# After cloud is added to scene, tag it on nd
old_cloud_add = "scene.add(cloud);nd.mesh=sphere;"
new_cloud_add = "scene.add(cloud);nd.mesh=sphere;nd._cloud=cloud;"
if old_cloud_add in h and new_cloud_add not in h:
    h = h.replace(old_cloud_add, new_cloud_add)
    print("nd._cloud stored")
else:
    # Try alternative
    h = h.replace(
        "scene.add(cloud);\n    nd.mesh=sphere;",
        "scene.add(cloud);\n    nd.mesh=sphere;nd._cloud=cloud;"
    )
    print("nd._cloud stored (fallback)")

hf.write_text(h, encoding="utf-8")
print(f"\nDONE: {len(h)} chars")
print(f"FS 3D present: {'enterFSMode3D' in h}")
print(f"Chat toggle present: {'toggleChatDrawer' in h}")
print(f"FS HUD present: {'fs-hud' in h}")
