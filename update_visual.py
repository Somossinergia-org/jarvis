"""
ONE SHOT — Everything the user wants:
1. All particle clouds ALWAYS spin (self-rotation on pts.rotation)
2. FS3D shows 40 items max (was 22)
3. Extended system info: network, processes, temps, uptime
4. Main brain nodes ALSO have ring that keeps spinning + particle self-rotation
5. FS3D cells identical visual to brain nodes (already done)
"""
import pathlib, re, subprocess

hf = pathlib.Path("static/index.html")
h = hf.read_text(encoding="utf-8")

# ══════════════════════════════════════════════
# 1. MAIN BRAIN — particles always self-rotate
# Replace node animation in render loop
# ══════════════════════════════════════════════
OLD_NODE_ANIM = """  // Animate nodes
  NODES.forEach((nd,i)=>{
    const t=frame*.02+i*1.2;
    const pulse=.5+.5*Math.sin(t);
    const hov=hoveredNode===nd;
    const act=activeNode===nd;
    const speaking=window.jSpeaking;
    nd.pts.material.opacity=hov?.95:act?.85:(.5+pulse*.15)*(speaking?1.3:1);
    nd.pts.material.size=hov?.07:.055;
    nd.core.material.emissiveIntensity=hov?1.2:act?.8:(.3+pulse*.25);
    nd.ring.rotation.z+=hov?.04:.01;
    nd.ring.material.opacity=hov?.6:(.12+pulse*.08);
    nd.light.intensity=hov?1.5:act?.8:0;
    // Labels
    if(!activeNode&&nd.labelEl){
      const v=nd.pos.clone().project(cam);
      const x=(v.x+1)/2*window.innerWidth;
      const y=(-v.y+1)/2*window.innerHeight;
      nd.labelEl.style.left=x+'px';nd.labelEl.style.top=y+'px';
      nd.labelEl.classList.toggle('vis',true);
    }else if(nd.labelEl){nd.labelEl.classList.remove('vis');}
  });"""

NEW_NODE_ANIM = """  // Animate nodes — ALWAYS spinning, always alive
  NODES.forEach((nd,i)=>{
    const t=frame*.02+i*1.2;
    const pulse=.5+.5*Math.sin(t);
    const hov=hoveredNode===nd;
    const act=activeNode===nd;
    const speaking=window.jSpeaking;
    // Particle cloud — always self-rotating
    nd.pts.rotation.y+=.0018+i*.0003;
    nd.pts.rotation.x+=.0006+i*.0001;
    nd.pts.material.opacity=hov?.95:act?.85:(.55+pulse*.18)*(speaking?1.4:1);
    nd.pts.material.size=hov?.075:(.052+pulse*.008);
    // Core pulse
    nd.core.material.emissiveIntensity=hov?1.5:act?1.0:(.35+pulse*.35);
    nd.core.rotation.y+=.008;
    // Ring — always spinning (faster when hovered)
    nd.ring.rotation.z+=hov?.06:.022;
    nd.ring.rotation.x+=.006;
    nd.ring.material.opacity=hov?.7:(.15+pulse*.12);
    nd.light.intensity=hov?2.0:act?1.0:(.1+pulse*.2);
    // Labels — show always (even when panel active, just update position)
    if(nd.labelEl){
      const v=nd.pos.clone().project(cam);
      const x=(v.x+1)/2*window.innerWidth;
      const y=(-v.y+1)/2*window.innerHeight;
      nd.labelEl.style.left=x+'px';nd.labelEl.style.top=y+'px';
      // Show labels unless FS mode is active (FS has its own labels)
      nd.labelEl.classList.toggle('vis',!fsModeActive&&v.z<1);
    }
  });"""

if OLD_NODE_ANIM in h:
    h = h.replace(OLD_NODE_ANIM, NEW_NODE_ANIM)
    print("1. Brain node animation: always-spinning DONE")
else:
    print("WARN: could not find node anim block exactly")

# ══════════════════════════════════════════════
# 2. FS3D — self-rotation in updateFS3DLabels
# ══════════════════════════════════════════════
OLD_FS_PULSE = """    // Pulse after fully visible
    if(progress>=1){
      const pulse=0.5+0.5*Math.sin(t*1.8+i*1.1);
      n.pts.material.size=isDir?(0.055+pulse*0.01):(0.038+pulse*0.007);
      n.ring.rotation.z+=isDir?0.012:0.007;
      n.pts.material.opacity=isDir?(0.65+pulse*0.1):(0.45+pulse*0.1);
    }"""

NEW_FS_PULSE = """    // Always rotating — regardless of animation state
    n.pts.rotation.y+=0.0022+i*0.0002;
    n.pts.rotation.x+=0.0008;
    n.core.rotation.y+=0.01;
    n.ring.rotation.z+=isDir?0.018:0.010;
    n.ring.rotation.x+=0.004;
    if(progress>=1){
      const pulse=0.5+0.5*Math.sin(t*1.8+i*1.1);
      n.pts.material.size=isDir?(0.055+pulse*0.012):(0.038+pulse*0.008);
      n.pts.material.opacity=isDir?(0.65+pulse*0.12):(0.45+pulse*0.12);
      n.light.intensity=(0.3+pulse*0.4)*(isDir?1.2:0.7);
    }"""

if OLD_FS_PULSE in h:
    h = h.replace(OLD_FS_PULSE, NEW_FS_PULSE)
    print("2. FS3D cells: always-spinning DONE")
else:
    print("WARN: FS pulse block not found")

# ══════════════════════════════════════════════
# 3. FS3D — increase max items from 22 to 40
# ══════════════════════════════════════════════
h = h.replace("const items=data.items.slice(0,22);", "const items=data.items.slice(0,40);")
print("3. FS3D max items: 22→40 DONE")

# ══════════════════════════════════════════════
# 4. Extended system info in the header
#    Add NET, processes, uptime to header bar
# ══════════════════════════════════════════════
# Add extra stat spans to the header
OLD_HDR_STATS = """      <div class="hstat"><div class="hsd" style="background:#af9"></div><span id="v-disk">DISCO --%</span></div>
    </div>"""

NEW_HDR_STATS = """      <div class="hstat"><div class="hsd" style="background:#af9"></div><span id="v-disk">DISCO --%</span></div>
      <div class="hstat"><div class="hsd" style="background:#f80"></div><span id="v-net">RED --</span></div>
      <div class="hstat"><div class="hsd" style="background:#f55"></div><span id="v-proc">PROC --</span></div>
      <div class="hstat"><div class="hsd" style="background:#5ff"></div><span id="v-up">UP --</span></div>
    </div>"""

if OLD_HDR_STATS in h:
    h = h.replace(OLD_HDR_STATS, NEW_HDR_STATS)
    print("4. Header: NET/PROC/UPTIME stats added DONE")
else:
    print("WARN: Header stats not found")

# ══════════════════════════════════════════════
# 5. Update updateSysStats to fetch extended info
# ══════════════════════════════════════════════
OLD_SYS_STATS = """async function updateSysStats(){
  try{const d=await fetch('/api/system').then(r=>r.json());
    document.getElementById('v-cpu').textContent='CPU '+d.cpu_uso_porcentaje+'%';
    document.getElementById('v-ram').textContent='RAM '+d.ram_uso_porcentaje+'%';
    document.getElementById('v-disk').textContent='DISCO '+d.disco_uso_porcentaje+'%';
  }catch(e){}
}"""

NEW_SYS_STATS = """async function updateSysStats(){
  try{
    const d=await fetch('/api/system/extended').then(r=>r.json());
    document.getElementById('v-cpu').textContent='CPU '+d.cpu+'%';
    document.getElementById('v-ram').textContent='RAM '+d.ram+'%';
    document.getElementById('v-disk').textContent='DISCO '+d.disk+'%';
    const ne=document.getElementById('v-net');
    if(ne)ne.textContent='↑'+d.net_up+' ↓'+d.net_dn;
    const pe=document.getElementById('v-proc');
    if(pe)pe.textContent='PROC '+d.procs;
    const ue=document.getElementById('v-up');
    if(ue)ue.textContent='UP '+d.uptime;
    // Also update system panel
    const sc=document.getElementById('sp-cpu');if(sc)sc.textContent=d.cpu+'%';
    const sr=document.getElementById('sp-ram');if(sr)sr.textContent=d.ram+'%';
    const sd=document.getElementById('sp-disk');if(sd)sd.textContent=d.disk+'%';
    const bc=document.getElementById('sb-cpu');if(bc)bc.style.width=d.cpu+'%';
    const br=document.getElementById('sb-ram');if(br)br.style.width=d.ram+'%';
    const bd=document.getElementById('sb-disk');if(bd)bd.style.width=d.disk+'%';
  }catch(e){
    // fallback to old endpoint
    try{const d=await fetch('/api/system').then(r=>r.json());
      document.getElementById('v-cpu').textContent='CPU '+d.cpu_uso_porcentaje+'%';
      document.getElementById('v-ram').textContent='RAM '+d.ram_uso_porcentaje+'%';
      document.getElementById('v-disk').textContent='DISCO '+d.disco_uso_porcentaje+'%';
    }catch(e2){}
  }
}"""

if OLD_SYS_STATS in h:
    h = h.replace(OLD_SYS_STATS, NEW_SYS_STATS)
    print("5. updateSysStats: extended API DONE")
else:
    print("WARN: updateSysStats not found exactly")

# ══════════════════════════════════════════════
# 6. SISTEMA panel — add more stats (net, procs, uptime, temp)
# ══════════════════════════════════════════════
OLD_SYS_PANEL_END = """        <div class="np-section">
          <div class="np-slabel" style="color:#ff3355;">CONTROLES</div>"""

NEW_SYS_PANEL_END = """        <div class="np-section">
          <div class="np-slabel" style="color:#ff3355;">RED & PROCESOS</div>
          <div class="np-stat">
            <div class="np-stat-row"><span class="np-skey">SUBIDA</span><span class="np-sval" id="sp-net-up" style="color:#ffb300;">--</span></div>
            <div class="np-stat-row"><span class="np-skey">BAJADA</span><span class="np-sval" id="sp-net-dn" style="color:#00d4ff;">--</span></div>
            <div class="np-stat-row"><span class="np-skey">PROCESOS</span><span class="np-sval" id="sp-procs" style="color:#00ff88;">--</span></div>
            <div class="np-stat-row"><span class="np-skey">UPTIME</span><span class="np-sval" id="sp-uptime" style="color:#9955ff;">--</span></div>
            <div class="np-stat-row"><span class="np-skey">TEMPERATURA</span><span class="np-sval" id="sp-temp" style="color:#ff3355;">--</span></div>
          </div>
        </div>
        <div class="np-section">
          <div class="np-slabel" style="color:#ff3355;">CONTROLES</div>"""

if OLD_SYS_PANEL_END in h:
    h = h.replace(OLD_SYS_PANEL_END, NEW_SYS_PANEL_END, 1)
    print("6. Sistema panel: extended stats DONE")
else:
    print("WARN: Sistema panel section not found")

# ══════════════════════════════════════════════
# 7. Update refreshSysPanel to show extended stats  
# ══════════════════════════════════════════════
OLD_REFRESH = """async function refreshSysPanel(){
  try{
    const d=await fetch('/api/system').then(r=>r.json());
    const cpu=d.cpu_uso_porcentaje||0,ram=d.ram_uso_porcentaje||0,disk=d.disco_uso_porcentaje||0;
    ['sp-cpu','sp-ram','sp-disk'].forEach((id,i)=>{
      const el=document.getElementById(id);if(el)el.textContent=[cpu,ram,disk][i]+'%';});
    [['sb-cpu',cpu],['sb-ram',ram],['sb-disk',disk]].forEach(([id,v])=>{
      const el=document.getElementById(id);if(el)el.style.width=v+'%';});
  }catch(e){}
}"""

NEW_REFRESH = """async function refreshSysPanel(){
  try{
    const d=await fetch('/api/system/extended').then(r=>r.json());
    [['sp-cpu',d.cpu],['sp-ram',d.ram],['sp-disk',d.disk]].forEach(([id,v])=>{
      const el=document.getElementById(id);if(el)el.textContent=(v||0)+'%';});
    [['sb-cpu',d.cpu],['sb-ram',d.ram],['sb-disk',d.disk]].forEach(([id,v])=>{
      const el=document.getElementById(id);if(el)el.style.width=(v||0)+'%';});
    // Extended
    const map={
      'sp-net-up': d.net_up, 'sp-net-dn': d.net_dn,
      'sp-procs': d.procs, 'sp-uptime': d.uptime, 'sp-temp': d.temp
    };
    Object.entries(map).forEach(([id,val])=>{
      const el=document.getElementById(id);if(el&&val)el.textContent=val;
    });
  }catch(e){
    try{const d=await fetch('/api/system').then(r=>r.json());
      const cpu=d.cpu_uso_porcentaje||0,ram=d.ram_uso_porcentaje||0,disk=d.disco_uso_porcentaje||0;
      ['sp-cpu','sp-ram','sp-disk'].forEach((id,i)=>{const el=document.getElementById(id);if(el)el.textContent=[cpu,ram,disk][i]+'%';});
      [['sb-cpu',cpu],['sb-ram',ram],['sb-disk',disk]].forEach(([id,v])=>{const el=document.getElementById(id);if(el)el.style.width=v+'%';});
    }catch(e2){}
  }
}"""

if OLD_REFRESH in h:
    h = h.replace(OLD_REFRESH, NEW_REFRESH)
    print("7. refreshSysPanel: extended DONE")
else:
    print("WARN: refreshSysPanel not found")

# Save HTML
hf.write_text(h, encoding="utf-8")
print(f"\nHTML saved: {len(h)} chars")

# Validate JS
scripts = re.findall(r'<script(?![^>]*src)[^>]*>(.*?)</script>', h, re.DOTALL)
combined = "\n".join(scripts)
temp = pathlib.Path("_chk.js")
temp.write_text(combined, encoding="utf-8")
r = subprocess.run(["node","--check","_chk.js"], capture_output=True, text=True)
temp.unlink()
print("JS SYNTAX:", "PASS" if r.returncode==0 else "FAIL:\n"+r.stderr[:300])
