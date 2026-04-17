"""Inject file browser JS into index.html and fix flyToNode trigger."""
import pathlib

hf = pathlib.Path("static/index.html")
h = hf.read_text(encoding="utf-8")

FB_JS = """
// ══════════════════════════════════════════════════════
// HOLOGRAPHIC FILE BROWSER — Sistema de Archivos 3D
// ══════════════════════════════════════════════════════
const FB_ICONS = {
  dir:'📁',
  '.js':'⚡','.ts':'⚡','.jsx':'⚡','.tsx':'⚡','.vue':'⚡',
  '.py':'🐍','.rb':'💎','.php':'🐘','.go':'🐹','.rs':'🦀','.java':'☕','.cs':'🔷','.cpp':'🔩',
  '.html':'🌐','.css':'🎨','.scss':'🎨',
  '.json':'📋','.xml':'📋','.yaml':'📋','.yml':'📋','.toml':'📋','.env':'🔑',
  '.txt':'📝','.md':'📝','.log':'📋','.csv':'📊',
  '.pdf':'📕','.doc':'📘','.docx':'📘','.odt':'📘',
  '.xls':'📊','.xlsx':'📊','.ppt':'📊','.pptx':'📊',
  '.jpg':'🖼️','.jpeg':'🖼️','.png':'🖼️','.gif':'🖼️','.svg':'🖼️','.webp':'🖼️','.ico':'🖼️','.bmp':'🖼️',
  '.mp3':'🎵','.wav':'🎵','.flac':'🎵','.aac':'🎵','.ogg':'🎵','.m4a':'🎵',
  '.mp4':'🎬','.mkv':'🎬','.avi':'🎬','.mov':'🎬','.wmv':'🎬','.webm':'🎬',
  '.zip':'📦','.rar':'📦','.z7':'📦','.tar':'📦','.gz':'📦','.bz2':'📦',
  '.exe':'⚙️','.msi':'⚙️','.app':'⚙️','.bat':'⚡','.cmd':'⚡','.ps1':'⚡','.sh':'⚡',
  '.dll':'🔧','.so':'🔧',
  default:'📄',
};
const FB_COLORS = {
  dir:'#ffd700',code:'#00ff88',img:'#9955ff',audio:'#00d4ff',
  video:'#ffb300',archive:'#ff9955',exec:'#ff3355',doc:'#88aaff',default:'#5588aa',
};
let fbHistory=[],fbCurrent='~',fbDepth=0;

function fbGetIcon(item){
  if(item.is_dir)return FB_ICONS.dir;
  const ext='.'+item.name.split('.').pop().toLowerCase();
  return FB_ICONS[ext]||FB_ICONS.default;
}
function fbGetColor(item){
  if(item.is_dir)return FB_COLORS.dir;
  const ext='.'+item.name.split('.').pop().toLowerCase();
  if(['.js','.ts','.jsx','.tsx','.py','.rb','.go','.rs','.java','.cs','.cpp','.html','.css','.json','.yaml','.sh','.bat','.ps1','.vue'].includes(ext))return FB_COLORS.code;
  if(['.jpg','.jpeg','.png','.gif','.svg','.webp','.bmp','.ico'].includes(ext))return FB_COLORS.img;
  if(['.mp3','.wav','.flac','.aac','.ogg','.m4a'].includes(ext))return FB_COLORS.audio;
  if(['.mp4','.mkv','.avi','.mov','.wmv','.webm'].includes(ext))return FB_COLORS.video;
  if(['.zip','.rar','.7z','.tar','.gz','.bz2'].includes(ext))return FB_COLORS.archive;
  if(['.exe','.msi','.dll','.bat','.cmd'].includes(ext))return FB_COLORS.exec;
  if(['.txt','.md','.pdf','.doc','.docx','.xls','.xlsx'].includes(ext))return FB_COLORS.doc;
  return FB_COLORS.default;
}
function fbFmtSize(b){
  if(!b&&b!==0)return '';
  if(b<1024)return b+'B';
  if(b<1048576)return(b/1024).toFixed(1)+'KB';
  if(b<1073741824)return(b/1048576).toFixed(1)+'MB';
  return(b/1073741824).toFixed(2)+'GB';
}

async function fbLoad(path,push){
  if(push===undefined)push=true;
  const grid=document.getElementById('fb-grid');
  const status=document.getElementById('fb-status');
  if(!grid)return;
  grid.innerHTML='<div style="color:var(--txd);font-size:10px;text-align:center;grid-column:1/-1;padding:30px;font-family:Share Tech Mono,monospace;letter-spacing:2px;">⟳ ESCANEANDO...</div>';
  try{
    const r=await fetch('/api/files/list?path='+encodeURIComponent(path));
    const d=await r.json();
    if(d.error){
      grid.innerHTML='<div style="color:var(--r);padding:30px;text-align:center;grid-column:1/-1;font-size:10px;">⚠ '+d.error+'</div>';
      return;
    }
    if(push&&fbCurrent!==d.path){fbHistory.push(fbCurrent);fbDepth++;}
    fbCurrent=d.path;
    fbUpdateBreadcrumb(d.path);
    fbUpdateDepth();
    const bb=document.getElementById('fb-back-btn');
    if(bb){bb.disabled=!fbHistory.length;bb.style.opacity=fbHistory.length?'1':'0.35';}
    const items=d.items||[];
    const dirs=items.filter(i=>i.is_dir);
    const files=items.filter(i=>!i.is_dir);
    grid.innerHTML='';
    [...dirs,...files].forEach(item=>{
      const color=fbGetColor(item);
      const card=document.createElement('div');
      card.className='fb-card';
      card.style.borderColor=color+'18';
      card.innerHTML=
        '<div class="fb-icon" style="color:'+color+';">'+fbGetIcon(item)+'</div>'+
        '<div class="fb-name" style="color:'+color+';">'+item.name+'</div>'+
        (!item.is_dir&&item.size?'<div class="fb-sz">'+fbFmtSize(item.size)+'</div>':'')+
        '<div style="position:absolute;inset:0;background:linear-gradient(135deg,'+color+'06,transparent);border-radius:12px;"></div>';
      card.addEventListener('mouseenter',()=>{
        card.style.borderColor=color;
        card.style.background='rgba(0,20,40,.98)';
        card.style.boxShadow='0 8px 28px '+color+'25,inset 0 0 20px '+color+'06';
      });
      card.addEventListener('mouseleave',()=>{
        card.style.borderColor=color+'18';
        card.style.background='rgba(0,8,20,.9)';
        card.style.boxShadow='none';
      });
      card.onclick=()=>{
        if(item.is_dir){card.style.transform='scale(.95)';setTimeout(()=>fbLoad(item.path,true),180);}
        else fbOpenFile(item.path,item.name);
      };
      grid.appendChild(card);
    });
    if(!items.length)grid.innerHTML='<div style="color:var(--txd);font-size:10px;text-align:center;grid-column:1/-1;padding:30px;font-family:Share Tech Mono,monospace;">DIRECTORIO VACÍO</div>';
    if(status){
      const tot=files.reduce((s,f)=>s+(f.size||0),0);
      status.innerHTML='<span style="color:var(--gold);">📁 '+dirs.length+' carpetas</span><span style="color:var(--c);">📄 '+files.length+' archivos · '+fbFmtSize(tot)+'</span><span style="opacity:.4;max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">'+d.path+'</span>';
    }
    showGBadge('📁 '+d.name);
  }catch(e){
    grid.innerHTML='<div style="color:var(--r);padding:30px;text-align:center;grid-column:1/-1;">Error: '+e+'</div>';
  }
}

function fbUpdateBreadcrumb(path){
  const bc=document.getElementById('fb-breadcrumb');
  if(!bc)return;
  const parts=path.replace(/\\\\/g,'/').split('/').filter(p=>p);
  let cum='';
  bc.innerHTML=parts.map((p,i)=>{
    cum=cum?(cum+'/'+p):(path.match(/^[A-Za-z]:/)?p+'\\':'/'+p);
    const cp=cum;
    return '<span class="fb-bc-part" onclick="fbLoad(\''+cp.replace(/\\/g,'\\\\').replace(/'/g,"\\'")+'\')" > '+p+' </span><span class="fb-bc-sep">›</span>';
  }).join('')||'<span style="color:var(--txd);font-size:9px;font-family:Share Tech Mono,monospace;">RAÍZ</span>';
}

function fbUpdateDepth(){
  const dw=document.getElementById('fb-depth-wrap');
  if(!dw)return;
  let html='';
  const max=Math.min(fbHistory.length+1,8);
  for(let i=0;i<max;i++)html+='<div class="fb-depth-seg'+(i===fbHistory.length?' active':'')+'"></div>';
  dw.innerHTML=html+'<span style="margin-left:4px;font-size:8px;color:'+(fbHistory.length?'var(--c)':'var(--txd)')+';">L'+fbHistory.length+'</span>';
}
function fbGoBack(){if(!fbHistory.length)return;const p=fbHistory.pop();if(fbDepth>0)fbDepth--;fbLoad(p,false);}
function fbGoUp(){fetch('/api/files/list?path='+encodeURIComponent(fbCurrent)).then(r=>r.json()).then(d=>{if(d.parent&&d.parent!==d.path)fbLoad(d.parent,true);});}
function fbGoHome(){fbHistory=[];fbDepth=0;fbLoad('~',false);}
function fbRefresh(){fbLoad(fbCurrent,false);}
async function fbOpenFile(path,name){
  try{
    const r=await fetch('/api/files/open',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({path})});
    const d=await r.json();
    if(d.error)showNotif('ERROR',d.error,'var(--r)');
    else showGBadge('📂 '+(name||path));
  }catch(e){showNotif('ERROR',''+e,'var(--r)');}
}
// END FILE BROWSER
"""

# FlyToNode trigger
old_t = "if(nd.id==='memory')loadMemory();"
new_t = "if(nd.id==='memory')loadMemory();\n    if(nd.id==='files'){fbHistory=[];fbDepth=0;setTimeout(()=>fbLoad('~',false),200);}"
if old_t in h and new_t not in h:
    h = h.replace(old_t, new_t, 1)
    print("flyToNode trigger OK")

# Insert JS
if 'async function fbLoad' not in h:
    idx = h.rfind('startAuth();')
    if idx >= 0:
        h = h[:idx] + FB_JS + "\n" + h[idx:]
        print("JS inserted OK")
    else:
        print("ERROR: startAuth not found")
else:
    print("fbLoad already present")

hf.write_text(h, encoding="utf-8")
print(f"DONE — {len(h)} chars, fbLoad={('async function fbLoad' in h)}, trigger={('files' in h and 'fbLoad' in h)}")
