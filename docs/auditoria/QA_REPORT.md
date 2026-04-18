# QA REPORT — JARVIS Nexus 3D
Fecha: 2026-04-18
Rama: hardening/phase-3-qa

## Resumen ejecutivo

| Métrica | Resultado |
|---|---|
| Lint crítico (F4xx, F8xx) | ✅ **0 errores** |
| Lint total (estilo) | ⚠️ ~120 warnings de estilo (E2xx/E3xx) — no críticos |
| Tests unitarios | ✅ **65/65 PASSED** |
| Test time | 2.08s |
| Cobertura estimada | ~92% (vault_plugin) / 100% (models) |
| Servidor arranca | ✅ Verificado |
| Funcionalidad 3D | ✅ Verificado en browser |

---

## Bloque A — Lint

### Errores críticos corregidos
| Error | Archivo | Descripción | Estado |
|---|---|---|---|
| F821 `add_note` undefined | `server.py:442` | Nombre no importado en scope | ✅ CORREGIDO |
| F821 `list_notes` undefined | `server.py:446` | Ídem | ✅ CORREGIDO |
| F821 `search_notes` undefined | `server.py:450` | Ídem | ✅ CORREGIDO |
| F401 `asyncio` unused | `server.py:4` | Import sin uso | ✅ CORREGIDO |
| F401 `Request` unused | `server.py:14` | Import sin uso | ✅ CORREGIDO |
| F401 `FileResponse` unused | `server.py:15` | Import sin uso | ✅ CORREGIDO |
| F811 `asyncio` redefined | `server.py:328` | Import duplicado | ✅ CORREGIDO |
| F401 `sys` unused | `system_plugin.py:5` | Import sin uso | ✅ CORREGIDO |
| F841 `result` unused | `system_plugin.py:218` | Variable silenciosa | ✅ CORREGIDO |
| F401 `delete_task` unused | `brain.py:235` | Import sin uso | ✅ CORREGIDO |
| F401 `json` unused | `brain.py:239` | Import sin uso | ✅ CORREGIDO |
| F841 `level` unused | `brain.py:293` | Variable silenciosa | ✅ CORREGIDO |

### Warnings de estilo (no críticos)
- E302 spacing: ~40 instancias — estilo (no rompe funcionalidad)
- E501 líneas largas: 2 instancias en vault_plugin — aceptables
- Recomendación: normalizar progresivamente con black formatter

---

## Bloque B — Bugs reales detectados por los tests

| Bug | Impacto | Corrección |
|---|---|---|
| `sqlite3.OperationalError: database is locked` | Medio — fallo en concurrencia alta | ✅ Context manager + `busy_timeout=3000` |
| Self-loop en grafo (nota → sí misma) | Alto — grafo corrupto | ✅ Filtrado en `create_note`, `update_note`, `reindex_vault`, query SQL |
| FTS5 `delete` con 5 columns (schema 3-col) | Alto — delete_note falla en producción | ✅ `INSERT INTO notes_fts(notes_fts, rowid) VALUES ('delete', ?)` |
| Título vacío aceptado sin validación | Medio — nota inválida creada | ✅ Guard en `create_note` |
| Constructor `_db()` no usaba env override | Medio — tests sin aislamiento | ✅ `_resolve_paths()` refactorizado |

---

## Bloque C — Tests (Fase 4 completada)

### Tests creados
- `__tests__/test_vault_plugin.py` — 47 tests
- `__tests__/test_models.py` — 18 tests

### Cobertura por clase
| Clase | Tests | Resultado |
|---|---|---|
| TestVaultInit | 3 | ✅ 3/3 |
| TestCreateNote | 7 | ✅ 7/7 |
| TestGetNote | 6 | ✅ 6/6 |
| TestUpdateNote | 4 | ✅ 4/4 |
| TestDeleteNote | 3 | ✅ 3/3 |
| TestListNotes | 4 | ✅ 4/4 |
| TestSearchNotes | 5 | ✅ 5/5 |
| TestGraph | 5 | ✅ 5/5 |
| TestDailyNote | 3 | ✅ 3/3 |
| TestStats | 2 | ✅ 2/2 |
| TestEdgeCases | 5 | ✅ 5/5 |
| TestGraphNodeContract | 7 | ✅ 7/7 |
| TestGraphEdgeContract | 4 | ✅ 4/4 |
| TestGraphDataContract | 2 | ✅ 2/2 |
| TestVaultNoteContract | 3 | ✅ 3/3 |
| TestVaultStatsContract | 2 | ✅ 2/2 |

---

## Bloque D — Contratos de datos

Creado: `plugins/models.py`

### GraphNode (contrato completo)
```
id, parent_id, type, label, status, metadata, children_count,
depth, is_expanded, is_visible, is_focused, weight, folder, tags
```
- Tipado con Pydantic v2
- Enums: NodeType (8 tipos), NodeStatus (4 estados)
- Validación automática en tiempo de ejecución

### GraphEdge
```
from_id (alias: from), to_id (alias: to), weight, label
```

### GraphData
```
nodes[], edges[], total_nodes, total_edges, max_depth
```

---

## Riesgos vigilados

| Riesgo | Estado |
|---|---|
| Fuga de memoria Three.js | ⚠️ `exitNotesGraph3D_cleanup()` hace dispose — verificado manual |
| Re-render excesivo del canvas | ✅ Actualización solo cuando `notesModeActive` |
| Búsqueda por tecla en grafo | ✅ Sólo ejecuta en Enter, no por cada tecla |
| Focus mode sin contrato de edges | ✅ `line.userData = {from, to}` añadido |
| Breadcrumb desinc con cámara | ⚠️ Riesgo bajo — pushBreadcrumb llamado en onNoteNodeClick |
| Self-loops en grafo | ✅ Corregido en código + test específico |

---

## Estado del sistema

```
✅ main arranca — verificado
✅ lint 0 errores críticos — verificado
✅ 65/65 tests pasan — verificado
✅ no self-loops — test corregido + code fix
✅ delete FTS5 correcto — test corregido + code fix
✅ DB no se queda bloqueada — context manager
✅ contratos de nodo documentados y validados
✅ grafo 3D con minimapa, breadcrumb, search, focus mode
```
