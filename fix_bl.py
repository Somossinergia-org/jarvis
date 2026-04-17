"""Fix the backlinks HTML generation (quote issue inside onclick)"""
import pathlib, re, subprocess

h = pathlib.Path('static/index.html').read_text(encoding='utf-8')

# Fix the backlinks section in openNote
OLD_BL = """    if(blEl){
      let html='';
      if(bl.length)html+='<div style="margin-bottom:4px;">⬅ Desde: '+bl.map(t=>'<span onclick="openNote(\''+t+'\')" style="color:#ff55cc;cursor:pointer;">'+t+'</span>').join(', ')+'</div>';
      if(ol.length)html+='<div>➡ Hacia: '+ol.map(t=>'<span onclick="openNote(\''+t+'\')" style="color:#ff55cc44;cursor:pointer;">'+t+'</span>').join(', ')+'</div>';
      blEl.innerHTML=html;
    }"""

NEW_BL = """    if(blEl){
      let html='';
      if(bl.length)html+='<div style="margin-bottom:4px">&#8592; Desde: '+bl.map(t=>'<span onclick="openNoteByKey(\''+encodeURIComponent(t)+'\')" style="color:#ff55cc;cursor:pointer">'+t+'</span>').join(', ')+'</div>';
      if(ol.length)html+='<div>&#8594; Hacia: '+ol.map(t=>'<span onclick="openNoteByKey(\''+encodeURIComponent(t)+'\')" style="color:#ff55cc;cursor:pointer;opacity:.6">'+t+'</span>').join(', ')+'</div>';
      blEl.innerHTML=html;
    }"""

h = h.replace(OLD_BL, NEW_BL)
print("backlinks fixed:", "encodeURIComponent(t)" in h)

pathlib.Path('static/index.html').write_text(h, encoding='utf-8')

scripts = re.findall(r'<script(?![^>]*src)[^>]*>(.*?)</script>', h, re.DOTALL)
tmp = pathlib.Path('_chk.js')
tmp.write_text('\n'.join(scripts), encoding='utf-8')
r = subprocess.run(['node','--check','_chk.js'], capture_output=True, text=True)
tmp.unlink()
print("SYNTAX:", "PASS" if r.returncode==0 else "FAIL: "+r.stderr[:300])
