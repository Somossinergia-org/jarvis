"""
scripts/audit_repo.py
Script de auditoría automática del repositorio JARVIS.
Genera docs/auditoria/AUDIT_INVENTORY.md
"""
import pathlib, json
from datetime import datetime

ROOT = pathlib.Path(__file__).parent.parent
DOCS = ROOT / "docs" / "auditoria"
DOCS.mkdir(parents=True, exist_ok=True)

def audit():
    lines = []
    lines.append(f"# JARVIS — Inventario de auditoría\n")
    lines.append(f"_Generado: {datetime.now().isoformat()}_\n\n")

    # File tree
    lines.append("## Árbol de archivos (raíz)\n```\n")
    skip = {"__pycache__", ".git", "audio_cache", "archive", "node_modules"}
    for p in sorted(ROOT.rglob("*")):
        if any(s in p.parts for s in skip): continue
        rel = p.relative_to(ROOT)
        depth = len(rel.parts) - 1
        indent = "  " * depth
        size = f" ({p.stat().st_size:,}B)" if p.is_file() else "/"
        lines.append(f"{indent}{'└─' if p.is_file() else '📁'} {rel.name}{size}\n")
    lines.append("```\n\n")

    # Python modules
    lines.append("## Módulos Python\n")
    for py in sorted(ROOT.rglob("*.py")):
        if any(s in py.parts for s in skip): continue
        rel = py.relative_to(ROOT)
        size = py.stat().st_size
        content = py.read_text(encoding="utf-8", errors="ignore")
        funcs = [l.strip() for l in content.splitlines() if l.strip().startswith("def ") or l.strip().startswith("async def ")]
        lines.append(f"### `{rel}` ({size:,}B)\n")
        if funcs:
            lines.append("Funciones: " + ", ".join(f.split("(")[0].replace("def ","").replace("async ","") for f in funcs[:15]) + "\n\n")
        else:
            lines.append("_(sin funciones detectadas)_\n\n")

    # Static assets
    lines.append("## Activos estáticos\n")
    for f in sorted((ROOT / "static").rglob("*")):
        if f.is_file():
            lines.append(f"- `static/{f.name}` — {f.stat().st_size:,}B\n")

    # Requirements
    req = ROOT / "requirements.txt"
    if req.exists():
        lines.append("\n## Dependencias Python\n```\n")
        lines.append(req.read_text(encoding="utf-8"))
        lines.append("```\n")

    out = DOCS / "AUDIT_INVENTORY.md"
    out.write_text("".join(lines), encoding="utf-8")
    print(f"[AUDIT] Inventario generado: {out}")
    return str(out)

if __name__ == "__main__":
    audit()
