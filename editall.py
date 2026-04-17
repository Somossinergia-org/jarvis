"""
JARVIS MIND PALACE — Comprehensive edit:
1. server.py: Spotify media key (ctypes, instant), /api/files/list, /api/files/open
2. index.html: Holographic file browser (full system), layered navigation
"""
import pathlib, re, sys

# ══════════════════════════════
# SERVER.PY
# ══════════════════════════════
sf = pathlib.Path("server.py")
sc = sf.read_text(encoding="utf-8")

NEW_STARTUP = '''
@app.post("/api/auth/startup")
async def auth_startup():
    """Startup biometrico: Spotify play via VK_MEDIA_PLAY_PAUSE + VS Code."""
    import asyncio, ctypes, time as _t

    async def _run():
        # 1. Abrir Spotify
        open_application("spotify")
        await asyncio.sleep(2.0)
        # 2. Play global via media key (sin necesitar foco en Spotify)
        try:
            u32 = ctypes.windll.user32
            u32.keybd_event(0xB3, 0, 0, 0)   # VK_MEDIA_PLAY_PAUSE down
            _t.sleep(0.08)
            u32.keybd_event(0xB3, 0, 2, 0)   # key up
            print("[Startup] PLAY via media key: OK")
        except Exception as ex:
            print(f"[Startup] media key: {ex}")
        # 3. VS Code
        await asyncio.sleep(0.6)
        open_application("code")
        print("[Startup] Secuencia OK")

    asyncio.create_task(_run())
    return {"message": "OK"}


@app.get("/api/files/list")
async def list_files(path: str = "~"):
    """Lista el contenido real de cualquier directorio del sistema."""
    import pathlib as pl
    try:
        clean = path.replace("/", "\\")
        p = pl.Path(clean).expanduser().resolve()
        if not p.exists():
            return JSONResponse({"error": f"No existe: {p}"}, status_code=404)
        items = []
        try:
            for item in sorted(p.iterdir(),
                               key=lambda x: (not x.is_dir(), x.name.lower())):
                try:
                    st = item.stat()
                    items.append({
                        "name":   item.name,
                        "path":   str(item).replace("\\", "/"),
                        "is_dir": item.is_dir(),
                        "size":   st.st_size if item.is_file() else None,
                    })
                except (PermissionError, OSError):
                    pass
        except PermissionError:
            return JSONResponse({"error": "Sin permisos"}, status_code=403)
        return {
            "path":   str(p).replace("\\", "/"),
            "parent": str(p.parent).replace("\\", "/"),
            "name":   p.name or str(p),
            "items":  items[:150],
        }
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/api/files/open")
async def open_file_ep(req: dict):
    """Abre archivo o carpeta con la app predeterminada de Windows."""
    import subprocess, pathlib as pl, os
    raw = req.get("path", "").replace("/", "\\")
    try:
        p = pl.Path(raw).resolve()
        if not p.exists():
            return JSONResponse({"error": "No existe"}, status_code=404)
        if p.is_dir():
            subprocess.Popen(["explorer", str(p)])
        else:
            os.startfile(str(p))
        return {"message": f"Abriendo: {p.name}"}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

'''

voices_marker = '@app.get("/api/voices")'
startup_marker = '@app.post("/api/auth/startup")'
files_marker = '@app.get("/api/files/list")'

# Remove existing startup + files endpoints if present
start_idx = sc.find(startup_marker)
voices_idx = sc.find(voices_marker)
if start_idx >= 0 and voices_idx > start_idx:
    sc = sc[:start_idx] + sc[voices_idx:]
    voices_idx = sc.find(voices_marker)

# Insert new endpoints before voices
sc = sc[:voices_idx] + NEW_STARTUP + sc[voices_idx:]
sf.write_text(sc, encoding="utf-8")
print(f"server.py OK: {len(sc)} chars")

# ══════════════════════════════
# INDEX.HTML
# ══════════════════════════════
hf = pathlib.Path("static/index.html")
hc = hf.read_text(encoding="utf-8")

# ── CSS to inject ──────────────────────────────────────────
FB_CSS = """
/* ── HOLOGRAPHIC FILE BROWSER ─── */
.fb-panel-box{width:min(960px,95vw);max-height:90vh;}
#fb-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(110px,1fr));gap:10px;max-height:48vh;overflow-y:auto;padding:4px 2px;scrollbar-width:thin;scrollbar-color:rgba(0,212,255,.1) transparent;}
#fb-grid::-webkit-scrollbar{width:4px;} #fb-grid::-webkit-scrollbar-thumb{background:rgba(0,212,255,.15);border-radius:2px;}
.fb-card{padding:14px 8px 11px;border-radius:12px;text-align:center;cursor:pointer;background:rgba(0,8,20,.9);border:1px solid rgba(0,212,255,.08);transition:all .18s ease;position:relative;overflow:hidden;display:flex;flex-direction:column;align-items:center;user-select:none;}
.fb-card:hover{transform:translateY(-3px) scale(1.04);}
.fb-card::after{content:'';position:absolute;inset:0;background:linear-gradient(135deg,rgba(255,255,255,.025),transparent);border-radius:12px;pointer-events:none;}
.fb-icon{font-size:28px;margin-bottom:7px;line-height:1;filter:drop-shadow(0 0 6px currentColor);}
.fb-name{font-family:'Rajdhani',sans-serif;font-size:10px;font-weight:600;word-break:break-word;line-height:1.3;margin-bottom:2px;overflow:hidden;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;max-width:100%;}
.fb-sz{font-family:'Share Tech Mono',monospace;font-size:7px;opacity:.45;letter-spacing:.5px;}
.fb-bc-sep{color:var(--txd);margin:0 3px;}
.fb-bc-part{cursor:pointer;color:var(--c);font-family:'Share Tech Mono',monospace;font-size:9px;letter-spacing:1px;transition:color .15s;}
.fb-bc-part:hover{color:#fff;}
.fb-quick{padding:5px 10px;font-size:10px;width:auto;flex-shrink:0;}
.fb-depth-layer{display:flex;align-items:center;gap:3px;font-family:'Share Tech Mono',monospace;font-size:8px;color:var(--txd);letter-spacing:1px;}
.fb-depth-seg{width:20px;height:2px;border-radius:1px;background:rgba(0,212,255,.15);}
.fb-depth-seg.active{background:var(--c);}
"""

if "HOLOGRAPHIC FILE BROWSER" not in hc:
    hc = hc.replace("</style>", FB_CSS + "</style>", 1)
    print("CSS añadido")
else:
    print("CSS ya presente")

# ── Replace panel-files ────────────────────────────────────
OLD_PANEL_FILES_START = '  <!-- ARCHIVOS -->\n  <div class="node-panel" id="panel-files">'
OLD_PANEL_FILES_END = '  <!-- SISTEMA -->'

NEW_PANEL_FILES = '''  <!-- ARCHIVOS — HOLOGRAPHIC FILE BROWSER -->
  <div class="node-panel" id="panel-files">
    <div class="np-box fb-panel-box">
      <div class="np-inner">
        <!-- Header -->
        <div class="np-hdr" style="border-color:rgba(255,215,0,.15);">
          <div class="np-hicon">📁</div>
          <div class="np-htitle" style="color:#ffd700;">SISTEMA DE ARCHIVOS</div>
          <div id="fb-depth-wrap" class="fb-depth-layer"></div>
          <div style="flex:1;"></div>
          <button class="np-hback" id="fb-back-btn" onclick="fbGoBack()" disabled style="opacity:.4;">← ATRÁS</button>
          <button class="np-hback" onclick="flyBack()" style="margin-left:6px;">⬡ CEREBRO</button>
          <button class="np-hclose" onclick="flyBack()">✕</button>
        </div>

        <!-- Path bar + breadcrumb -->
        <div style="display:flex;align-items:center;gap:6px;margin-bottom:10px;flex-wrap:wrap;">
          <button onclick="fbGoUp()" class="npbtn fb-quick" title="Subir un nivel">⬆ SUBIR</button>
          <div id="fb-breadcrumb" style="flex:1;display:flex;align-items:center;flex-wrap:wrap;gap:2px;padding:7px 12px;background:rgba(0,212,255,.04);border:1px solid rgba(0,212,255,.1);border-radius:8px;min-height:34px;"></div>
          <button onclick="fbRefresh()" class="npbtn fb-quick" title="Actualizar">↺</button>
        </div>

        <!-- Quick access drives / folders -->
        <div style="display:flex;gap:6px;margin-bottom:14px;flex-wrap:wrap;">
          <button onclick="fbLoad('~')"              class="npbtn fb-quick">🏠 Inicio</button>
          <button onclick="fbLoad('~/Desktop')"      class="npbtn fb-quick">🖥️ Escritorio</button>
          <button onclick="fbLoad('~/Downloads')"    class="npbtn fb-quick">⬇️ Descargas</button>
          <button onclick="fbLoad('~/Documents')"    class="npbtn fb-quick">📄 Documentos</button>
          <button onclick="fbLoad('~/Pictures')"     class="npbtn fb-quick">🖼️ Imágenes</button>
          <button onclick="fbLoad('~/Music')"        class="npbtn fb-quick">🎵 Música</button>
          <button onclick="fbLoad('C:/')"            class="npbtn fb-quick">💾 C:\\</button>
          <button onclick="fbLoad('D:/')"            class="npbtn fb-quick" id="fb-d-btn">📀 D:\\</button>
        </div>

        <!-- File grid -->
        <div id="fb-grid">
          <div style="color:var(--txd);font-size:11px;text-align:center;grid-column:1/-1;padding:30px;font-family:Share Tech Mono,monospace;letter-spacing:2px;">⟳ CARGANDO SISTEMA...</div>
        </div>

        <!-- Status bar -->
        <div id="fb-status" style="margin-top:10px;display:flex;justify-content:space-between;flex-wrap:wrap;gap:6px;padding:8px 12px;background:rgba(0,0,0,.4);border-radius:8px;font-family:Share Tech Mono,monospace;font-size:8px;color:var(--txd);letter-spacing:1px;border:1px solid rgba(0,212,255,.05);"></div>
      </div>
    </div>
  </div>

  <!-- SISTEMA -->'''

# Find and replace
p1 = hc.find(OLD_PANEL_FILES_START)
p2 = hc.find(OLD_PANEL_FILES_END)
if p1 >= 0 and p2 > p1:
    hc = hc[:p1] + NEW_PANEL_FILES + hc[p2 + len(OLD_PANEL_FILES_END):]
    print("panel-files reemplazado OK")
else:
    # Try simpler search
    p1b = hc.find('<div class="node-panel" id="panel-files">')
    if p1b >= 0:
        p2b = hc.find('<!-- SISTEMA -->', p1b)
        if p2b > p1b:
            hc = hc[:p1b] + NEW_PANEL_FILES + hc[p2b + len('<!-- SISTEMA -->'):]
            print("panel-files reemplazado (fallback) OK")
        else:
            print("ERROR: no se encontró fin del panel-files")
    else:
        print("ERROR: no se encontró panel-files")
        print("Buscando posición aproximada...")
        idx = hc.find("panel-files")
        print(f"  'panel-files' encontrado en: {idx}")
        if idx >= 0:
            print(f"  contexto: {hc[idx-50:idx+200]}")

# ── File Browser JS to inject ──────────────────────────────
FB_JS = r"""
// ══════════════════════════════════════════════════════
// HOLOGRAPHIC FILE BROWSER
// ══════════════════════════════════════════════════════
const FB_ICONS = {
  'dir':'📁',
  '.js':'⚡','.ts':'⚡','.jsx':'⚡','.tsx':'⚡',
  '.py':'🐍','.rb':'💎','.php':'🐘','.go':'🐹','.rs':'🦀',
  '.html':'🌐','.css':'🎨','.scss':'🎨','.sass':'🎨',
  '.json':'📋','.xml':'📋','.yaml':'📋','.yml':'📋','.toml':'📋','.env':'🔑',
  '.txt':'📝','.md':'📝','.log':'📋','.csv':'📊',
  '.pdf':'📕','.doc':'📘','.docx':'📘','.odt':'📘',
  '.xls':'📊','.xlsx':'📊','.ods':'📊',
  '.ppt':'📊','.pptx':'📊','.odp':'📊',
  '.jpg':'🖼️','.jpeg':'🖼️','.png':'🖼️','.gif':'🖼️','.svg':'🖼️',
  '.webp':'🖼️','.ico':'🖼️','.bmp':'🖼️','.tiff':'🖼️','.raw':'🖼️',
  '.mp3':'🎵','.wav':'🎵','.flac':'🎵','.aac':'🎵','.ogg':'🎵','.m4a':'🎵',
  '.mp4':'🎬','.mkv':'🎬','.avi':'🎬','.mov':'🎬','.wmv':'🎬','.webm':'🎬',
  '.zip':'📦','.rar':'📦','.7z':'📦','.tar':'📦','.gz':'📦','.bz2':'📦',
  '.exe':'⚙️','.msi':'⚙️','.app':'⚙️',
  '.bat':'⚡','.cmd':'⚡','.ps1':'⚡','.sh':'⚡',
  '.dll':'🔧','.so':'🔧','.dylib':'🔧',
  'default':'📄',
};
const FB_COLORS = {
  'dir':'#ffd700',
  'code':'#00ff88','img':'#9955ff','audio':'#00d4ff','video':'#ffb300',
  'archive':'#ff9955','exec':'#ff3355','doc':'#88aaff','default':'#5588aa',
};

let fbHistory=[], fbCurrent='~', fbDepth=0;

function fbGetIcon(item){
  if(item.is_dir)return FB_ICONS.dir;
  const ext='.'+item.name.split('.').pop().toLowerCase();
  return FB_ICONS[ext]||FB_ICONS.default;
}
function fbGetColor(item){
  if(item.is_dir)return FB_COLORS.dir;
  const ext='.'+item.name.split('.').pop().toLowerCase();
  if(['.js','.ts','.jsx','.tsx','.py','.rb','.go','.rs','.php','.html','.css','.json','.yaml','.sh','.bat','.ps1'].includes(ext))return FB_COLORS.code;
  if(['.jpg','.jpeg','.png','.gif','.svg','.webp','.bmp','.ico'].includes(ext))return FB_COLORS.img;
  if(['.mp3','.wav','.flac','.aac','.ogg','.m4a'].includes(ext))return FB_COLORS.audio;
  if(['.mp4','.mkv','.avi','.mov','.wmv','.webm'].includes(ext))return FB_COLORS.video;
  if(['.zip','.rar','.7z','.tar','.gz','.bz2'].includes(ext))return FB_COLORS.archive;
  if(['.exe','.msi','.dll','.bat','.cmd'].includes(ext))return FB_COLORS.exec;
  if(['.txt','.md','.pdf','.doc','.docx','.xls','.xlsx'].includes(ext))return FB_COLORS.doc;
  return FB_COLORS.default;
}
function fbFmtSize(bytes){
  if(!bytes&&bytes!==0)return '';
  if(bytes<1024)return bytes+'B';
  if(bytes<1048576)return(bytes/1024).toFixed(1)+'KB';
  if(bytes<1073741824)return(bytes/1048576).toFixed(1)+'MB';
  return(bytes/1073741824).toFixed(2)+'GB';
}

async function fbLoad(path, push=true){
  const grid=document.getElementById('fb-grid');
  const status=document.getElementById('fb-status');
  if(!grid)return;
  grid.innerHTML='<div style="color:var(--txd);font-size:10px;text-align:center;grid-column:1/-1;padding:30px;font-family:Share Tech Mono,monospace;letter-spacing:2px;animation:bk 1s infinite;">⟳ ESCANEANDO CLÚSTER...</div>';
  try{
    const r=await fetch('/api/files/list?path='+encodeURIComponent(path));
    const d=await r.json();
    if(d.error){
      grid.innerHTML=`<div style="color:var(--r);padding:30px;text-align:center;grid-column:1/-1;font-family:Share Tech Mono,monospace;font-size:10px;">⚠ ${d.error}</div>`;
      return;
    }
    if(push&&fbCurrent!==d.path){fbHistory.push(fbCurrent);fbDepth++;}
    fbCurrent=d.path;
    fbUpdateBreadcrumb(d.path);
    fbUpdateDepth();
    const backBtn=document.getElementById('fb-back-btn');
    if(backBtn){backBtn.disabled=fbHistory.length===0;backBtn.style.opacity=fbHistory.length?'1':'0.35';}
    const items=d.items||[];
    const dirs=items.filter(i=>i.is_dir);
    const files=items.filter(i=>!i.is_dir);
    grid.innerHTML='';
    [...dirs,...files].forEach(item=>{
      const color=fbGetColor(item);
      const card=document.createElement('div');
      card.className='fb-card';
      card.style.borderColor=`${color}18`;
      card.innerHTML=`
        <div class="fb-icon" style="color:${color};">${fbGetIcon(item)}</div>
        <div class="fb-name" style="color:${color};">${item.name}</div>
        ${!item.is_dir&&item.size?`<div class="fb-sz">${fbFmtSize(item.size)}</div>`:''}
        <div style="position:absolute;inset:0;background:linear-gradient(135deg,${color}06,transparent);border-radius:12px;"></div>
      `;
      card.addEventListener('mouseenter',()=>{
        card.style.borderColor=color;
        card.style.background=`rgba(0,20,40,.98)`;
        card.style.boxShadow=`0 8px 28px ${color}25, inset 0 0 20px ${color}06`;
      });
      card.addEventListener('mouseleave',()=>{
        card.style.borderColor=`${color}18`;
        card.style.background='rgba(0,8,20,.9)';
        card.style.boxShadow='none';
      });
      card.onclick=()=>{
        if(item.is_dir){
          card.style.transform='scale(.95)';
          setTimeout(()=>fbLoad(item.path),180);
        } else {
          fbOpenFile(item.path,item.name);
        }
      };
      grid.appendChild(card);
    });
    if(!items.length){
      grid.innerHTML='<div style="color:var(--txd);font-size:10px;text-align:center;grid-column:1/-1;padding:30px;font-family:Share Tech Mono,monospace;">DIRECTORIO VACÍO</div>';
    }
    const totalSize=files.reduce((s,f)=>s+(f.size||0),0);
    if(status){
      status.innerHTML=`
        <span style="color:var(--gold);">📁 ${dirs.length} carpetas</span>
        <span style="color:var(--c);">📄 ${files.length} archivos · ${fbFmtSize(totalSize)}</span>
        <span style="opacity:.4;">${d.path}</span>
      `;
    }
    showGBadge('📁 '+d.name);
  }catch(e){
    grid.innerHTML=`<div style="color:var(--r);padding:30px;text-align:center;grid-column:1/-1;font-size:10px;">Error: ${e}</div>`;
  }
}

function fbUpdateBreadcrumb(path){
  const bc=document.getElementById('fb-breadcrumb');
  if(!bc)return;
  const parts=path.replace(/\\/g,'/').split('/').filter(p=>p);
  let cumPath='';
  bc.innerHTML=parts.map((p,i)=>{
    if(i===0&&path.match(/^[A-Z]:/i))cumPath=p+'\\';
    else cumPath=cumPath?cumPath+'/'+p:'/'+p;
    const cp=cumPath;
    return `<span class="fb-bc-part" onclick="fbLoad('${cp.replace(/'/g,"\\'")}')"> ${p} </span><span class="fb-bc-sep">›</span>`;
  }).join('')||'<span style="color:var(--txd);font-size:9px;font-family:Share Tech Mono,monospace;">RAÍZ</span>';
}

function fbUpdateDepth(){
  const dw=document.getElementById('fb-depth-wrap');
  if(!dw)return;
  const max=Math.min(fbHistory.length+1,8);
  let html='';
  for(let i=0;i<max;i++){
    const active=i===fbHistory.length;
    html+=`<div class="fb-depth-seg${active?' active':''}" title="Nivel ${i+1}"></div>`;
  }
  dw.innerHTML=html+`<span style="margin-left:4px;font-size:8px;color:${fbHistory.length>0?'var(--c)':'var(--txd)'};"> L${fbHistory.length}</span>`;
}

function fbGoBack(){
  if(!fbHistory.length)return;
  const prev=fbHistory.pop();
  if(fbDepth>0)fbDepth--;
  fbLoad(prev,false);
}

function fbGoUp(){
  fetch('/api/files/list?path='+encodeURIComponent(fbCurrent))
    .then(r=>r.json())
    .then(d=>{if(d.parent&&d.parent!==d.path)fbLoad(d.parent);});
}

function fbGoHome(){fbHistory=[];fbDepth=0;fbLoad('~',false);}
function fbRefresh(){fbLoad(fbCurrent,false);}

async function fbOpenFile(path,name){
  try{
    const r=await fetch('/api/files/open',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({path})});
    const d=await r.json();
    if(d.error)showNotif('ERROR',d.error,'var(--r)');
    else showGBadge('📂 '+name);
  }catch(e){showNotif('ERROR',String(e),'var(--r)');}
}
// End File Browser
"""

# Insert FB_JS before closing script tag
if "HOLOGRAPHIC FILE BROWSER" not in hc:
    insert_pos = hc.rfind("// ══════════════════════════════════════════════════════\n// INIT")
    if insert_pos >= 0:
        hc = hc[:insert_pos] + FB_JS + "\n" + hc[insert_pos:]
        print("JS del file browser añadido")
    else:
        # fallback: insert before closing script
        insert_pos = hc.rfind("startAuth();")
        if insert_pos >= 0:
            hc = hc[:insert_pos] + FB_JS + "\n" + hc[insert_pos:]
            print("JS del file browser añadido (fallback)")
        else:
            print("ERROR: no se encontró punto de inserción para JS")
else:
    print("JS ya presente")

# ── Load files when entering FILES node ───────────────
if "if(nd.id===" in hc and "loadMemory" in hc:
    old_load = "    if(nd.id==='memory')loadMemory();\n    if(nd.id==='system')refreshSysPanel();"
    new_load = "    if(nd.id==='memory')loadMemory();\n    if(nd.id==='system')refreshSysPanel();\n    if(nd.id==='files'){fbHistory=[];fbDepth=0;setTimeout(()=>fbLoad('~',false),200);}"
    if old_load in hc:
        hc = hc.replace(old_load, new_load)
        print("fbLoad en flyToNode añadido")
    else:
        print("WARN: flyToNode trigger not found, trying alternate")
        hc = hc.replace(
            "if(nd.id==='memory')loadMemory();",
            "if(nd.id==='memory')loadMemory();\n    if(nd.id==='files'){fbHistory=[];fbDepth=0;setTimeout(()=>fbLoad('~',false),200);}"
        )

# Write result
hf.write_text(hc, encoding="utf-8")
print(f"\nindex.html OK: {len(hc)} chars")
print("DONE — Reinicia el servidor con: py -3.12 -m uvicorn server:app --host 0.0.0.0 --port 8000")
