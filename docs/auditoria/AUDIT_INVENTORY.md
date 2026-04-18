# JARVIS — Inventario de auditoría
_Generado: 2026-04-18T09:19:02.289909_

## Árbol de archivos (raíz)
```
└─ .env (773B)
└─ .env.example (265B)
└─ .gitignore (56B)
📁 .vscode/
  └─ settings.json (836B)
  └─ tasks.json (1,054B)
└─ brain.py (17,892B)
└─ config.py (1,852B)
📁 data/
  └─ memory.json (17,585B)
📁 docs/
  📁 arquitectura/
  📁 auditoria/
  📁 decisiones/
└─ INSTALAR_Y_ARRANCAR.bat (3,154B)
└─ jarvis.log (134B)
└─ jarvis_app.py (2,409B)
└─ jarvis_inicio.vbs (787B)
└─ LEEME.md (2,916B)
└─ package.json (303B)
📁 plugins/
  └─ __init__.py (36B)
  └─ memory_plugin.py (1,773B)
  └─ productivity_plugin.py (2,688B)
  └─ system_plugin.py (12,699B)
  └─ vault_plugin.py (10,479B)
└─ requirements.txt (174B)
📁 scripts/
  └─ audit_repo.py (2,319B)
└─ server.py (16,908B)
└─ start.py (3,483B)
└─ start_jarvis.bat (255B)
📁 static/
  📁 css/
  └─ index.html (145,114B)
  └─ jarvis_logo.png (707,291B)
  📁 js/
└─ tts_engine.py (6,744B)
```

## Módulos Python
### `brain.py` (17,892B)
Funciones: _get_weather, _search_web, _control_home, _execute_tool, __init__, _load_persistent_memory, _get_system_prompt, think, clear_history, get_stats

### `config.py` (1,852B)
_(sin funciones detectadas)_

### `jarvis_app.py` (2,409B)
Funciones: start_server, wait_for_server

### `plugins\__init__.py` (36B)
_(sin funciones detectadas)_

### `plugins\memory_plugin.py` (1,773B)
Funciones: _load_memory, _save_memory, save_memory, load_recent_memory, get_memory_stats, clear_memory

### `plugins\productivity_plugin.py` (2,688B)
Funciones: _load_json, _save_json, add_task, list_tasks, complete_task, delete_task, add_note, list_notes, search_notes

### `plugins\system_plugin.py` (12,699B)
Funciones: open_application, close_application, execute_command, open_url, control_volume, control_media, take_screenshot, type_text_at_cursor, press_key, list_running_apps, get_system_info, get_datetime_info

### `plugins\vault_plugin.py` (10,479B)
Funciones: init_vault, _db, _extract, _safe_path, create_note, get_note, update_note, delete_note, list_notes, search_notes, get_graph, get_daily_note, reindex_vault, _recalc, get_stats

### `scripts\audit_repo.py` (2,319B)
Funciones: audit

### `server.py` (16,908B)
Funciones: lifespan, home, chat, tts_direct, clear_history, stats, system_info, system_extended, _fmt, datetime_info, sys_volume, sys_media, sys_mouse, websocket_hands, launch_app

### `start.py` (3,483B)
Funciones: check_dependencies, check_env, create_dirs, main

### `tts_engine.py` (6,744B)
Funciones: _clean_text, _elevenlabs_tts, _openai_tts, _edgetts_tts, _gtts_tts, _gen, text_to_speech, list_spanish_voices, clean_cache

## Activos estáticos
- `static/index.html` — 145,114B
- `static/jarvis_logo.png` — 707,291B

## Dependencias Python
```
fastapi==0.115.6
uvicorn[standard]==0.34.0
openai==1.82.0
edge-tts==7.0.2
python-dotenv==1.1.0
pydantic==2.11.1
aiofiles==24.1.0
websockets==14.2
httpx==0.28.1
psutil==7.0.0
```
