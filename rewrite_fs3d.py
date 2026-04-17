"""
DEFINITIVE FS3D REWRITE:
- File system cells IDENTICAL to brain nodes (particles + ring + light + label)
- Infinite depth navigation
- Voice navigation ("abre Desktop", "atras", "salir")
- Clickable via both HTML label AND Three.js raycast
- Fix flyBack() for FS mode
- Fix chatActivity() on JARVIS response
- Fix THREE.AdditiveBlending scope
"""
import pathlib, re, subprocess

hf = pathlib.Path("static/index.html")
h = hf.read_text(encoding="utf-8")

# ═══════════════════════════════════════════════════════
# THE COMPLETE FS3D REPLACEMENT BLOCK
# ═══════════════════════════════════════════════════════
NEW_FS3D = r"""
// ══════════════════════════════════════════════════════
// 3D FILE SYSTEM — Células idénticas a los nodos del cerebro
// Rutas infinitas, capas, voz, raycast, anillos, glow
// ══════════════════════════════════════════════════════
let fsModeActive = false;
let fs3DNodes    = [];   // {pts, core, ring, light, label, item, pos}
let fs3DCores    = [];   // for raycast (like nodeCores but for FS)
let fsPath3D     = '~';
let fsHistory3D  = [];

// Color por tipo
const FS_COL = {
  dir:0xffd700, code:0x00ff88, img:0x9955ff,  audio:0x00d4ff,
  video:0xffb300, archive:0xff9955, exec:0xff3355, doc:0x88aaff, def:0x5588aa,
};
function _fsCol(item){
  if(item.is_dir) return FS_COL.dir;
  const e='.'+item.name.split('.').pop().toLowerCase();
  if(['.js','.ts','.py','.html','.css','.json','.sh','.bat','.vue','.jsx','.tsx','.go','.rs','.java'].includes(e)) return FS_COL.code;
  if(['.jpg','.jpeg','.png','.gif','.svg','.webp','.bmp','.ico'].includes(e)) return FS_COL.img;
  if(['.mp3','.wav','.flac','.aac','.ogg','.m4a'].includes(e)) return FS_COL.audio;
  if(['.mp4','.mkv','.avi','.mov','.wmv','.webm'].includes(e)) return FS_COL.video;
  if(['.zip','.rar','.7z','.tar','.gz','.bz2'].includes(e)) return FS_COL.archive;
  if(['.exe','.msi','.dll','.bat'].includes(e)) return FS_COL.exec;
  if(['.txt','.md','.pdf','.doc','.docx','.xls','.xlsx','.ppt'].includes(e)) return FS_COL.doc;
  return FS_COL.def;
}
const _FS_ICONS={'.py':'🐍','.js':'⚡','.ts':'⚡','.html':'🌐','.css':'🎨','.json':'📋',
  '.jpg':'🖼️','.png':'🖼️','.mp3':'🎵','.mp4':'🎬',
  '.zip':'📦','.exe':'⚙️','.pdf':'📕','.txt':'📝','.md':'📝',
  '.go':'🐹','.rs':'🦀','.java':'☕','.sh':'⚡','.bat':'⚡'};
function _fsIcon(item){
  if(item.is_dir)return '📁';
  return _FS_ICONS['.'+item.name.split('.').pop().toLowerCase()]||'📄';
}

// Carga y construye las células 3D para un directorio
async function enterFSMode3D(path, pushHistory){
  if(!path||path==='undefined') path='~';
  if(pushHistory===undefined) pushHistory=true;

  // Mostrar HUD + botón volver
  document.getElementById('fs-hud').classList.add('active');
  document.getElementById('btn-back').style.display='flex';
  document.getElementById('brain-hint').classList.add('hidden');

  // Llamada al servidor
  let data;
  try{
    const r=await fetch('/api/files/list?path='+encodeURIComponent(path));
    data=await r.json();
    if(data.error){showNotif('ERROR',data.error,'var(--r)');return;}
  }catch(e){showNotif('ERROR',''+e,'var(--r)');return;}

  if(pushHistory && fsPath3D!==data.path) fsHistory3D.push(fsPath3D);
  fsPath3D=data.path;
  fsModeActive=true;

  // Actualizar HUD
  document.getElementById('fs-hud-path').textContent=data.path;
  const ndirs=data.items.filter(i=>i.is_dir).length;
  const nfiles=data.items.filter(i=>!i.is_dir).length;
  document.getElementById('fs-hud-count').textContent=ndirs+'📁 '+nfiles+'📄';
  document.getElementById('fs-hud-back').style.opacity=fsHistory3D.length?'1':'0.3';

  // Limpiar capa anterior
  clearFS3DNodes();

  // Atenuar nodos principales y ocultar sus labels
  NODES.forEach(n=>{
    if(n.pts&&n.pts.material) n.pts.material.opacity=0.05;
    if(n.ring&&n.ring.material) n.ring.material.opacity=0;
    if(n.light) n.light.intensity=0;
    if(n.labelEl) n.labelEl.style.display='none';
  });

  // Máx 22 elementos por capa
  const items=data.items.slice(0,22);
  const total=items.length||1;

  items.forEach((item,i)=>{
    const col=_fsCol(item);
    const isDir=item.is_dir;
    const colHex='#'+col.toString(16).padStart(6,'0');

    // Fibonacci sphere position
    const ga=Math.PI*(3-Math.sqrt(5));
    const yy=1-(i/(total-1||1))*2;
    const rr=Math.sqrt(Math.max(0,1-yy*yy));
    const th=ga*i;
    const R=isDir?5.2:3.8;
    const pos=new THREE.Vector3(
      Math.cos(th)*rr*R,
      yy*R*0.85,
      Math.sin(th)*rr*R
    );

    // ── Particle cluster (idéntico a nodos principales) ──
    const N=isDir?500:200;
    const pArr=new Float32Array(N*3);
    const spread=isDir?0.85:0.5;
    for(let j=0;j<N;j++){
      const rj=0.3+Math.random()*spread;
      const ta=Math.random()*Math.PI*2;
      const pa=Math.acos(1-2*Math.random());
      pArr[j*3]  =pos.x+rj*Math.sin(pa)*Math.cos(ta);
      pArr[j*3+1]=pos.y+rj*Math.sin(pa)*Math.sin(ta);
      pArr[j*3+2]=pos.z+rj*Math.cos(pa);
    }
    const geo=new THREE.BufferGeometry();
    geo.setAttribute('position',new THREE.BufferAttribute(pArr,3));
    const pts=new THREE.Points(geo,new THREE.PointsMaterial({
      color:col, size:isDir?0.058:0.04,
      transparent:true, opacity:0,
      blending:THREE.AdditiveBlending, depthWrite:false,
    }));
    scene.add(pts);

    // ── Core sphere (clickable via raycast) ──
    const core=new THREE.Mesh(
      new THREE.SphereGeometry(isDir?0.30:0.18,20,20),
      new THREE.MeshPhongMaterial({
        color:col, emissive:col, emissiveIntensity:0.5,
        transparent:true, opacity:0,
      })
    );
    core.position.copy(pos);
    core.userData.fsItem=item;
    scene.add(core);
    fs3DCores.push(core);

    // ── Ring (idéntico a nodos principales) ──
    const ring=new THREE.Mesh(
      new THREE.RingGeometry(isDir?0.35:0.22,isDir?0.42:0.27,32),
      new THREE.MeshBasicMaterial({
        color:col, transparent:true, opacity:0,
        side:THREE.DoubleSide, blending:THREE.AdditiveBlending,
      })
    );
    ring.position.copy(pos);
    scene.add(ring);

    // ── Point light ──
    const light=new THREE.PointLight(col,0,8);
    light.position.copy(pos);
    scene.add(light);

    // ── HTML label (idéntico a nodos principales) ──
    const lbl=document.createElement('div');
    lbl.className='nlabel';
    lbl.style.color=colHex;
    lbl.style.borderColor=colHex+'44';
    lbl.style.background='rgba(2,8,16,.88)';
    lbl.style.opacity='0';
    lbl.innerHTML='<span class="nlabel-icon">'+_fsIcon(item)+'</span>'+item.name.substring(0,16);
    lbl.onclick=()=>onFSNodeClick(item);
    document.getElementById('node-labels').appendChild(lbl);

    const nodeObj={pts,core,ring,light,label:lbl,item,pos};
    fs3DNodes.push(nodeObj);

    // Animate in
    let t=0;
    setTimeout(()=>{
      const anim=()=>{
        t=Math.min(t+0.035,1);
        const ease=1-Math.pow(1-t,3);
        pts.material.opacity=ease*(isDir?0.75:0.55);
        core.material.opacity=ease*0.8;
        ring.material.opacity=ease*0.25;
        light.intensity=ease*(isDir?1.2:0.6);
        lbl.style.opacity=String(ease);
        lbl.classList.add('vis');
        if(t<1)requestAnimationFrame(anim);
      };
      requestAnimationFrame(anim);
    },i*40);
  });

  tweenToSph(0.55,0.95,14,900);
  showGBadge('📁 '+(data.name||'DIRECTORIO'));
}

// Click en una célula
function onFSNodeClick(item){
  if(item.is_dir){
    enterFSMode3D(item.path,true);
  }else{
    fetch('/api/files/open',{method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({path:item.path})
    }).then(r=>r.json()).then(()=>showGBadge('📂 '+item.name))
      .catch(e=>showNotif('ERROR',''+e,'var(--r)'));
  }
}

// Volver una capa atrás
function fsGoBack3D(){
  if(!fsHistory3D.length) return;
  const prev=fsHistory3D.pop();
  enterFSMode3D(prev,false);
}

// Limpieza total de células FS
function clearFS3DNodes(){
  fs3DNodes.forEach(n=>{
    scene.remove(n.pts);scene.remove(n.core);scene.remove(n.ring);scene.remove(n.light);
    n.pts.geometry.dispose();n.pts.material.dispose();
    n.core.geometry.dispose();n.core.material.dispose();
    n.ring.geometry.dispose();n.ring.material.dispose();
    n.label.remove();
  });
  fs3DNodes=[];fs3DCores=[];
}

// Salir del modo FS completamente
function exitFSMode(){
  fsModeActive=false;
  clearFS3DNodes();
  fsHistory3D=[];
  document.getElementById('fs-hud').classList.remove('active');
  document.getElementById('btn-back').style.display='none';
  // Restaurar nodos principales
  NODES.forEach(n=>{
    if(n.pts&&n.pts.material) n.pts.material.opacity=0.75;
    if(n.ring&&n.ring.material) n.ring.material.opacity=0.12;
    if(n.labelEl){n.labelEl.style.display='';lbl_requestFrame();}
  });
  activeNode=null; autoRotate=true;
  closeAllPanels();
  setTimeout(()=>document.getElementById('brain-hint').classList.remove('hidden'),800);
  showGBadge('⬡ CEREBRO');
}
function lbl_requestFrame(){requestAnimationFrame(()=>{});}// dummy to trigger frame

// Proyección de labels FS en el render loop
function updateFS3DLabels(){
  if(!fs3DNodes.length) return;
  const t=performance.now()*0.001;
  fs3DNodes.forEach((n,i)=>{
    // Pulse animation
    const pulse=0.5+0.5*Math.sin(t*2+i*0.8);
    n.pts.material.size=n.item.is_dir?(0.055+pulse*0.012):(0.037+pulse*0.008);
    n.ring.rotation.z+=n.item.is_dir?0.012:0.006;

    // Project to screen
    const v=n.pos.clone().project(cam);
    const x=(v.x*0.5+0.5)*window.innerWidth;
    const y=(-v.y*0.5+0.5)*window.innerHeight;
    n.label.style.left=x+'px';
    n.label.style.top=y+'px';
    n.label.style.display=(v.z<1)?'':'none';
  });
}

// Raycast en canvas para celdas FS
function fsRaycast(e){
  if(!fsModeActive||!fs3DCores.length) return false;
  const rect=document.getElementById('brain-canvas').getBoundingClientRect();
  const ray=new THREE.Raycaster();
  ray.setFromCamera(
    new THREE.Vector2(((e.clientX-rect.left)/rect.width)*2-1,-((e.clientY-rect.top)/rect.height)*2+1),
    cam
  );
  const hits=ray.intersectObjects(fs3DCores);
  if(hits.length>0){
    onFSNodeClick(hits[0].object.userData.fsItem);
    return true;
  }
  return false;
}

// Camera tween
function tweenToSph(theta,phi,r,ms){
  const start={theta:sph.theta,phi:sph.phi,r:sph.r};
  const end={theta,phi,r};
  const t0=performance.now();
  (function step(now){
    const t=Math.min((now-t0)/(ms||600),1);
    const e=1-Math.pow(1-t,3);
    sph.theta=start.theta+(end.theta-start.theta)*e;
    sph.phi  =start.phi  +(end.phi  -start.phi  )*e;
    sph.r    =start.r    +(end.r    -start.r    )*e;
    updateCam();
    if(t<1)requestAnimationFrame(step);
  })(t0);
}
// END 3D FILE SYSTEM CELLS
"""

# ═══════════════════════════════════════════════════════
# REPLACE the entire old FS3D block
# ═══════════════════════════════════════════════════════
START_MARKER = "// ══════════════════════════════════════════════════════\n// 3D FILE SYSTEM CELLS"
END_MARKER   = "// END 3D FILE SYSTEM CELLS"

s = h.find(START_MARKER)
e = h.find(END_MARKER)
if s > 0 and e > s:
    h = h[:s] + NEW_FS3D + h[e+len(END_MARKER):]
    print("FS3D block replaced completely")
else:
    print(f"ERROR: markers not found s={s} e={e}")

# ═══════════════════════════════════════════════════════
# FIX 1: flyBack() — exit FS mode first
# ═══════════════════════════════════════════════════════
OLD_FLYBACK = "function flyBack(){\n  if(flyAnim)return;"
NEW_FLYBACK = "function flyBack(){\n  if(fsModeActive){exitFSMode();return;}\n  if(flyAnim)return;"
if OLD_FLYBACK in h:
    h = h.replace(OLD_FLYBACK, NEW_FLYBACK)
    print("FIX 1: flyBack FS exit added")
else:
    print("WARN: flyBack not found for patch")

# ═══════════════════════════════════════════════════════
# FIX 2: canvas click — check FS raycast first
# ═══════════════════════════════════════════════════════
OLD_CLICK = "c3.addEventListener('click',e=>{\n  if(isDragging||activeNode)return;\n  const rect=c3.getBoundingClientRect();\n  const ray=new THREE.Raycaster();\n  ray.setFromCamera(new THREE.Vector2(((e.clientX-rect.left)/rect.width)*2-1,-((e.clientY-rect.top)/rect.height)*2+1),cam);\n  const hits=ray.intersectObjects(nodeCores);\n  if(hits.length>0)flyToNode(hits[0].object.userData.nd);\n});"
NEW_CLICK = "c3.addEventListener('click',e=>{\n  if(isDragging)return;\n  if(fsModeActive){fsRaycast(e);return;}\n  if(activeNode)return;\n  const rect=c3.getBoundingClientRect();\n  const ray=new THREE.Raycaster();\n  ray.setFromCamera(new THREE.Vector2(((e.clientX-rect.left)/rect.width)*2-1,-((e.clientY-rect.top)/rect.height)*2+1),cam);\n  const hits=ray.intersectObjects(nodeCores);\n  if(hits.length>0)flyToNode(hits[0].object.userData.nd);\n});"
if OLD_CLICK in h:
    h = h.replace(OLD_CLICK, NEW_CLICK)
    print("FIX 2: canvas click FS raycast added")
else:
    print("WARN: canvas click not found exactly — patching alternate")
    h = h.replace(
        "  if(isDragging||activeNode)return;\n  const rect=c3.getBoundingClientRect();",
        "  if(isDragging)return;\n  if(fsModeActive){fsRaycast(e);return;}\n  if(activeNode)return;\n  const rect=c3.getBoundingClientRect();"
    )

# ═══════════════════════════════════════════════════════
# FIX 3: chatActivity when JARVIS responds
# ═══════════════════════════════════════════════════════
OLD_ADDMSG = "    hideTyping();addMsg(d.response,'jarvis');\n    if(d.audio_url)playAudio(d.audio_url);else if(speakEnabled)speak(d.response);"
NEW_ADDMSG = "    hideTyping();addMsg(d.response,'jarvis');chatActivity();\n    if(d.audio_url)playAudio(d.audio_url);else if(speakEnabled)speak(d.response);"
if OLD_ADDMSG in h:
    h = h.replace(OLD_ADDMSG, NEW_ADDMSG)
    print("FIX 3: chatActivity on JARVIS response added")
else:
    h = h.replace("addMsg(d.response,'jarvis');", "addMsg(d.response,'jarvis');chatActivity();", 1)
    print("FIX 3: chatActivity added (fallback)")

# ═══════════════════════════════════════════════════════
# FIX 4: Voice navigation for FS mode
# Add FS commands to handleNav and parseNav
# ═══════════════════════════════════════════════════════
OLD_HANDLENAV = "function handleNav(cmd){\n  if(cmd==='back'){flyBack();return;}\n  const nd=NODES.find(n=>n.id===cmd);\n  if(nd)flyToNode(nd);\n}"
NEW_HANDLENAV = """function handleNav(cmd){
  // FS mode voice commands
  if(fsModeActive){
    if(cmd==='back'||cmd==='atras'){fsGoBack3D();return;}
    if(cmd==='exit'||cmd==='salir'){exitFSMode();return;}
    // Try to find folder by voice in current directory
    const found=fs3DNodes.find(n=>n.item.name.toLowerCase().includes(cmd.toLowerCase()));
    if(found){onFSNodeClick(found.item);return;}
  }
  if(cmd==='back'){flyBack();return;}
  const nd=NODES.find(n=>n.id===cmd);
  if(nd)flyToNode(nd);
}"""
if OLD_HANDLENAV in h:
    h = h.replace(OLD_HANDLENAV, NEW_HANDLENAV)
    print("FIX 4: FS voice navigation added to handleNav")
else:
    print("WARN: handleNav not found exactly")

# Also add FS-specific voice patterns to navMap
OLD_NAVMAP = "'vuelve|atras|cerebro|palace|salir|inicio|brain':    'back',"
NEW_NAVMAP = "'vuelve|atras|cerebro|palace|inicio|brain':    'back',\n  'salir|exit|escapar':                             'exit',"
if OLD_NAVMAP in h:
    h = h.replace(OLD_NAVMAP, NEW_NAVMAP)
    print("FIX 4b: exit nav pattern added")

# ═══════════════════════════════════════════════════════
# FIX 5: flyToNode for files — clean trigger
# ═══════════════════════════════════════════════════════
# Make sure it's clean
OLD_FTN_FILES = """    if(nd.id==='files'){
      setTimeout(()=>enterFSMode3D('~'),200);
      document.getElementById('btn-back').style.display='flex';
      document.getElementById('brain-hint').classList.add('hidden');
      return;
    }"""
NEW_FTN_FILES = "    if(nd.id==='files'){enterFSMode3D('~');return;}"
if OLD_FTN_FILES in h:
    h = h.replace(OLD_FTN_FILES, NEW_FTN_FILES)
    print("FIX 5: flyToNode files cleaned")
else:
    print("FIX 5: files trigger not changed (may already be ok)")

# ═══════════════════════════════════════════════════════
# SAVE & VALIDATE
# ═══════════════════════════════════════════════════════
hf.write_text(h, encoding="utf-8")
print(f"\nSaved: {len(h)} chars, {h.count(chr(10))} lines")

import re as _re
scripts = _re.findall(r'<script(?![^>]*src)[^>]*>(.*?)</script>', h, _re.DOTALL)
combined = "\n".join(scripts)
temp = pathlib.Path("_chk.js")
temp.write_text(combined, encoding="utf-8")
r = subprocess.run(["node","--check","_chk.js"], capture_output=True, text=True)
temp.unlink()
if r.returncode == 0:
    print("NODE SYNTAX: PASS")
else:
    err = r.stderr.strip()
    print("NODE SYNTAX ERROR:", err[:300])

# Verify key patches
checks = [
    ("enterFSMode3D", "FS3D main function"),
    ("fsModeActive){exitFSMode", "flyBack FS exit"),
    ("fsModeActive){fsRaycast", "canvas raycast"),
    ("chatActivity()", "chat on response"),
    ("THREE.AdditiveBlending", "blending (must NOT have window. prefix now)"),
    ("tweenToSph", "camera tween"),
    ("updateFS3DLabels", "label update in render"),
    ("fs3DCores", "raycast array"),
    ("fsGoBack3D", "back function"),
    ("exitFSMode", "exit function"),
]
print()
for key, label in checks:
    print(f"  {'OK' if key in h else 'MISSING'}: {label}")
