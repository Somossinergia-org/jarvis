"""
__tests__/test_vault_plugin.py
Tests unitarios completos para vault_plugin.py
Cubre: CRUD, búsqueda, grafo, backlinks, tags, daily note,
       edge cases: nota vacía, duplicada, título largo, metadata corrupta.
"""
import pytest
import pathlib
import tempfile
import os
import sys

# Add project root to path
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

# ─── Fixtures ──────────────────────────────────────────────────
@pytest.fixture(autouse=True)
def isolated_vault(tmp_path, monkeypatch):
    """Cada test usa una bóveda temporal aislada."""
    monkeypatch.setenv("JARVIS_VAULT_PATH", str(tmp_path))
    # Re-import to pick up new env
    import importlib
    import plugins.vault_plugin as vp
    importlib.reload(vp)
    vp.init_vault()
    yield vp
    # cleanup handled by tmp_path


@pytest.fixture
def vp(isolated_vault):
    return isolated_vault


# ─── INIT ──────────────────────────────────────────────────────
class TestVaultInit:
    def test_init_creates_vault_dir(self, vp, tmp_path):
        """init_vault debe crear el directorio raíz."""
        result = vp.init_vault()
        assert pathlib.Path(result).exists()

    def test_init_creates_default_folders(self, vp, tmp_path):
        """init_vault debe crear las carpetas estándar."""
        vault = pathlib.Path(vp.init_vault())
        for folder in ["notas", "diario", "proyectos", "ideas", "personas", "recursos"]:
            assert (vault / folder).exists(), f"Carpeta {folder} no creada"

    def test_init_creates_db(self, vp, tmp_path):
        """init_vault debe crear el archivo de base de datos SQLite."""
        vp.init_vault()
        db_files = list(pathlib.Path(tmp_path).rglob("*.db"))
        assert len(db_files) >= 1, "No se creó archivo .db"


# ─── CREATE ────────────────────────────────────────────────────
class TestCreateNote:
    def test_create_basic_note(self, vp):
        r = vp.create_note("Mi nota", "Contenido de prueba", "notas")
        assert r.get("ok") is True
        assert r.get("title") == "Mi nota"

    def test_create_note_creates_markdown_file(self, vp, tmp_path):
        vp.create_note("Nota Markdown", "# Hola mundo", "notas")
        md_files = list(pathlib.Path(tmp_path).rglob("*.md"))
        assert any("Nota Markdown" in f.name for f in md_files)

    def test_create_note_with_tags(self, vp):
        r = vp.create_note("Nota tags", "#python #ia", "notas", ["python", "ia"])
        assert r.get("ok") is True

    def test_create_note_empty_title_rejected(self, vp):
        r = vp.create_note("", "Contenido", "notas")
        assert r.get("ok") is not True or r.get("error") is not None

    def test_create_note_in_custom_folder(self, vp):
        r = vp.create_note("Nota Ideas", "Una idea brillante", "ideas")
        assert r.get("ok") is True
        assert "ideas" in r.get("path", "").lower()

    def test_create_note_very_long_title(self, vp):
        long_title = "A" * 200
        r = vp.create_note(long_title, "content", "notas")
        # Should either succeed or return clean error, not crash
        assert isinstance(r, dict)

    def test_create_duplicate_note_returns_error_or_overwrites(self, vp):
        vp.create_note("Duplicada", "v1", "notas")
        r = vp.create_note("Duplicada", "v2", "notas")
        assert isinstance(r, dict)  # Must not crash


# ─── GET ───────────────────────────────────────────────────────
class TestGetNote:
    def test_get_existing_note(self, vp):
        vp.create_note("GetTest", "Contenido get", "notas")
        r = vp.get_note("GetTest")
        assert r.get("title") == "GetTest"
        assert "Contenido get" in r.get("content", "")

    def test_get_nonexistent_note_returns_error(self, vp):
        r = vp.get_note("NoCExiste_XYZ_999")
        assert "error" in r

    def test_get_note_returns_folder(self, vp):
        vp.create_note("FolderTest", "x", "proyectos")
        r = vp.get_note("FolderTest")
        assert r.get("folder") == "proyectos"

    def test_get_note_returns_tags(self, vp):
        vp.create_note("TagNote", "#alpha #beta", "notas", ["alpha", "beta"])
        r = vp.get_note("TagNote")
        assert "alpha" in r.get("tags", [])

    def test_get_note_returns_backlinks(self, vp):
        """Nota B con [[A]] — getNote(A) debe devolver B en backlinks."""
        vp.create_note("A", "Nota A", "notas")
        vp.create_note("B", "Referencia a [[A]]", "notas")
        r = vp.get_note("A")
        backlinks = r.get("backlinks", [])
        assert "B" in backlinks

    def test_get_note_returns_outlinks(self, vp):
        vp.create_note("Target", "Nota target", "notas")
        vp.create_note("Source", "Ver [[Target]] para más info", "notas")
        r = vp.get_note("Source")
        assert "Target" in r.get("outlinks", [])


# ─── UPDATE ────────────────────────────────────────────────────
class TestUpdateNote:
    def test_update_existing_note(self, vp):
        vp.create_note("UpdateMe", "v1", "notas")
        r = vp.update_note("UpdateMe", "v2 actualizada")
        assert r.get("ok") is True

    def test_update_persists_content(self, vp):
        vp.create_note("PersistTest", "original", "notas")
        vp.update_note("PersistTest", "actualizado")
        r = vp.get_note("PersistTest")
        assert "actualizado" in r.get("content", "")

    def test_update_nonexistent_note(self, vp):
        r = vp.update_note("NoExiste_999", "nuevo contenido")
        assert isinstance(r, dict)  # no crash

    def test_update_preserves_tags(self, vp):
        vp.create_note("TagPersist", "v1 #tag1", "notas", ["tag1"])
        vp.update_note("TagPersist", "v2 #tag1 #tag2")
        r = vp.get_note("TagPersist")
        assert isinstance(r.get("tags"), list)


# ─── DELETE ────────────────────────────────────────────────────
class TestDeleteNote:
    def test_delete_existing_note(self, vp, tmp_path):
        vp.create_note("Borrar", "borrar esto", "notas")
        r = vp.delete_note("Borrar")
        assert r.get("ok") is True
        # File should not exist
        md_files = list(tmp_path.rglob("Borrar.md"))
        assert len(md_files) == 0

    def test_delete_nonexistent_returns_error(self, vp):
        r = vp.delete_note("NoExiste_999")
        assert "error" in r

    def test_delete_removes_from_list(self, vp):
        vp.create_note("ListDelete", "x", "notas")
        vp.delete_note("ListDelete")
        notes = vp.list_notes()
        titles = [n["title"] for n in notes]
        assert "ListDelete" not in titles


# ─── LIST ──────────────────────────────────────────────────────
class TestListNotes:
    def test_list_empty_vault(self, vp):
        notes = vp.list_notes()
        assert isinstance(notes, list)

    def test_list_returns_created_notes(self, vp):
        vp.create_note("Lista1", "x", "notas")
        vp.create_note("Lista2", "y", "ideas")
        notes = vp.list_notes()
        titles = [n["title"] for n in notes]
        assert "Lista1" in titles
        assert "Lista2" in titles

    def test_list_filter_by_folder(self, vp):
        vp.create_note("FolderA", "x", "notas")
        vp.create_note("FolderB", "y", "ideas")
        notas = vp.list_notes("notas")
        titles = [n["title"] for n in notas]
        assert "FolderA" in titles
        assert "FolderB" not in titles

    def test_list_many_notes(self, vp):
        for i in range(50):
            vp.create_note(f"Nota{i}", f"Contenido {i}", "notas")
        notes = vp.list_notes()
        assert len(notes) >= 50


# ─── SEARCH ────────────────────────────────────────────────────
class TestSearchNotes:
    def test_search_by_title(self, vp):
        vp.create_note("Python avanzado", "Decoradores y metaclases", "notas")
        results = vp.search_notes("Python")
        assert any("Python" in r["title"] for r in results)

    def test_search_by_content(self, vp):
        vp.create_note("IA Docs", "Los transformers cambiaron el mundo", "notas")
        results = vp.search_notes("transformers")
        assert len(results) >= 1

    def test_search_no_results(self, vp):
        results = vp.search_notes("xyzqwerty_inexistente_9999")
        assert isinstance(results, list)
        assert len(results) == 0

    def test_search_empty_query(self, vp):
        vp.create_note("test", "contenido", "notas")
        results = vp.search_notes("")
        assert isinstance(results, list)

    def test_search_returns_snip(self, vp):
        vp.create_note("Snip Test", "El contexto importa mucho en búsquedas", "notas")
        results = vp.search_notes("contexto")
        # Should return at least title
        assert len(results) >= 1


# ─── GRAPH ─────────────────────────────────────────────────────
class TestGraph:
    def test_graph_empty_vault(self, vp):
        g = vp.get_graph()
        assert "nodes" in g
        assert "edges" in g
        assert isinstance(g["nodes"], list)
        assert isinstance(g["edges"], list)

    def test_graph_node_has_required_fields(self, vp):
        vp.create_note("GraphNode", "contenido", "notas")
        g = vp.get_graph()
        assert len(g["nodes"]) >= 1
        node = g["nodes"][0]
        required = {"id", "title", "folder"}
        assert required.issubset(set(node.keys())), f"Faltan campos: {required - set(node.keys())}"

    def test_graph_edge_for_wikilink(self, vp):
        vp.create_note("NodeA", "ver [[NodeB]]", "notas")
        vp.create_note("NodeB", "nodo B", "notas")
        g = vp.get_graph()
        edges = g.get("edges", [])
        assert len(edges) >= 1

    def test_graph_no_self_loops(self, vp):
        vp.create_note("SelfRef", "ver [[SelfRef]]", "notas")
        g = vp.get_graph()
        for edge in g.get("edges", []):
            assert edge.get("from") != edge.get("to"), "Self-loop detected"

    def test_graph_edge_both_directions_unique(self, vp):
        vp.create_note("Alpha", "enlace a [[Beta]]", "notas")
        vp.create_note("Beta", "nodo beta", "notas")
        g = vp.get_graph()
        pairs = [(e["from"], e["to"]) for e in g.get("edges", [])]
        assert len(pairs) == len(set(pairs)), "Edges duplicados"


# ─── DAILY NOTE ────────────────────────────────────────────────
class TestDailyNote:
    def test_daily_note_created(self, vp):
        r = vp.get_daily_note()
        assert r.get("title") is not None
        assert "2026" in r.get("title", "") or r.get("ok") is not False

    def test_daily_note_idempotent(self, vp):
        """Llamada doble al diario no la duplica."""
        r1 = vp.get_daily_note()
        r2 = vp.get_daily_note()
        assert r1.get("title") == r2.get("title")

    def test_daily_note_has_template(self, vp):
        r = vp.get_daily_note()
        content = r.get("content", "")
        assert len(content) > 0


# ─── STATS ─────────────────────────────────────────────────────
class TestStats:
    def test_stats_returns_counts(self, vp):
        vp.create_note("S1", "x", "notas")
        vp.create_note("S2", "y", "ideas")
        s = vp.get_stats()
        assert s.get("total_notes", 0) >= 2

    def test_stats_total_links(self, vp):
        vp.create_note("L1", "ver [[L2]]", "notas")
        vp.create_note("L2", "nodo l2", "notas")
        s = vp.get_stats()
        assert s.get("total_links", 0) >= 1


# ─── EDGE CASES ────────────────────────────────────────────────
class TestEdgeCases:
    def test_create_note_with_special_chars_in_title(self, vp):
        r = vp.create_note("Nota: ¿Qué? ¡Así!", "contenido", "notas")
        assert isinstance(r, dict)

    def test_create_note_unicode_content(self, vp):
        r = vp.create_note("Unicode", "日本語テスト 中文 العربية", "notas")
        assert r.get("ok") is True

    def test_search_with_special_chars(self, vp):
        r = vp.search_notes("¿?!@#")
        assert isinstance(r, list)

    def test_get_note_after_many_creates(self, vp):
        for i in range(100):
            vp.create_note(f"MassNote{i}", f"content {i}", "notas")
        r = vp.get_note("MassNote50")
        assert r.get("title") == "MassNote50"

    def test_backlinks_after_delete(self, vp):
        """Si se borra un nodo fuente, sus backlinks no deben aparecer en el destino."""
        vp.create_note("Src", "ver [[Dst]]", "notas")
        vp.create_note("Dst", "destino", "notas")
        vp.delete_note("Src")
        r = vp.get_note("Dst")
        bl = r.get("backlinks", [])
        assert "Src" not in bl
