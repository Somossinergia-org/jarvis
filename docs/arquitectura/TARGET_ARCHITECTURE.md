# JARVIS v5.0 — Arquitectura Final

## Visión general

JARVIS es un asistente de escritorio personal inmersivo construido sobre un stack Python/FastAPI + Three.js que combina inteligencia artificial, control por voz/gestos/biometría y un grafo de conocimiento 3D navegable.

## Stack técnico

```
┌─────────────────────────────────────────────────────┐
│                    JARVIS v5.0                       │
│                                                      │
│  Frontend: Three.js (CDN) + HTML/CSS/JS              │
│  ┌──────────────────────────────────────────────┐   │
│  │  Cerebro 3D (7 nodos)                        │   │
│  │  ├── MÚSICA · TRABAJO · COMM · MEMORIA       │   │
│  │  ├── ARCHIVOS (FS3D navegable)               │   │
│  │  ├── SISTEMA (telemetría en tiempo real)     │   │
│  │  └── NOTAS (Knowledge Graph 3D)             │   │
│  │       ├── Partículas por nota                │   │
│  │       ├── Líneas de conexión ([[enlaces]])   │   │
│  │       ├── Minimapa 2D + Breadcrumb           │   │
│  │       ├── Search + Focus Mode                │   │
│  │       └── Editor inline por nodo             │   │
│  └──────────────────────────────────────────────┘   │
│                                                      │
│  Backend: Python 3.12 + FastAPI + Uvicorn            │
│  ┌──────────────────────────────────────────────┐   │
│  │  brain.py       → GPT-4o + function calling  │   │
│  │  tts_engine.py  → edge-tts (voz española)    │   │
│  │  server.py      → API REST + WebSocket       │   │
│  │  plugins/                                    │   │
│  │  ├── vault_plugin.py  → SQLite + notas .md   │   │
│  │  ├── system_plugin.py → psutil + OS          │   │
│  │  └── memory_plugin.py → historial JSON       │   │
│  └──────────────────────────────────────────────┘   │
│                                                      │
│  Persistencia: C:\Users\orihu\JarvisVault\           │
│  Base de datos: jarvis.db (SQLite)                   │
│  Memoria: data/memory.json                           │
└─────────────────────────────────────────────────────┘
```

## Estructura de carpetas

```
jarvis/
├── server.py            ← API principal FastAPI
├── brain.py             ← Orquestador GPT-4o
├── tts_engine.py        ← Síntesis de voz
├── config.py            ← Variables de entorno
├── start.py             ← Script de arranque
├── requirements.txt     ← Dependencias Python
├── .env                 ← Secretos (no commitear)
├── .env.example         ← Plantilla de secretos
├── .gitignore
├── plugins/
│   ├── vault_plugin.py      ← Conocimiento + notas
│   ├── system_plugin.py     ← Sistema operativo
│   └── memory_plugin.py     ← Historial conversación
├── static/
│   ├── index.html           ← Frontend (108KB)
│   ├── css/jarvis.css       ← Estilos (separados)
│   └── jarvis_logo.png
├── data/
│   └── memory.json          ← Memoria persistente
├── scripts/
│   ├── audit_repo.py        ← Auditoría automática
│   ├── modularize_html.py   ← Extractor CSS/JS
│   └── add_graph_features.py
├── docs/
│   ├── auditoria/           ← Reportes de auditoría
│   ├── arquitectura/        ← Este documento
│   └── decisiones/          ← ADRs
├── archive/
│   └── quarantine/          ← Código archivado
└── .vscode/
    ├── settings.json
    └── tasks.json
```

## Módulos activos

| Módulo | Responsabilidad | API |
|---|---|---|
| `brain.py` | LLM + tool calling + memoria | `/api/chat` |
| `tts_engine.py` | Síntesis de voz | `/api/tts` |
| `vault_plugin.py` | Notas + grafo + búsqueda | `/api/vault/*` |
| `system_plugin.py` | SO + apps + telemetría | `/api/system/*` |
| `memory_plugin.py` | Historial conversación | interno |

## API Endpoints

```
POST /api/chat              — Chat con JARVIS
POST /api/tts               — Text-to-speech
GET  /api/system/info       — Info del sistema
GET  /api/system/extended   — Telemetría completa
POST /api/apps/{name}       — Abrir aplicación
GET  /api/vault/stats       — Stats de la bóveda
GET  /api/vault/graph       — Grafo completo (nodos+edges)
GET  /api/vault/notes       — Listar notas
GET  /api/vault/note/{title}— Obtener nota
POST /api/vault/note        — Crear nota
PUT  /api/vault/note/{title}— Actualizar nota
DELETE /api/vault/note/{title} — Eliminar nota
GET  /api/vault/search?q=  — Búsqueda full-text
GET  /api/vault/daily       — Nota diaria
POST /api/vault/reindex     — Reindexar vault
WS   /ws/hands              — WebSocket gestos
```

## Convenciones

- Python: snake_case para funciones/vars, PascalCase para clases
- JS: camelCase para funciones/vars
- HTML IDs: kebab-case
- Commits: `type(scope): description`
- Ramas: `feature/`, `fix/`, `audit/`, `docs/`

## Rollback

```bash
git checkout main          # Restaurar estado anterior a audit
git stash                  # Guardar cambios sin commit
git log --oneline -10      # Ver historial
```
