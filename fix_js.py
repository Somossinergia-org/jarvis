"""
Final comprehensive fix for JARVIS Mind Palace:
1. Fix fbUpdateBreadcrumb broken backslash (JS syntax error breaking everything)
2. Fix flyToNode trigger for files panel
3. No other changes
"""
import pathlib, re

f = pathlib.Path("static/index.html")
h = f.read_text(encoding="utf-8")

# ── REPLACE the ENTIRE fbUpdateBreadcrumb function with a clean, working version
# The old version has malformed string literals

# Find exact boundaries
start_marker = "function fbUpdateBreadcrumb(path){"
end_marker = "function fbUpdateDepth(){"

s = h.find(start_marker)
e = h.find(end_marker)
if s < 0 or e < 0 or e <= s:
    print(f"ERROR: markers not found. s={s}, e={e}")
else:
    OLD_FUNC = h[s:e]
    NEW_FUNC = r"""function fbUpdateBreadcrumb(path){
  const bc=document.getElementById('fb-breadcrumb');
  if(!bc)return;
  const parts=path.replace(/\\/g,'/').split('/').filter(p=>p);
  let cum='';
  bc.innerHTML=parts.map((p,i)=>{
    if(i===0 && /^[A-Za-z]:/.test(path)) cum=p+'\\';
    else cum=cum?(cum+'/'+p):('/'+p);
    const cp=cum;
    const safe=cp.replace(/\\/g,'\\\\').replace(/'/g,"\\'");
    return '<span class="fb-bc-part" onclick="fbLoad(\''+safe+'\')" >'+p+'</span><span class="fb-bc-sep">›</span>';
  }).join('')||'<span style="color:var(--txd);font-size:9px;">RAÍZ</span>';
}

"""
    h = h[:s] + NEW_FUNC + h[e:]
    print(f"fbUpdateBreadcrumb replaced OK (was {len(OLD_FUNC)} chars, now {len(NEW_FUNC)} chars)")

# ── Fix flyToNode trigger for files
old_t = "if(nd.id==='memory')loadMemory();"
new_t = "if(nd.id==='memory')loadMemory();\n    if(nd.id==='files'){fbHistory=[];fbDepth=0;setTimeout(()=>fbLoad('~',false),200);}"
# Only add once
if old_t in h and "fbLoad" not in h[h.find(old_t)-5:h.find(old_t)+200]:
    h = h.replace(old_t, new_t, 1)
    print("flyToNode files trigger added")
else:
    print("flyToNode files trigger: already present or not found")

f.write_text(h, encoding="utf-8")
print(f"DONE: {len(h)} chars")

# Verify: check for the broken string
broken_check = "?p+'" + chr(92) + "':'" 
if broken_check in h:
    print("WARNING: broken backslash pattern still present!")
else:
    print("OK: No broken backslash patterns found")
