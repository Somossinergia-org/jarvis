QUARANTINE LOG — Archivos movidos durante auditoría JARVIS Nexus 3D
Fecha: 2026-04-18
Rama: audit/jarvis-nexus-3d
Commit base: 42b9184

═══════════════════════════════════════════════════
MÓDULOS ARCHIVADOS Y MOTIVO
═══════════════════════════════════════════════════

app_nextjs_dead/
  Motivo: Carpeta app/ de Next.js. Contiene API routes (chat, tts, clear) y 
  page.js de 39KB que duplican funcionalidad ya existente en server.py/FastAPI.
  Nunca se arrancaba (package.json apunta a next dev pero el sistema real usa uvicorn).
  Decisión: ARCHIVAR. No tiene owner funcional activo.

bigfix.py, editall.py, master_fix.py
  Motivo: Scripts de parche masivo acumulados durante el desarrollo iterativo.
  No forman parte de la arquitectura; son artefactos del proceso de construcción.
  Decisión: ARCHIVAR.

fix_bl.py, fix_bl2.py, fix_bugs3.py, fix_camera.py, fix_dim.py
fix_fs_anim.py, fix_js.py, fix_notes_strings.py, fix_orphan.py
fix_regex.py, fix_scope.py, fix_server.py, fix_tdz.py, fix_tdz_fs.py
  Motivo: Scripts de corrección puntual. Cada uno solucionó un bug específico
  mediante manipulación de texto del index.html. Su funcionalidad ya está
  integrada en el código actual. No deben ejecutarse de nuevo.
  Decisión: ARCHIVAR.

inject_fb.py, inject_notes.py, patch_notes_final.py, build_notes_3d.py
rewrite_fs3d.py, update_visual.py
  Motivo: Scripts de inyección de código. Su contenido ya está en index.html.
  Ejecución repetida causaría duplicados.
  Decisión: ARCHIVAR.

test_*.mp3, test_edge_es.mp3, test_es_voz.mp3, test_jarvis.mp3
  Motivo: Archivos de audio residuales de pruebas de TTS. Sin uso en producción.
  Decisión: BORRAR (archivados aquí por seguridad).

dedup.py, validate_js.py, list_voices.py, test_voices.py, chk.py
  Motivo: Scripts de utilidad de desarrollo. No pertenecen al runtime.
  Decisión: ARCHIVAR hasta refactor a scripts/ estructurado.

next.config.js
  Motivo: Configuración de Next.js. Sin uso — stack es FastAPI.
  Decisión: ARCHIVAR junto con app_nextjs_dead/.

═══════════════════════════════════════════════════
RESTAURACIÓN
═══════════════════════════════════════════════════
Para restaurar cualquier archivo: 
  git checkout main -- <archivo>
o copiar manualmente desde archive/quarantine/

Para restaurar todo el estado anterior:
  git checkout main
