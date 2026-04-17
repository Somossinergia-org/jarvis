import pathlib, re, subprocess

h = pathlib.Path("static/index.html").read_text(encoding="utf-8")
scripts = re.findall(r'<script(?![^>]*src)[^>]*>(.*?)</script>', h, re.DOTALL)
combined = "\n".join(scripts)
temp = pathlib.Path("_chk.js")
temp.write_text(combined, encoding="utf-8")
r = subprocess.run(["node", "--check", "_chk.js"], capture_output=True, text=True)
temp.unlink()
if r.returncode == 0:
    print("SYNTAX OK")
else:
    print("ERROR:", r.stderr[:500])
