"""
__tests__/test_models.py
Tests para los contratos de datos (plugins/models.py).
Valida que el contrato GraphNode, GraphEdge, VaultNote son correctos.
"""
import pytest
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from plugins.models import (
    GraphNode, GraphEdge, GraphData, VaultNote, VaultStats,
    NodeType, NodeStatus
)


class TestGraphNodeContract:
    def test_valid_node_creation(self):
        node = GraphNode(id="n1", type=NodeType.NOTE, label="Mi nota")
        assert node.id == "n1"
        assert node.label == "Mi nota"
        assert node.is_visible is True
        assert node.is_expanded is False
        assert node.children_count == 0

    def test_node_defaults(self):
        node = GraphNode(id="n2", type=NodeType.DOMAIN, label="Dominio")
        assert node.parent_id is None
        assert node.depth == 0
        assert node.status == NodeStatus.ACTIVE
        assert node.tags == []

    def test_node_with_metadata(self):
        node = GraphNode(
            id="n3", type=NodeType.MODULE, label="Módulo",
            metadata={"version": "5.0", "owner": "backend"}
        )
        assert node.metadata["owner"] == "backend"

    def test_node_invalid_missing_required(self):
        with pytest.raises(Exception):
            GraphNode(label="Sin ID ni tipo")  # id y type son requeridos

    def test_node_all_types_valid(self):
        for nt in NodeType:
            node = GraphNode(id=f"n-{nt}", type=nt, label=nt.value)
            assert node.type == nt.value

    def test_node_all_statuses_valid(self):
        for ns in NodeStatus:
            node = GraphNode(id="x", type=NodeType.NOTE, label="x", status=ns)
            assert node.status == ns.value

    def test_node_focus_state(self):
        node = GraphNode(id="f1", type=NodeType.NOTE, label="Focus")
        assert node.is_focused is False
        node2 = node.model_copy(update={"is_focused": True})
        assert node2.is_focused is True


class TestGraphEdgeContract:
    def test_valid_edge(self):
        edge = GraphEdge(**{"from": "n1", "to": "n2"})
        assert edge.from_id == "n1"
        assert edge.to_id == "n2"
        assert edge.weight == 1.0

    def test_edge_no_self_loop_constraint(self):
        # El contrato no prohíbe self-loops (la validación está en el grafo)
        edge = GraphEdge(**{"from": "n1", "to": "n1"})
        assert edge.from_id == edge.to_id  # Existente pero inválido semánticamente

    def test_edge_with_label(self):
        edge = GraphEdge(**{"from": "a", "to": "b", "label": "enlace"})
        assert edge.label == "enlace"

    def test_edge_invalid_missing_from(self):
        with pytest.raises(Exception):
            GraphEdge(**{"to": "n2"})


class TestGraphDataContract:
    def test_empty_graph(self):
        gd = GraphData(nodes=[], edges=[], total_nodes=0, total_edges=0)
        assert gd.total_nodes == 0
        assert gd.max_depth == 0

    def test_graph_with_nodes_and_edges(self):
        n1 = GraphNode(id="n1", type=NodeType.NOTE, label="N1")
        n2 = GraphNode(id="n2", type=NodeType.NOTE, label="N2")
        e = GraphEdge(**{"from": "n1", "to": "n2"})
        gd = GraphData(nodes=[n1, n2], edges=[e], total_nodes=2, total_edges=1)
        assert len(gd.nodes) == 2
        assert len(gd.edges) == 1


class TestVaultNoteContract:
    def test_valid_note(self):
        note = VaultNote(id="v1", title="Mi nota")
        assert note.title == "Mi nota"
        assert note.folder == "notas"
        assert note.tags == []

    def test_note_with_links(self):
        note = VaultNote(
            id="v2", title="Nota con links",
            outlinks=["Otra nota"], backlinks=["Referencia"]
        )
        assert "Otra nota" in note.outlinks
        assert "Referencia" in note.backlinks

    def test_note_weight_default(self):
        note = VaultNote(id="v3", title="test")
        assert note.weight == 1


class TestVaultStatsContract:
    def test_valid_stats(self):
        s = VaultStats(total_notes=5, total_links=3)
        assert s.total_notes == 5
        assert s.folders == {}

    def test_stats_with_folders(self):
        s = VaultStats(
            total_notes=10, total_links=5,
            folders={"notas": 6, "ideas": 4}
        )
        assert s.folders["notas"] == 6
