import pathlib, re, subprocess
h = pathlib.Path("static/index.html").read_text(encoding="utf-8")

# 5. render loop
old5 = "  if(fs3DNodes.length) updateFS3DLabels();"
new5 = "  if(fs3DNodes.length) updateFS3DLabels();\n  if(notesModeActive&&notesGraph3D.nodes.length) updateNotesGraph3D();"
h = h.replace(old5, new5, 1)
print("5 render:", "updateNotesGraph3D" in h)

# 6. canvas raycast
old6 = "    if(fsModeActive&&fs3DCores.length){"
new6 = """    if(notesModeActive&&notesGraph3D.cores.length){
      const nHits=raycaster.intersectObjects(notesGraph3D.cores,false);
      if(nHits.length){const nd2=nHits[0].object.userData.nd;if(nd2)onNoteNodeClick(nd2);return;}
    }
    if(fsModeActive&&fs3DCores.length){"""
h = h.replace(old6, new6, 1)
print("6 raycast:", "onNoteNodeClick" in h)

pathlib.Path("static/index.html").write_text(h, encoding="utf-8")

scripts = re.findall(r'<script(?![^>]*src)[^>]*>(.*?)</script>', h, re.DOTALL)
tmp = pathlib.Path("_chk.js"); tmp.write_text("\n".join(scripts), encoding="utf-8")
r = subprocess.run(["node","--check","_chk.js"], capture_output=True, text=True); tmp.unlink()
print("SYNTAX:", "PASS" if r.returncode==0 else "FAIL:"+r.stderr[:200])
