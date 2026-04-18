# APP MATRIX — JARVIS Nexus 3D

Fecha auditoría: 2026-04-18
Auditor: Antigravity AI
Rama: audit/jarvis-nexus-3d

## Decisiones por módulo

| Módulo | Tipo | Decisión | Owner Funcional | Owner Técnico | Fuente de Verdad | Justificación |
|---|---|---|---|---|---|---|
| `brain.py` | CORE_CANONICO | ✅ CONSERVAR | Sistema IA | Backend | `brain.py` | Orquestador central GPT-4o, función calling, memoria |
| `server.py` | CORE_CANONICO | ✅ CONSERVAR + REFACTOR | Sistema | Backend | `server.py` | API principal, WebSocket, rutas — refactor menor de imports |
| `config.py` | CORE_CANONICO | ✅ CONSERVAR | Config | Backend | `.env` | Variables de entorno centralizadas |
| `tts_engine.py` | CORE_CANONICO | ✅ CONSERVAR | Voz | Backend | `tts_engine.py` | Único proveedor TTS funcional (edge-tts) |
| `plugins/vault_plugin.py` | CORE_CANONICO | ✅ CONSERVAR | Conocimiento | Backend | `JarvisVault/*.md` + `jarvis.db` | ORM del sistema de notas, SQLite, grafo |
| `plugins/system_plugin.py` | CORE_CANONICO | ✅ CONSERVAR | Sistema | Backend | `psutil` + OS | Telemetría, control de apps, volumen |
| `plugins/memory_plugin.py` | CORE_CANONICO | ✅ CONSERVAR | Memoria | Backend | `data/memory.json` | Historial de conversación persistente |
| `plugins/productivity_plugin.py` | DUPLICADO_A_FUSIONAR | ⚠️ FUSIONAR en vault | Productividad | Backend | `vault_plugin` | Tareas simples duplicadas por vault; migrar tasks a vault |
| `static/index.html` | REEMPLAZABLE | 🔄 MODULARIZAR | UI | Frontend | `index.html` | Monolito 145KB — separar en módulos JS/CSS sin cambiar funcionalidad |
| `start.py` | CORE_CANONICO | ✅ CONSERVAR | Arranque | Backend | `start.py` | Script de arranque con auto-install |
| `jarvis_app.py` | EXPERIMENTAL_DESACTIVADO | ⚠️ EVALUAR | UI Desktop | Backend | — | PyWebView shell; sin uso activo desde migración a web |
| `app/` (Next.js) | LEGACY_A_ARCHIVAR | ❌ ARCHIVADO | — | — | — | Dead code. API routes duplicadas. Nunca en runtime. |
| `fix_*.py` (18 scripts) | LEGACY_A_ARCHIVAR | ❌ ARCHIVADO | — | — | — | Scripts de parche temporal. Ya integrados en código. |
| `test_*.mp3` (8 archivos) | LEGACY_A_ARCHIVAR | ❌ ARCHIVADO | — | — | — | Residuos de testing TTS |
| `scripts/audit_repo.py` | CORE_CANONICO | ✅ NUEVO | DevOps | Backend | — | Script de auditoría automática |

## Reglas de módulo

Cada módulo activo declara:
- **Owner funcional**: quién lo usa en la experiencia de usuario
- **Owner técnico**: archivo/equipo responsable del código
- **Fuente de verdad**: de dónde viene el dato canónico
- **Decisión**: conservar / fusionar / reemplazar / archivar

## Módulos por crear (roadmap)

| Módulo | Prioridad | Descripción |
|---|---|---|
| `plugins/tasks_plugin.py` | ALTA | Gestión de tareas (fusión de productivity_plugin) |
| `static/js/brain3d.js` | ALTA | Three.js scene separada del monolito |
| `static/js/notes-graph.js` | ALTA | Grafo 3D de notas separado |
| `static/js/voice.js` | MEDIA | Web Speech API separado |
| `static/js/ui.js` | MEDIA | Paneles y HUD separados |
| `static/css/jarvis.css` | MEDIA | Estilos separados |
| `tests/test_vault.py` | ALTA | Tests unitarios vault_plugin |
| `tests/test_brain.py` | MEDIA | Tests unitarios brain.py |
