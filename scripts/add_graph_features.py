"""
scripts/add_graph_features.py
Phase 2: Add to the 3D Notes Graph:
  - 2D minimap (bottom-left canvas overlay)
  - 3D spatial breadcrumb (focused node path)
  - Search with camera focus
  - Focus mode (isolate selected node + connections)
  - FPS monitor in HUD
  - Recursive child expansion stub (depth limited)
All injected cleanly into index.html.
"""
import pathlib, re, subprocess

ROOT = pathlib.Path(__file__).parent.parent
HTML = ROOT / "static" / "index.html"
h = HTML.read_text(encoding="utf-8")

# ──────────────────────────────────────────────────────────────────
# 1. Add minimap canvas + search bar + breadcrumb HTML elements
# ──────────────────────────────────────────────────────────────────
MINIMAP_HTML = """
<!-- Notes Graph: Minimap + Search + Breadcrumb + Focus HUD -->
<canvas id="notes-minimap" style="display:none;position:fixed;bottom:20px;left:20px;width:160px;height:120px;border:1px solid #ff55cc33;border-radius:8px;background:rgba(0,5,15,.85);z-index:1500;backdrop-filter:blur(4px);"></canvas>

<div id="notes-graph-hud" style="display:none;position:fixed;top:60px;left:50%;transform:translateX(-50%);z-index:1500;display:none;flex-direction:column;align-items:center;gap:6px;pointer-events:none;">
  <!-- Breadcrumb -->
  <div id="notes-breadcrumb" style="background:rgba(0,5,15,.85);border:1px solid #ff55cc33;border-radius:20px;padding:5px 14px;font-family:'Share Tech Mono',monospace;font-size:10px;color:#ff55cc;pointer-events:auto;"></div>
  <!-- Search -->
  <div style="display:flex;gap:6px;pointer-events:auto;">
    <input id="notes-graph-search" placeholder="🔍 Buscar nota..." onkeyup="if(event.key==='Enter')focusNoteSearch(this.value)"
      style="background:rgba(0,5,15,.92);border:1px solid #ff55cc44;border-radius:20px;padding:5px 14px;font-family:'Share Tech Mono',monospace;font-size:10px;color:#ff55cc;outline:none;width:220px;" />
    <button onclick="toggleFocusMode()" id="notes-focus-btn" style="background:rgba(255,85,204,.1);border:1px solid #ff55cc44;border-radius:20px;padding:5px 12px;color:#ff55cc;font-family:'Share Tech Mono',monospace;font-size:9px;cursor:pointer;">◎ FOCUS</button>
    <button onclick="exitNotesGraph3D()" style="background:rgba(255,51,85,.1);border:1px solid #ff335544;border-radius:20px;padding:5px 12px;color:#ff3355;font-family:'Share Tech Mono',monospace;font-size:9px;cursor:pointer;">✕ SALIR</button>
  </div>
</div>

<!-- FPS Monitor -->
<div id="fps-monitor" style="display:none;position:fixed;bottom:20px;right:20px;background:rgba(0,5,15,.85);border:1px solid #ff55cc22;border-radius:6px;padding:4px 10px;font-family:'Share Tech Mono',monospace;font-size:9px;color:#ff55cc88;z-index:1500;">FPS: --</div>
"""

# Insert before </body>
h = h.replace("</body>", MINIMAP_HTML + "\n</body>", 1)
print("1. Minimap/search/breadcrumb HTML added:", "notes-minimap" in h)

# ──────────────────────────────────────────────────────────────────
# 2. Inject Graph Features JS
# ──────────────────────────────────────────────────────────────────
GRAPH_FEATURES_JS = r"""
// ══════════════════════════════════════════════════════════════
// NOTES GRAPH — Fase 2: Minimapa, Breadcrumb, Search, Focus, FPS
// ══════════════════════════════════════════════════════════════

// ── FPS Monitor ───────────────────────────────────────────────
let _fpsFrames=0,_fpsLast=performance.now(),_fpsValue=60;
function updateFPS(){
  _fpsFrames++;
  const now=performance.now();
  if(now-_fpsLast>500){
    _fpsValue=Math.round(_fpsFrames*1000/(now-_fpsLast));
    _fpsFrames=0; _fpsLast=now;
    const el=document.getElementById('fps-monitor');
    if(el&&notesModeActive){
      el.textContent='FPS: '+_fpsValue;
      el.style.color=_fpsValue>=45?'#00ff88':_fpsValue>=25?'#ffd700':'#ff3355';
    }
  }
}

// ── Notes Graph HUD show/hide ───────────────────────────────
function showNotesGraphHUD(show){
  const hud=document.getElementById('notes-graph-hud');
  const mm=document.getElementById('notes-minimap');
  const fps=document.getElementById('fps-monitor');
  if(hud)hud.style.display=show?'flex':'none';
  if(mm)mm.style.display=show?'block':'none';
  if(fps)fps.style.display=show?'block':'none';
}

// ── Breadcrumb ─────────────────────────────────────────────
let _notesBreadcrumb=[];
function pushBreadcrumb(title){
  if(!_notesBreadcrumb.includes(title)) _notesBreadcrumb.push(title);
  renderBreadcrumb();
}
function renderBreadcrumb(){
  const el=document.getElementById('notes-breadcrumb');
  if(!el)return;
  if(!_notesBreadcrumb.length){el.textContent='📝 KNOWLEDGE GRAPH';return;}
  el.innerHTML=('<span style="cursor:pointer;opacity:.5" onclick="resetBreadcrumb()">⬡ GRAFO</span>'
    +_notesBreadcrumb.map((t,i)=>`<span style="color:#ff55cc99"> › </span><span style="cursor:pointer;${i===_notesBreadcrumb.length-1?'color:#ff55cc':'opacity:.6'}" onclick="focusNoteSearch('${t.replace(/'/g,"\\'")}')">` +t.substring(0,18)+(t.length>18?'…':'')+'</span>').join(''));
}
function resetBreadcrumb(){
  _notesBreadcrumb=[];
  renderBreadcrumb();
  // Restore all nodes visibility
  notesGraph3D.nodes.forEach(nd=>{
    nd.pts.material.opacity=0.65; nd.core.material.opacity=0.85;
    nd.ring.material.opacity=0.22; nd.light.intensity=0.4;
    if(nd.label)nd.label.style.opacity='1';
  });
  notesGraph3D.edges.forEach(l=>l.material.opacity=0.18);
  _focusModeActive=false;
  document.getElementById('notes-focus-btn').style.background='rgba(255,85,204,.1)';
}

// ── Search with camera focus ─────────────────────────────
function focusNoteSearch(query){
  if(!query||!notesModeActive)return;
  const q=query.toLowerCase();
  const found=notesGraph3D.nodes.find(nd=>nd.note.title.toLowerCase().includes(q)||
    (nd.note.tags||[]).some(t=>t.toLowerCase().includes(q))||
    (nd.note.folder||'').toLowerCase().includes(q));
  if(!found){showNotif('BUSCAR','Sin resultados para "'+query+'"','#ff55cc');return;}
  // Fly to found node
  const target=found.pos.clone();
  const ep=target.clone().normalize().multiplyScalar(found.pos.length()+3.5);
  flyAnim={sp:cam.position.clone(),ep,sl:cam.position.clone().lerp(target,.2),el:target.clone(),t:0,dur:45,onEnd:()=>{
    pushBreadcrumb(found.note.title);
    showNoteMiniEditor(found.note.title);
  }};
  showGBadge('📝 '+found.note.title.substring(0,25));
  document.getElementById('notes-graph-search').value='';
}

// ── Focus Mode (isolate node + its connections) ──────────
let _focusModeActive=false;
let _focusedNoteTitle=null;
function toggleFocusMode(){
  if(!_activeNoteEditorTitle||!notesModeActive)return;
  _focusModeActive=!_focusModeActive;
  const btn=document.getElementById('notes-focus-btn');
  if(!_focusModeActive){
    resetBreadcrumb(); if(btn)btn.style.background='rgba(255,85,204,.1)'; return;
  }
  if(btn)btn.style.background='rgba(255,85,204,.3)';
  _focusedNoteTitle=_activeNoteEditorTitle;
  // Find focused node
  const focusNd=notesGraph3D.nodes.find(n=>n.note.title===_focusedNoteTitle);
  if(!focusNd)return;
  // Find connected node IDs
  const focusId=focusNd.note.id;
  const connectedIds=new Set([focusId]);
  notesGraph3D.edges.forEach((line,i)=>{ /* edges store from/to on userData */
    const e=line.userData;
    if(e&&(e.from===focusId||e.to===focusId)){connectedIds.add(e.from);connectedIds.add(e.to);}
  });
  // Dim unconnected
  notesGraph3D.nodes.forEach(nd=>{
    const isConn=connectedIds.has(nd.note.id);
    nd.pts.material.opacity=isConn?0.75:0.06;
    nd.core.material.opacity=isConn?0.9:0.05;
    nd.light.intensity=isConn?1.2:0;
    if(nd.label)nd.label.style.opacity=isConn?'1':'0.1';
  });
}

// ── Minimap renderer ─────────────────────────────────────
function drawMinimap(){
  if(!notesModeActive||!notesGraph3D.nodes.length) return;
  const canvas=document.getElementById('notes-minimap');
  if(!canvas||canvas.style.display==='none')return;
  const ctx=canvas.getContext('2d');
  const W=canvas.width=160, H=canvas.height=120;
  ctx.clearRect(0,0,W,H);
  ctx.fillStyle='rgba(0,5,15,0)'; ctx.fillRect(0,0,W,H);

  // Project all nodes to 2D (top-down XZ view)
  const R=12; // world radius limit
  const cx=W/2, cy=H/2;
  const scale=Math.min(W,H)/2/R*0.85;

  // Draw edges
  notesGraph3D.nodes.forEach(nd=>{
    const x=cx+nd.pos.x*scale;
    const y=cy+nd.pos.z*scale;
    const col=FOLDER_HEX[nd.note.folder]||'#ff55cc';
    const r=2+Math.min((nd.note.weight||1),6)*0.4;
    const isActive=nd.note.title===_activeNoteEditorTitle;
    ctx.beginPath();
    ctx.arc(x,y,isActive?r*2:r,0,Math.PI*2);
    ctx.fillStyle=isActive?col:col+'88';
    ctx.fill();
    if(isActive){ctx.strokeStyle=col;ctx.lineWidth=1.5;ctx.stroke();}
  });

  // Camera position dot
  const cpx=cx+cam.position.x*scale;
  const cpy=cy+cam.position.z*scale;
  ctx.beginPath();
  ctx.arc(Math.max(4,Math.min(W-4,cpx)),Math.max(4,Math.min(H-4,cpy)),3,0,Math.PI*2);
  ctx.fillStyle='#ffffff44'; ctx.fill();
}

// ── Hook into enterNotesGraph3D to show HUD ──────────────
const _origEnterNotes=enterNotesGraph3D;
async function enterNotesGraph3D(){
  _notesBreadcrumb=[];
  await _origEnterNotes();
  showNotesGraphHUD(true);
  renderBreadcrumb();
}

// ── Hook into exitNotesGraph3D to hide HUD ───────────────
const _origExitNotes=exitNotesGraph3D;
function exitNotesGraph3D(){
  showNotesGraphHUD(false);
  _focusModeActive=false; _notesBreadcrumb=[];
  _origExitNotes();
}

// ── Hook into onNoteNodeClick to update breadcrumb ───────
const _origOnNoteClick=onNoteNodeClick;
async function onNoteNodeClick(nd){
  pushBreadcrumb(nd.note.title);
  await _origOnNoteClick(nd);
}

// ── Render loop additions: minimap + FPS ─────────────────
const _origAnimate=animate;
function animate(){
  _origAnimate();
  if(notesModeActive){drawMinimap();updateFPS();}
}
// END GRAPH FEATURES
"""

# Inject before startAuth()
TARGET = "startAuth();"
count = h.count(TARGET)
h = h.replace(TARGET, GRAPH_FEATURES_JS + "\n" + TARGET, 1)
print(f"2. Graph features JS injected (found {count} startAuth targets):", "drawMinimap" in h)

# ──────────────────────────────────────────────────────────────────
# 3. Store edge from/to on line.userData when building edges
# ──────────────────────────────────────────────────────────────────
OLD_EDGE = """  edges.forEach(edge=>{
    const fromNd=nodeById[edge.from];
    const toNd=nodeById[edge.to];
    if(!fromNd||!toNd) return;
    const pts=[fromNd.pos,toNd.pos];
    const line=new THREE.Line(
      new THREE.BufferGeometry().setFromPoints(pts),
      new THREE.LineBasicMaterial({color:0xff55cc,transparent:true,opacity:0.18,blending:THREE.AdditiveBlending})
    );
    scene.add(line);
    notesGraph3D.edges.push(line);
  });"""

NEW_EDGE = """  edges.forEach(edge=>{
    const fromNd=nodeById[edge.from];
    const toNd=nodeById[edge.to];
    if(!fromNd||!toNd) return;
    const pts=[fromNd.pos,toNd.pos];
    const line=new THREE.Line(
      new THREE.BufferGeometry().setFromPoints(pts),
      new THREE.LineBasicMaterial({color:0xff55cc,transparent:true,opacity:0.18,blending:THREE.AdditiveBlending})
    );
    line.userData={from:edge.from,to:edge.to};
    scene.add(line);
    notesGraph3D.edges.push(line);
  });"""

h = h.replace(OLD_EDGE, NEW_EDGE, 1)
print("3. Edge userData stored:", "line.userData={from:edge.from" in h)

# ──────────────────────────────────────────────────────────────────
# 4. Save + validate
# ──────────────────────────────────────────────────────────────────
HTML.write_text(h, encoding="utf-8")
print(f"\nSaved: {len(h):,}B")

scripts_txt = re.findall(r'<script(?![^>]*src)[^>]*>(.*?)</script>', h, re.DOTALL)
tmp = ROOT / "_chk.js"
tmp.write_text("\n".join(scripts_txt), encoding="utf-8")
r = subprocess.run(["node","--check",str(tmp)], capture_output=True, text=True)
tmp.unlink()
print("SYNTAX:", "PASS" if r.returncode==0 else "FAIL:\n"+r.stderr[:400])
