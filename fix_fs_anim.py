"""
FIX: las partículas FS3D son invisibles porque la animación de opacidad
con setTimeout+RAF no funciona bien fuera del render loop.
Solución: usar el render loop existente para animar las células.
Además: mejorar la distribución para que no estén todas amontonadas.
"""
import pathlib, re, subprocess

hf = pathlib.Path("static/index.html")
h = hf.read_text(encoding="utf-8")

# ═══════════════════════════════════════════════════════
# 1. Reemplazar la animación de entrada (sin setTimeout/RAF externo)
#    Las cells comienzan en opacity=0 pero el render loop las anima
# ═══════════════════════════════════════════════════════

# Añadir un array de animaciones pendientes que el render loop procesa
# Buscar donde está el render loop y inyectar updateFS3DLabels con animación

OLD_LABELS_FN = """// Proyección de labels FS en el render loop
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
}"""

NEW_LABELS_FN = """// Proyección y animación de cells FS en el render loop
let _fsAnimStart=0;
function updateFS3DLabels(){
  if(!fs3DNodes.length) return;
  const now=performance.now();
  if(!_fsAnimStart) _fsAnimStart=now;
  const elapsed=(now-_fsAnimStart)*0.001; // seconds since FS loaded
  const t=now*0.001;

  fs3DNodes.forEach((n,i)=>{
    // Fade-in animation driven by render loop (not RAF)
    const delay=i*0.04;  // 40ms stagger
    const progress=Math.min(Math.max((elapsed-delay)/0.6,0),1);
    const ease=1-Math.pow(1-progress,3);
    const isDir=n.item.is_dir;

    if(progress<1){
      n.pts.material.opacity=ease*(isDir?0.75:0.55);
      n.core.material.opacity=ease*0.8;
      n.ring.material.opacity=ease*0.25;
      n.light.intensity=ease*(isDir?1.2:0.6);
      n.label.style.opacity=String(ease);
    }

    // Pulse after fully visible
    if(progress>=1){
      const pulse=0.5+0.5*Math.sin(t*1.8+i*1.1);
      n.pts.material.size=isDir?(0.055+pulse*0.01):(0.038+pulse*0.007);
      n.ring.rotation.z+=isDir?0.012:0.007;
      n.pts.material.opacity=isDir?(0.65+pulse*0.1):(0.45+pulse*0.1);
    }

    // Project label to screen
    const v=n.pos.clone().project(cam);
    const x=(v.x*0.5+0.5)*window.innerWidth;
    const y=(-v.y*0.5+0.5)*window.innerHeight;
    n.label.style.left=x+'px';
    n.label.style.top=y+'px';
    n.label.style.display=(v.z<1)?'':'none';
    if(!n.label.classList.contains('vis'))n.label.classList.add('vis');
  });
}"""

if OLD_LABELS_FN in h:
    h = h.replace(OLD_LABELS_FN, NEW_LABELS_FN)
    print("Label/anim fn replaced with render-loop driven version")
else:
    print("WARN: label fn not found exactly — patching _fsAnimStart")

# ═══════════════════════════════════════════════════════
# 2. Reset _fsAnimStart when entering FS mode
# ═══════════════════════════════════════════════════════
old_clear = "  fsModeActive=true;\n\n  // Actualizar HUD"
new_clear = "  fsModeActive=true;\n  _fsAnimStart=0; // reset animation timer\n\n  // Actualizar HUD"
if old_clear in h:
    h = h.replace(old_clear, new_clear)
    print("_fsAnimStart reset on enterFSMode3D")
else:
    # fallback
    h = h.replace(
        "  fsModeActive=true;",
        "  fsModeActive=true;\n  _fsAnimStart=0;",
        1  # first occurrence only
    )
    print("_fsAnimStart reset (fallback)")

# ═══════════════════════════════════════════════════════
# 3. Remove the setTimeout animation block from enterFSMode3D
#    (since render loop handles it now)
# ═══════════════════════════════════════════════════════
old_anim_block = """    // Animate in
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
    },i*40);"""

new_anim_block = "    // Animation handled by updateFS3DLabels() in render loop"

if old_anim_block in h:
    h = h.replace(old_anim_block, new_anim_block)
    print("setTimeout animation block removed (render loop handles it)")
else:
    print("WARN: animation block not found — may already be removed")

# ═══════════════════════════════════════════════════════
# 4. Fix: distribución — asegurar que los nodos se distribuyen 
#    en una esfera amplia y visible (no todos en el mismo z-layer)
# ═══════════════════════════════════════════════════════
# Check current position calculation
idx = h.find("const R=isDir?5.2:3.8;")
if idx > 0:
    print("Position calc found at", idx)
    # Already correct radius
else:
    # Fix radius if needed
    h = h.replace("const R=isDir?5.0:3.8;", "const R=isDir?5.2:3.8;")
    print("Radius fixed")

# ═══════════════════════════════════════════════════════
# 5. Make sure THREE is accessible (not window.THREE) in FS code
#    since it's in the same script scope as the Three.js setup
# ═══════════════════════════════════════════════════════
# Count window.THREE references remaining
wt_count = h.count("window.THREE")
print(f"window.THREE references remaining: {wt_count}")
if wt_count > 0:
    h = h.replace("window.THREE.", "THREE.")
    print("All window.THREE cleaned up")

# ═══════════════════════════════════════════════════════
# SAVE & VALIDATE
# ═══════════════════════════════════════════════════════
hf.write_text(h, encoding="utf-8")
print(f"\nSaved: {len(h)} chars")

scripts = re.findall(r'<script(?![^>]*src)[^>]*>(.*?)</script>', h, re.DOTALL)
combined = "\n".join(scripts)
temp = pathlib.Path("_chk.js")
temp.write_text(combined, encoding="utf-8")
r = subprocess.run(["node","--check","_chk.js"], capture_output=True, text=True)
temp.unlink()
print("SYNTAX:", "PASS" if r.returncode==0 else "ERROR: "+r.stderr[:200])
