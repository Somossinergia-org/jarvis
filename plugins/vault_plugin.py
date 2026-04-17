"""
plugins/vault_plugin.py
Sistema de conocimiento personal JARVIS — Bóveda local SQLite + Markdown
"""
import sqlite3, pathlib, re, json
from datetime import datetime, date

VAULT_PATH = pathlib.Path.home() / "JarvisVault"
DB_PATH    = VAULT_PATH / "jarvis.db"
FOLDERS    = ["notas", "diario", "proyectos", "ideas", "personas", "recursos"]

FOLDER_COLORS = {
    "notas":     "#ff55cc",
    "diario":    "#00d4ff",
    "proyectos": "#00ff88",
    "ideas":     "#ffd700",
    "personas":  "#ffb300",
    "recursos":  "#9955ff",
}

def init_vault() -> str:
    VAULT_PATH.mkdir(exist_ok=True)
    for f in FOLDERS:
        (VAULT_PATH / f).mkdir(exist_ok=True)
    conn = _db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS notes (
        id        INTEGER PRIMARY KEY AUTOINCREMENT,
        title     TEXT    NOT NULL UNIQUE,
        path      TEXT    NOT NULL UNIQUE,
        folder    TEXT    DEFAULT 'notas',
        content   TEXT    DEFAULT '',
        tags      TEXT    DEFAULT '[]',
        created   TEXT,
        updated   TEXT,
        link_count     INTEGER DEFAULT 0,
        backlink_count INTEGER DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS edges (
        from_id  INTEGER,
        to_title TEXT,
        UNIQUE(from_id, to_title)
    );
    CREATE VIRTUAL TABLE IF NOT EXISTS notes_fts
        USING fts5(title, content, tags, tokenize='unicode61');
    """)
    conn.commit(); conn.close()
    # Create welcome note if vault is empty
    if not list(VAULT_PATH.rglob("*.md")):
        create_note(
            "Bienvenido a JARVIS",
            "# Bienvenido a JARVIS\n\nEste es tu segundo cerebro. Escribe [[ideas]], conecta [[proyectos]] y organiza tu conocimiento.\n\n#inicio #jarvis",
            folder="notas"
        )
    return str(VAULT_PATH)

def _db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def _extract(content: str):
    links = list(set(re.findall(r'\[\[([^\]|#\n]+?)(?:\|[^\]]+)?\]\]', content)))
    tags  = list(set(re.findall(r'(?<!\w)#([\w/-]+)', content)))
    return links, tags

def _safe_path(title: str, folder: str) -> pathlib.Path:
    safe = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', title)[:80]
    return VAULT_PATH / folder / f"{safe}.md"

def create_note(title: str, content: str = "", folder: str = "notas", tags: list = None) -> dict:
    tags = tags or []
    now  = datetime.now().isoformat()
    links, found_tags = _extract(content)
    all_tags = list(set(tags + found_tags))
    path = _safe_path(title, folder)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    conn = _db()
    try:
        conn.execute(
            "INSERT INTO notes (title,path,folder,content,tags,created,updated) VALUES (?,?,?,?,?,?,?)",
            (title, str(path), folder, content, json.dumps(all_tags), now, now)
        )
        nid = conn.execute("SELECT id FROM notes WHERE title=?", (title,)).fetchone()["id"]
        for lk in links:
            conn.execute("INSERT OR IGNORE INTO edges VALUES (?,?)", (nid, lk))
        # FTS
        conn.execute("INSERT INTO notes_fts(rowid,title,content,tags) VALUES (?,?,?,?)",
                     (nid, title, content, " ".join(all_tags)))
        _recalc(conn); conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return {"error": f"La nota '{title}' ya existe"}
    conn.close()
    return {"ok": True, "title": title, "path": str(path), "folder": folder}

def get_note(title: str) -> dict:
    conn = _db()
    row = conn.execute("SELECT * FROM notes WHERE title=?", (title,)).fetchone()
    conn.close()
    if not row: return {"error": "Nota no encontrada"}
    r = dict(row); r["tags"] = json.loads(r["tags"])
    conn2 = _db()
    bl = conn2.execute(
        "SELECT n.title FROM edges e JOIN notes n ON e.from_id=n.id WHERE e.to_title=?", (title,)
    ).fetchall()
    ol = conn2.execute("SELECT to_title FROM edges WHERE from_id=?", (r["id"],)).fetchall()
    conn2.close()
    r["backlinks"] = [b["title"] for b in bl]
    r["outlinks"]  = [o["to_title"] for o in ol]
    return r

def update_note(title: str, content: str) -> dict:
    now = datetime.now().isoformat()
    links, tags = _extract(content)
    conn = _db()
    row = conn.execute("SELECT id, path FROM notes WHERE title=?", (title,)).fetchone()
    if not row: conn.close(); return {"error": "Nota no encontrada"}
    pathlib.Path(row["path"]).write_text(content, encoding="utf-8")
    conn.execute("UPDATE notes SET content=?,tags=?,updated=? WHERE id=?",
                 (content, json.dumps(tags), now, row["id"]))
    conn.execute("DELETE FROM edges WHERE from_id=?", (row["id"],))
    for lk in links:
        conn.execute("INSERT OR IGNORE INTO edges VALUES (?,?)", (row["id"], lk))
    # FTS update
    conn.execute("INSERT INTO notes_fts(notes_fts,rowid,title,content,tags) VALUES ('delete',?,?,?,?)",
                 (row["id"], title, "", ""))
    conn.execute("INSERT INTO notes_fts(rowid,title,content,tags) VALUES (?,?,?,?)",
                 (row["id"], title, content, " ".join(tags)))
    _recalc(conn); conn.commit(); conn.close()
    return {"ok": True}

def delete_note(title: str) -> dict:
    conn = _db()
    row = conn.execute("SELECT id, path FROM notes WHERE title=?", (title,)).fetchone()
    if not row: conn.close(); return {"error": "Nota no encontrada"}
    try: pathlib.Path(row["path"]).unlink(missing_ok=True)
    except Exception: pass
    conn.execute("DELETE FROM edges WHERE from_id=?", (row["id"],))
    conn.execute("INSERT INTO notes_fts(notes_fts,rowid,title,content,tags) VALUES ('delete',?,?,?,?)",
                 (row["id"], title, "", ""))
    conn.execute("DELETE FROM notes WHERE id=?", (row["id"],))
    _recalc(conn); conn.commit(); conn.close()
    return {"ok": True}

def list_notes(folder: str = None) -> list:
    conn = _db()
    q = "SELECT id,title,folder,tags,created,updated,link_count,backlink_count FROM notes"
    rows = conn.execute(q + (" WHERE folder=? ORDER BY updated DESC" if folder else " ORDER BY updated DESC"),
                        (folder,) if folder else ()).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r); d["tags"] = json.loads(d["tags"]); result.append(d)
    return result

def search_notes(query: str) -> list:
    conn = _db()
    try:
        rows = conn.execute(
            "SELECT n.id,n.title,n.folder,n.tags,n.updated,n.link_count,snippet(notes_fts,1,'<b>','</b>','...',20) AS snip "
            "FROM notes_fts f JOIN notes n ON f.rowid=n.id "
            "WHERE notes_fts MATCH ? ORDER BY rank LIMIT 20",
            (query,)
        ).fetchall()
    except Exception:
        # fallback to LIKE
        rows = conn.execute(
            "SELECT id,title,folder,tags,updated,link_count FROM notes "
            "WHERE title LIKE ? OR content LIKE ? ORDER BY updated DESC LIMIT 20",
            (f"%{query}%", f"%{query}%")
        ).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r); d["tags"] = json.loads(d["tags"]); result.append(d)
    return result

def get_graph() -> dict:
    conn = _db()
    notes = conn.execute(
        "SELECT id,title,folder,tags,link_count,backlink_count FROM notes"
    ).fetchall()
    edges = conn.execute(
        "SELECT e.from_id, n.id as to_id FROM edges e JOIN notes n ON e.to_title=n.title"
    ).fetchall()
    conn.close()
    nodes = []
    for n in notes:
        d = dict(n); d["tags"] = json.loads(d["tags"])
        d["weight"] = max(1, d["link_count"] + d["backlink_count"])
        d["color"]  = FOLDER_COLORS.get(d["folder"], "#ff55cc")
        nodes.append(d)
    return {
        "nodes": nodes,
        "edges": [{"from": e["from_id"], "to": e["to_id"]} for e in edges],
        "folder_colors": FOLDER_COLORS,
    }

def get_daily_note() -> dict:
    today = date.today().isoformat()
    title = f"Diario {today}"
    existing = get_note(title)
    if "error" not in existing: return existing
    now_str = datetime.now().strftime("%H:%M")
    content = f"""# {title}

## 🌅 Mañana

## 📋 Tareas del día
- [ ] 

## 💡 Ideas y pensamientos

## 📝 Notas rápidas

---
*Creado por JARVIS · {now_str}*"""
    create_note(title, content, folder="diario")
    return get_note(title)

def reindex_vault() -> dict:
    conn = _db()
    conn.execute("DELETE FROM edges")
    conn.execute("DELETE FROM notes")
    conn.execute("DELETE FROM notes_fts")
    conn.commit()
    count = 0
    for md in VAULT_PATH.rglob("*.md"):
        try:
            content = md.read_text(encoding="utf-8")
            title   = md.stem
            folder  = md.parent.name if md.parent != VAULT_PATH else "notas"
            links, tags = _extract(content)
            now = datetime.now().isoformat()
            mtime = datetime.fromtimestamp(md.stat().st_mtime).isoformat()
            conn.execute(
                "INSERT OR REPLACE INTO notes (title,path,folder,content,tags,created,updated) VALUES (?,?,?,?,?,?,?)",
                (title, str(md), folder, content, json.dumps(tags), now, mtime)
            )
            count += 1
        except Exception:
            pass
    for row in conn.execute("SELECT id,title,content,tags FROM notes").fetchall():
        links, _ = _extract(row["content"])
        for lk in links:
            conn.execute("INSERT OR IGNORE INTO edges VALUES (?,?)", (row["id"], lk))
        conn.execute("INSERT INTO notes_fts(rowid,title,content,tags) VALUES (?,?,?,?)",
                     (row["id"], row["title"], row["content"], row["tags"]))
    _recalc(conn); conn.commit(); conn.close()
    return {"ok": True, "indexed": count}

def _recalc(conn):
    conn.execute("UPDATE notes SET link_count=(SELECT COUNT(*) FROM edges WHERE from_id=notes.id)")
    conn.execute("""UPDATE notes SET backlink_count=(
        SELECT COUNT(*) FROM edges e JOIN notes n ON e.from_id=n.id WHERE e.to_title=notes.title)""")

def get_stats() -> dict:
    conn = _db()
    total  = conn.execute("SELECT COUNT(*) FROM notes").fetchone()[0]
    by_fol = conn.execute("SELECT folder,COUNT(*) as c FROM notes GROUP BY folder").fetchall()
    edges  = conn.execute("SELECT COUNT(*) FROM edges").fetchone()[0]
    conn.close()
    return {
        "total_notes": total,
        "total_links": edges,
        "by_folder": {r["folder"]: r["c"] for r in by_fol},
        "vault_path": str(VAULT_PATH),
    }
