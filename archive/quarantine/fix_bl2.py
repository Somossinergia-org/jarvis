"""Final fix: use data attributes for note links to avoid quote hell"""
import pathlib, re, subprocess

h = pathlib.Path('static/index.html').read_text(encoding='utf-8')

# Fix openNote backlinks using data-title
OLD_BL = """    if(blEl){
      let html='';
      if(bl.length)html+='<div style="margin-bottom:4px">&#8592; Desde: '+bl.map(t=>'<span onclick="openNoteByKey(\''+encodeURIComponent(t)+'\')" style="color:#ff55cc;cursor:pointer">'+t+'</span>').join(', ')+'</div>';
      if(ol.length)html+='<div>&#8594; Hacia: '+ol.map(t=>'<span onclick="openNoteByKey(\''+encodeURIComponent(t)+'\')" style="color:#ff55cc;cursor:pointer;opacity:.6">'+t+'</span>').join(', ')+'</div>';
      blEl.innerHTML=html;
    }"""

NEW_BL = """    if(blEl){
      let html='';
      if(bl.length)html+='<div style="margin-bottom:4px">&#8592; '+bl.map(t=>'<span class="nlk" data-k="'+encodeURIComponent(t)+'" style="color:#ff55cc;cursor:pointer">'+t+'</span>').join(', ')+'</div>';
      if(ol.length)html+='<div>&#8594; '+ol.map(t=>'<span class="nlk" data-k="'+encodeURIComponent(t)+'" style="color:#ff55cc;opacity:.6;cursor:pointer">'+t+'</span>').join(', ')+'</div>';
      blEl.innerHTML=html;
      blEl.querySelectorAll('.nlk').forEach(s=>s.addEventListener('click',()=>openNoteByKey(s.dataset.k)));
    }"""

h = h.replace(OLD_BL, NEW_BL)
print("backlinks data-attr:", ".nlk" in h)

pathlib.Path('static/index.html').write_text(h, encoding='utf-8')

scripts = re.findall(r'<script(?![^>]*src)[^>]*>(.*?)</script>', h, re.DOTALL)
tmp = pathlib.Path('_chk.js')
tmp.write_text('\n'.join(scripts), encoding='utf-8')
r = subprocess.run(['node','--check','_chk.js'], capture_output=True, text=True)
tmp.unlink()
print("SYNTAX:", "PASS" if r.returncode==0 else "FAIL: "+r.stderr[:300])
