"""Fix the string escaping issue in loadNotesList and searchVault"""
import pathlib, re, subprocess

h = pathlib.Path('static/index.html').read_text(encoding='utf-8')

# Replace the problematic loadNotesList function with a cleaner version using template literals
OLD_LOAD = """function loadNotesList(folder, btn){
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
}"""

NEW_LOAD = """function loadNotesList(folder, btn){
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
    const FC={notas:'#ff55cc',diario:'#00d4ff',proyectos:'#00ff88',ideas:'#ffd700',personas:'#ffb300',recursos:'#9955ff'};
    list.innerHTML=notes.map(n=>{
      const col=FC[n.folder]||'#ff55cc';
      const tags=n.tags.slice(0,3).map(t=>'<span style="color:'+col+'55;font-size:8px">#'+t+'</span>').join(' ');
      const date=(n.updated||'').substring(0,10);
      const safeTitle=encodeURIComponent(n.title);
      return `<div onclick="openNoteByKey('${safeTitle}')" style="padding:8px 10px;background:rgba(0,12,28,.8);border:1px solid ${col}22;border-radius:8px;cursor:pointer;transition:.2s" onmouseenter="this.style.borderColor='${col}55'" onmouseleave="this.style.borderColor='${col}22'"><div style="color:${col};font-size:10px;font-weight:bold;margin-bottom:3px">${n.title}</div><div style="display:flex;justify-content:space-between"><div>${tags}</div><span style="color:var(--txd);font-size:8px">${date}</span></div></div>`;
    }).join('');
  }).catch(()=>{});
}
function openNoteByKey(encoded){openNote(decodeURIComponent(encoded));}"""

h = h.replace(OLD_LOAD, NEW_LOAD)
print("loadNotesList fixed:", "openNoteByKey" in h)

# Fix searchVault similarly
OLD_SEARCH = """    el.innerHTML=notes.map(n=>{
      const col=FC[n.folder]||'#ff55cc';
      return '<div onclick="openNote(\''+n.title.replace(/'/g,"\\'")+'\')" style="padding:8px 10px;background:rgba(0,12,28,.8);border:1px solid '+col+'22;border-radius:8px;cursor:pointer;">'
        +'<div style="color:'+col+';font-size:10px;font-weight:bold;">'+n.title+'</div>'
        +'<div style="color:var(--txd);font-size:8px;">'+n.folder+' · '+(n.snip||'')+'</div>'
        +'</div>';
    }).join('');"""

NEW_SEARCH = """    el.innerHTML=notes.map(n=>{
      const col=FC[n.folder]||'#ff55cc';
      const sk=encodeURIComponent(n.title);
      return `<div onclick="openNoteByKey('${sk}')" style="padding:8px 10px;background:rgba(0,12,28,.8);border:1px solid ${col}22;border-radius:8px;cursor:pointer"><div style="color:${col};font-size:10px;font-weight:bold">${n.title}</div><div style="color:var(--txd);font-size:8px">${n.folder}</div></div>`;
    }).join('');"""

h = h.replace(OLD_SEARCH, NEW_SEARCH)
print("searchVault fixed:", "encodeURIComponent(n.title)" in h)

pathlib.Path('static/index.html').write_text(h, encoding='utf-8')

scripts = re.findall(r'<script(?![^>]*src)[^>]*>(.*?)</script>', h, re.DOTALL)
tmp = pathlib.Path('_chk.js')
tmp.write_text('\n'.join(scripts), encoding='utf-8')
r = subprocess.run(['node','--check','_chk.js'], capture_output=True, text=True)
tmp.unlink()
print("SYNTAX:", "PASS" if r.returncode==0 else "FAIL: "+r.stderr[:300])
