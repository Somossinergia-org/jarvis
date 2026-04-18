"""
Build the full 3D Notes Graph Mode — identical aesthetic to brain nodes and FS3D cells.
When user clicks NOTAS node:
  - Brain dims out
  - All notes appear as particle cloud cells in 3D space
  - Connection lines glow between linked notes
  - Click a note cell → compact inline editor
  - ESC / voice "salir" → restore brain
"""
import pathlib, re, subprocess

hf = pathlib.Path("static/index.html")
h  = hf.read_text(encoding="utf-8")

# ─────────────────────────────────────────────────────────────
# 1. Add state variables next to FS3D state block
# ─────────────────────────────────────────────────────────────
OLD_STATE = "var _fsAnimStart=0;"
NEW_STATE = """var _fsAnimStart=0;

// ── Notes Graph 3D State ──────────────────────────────────
var notesModeActive=false;
var notesGraph3D={nodes:[],edges:[],cores:[]};
var _notesAnimStart=0;
var _activeNoteEditorTitle=null;"""

h = h.replace(OLD_STATE, NEW_STATE, 1)
print("1. State vars:", "notesModeActive" in h)

# ─────────────────────────────────────────────────────────────
# 2. flyToNode: notes node enters graph mode
# ─────────────────────────────────────────────────────────────
OLD_FLY = "    if(nd.id==='notes'){openNotesPanel();return;}"
NEW_FLY = "    if(nd.id==='notes'){enterNotesGraph3D();return;}"
h = h.replace(OLD_FLY, NEW_FLY, 1)
print("2. flyToNode notes:", "enterNotesGraph3D" in h)

# ─────────────────────────────────────────────────────────────
# 3. flyBack: exit notes graph if active
# ─────────────────────────────────────────────────────────────
OLD_FB = "  if(fsModeActive){exitFSMode();return;}"
NEW_FB = "  if(fsModeActive){exitFSMode();return;}\n  if(notesModeActive){exitNotesGraph3D();return;}"
h = h.replace(OLD_FB, NEW_FB, 1)
print("3. flyBack notes:", "exitNotesGraph3D" in h)

# ─────────────────────────────────────────────────────────────
# 4. ESC key: also exit notes graph
# ─────────────────────────────────────────────────────────────
OLD_ESC = "  if(fsModeActive){exitFSMode();return;}\n  flyBack();"
NEW_ESC = "  if(fsModeActive){exitFSMode();return;}\n  if(notesModeActive){exitNotesGraph3D();return;}\n  flyBack();"
h = h.replace(OLD_ESC, NEW_ESC, 1)
print("4. ESC notes:", h.count("exitNotesGraph3D") >= 2)

# ─────────────────────────────────────────────────────────────
# 5. render loop — call updateNotesGraph3D
# ─────────────────────────────────────────────────────────────
OLD_RENDER_FS = "  if(fs3DNodes.length) updateFS3DLabels();"
NEW_RENDER_FS = "  if(fs3DNodes.length) updateFS3DLabels();\n  if(notesModeActive&&notesGraph3D.nodes.length) updateNotesGraph3D();"
h = h.replace(OLD_RENDER_FS, NEW_RENDER_FS, 1)
print("5. render loop:", "updateNotesGraph3D" in h)

# ─────────────────────────────────────────────────────────────
# 6. canvas raycast — add notes graph raycast
# ─────────────────────────────────────────────────────────────
OLD_RAYCAST = "  if(fsModeActive&&fs3DCores.length){"
NEW_RAYCAST = """  // Notes graph raycast
  if(notesModeActive&&notesGraph3D.cores.length){
    const nHits=raycaster.intersectObjects(notesGraph3D.cores,false);
    if(nHits.length){const nd=nHits[0].object.userData.nd;if(nd)onNoteNodeClick(nd);return;}
  }
  if(fsModeActive&&fs3DCores.length){"""
h = h.replace(OLD_RAYCAST, NEW_RAYCAST, 1)
print("6. raycast notes:", "onNoteNodeClick" in h)

# ─────────────────────────────────────────────────────────────
# 7. Inject the full Notes Graph 3D JS system
# ─────────────────────────────────────────────────────────────
NOTES_3D_JS = r"""
// ══════════════════════════════════════════════════════════════
// NOTES GRAPH 3D — Grafo de Conocimiento en espacio 3D
// ══════════════════════════════════════════════════════════════

const FOLDER_COLS={
  notas:0xff55cc, diario:0x00d4ff, proyectos:0x00ff88,
  ideas:0xffd700, personas:0xffb300, recursos:0x9955ff
};
const FOLDER_HEX={
  notas:'#ff55cc', diario:'#00d4ff', proyectos:'#00ff88',
  ideas:'#ffd700', personas:'#ffb300', recursos:'#9955ff'
};

async function enterNotesGraph3D(){
  if(notesModeActive) return;
  notesModeActive=true;
  _notesAnimStart=0;

  // Fetch graph data from API
  let graphData;
  try{ graphData=await fetch('/api/vault/graph').then(r=>r.json()); }
  catch(e){ console.error('Notes graph error',e); notesModeActive=false; return; }

  const {nodes,edges}=graphData;
  if(!nodes||!nodes.length){ showNotif('NOTAS','Sin notas. Crea la primera.','#ff55cc'); notesModeActive=false; return; }

  // Hide brain nodes
  NODES.forEach(nd=>{ nd.pts.visible=false; nd.core.visible=false; nd.ring.visible=false; nd.light.intensity=0; if(nd.labelEl)nd.labelEl.classList.remove('vis'); });

  // Clear previous note nodes
  exitNotesGraph3D_cleanup();

  // Fibonacci sphere distribution
  function fibPos(i,total,R){
    const golden=Math.PI*(3-Math.sqrt(5));
    const y=1-((i/(total-1||1))*2);
    const r=Math.sqrt(Math.max(0,1-y*y));
    const theta=golden*i;
    return new THREE.Vector3(R*r*Math.cos(theta),R*y,R*r*Math.sin(theta));
  }

  const R=Math.max(5,Math.min(9,3+nodes.length*0.18));
  const nodeById={};

  nodes.forEach((note,i)=>{
    const col=FOLDER_COLS[note.folder]||0xff55cc;
    const hex=FOLDER_HEX[note.folder]||'#ff55cc';
    const pos=fibPos(i,nodes.length,R);
    const weight=Math.max(1,note.weight||1);

    // Scale with connection count
    const scale=0.85+Math.min(weight,8)*0.09;

    // Particle cloud
    const N=350+Math.floor(weight*30);
    const p=new Float32Array(N*3);
    const baseR=0.28*scale;
    for(let j=0;j<N;j++){
      const r=baseR+Math.random()*0.85*scale;
      const th=Math.random()*Math.PI*2;
      const ph=Math.acos(1-2*Math.random());
      p[j*3]  =pos.x+r*Math.sin(ph)*Math.cos(th);
      p[j*3+1]=pos.y+r*Math.sin(ph)*Math.sin(th);
      p[j*3+2]=pos.z+r*Math.cos(ph);
    }
    const pg=new THREE.BufferGeometry();
    pg.setAttribute('position',new THREE.BufferAttribute(p,3));
    const pts=new THREE.Points(pg,new THREE.PointsMaterial({
      color:col,size:0.048,transparent:true,opacity:0,
      blending:THREE.AdditiveBlending,depthWrite:false
    }));
    scene.add(pts);

    // Core sphere
    const core=new THREE.Mesh(
      new THREE.SphereGeometry(0.22*scale,16,16),
      new THREE.MeshPhongMaterial({color:col,emissive:col,emissiveIntensity:.5,transparent:true,opacity:0})
    );
    core.position.copy(pos);
    core.userData.nd={note,pos,pts,core,ring:null,light:null,label:null};
    scene.add(core);
    notesGraph3D.cores.push(core);

    // Ring
    const ring=new THREE.Mesh(
      new THREE.RingGeometry(0.24*scale,0.29*scale,28),
      new THREE.MeshBasicMaterial({color:col,transparent:true,opacity:0,side:THREE.DoubleSide,blending:THREE.AdditiveBlending})
    );
    ring.position.copy(pos);
    scene.add(ring);

    // Point light
    const light=new THREE.PointLight(col,0,4);
    light.position.copy(pos);
    scene.add(light);

    // HTML label
    const lbl=document.createElement('div');
    lbl.className='nlabel';
    lbl.style.color=hex;
    lbl.style.borderColor=hex+'33';
    lbl.style.background='rgba(2,8,16,.9)';
    lbl.style.maxWidth='140px';
    lbl.style.fontSize='9px';
    lbl.style.opacity='0';
    lbl.style.transition='opacity .4s';
    lbl.style.cursor='pointer';
    const icon=note.folder==='diario'?'📅':note.folder==='proyectos'?'🚀':note.folder==='ideas'?'💡':note.folder==='personas'?'👤':note.folder==='recursos'?'📚':'📝';
    lbl.innerHTML=`<span class="nlabel-icon">${icon}</span>${note.title.substring(0,22)}${note.title.length>22?'…':''}`;
    lbl.onclick=()=>onNoteNodeClick(core.userData.nd);
    document.getElementById('node-labels').appendChild(lbl);

    // Finalize node obj
    const nd={note,pos,pts,core,ring,light,label:lbl};
    core.userData.nd=nd;
    notesGraph3D.nodes.push(nd);
    nodeById[note.id]=nd;
  });

  // Draw edges (connections between notes)
  edges.forEach(edge=>{
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
  });

  // HUD
  const hud=document.getElementById('fs-hud');
  if(hud){
    hud.style.display='flex';
    document.getElementById('fs-path').textContent='📝 KNOWLEDGE GRAPH';
    document.getElementById('fs-count').textContent=nodes.length+' notas · '+edges.length+' enlaces';
    document.getElementById('fs-back').style.display='none'; // no back in graph
    document.getElementById('fs-exit').onclick=exitNotesGraph3D;
  }

  // Fly camera out for overview
  const flyDur=55;
  flyAnim={
    sp:cam.position.clone(), ep:new THREE.Vector3(0,2,R*1.8),
    sl:new THREE.Vector3(), el:new THREE.Vector3(0,0,0),
    t:0, dur:flyDur, onEnd:null
  };

  document.getElementById('brain-hint').classList.add('hidden');
  showGBadge('📝 GRAFO DE CONOCIMIENTO');
}

function exitNotesGraph3D(){
  notesModeActive=false;
  exitNotesGraph3D_cleanup();
  // Show brain nodes again
  NODES.forEach(nd=>{ nd.pts.visible=true; nd.core.visible=true; nd.ring.visible=true; });
  // Close mini editor if open
  const me=document.getElementById('note-mini-editor');
  if(me)me.style.display='none';
  // Hide HUD
  const hud=document.getElementById('fs-hud');
  if(hud)hud.style.display='none';
  flyBack();
  showGBadge('⬡ CEREBRO');
}

function exitNotesGraph3D_cleanup(){
  notesGraph3D.nodes.forEach(nd=>{
    if(nd.pts){scene.remove(nd.pts);nd.pts.geometry.dispose();}
    if(nd.core){scene.remove(nd.core);nd.core.geometry.dispose();}
    if(nd.ring){scene.remove(nd.ring);}
    if(nd.light){scene.remove(nd.light);}
    if(nd.label){nd.label.remove();}
  });
  notesGraph3D.edges.forEach(l=>{scene.remove(l);l.geometry.dispose();});
  notesGraph3D.nodes=[];
  notesGraph3D.edges=[];
  notesGraph3D.cores=[];
}

// Render loop update for notes graph
function updateNotesGraph3D(){
  if(!notesGraph3D.nodes.length) return;
  const now=performance.now();
  if(!_notesAnimStart) _notesAnimStart=now;
  const elapsed=(now-_notesAnimStart)*0.001;
  const t=now*0.001;

  notesGraph3D.nodes.forEach((nd,i)=>{
    const delay=i*0.035;
    const progress=Math.min(Math.max((elapsed-delay)/0.55,0),1);
    const ease=1-Math.pow(1-progress,3);
    const isActive=_activeNoteEditorTitle===nd.note.title;

    // Fade in
    if(progress<1){
      nd.pts.material.opacity=ease*0.65;
      nd.core.material.opacity=ease*0.85;
      nd.ring.material.opacity=ease*0.22;
      nd.light.intensity=ease*0.8;
      nd.label.style.opacity=String(ease);
    }

    // Always rotating
    nd.pts.rotation.y+=0.0020+i*0.0002;
    nd.pts.rotation.x+=0.0007;
    nd.core.rotation.y+=0.010;
    nd.ring.rotation.z+=0.018;
    nd.ring.rotation.x+=0.004;

    // Pulse
    if(progress>=1){
      const pulse=0.5+0.5*Math.sin(t*1.6+i*1.2);
      nd.pts.material.size=0.048+pulse*0.010;
      nd.pts.material.opacity=0.55+pulse*0.12;
      nd.light.intensity=(isActive?2.0:0.2)+pulse*0.3;
      nd.core.material.emissiveIntensity=isActive?1.5:0.4+pulse*0.3;
      nd.ring.material.opacity=0.15+pulse*0.12;
    }

    // Project label
    const v=nd.pos.clone().project(cam);
    const x=(v.x*0.5+0.5)*window.innerWidth;
    const y=(-v.y*0.5+0.5)*window.innerHeight;
    nd.label.style.left=x+'px';
    nd.label.style.top=y+'px';
    nd.label.style.display=(v.z<1)?'':'none';
  });
}

// Click on a note node in 3D space
async function onNoteNodeClick(nd){
  _activeNoteEditorTitle=nd.note.title;
  // Fly to note
  const target=nd.pos.clone();
  const ep=target.clone().normalize().multiplyScalar(nd.pos.length()+3.5);
  flyAnim={
    sp:cam.position.clone(), ep,
    sl:cam.position.clone().lerp(target,0.2),
    el:target.clone(),
    t:0, dur:40, onEnd:()=>showNoteMiniEditor(nd.note.title)
  };
  showGBadge('📝 '+nd.note.title.substring(0,25));
}

async function showNoteMiniEditor(title){
  let me=document.getElementById('note-mini-editor');
  if(!me){
    me=document.createElement('div');
    me.id='note-mini-editor';
    me.style.cssText='position:fixed;right:20px;top:50%;transform:translateY(-50%);width:400px;max-height:75vh;overflow-y:auto;background:rgba(2,5,16,.95);border:1px solid #ff55cc44;border-radius:14px;padding:20px;z-index:2000;box-shadow:0 0 40px #ff55cc22;backdrop-filter:blur(12px);';
    document.body.appendChild(me);
  }
  // Load note
  try{
    const note=await fetch('/api/vault/note/'+encodeURIComponent(title)).then(r=>r.json());
    const hex=FOLDER_HEX[note.folder]||'#ff55cc';
    me.innerHTML=`
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
        <div style="color:${hex};font-family:'Share Tech Mono',monospace;font-size:12px;font-weight:bold">📝 ${note.title}</div>
        <button onclick="document.getElementById('note-mini-editor').style.display='none';_activeNoteEditorTitle=null" style="background:none;border:1px solid #ff3355;border-radius:6px;color:#ff3355;padding:2px 8px;cursor:pointer;font-size:10px">✕</button>
      </div>
      <div style="color:var(--txd);font-size:9px;margin-bottom:8px">${note.folder} · ${(note.tags||[]).map(t=>'#'+t).join(' ')}</div>
      <textarea id="nme-content" style="width:100%;height:200px;background:rgba(0,12,28,.9);border:1px solid ${hex}33;border-radius:8px;color:#ccd;padding:10px;font-family:'Share Tech Mono',monospace;font-size:10px;line-height:1.6;resize:vertical;outline:none;box-sizing:border-box">${note.content||''}</textarea>
      ${note.backlinks&&note.backlinks.length?'<div style="margin-top:6px;font-size:8px;color:var(--txd)">⬅ '+note.backlinks.join(', ')+'</div>':''}
      ${note.outlinks&&note.outlinks.length?'<div style="margin-top:3px;font-size:8px;color:var(--txd)">➡ '+note.outlinks.join(', ')+'</div>':''}
      <div style="display:flex;gap:8px;margin-top:10px">
        <button onclick="saveMiniNote('${title.replace(/'/g,"\\'")}',this)" style="flex:1;background:rgba(255,85,204,.15);border:1px solid ${hex}44;border-radius:8px;color:${hex};padding:7px;cursor:pointer;font-family:'Share Tech Mono',monospace;font-size:10px">💾 GUARDAR</button>
        <button onclick="document.getElementById('note-mini-editor').style.display='none';_activeNoteEditorTitle=null" style="background:none;border:1px solid #334;border-radius:8px;color:var(--txd);padding:7px;cursor:pointer;font-size:10px">CERRAR</button>
      </div>`;
    me.style.display='block';
  }catch(e){ showNotif('ERROR',''+e,'var(--r)'); }
}

async function saveMiniNote(title, btn){
  const content=document.getElementById('nme-content')?.value||'';
  btn.textContent='⏳ Guardando...';
  try{
    const r=await fetch('/api/vault/note/'+encodeURIComponent(title),{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({content})});
    const d=await r.json();
    if(d.error){showNotif('ERROR',d.error,'var(--r)');}
    else{showNotif('GUARDADO',title.substring(0,20),'#ff55cc');showGBadge('💾 '+title.substring(0,20));}
  }catch(e){showNotif('ERROR',''+e,'var(--r)');}
  btn.textContent='💾 GUARDAR';
}
// END NOTES GRAPH 3D
"""

TARGET = "// ══════════════════════════════════════════════════════\n// SISTEMA DE NOTAS — Knowledge Base JARVIS"
if TARGET in h:
    h = h.replace(TARGET, NOTES_3D_JS + "\n" + TARGET, 1)
    print("7. Notes 3D JS injected before SISTEMA NOTAS")
else:
    h = h.replace("startAuth();", NOTES_3D_JS + "\nstartAuth();", 1)
    print("7. Notes 3D JS injected (fallback before startAuth)")

# ─────────────────────────────────────────────────────────────
# 8. Save and validate
# ─────────────────────────────────────────────────────────────
hf.write_text(h, encoding="utf-8")
print(f"\nSaved: {len(h)} chars")

scripts = re.findall(r'<script(?![^>]*src)[^>]*>(.*?)</script>', h, re.DOTALL)
tmp = pathlib.Path("_chk.js")
tmp.write_text("\n".join(scripts), encoding="utf-8")
r = subprocess.run(["node","--check","_chk.js"], capture_output=True, text=True)
tmp.unlink()
print("SYNTAX:", "PASS" if r.returncode==0 else "FAIL:\n"+r.stderr[:400])

checks = [
    "notesModeActive","enterNotesGraph3D","exitNotesGraph3D","updateNotesGraph3D",
    "onNoteNodeClick","showNoteMiniEditor","saveMiniNote",
    "notesGraph3D.nodes","FOLDER_COLS","fibPos"
]
for c in checks:
    print(f"  {'OK' if c in h else 'MISS'}: {c}")
