import pathlib, re, subprocess

h = pathlib.Path('static/index.html').read_text(encoding='utf-8')

# 1. flyToNode for notes
h = h.replace(
    "    if(nd.id==='files'){enterFSMode3D('~');return;}",
    "    if(nd.id==='files'){enterFSMode3D('~');return;}\n    if(nd.id==='notes'){openNotesPanel();return;}"
)

# 2. navMap entry for notes (replace obsidian only line)
h = h.replace(
    "  'obsidian|notas|vault|boveda':                    'obsidian',",
    "  'obsidian|vault|boveda':                          'obsidian',\n  'notas|nota|ideas|diario|conocimiento':             'notes',"
)

# 3. handleNav for notes
h = h.replace(
    "  if(cmd==='obsidian'){launchApp('obsidian');showGBadge('\U0001f7e3 OBSIDIAN');return;}",
    "  if(cmd==='obsidian'){launchApp('obsidian');showGBadge('\U0001f7e3 OBSIDIAN');return;}\n  if(cmd==='notes'){const nd2=NODES.find(n=>n.id==='notes');if(nd2)flyToNode(nd2);return;}"
)

# 4. Add complete Notes JS system before startAuth()
NOTES_JS = """
// ══════════════════════════════════════════════════════
// SISTEMA DE NOTAS — Knowledge Base JARVIS
// ══════════════════════════════════════════════════════
let currentNoteTitle = null;

function openNotesPanel(){
  const nd=NODES.find(n=>n.id==='notes');
  if(nd && !activeNode){
    flyToNode(nd);
  } else {
    // direct open panel
    const p=document.getElementById('panel-notes');
    if(p){p.style.display='block';}
  }
  loadNotesList(null);
  loadVaultStats();
}

function loadVaultStats(){
  fetch('/api/vault/stats').then(r=>r.json()).then(d=>{
    const el=document.getElementById('notes-stats-sub');
    if(el)el.textContent=d.total_notes+' notas · '+d.total_links+' enlaces';
  }).catch(()=>{});
}

function loadNotesList(folder, btn){
  // Update active folder button
  if(btn){
    document.querySelectorAll('#folder-btns .hbtn').forEach(b=>b.classList.remove('on'));
    btn.classList.add('on');
  }
  const url='/api/vault/notes'+(folder?'?folder='+folder:'');
  fetch(url).then(r=>r.json()).then(notes=>{
    const list=document.getElementById('notes-list');
    if(!list)return;
    if(!notes.length){
      list.innerHTML='<div style="color:var(--txd);text-align:center;padding:20px;font-size:10px;">Sin notas. Crea la primera.</div>';
      return;
    }
    const FC={'notas':'#ff55cc','diario':'#00d4ff','proyectos':'#00ff88','ideas':'#ffd700','personas':'#ffb300','recursos':'#9955ff'};
    list.innerHTML=notes.map(n=>{
      const col=FC[n.folder]||'#ff55cc';
      const tags=n.tags.slice(0,3).map(t=>'<span style="color:'+col+'55;font-size:8px;">#'+t+'</span>').join(' ');
      const date=n.updated?n.updated.substring(0,10):'';
      return '<div onclick="openNote(\\''+n.title.replace(/'/g,"\\\\'")+'\')" style="padding:8px 10px;background:rgba(0,12,28,.8);border:1px solid '+col+'22;border-radius:8px;cursor:pointer;transition:.2s;" '
        +'onmouseenter="this.style.borderColor=\\''+col+'55\\';this.style.background=\\'rgba(0,20,40,.95)\\'" '
        +'onmouseleave="this.style.borderColor=\\''+col+'22\\';this.style.background=\\'rgba(0,12,28,.8)\\'">'
        +'<div style="color:'+col+';font-size:10px;font-weight:bold;margin-bottom:3px;">'+n.title+'</div>'
        +'<div style="display:flex;justify-content:space-between;align-items:center;">'
        +'<div>'+tags+'</div>'
        +'<span style="color:var(--txd);font-size:8px;">'+date+'</span>'
        +'</div></div>';
    }).join('');
  }).catch(()=>{});
}

function openNote(title){
  fetch('/api/vault/note/'+encodeURIComponent(title)).then(r=>r.json()).then(note=>{
    if(note.error){showNotif('ERROR',note.error,'var(--r)');return;}
    currentNoteTitle=title;
    document.getElementById('note-title-input').value=title;
    document.getElementById('note-content-textarea').value=note.content||'';
    document.getElementById('note-folder-select').value=note.folder||'notas';
    // Show backlinks
    const bl=note.backlinks||[];
    const ol=note.outlinks||[];
    const blEl=document.getElementById('note-backlinks');
    if(blEl){
      let html='';
      if(bl.length)html+='<div style="margin-bottom:4px;">⬅ Desde: '+bl.map(t=>'<span onclick="openNote(\''+t+'\')" style="color:#ff55cc;cursor:pointer;">'+t+'</span>').join(', ')+'</div>';
      if(ol.length)html+='<div>➡ Hacia: '+ol.map(t=>'<span onclick="openNote(\''+t+'\')" style="color:#ff55cc44;cursor:pointer;">'+t+'</span>').join(', ')+'</div>';
      blEl.innerHTML=html;
    }
    showNTab('editor');
  }).catch(e=>showNotif('ERROR',''+e,'var(--r)'));
}

function newNote(){
  currentNoteTitle=null;
  document.getElementById('note-title-input').value='';
  document.getElementById('note-content-textarea').value='';
  document.getElementById('note-folder-select').value='notas';
  const blEl=document.getElementById('note-backlinks');
  if(blEl)blEl.innerHTML='';
  document.getElementById('note-title-input').focus();
}

async function saveNote(){
  const title=(document.getElementById('note-title-input').value||'').trim();
  const content=document.getElementById('note-content-textarea').value||'';
  const folder=document.getElementById('note-folder-select').value;
  if(!title){showNotif('ERROR','El título no puede estar vacío','var(--r)');return;}
  let r,d;
  if(currentNoteTitle && currentNoteTitle!==title){
    // Title changed — delete old, create new
    await fetch('/api/vault/note/'+encodeURIComponent(currentNoteTitle),{method:'DELETE'});
  }
  if(currentNoteTitle===title){
    r=await fetch('/api/vault/note/'+encodeURIComponent(title),{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({content})});
  } else {
    r=await fetch('/api/vault/note',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({title,content,folder})});
  }
  d=await r.json();
  if(d.error){showNotif('ERROR',d.error,'var(--r)');return;}
  currentNoteTitle=title;
  showNotif('GUARDADO',title,'#ff55cc');
  showGBadge('💾 '+title.substring(0,20));
  loadNotesList(null);
  loadVaultStats();
}

async function deleteCurrentNote(){
  if(!currentNoteTitle){showNotif('ERROR','No hay nota seleccionada','var(--r)');return;}
  if(!confirm('Borrar "'+currentNoteTitle+'"?'))return;
  const r=await fetch('/api/vault/note/'+encodeURIComponent(currentNoteTitle),{method:'DELETE'});
  const d=await r.json();
  if(d.error){showNotif('ERROR',d.error,'var(--r)');return;}
  showNotif('BORRADO',currentNoteTitle,'var(--r)');
  newNote();
  loadNotesList(null);
  loadVaultStats();
}

async function openDailyNote(){
  try{
    const d=await fetch('/api/vault/daily').then(r=>r.json());
    if(d.error){showNotif('ERROR',d.error,'var(--r)');return;}
    const nd=NODES.find(n=>n.id==='notes');
    if(nd&&!activeNode)flyToNode(nd);
    setTimeout(()=>{
      currentNoteTitle=d.title;
      document.getElementById('note-title-input').value=d.title;
      document.getElementById('note-content-textarea').value=d.content||'';
      document.getElementById('note-folder-select').value='diario';
      showNTab('editor');
    },500);
    showGBadge('📅 DIARIO DE HOY');
  }catch(e){showNotif('ERROR',''+e,'var(--r)');}
}

async function searchVault(){
  const q=(document.getElementById('note-search-input').value||'').trim();
  if(!q)return;
  const FC={'notas':'#ff55cc','diario':'#00d4ff','proyectos':'#00ff88','ideas':'#ffd700','personas':'#ffb300','recursos':'#9955ff'};
  try{
    const notes=await fetch('/api/vault/search?q='+encodeURIComponent(q)).then(r=>r.json());
    const el=document.getElementById('search-results');
    if(!el)return;
    if(!notes.length){el.innerHTML='<div style="color:var(--txd);text-align:center;padding:20px;font-size:10px;">Sin resultados para "'+q+'"</div>';return;}
    el.innerHTML=notes.map(n=>{
      const col=FC[n.folder]||'#ff55cc';
      return '<div onclick="openNote(\''+n.title.replace(/'/g,"\\'")+'\')" style="padding:8px 10px;background:rgba(0,12,28,.8);border:1px solid '+col+'22;border-radius:8px;cursor:pointer;">'
        +'<div style="color:'+col+';font-size:10px;font-weight:bold;">'+n.title+'</div>'
        +'<div style="color:var(--txd);font-size:8px;">'+n.folder+' · '+(n.snip||'')+'</div>'
        +'</div>';
    }).join('');
  }catch(e){showNotif('ERROR',''+e,'var(--r)');}
}

function showNTab(tab){
  ['list','editor','search'].forEach(t=>{
    const c=document.getElementById('ntab-'+t+'-content');
    const b=document.getElementById('ntab-'+t);
    if(c)c.style.display=(t===tab)?'':'none';
    if(b)b.className=(t===tab)?'hbtn on':'hbtn';
  });
}

// Voice: "nueva nota [título]", "busca [query]", "diario", "abre [título]"
function handleVaultVoice(text){
  const t=text.toLowerCase();
  if(/nueva nota|crear nota|añade nota/.test(t)){
    const title=text.replace(/nueva nota|crear nota|añade nota/i,'').trim()||'Nota sin título';
    document.getElementById('note-title-input').value=title;
    document.getElementById('note-content-textarea').value='';
    showNTab('editor');
    showGBadge('📝 NUEVA NOTA: '+title);
    return true;
  }
  if(/busca|buscar|encuentra/.test(t)){
    const q=text.replace(/busca[r]?|encuentra/i,'').trim();
    document.getElementById('note-search-input').value=q;
    showNTab('search');
    searchVault();
    return true;
  }
  if(/diario|nota del dia|nota de hoy/.test(t)){
    openDailyNote();return true;
  }
  return false;
}
// END SISTEMA DE NOTAS
"""

if "// \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\nstartAuth();" in h:
    h = h.replace("startAuth();", NOTES_JS + "\nstartAuth();", 1)
    print("Notes JS injected OK")
else:
    # fallback
    h = h.replace("startAuth();", NOTES_JS + "\nstartAuth();")
    print("Notes JS injected (fallback)")

pathlib.Path('static/index.html').write_text(h, encoding='utf-8')
print("Saved")

# validate
scripts = re.findall(r'<script(?![^>]*src)[^>]*>(.*?)</script>', h, re.DOTALL)
tmp = pathlib.Path('_chk.js')
tmp.write_text('\n'.join(scripts), encoding='utf-8')
r = subprocess.run(['node','--check','_chk.js'], capture_output=True, text=True)
tmp.unlink()
print("SYNTAX:", "PASS" if r.returncode==0 else "FAIL: "+r.stderr[:300])
print("Checks:")
for k in ["openNotesPanel","saveNote","deleteCurrentNote","openDailyNote","searchVault","handleVaultVoice","panel-notes","notes-list","'notes'"]:
    print(f"  {'OK' if k in h else 'MISS'}: {k}")
