"""
plugins/models.py
Contratos de datos canónicos para el sistema JARVIS.
Fuente de verdad para entidades del grafo, notas y sistema.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


# ─────────────────────────────────────────────────────────────
# GRAPH NODE CONTRACT
# Cada nodo del grafo 3D debe satisfacer este contrato.
# ─────────────────────────────────────────────────────────────

class NodeType(str, Enum):
    ROOT = "root"
    DOMAIN = "domain"
    MODULE = "module"
    NOTE = "note"
    FILE = "file"
    FOLDER = "folder"
    TAG = "tag"
    PERSON = "person"


class NodeStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    EXPERIMENTAL = "experimental"
    LEGACY = "legacy"


class GraphNode(BaseModel):
    """Contrato canónico de nodo del grafo 3D de JARVIS."""
    id: str = Field(..., description="Identificador único del nodo")
    parent_id: Optional[str] = Field(None, description="ID del nodo padre; None para raíz")
    type: NodeType = Field(..., description="Tipo de nodo")
    label: str = Field(..., description="Etiqueta visible en el grafo")
    status: NodeStatus = Field(NodeStatus.ACTIVE, description="Estado del nodo")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Datos adicionales del nodo")
    children_count: int = Field(0, description="Número de hijos (cargados o pendientes)")
    depth: int = Field(0, description="Profundidad en el árbol (0 = raíz)")
    is_expanded: bool = Field(False, description="Si el subgrafo está desplegado")
    is_visible: bool = Field(True, description="Si el nodo es visible en la escena")
    is_focused: bool = Field(False, description="Si el nodo está en modo focus")
    weight: int = Field(1, description="Importancia visual (links + conexiones)")
    folder: Optional[str] = Field(None, description="Carpeta de pertenencia (para notas)")
    tags: list[str] = Field(default_factory=list, description="Etiquetas semánticas")

    class Config:
        use_enum_values = True


class GraphEdge(BaseModel):
    """Arista entre dos nodos del grafo."""
    from_id: str = Field(..., alias="from")
    to_id: str = Field(..., alias="to")
    weight: float = Field(1.0, description="Fuerza de la conexión")
    label: Optional[str] = Field(None, description="Etiqueta de la arista (tipo de relación)")

    class Config:
        populate_by_name = True


class GraphData(BaseModel):
    """Respuesta completa del endpoint /api/vault/graph."""
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    total_nodes: int
    total_edges: int
    max_depth: int = 0


# ─────────────────────────────────────────────────────────────
# VAULT NOTE CONTRACT
# ─────────────────────────────────────────────────────────────

class VaultNote(BaseModel):
    """Contrato de nota en la bóveda."""
    id: str
    title: str
    content: str = ""
    folder: str = "notas"
    tags: list[str] = Field(default_factory=list)
    created: Optional[str] = None
    updated: Optional[str] = None
    outlinks: list[str] = Field(default_factory=list)
    backlinks: list[str] = Field(default_factory=list)
    weight: int = 1


class VaultStats(BaseModel):
    """Estadísticas de la bóveda."""
    total_notes: int
    total_links: int
    folders: dict[str, int] = Field(default_factory=dict)
    top_tags: list[str] = Field(default_factory=list)
