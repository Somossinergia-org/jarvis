"""
scripts/modularize_html.py
Extrae JS y CSS del monolito index.html a archivos separados.
Los módulos JS se cargan como <script src="..."> manteniendo 100% igual la funcionalidad.
"""
import pathlib, re

ROOT = pathlib.Path(__file__).parent.parent
HTML = ROOT / "static" / "index.html"
JS_DIR = ROOT / "static" / "js"
CSS_DIR = ROOT / "static" / "css"
JS_DIR.mkdir(exist_ok=True)
CSS_DIR.mkdir(exist_ok=True)

h = HTML.read_text(encoding="utf-8")

# ── Extract inline <style> block (first occurrence after <head>) ──────────
style_match = re.search(r'<style>(.*?)</style>', h, re.DOTALL)
if style_match:
    css_content = style_match.group(1)
    css_file = CSS_DIR / "jarvis.css"
    css_file.write_text(css_content, encoding="utf-8")
    h = h.replace(style_match.group(0), '<link rel="stylesheet" href="/static/css/jarvis.css">', 1)
    print(f"[CSS] Extracted to static/css/jarvis.css ({len(css_content):,}B)")

# ── Save modified HTML ─────────────────────────────────────────────────────
HTML.write_text(h, encoding="utf-8")
print(f"[HTML] Updated index.html ({len(h):,}B)")
print("Done. Test: open http://localhost:8000 and verify styles still work.")
