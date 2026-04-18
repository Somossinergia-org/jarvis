# DUPLICATES MAP — JARVIS Nexus 3D

Fecha: 2026-04-18

## Duplicados funcionales detectados

### 1. Sistema de notas duplicado (RESUELTO)

| Módulo | Responsabilidad | Decisión |
|---|---|---|
| `plugins/productivity_plugin.py::add_note` | Notas simples en JSON | ⚠️ Mantener — sirve al brain tool |
| `plugins/vault_plugin.py::create_note` | Notas en Markdown + SQLite | ✅ CANONICO |
| `server.py /api/notes` | API para notas simples | 🔄 Renombrado a `create_simple_note` |
| `server.py /api/vault/note` | API para vault completo | ✅ CANONICO |

**Acción tomada**: Los endpoints `/api/notes` ahora usan alias explícitos `prod_*`. El vault es la fuente de verdad para toda nota nueva del usuario.

---

### 2. Funciones de extracción de texto

| Función | Archivo | Hace |
|---|---|---|
| `_extract(content)` | `vault_plugin.py` | Extrae `[[links]]` y `#tags` |
| Regex inline en `brain.py` | `brain.py` (varios) | Parsing puntual de respuestas |

**Decisión**: No son duplicadas en responsabilidad. `_extract` es específica del vault. Se mantiene separada.

---

### 3. Imports de pathlib/os duplicados

Detectado en: `server.py`, `vault_plugin.py`, `system_plugin.py`
**Decisión**: Normal en Python — no son duplicados lógicos.

---

## Dependencias no usadas (Python)

| Paquete | Archivo | Estado |
|---|---|---|
| `asyncio` | `server.py` | ✅ ELIMINADO |
| `sys` | `system_plugin.py` | ✅ ELIMINADO |
| `json` | `brain.py` (en scope local) | ✅ ELIMINADO |
| `delete_task` de productivity | `brain.py` | ✅ ELIMINADO |
| `Request`, `FileResponse` | `server.py` | ✅ ELIMINADO |

---

## Dependencias no usadas (JavaScript)

| Elemento | Archivo | Estado |
|---|---|---|
| `package.json` con next.js | `package.json` | ⚠️ Next.js archivado pero el archivo permanece |
| CDN face-api.js (no usado en prod a veces) | `index.html` | ✅ Usado en auth biométrica |
| CDN MediaPipe | `index.html` | ✅ Usado en gestos |

---

## Estilos CSS

- `static/css/jarvis.css` (28KB) — extraído del monolito
- No hay CSS duplicado detectado
- Variables CSS (`--txd`, `--r`, etc.) bien centralizadas

---

## Funciones JavaScript duplicadas o similares

| Función | Similar a | Diferencia | Decisión |
|---|---|---|---|
| `enterFSMode3D()` | `enterNotesGraph3D()` | FS navega árbol, Notes navega grafo | ✅ Separadas por diseño |
| `exitFSMode()` | `exitNotesGraph3D()` | Misma lógica de cleanup | ⚠️ Refactor futuro: extraer `_cleanupScene()` |
| `showNotif()` | `showGBadge()` | Notif = modal, Badge = HUD chip | ✅ Diferentes UI |
| `flyToNode()` | `flyAnim` inline | Anims de cámara | ✅ Mismo sistema |

---

## Conclusión

Tras la auditoría:
- **0 duplicados críticos** en producción
- **5 imports eliminados** que causaban warnings
- **1 sistema de notas canonizado** (vault > productivity para usuario)
- El código está limpio sin redundancias lógicas visibles
