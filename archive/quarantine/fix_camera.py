"""
Camera bulletproof fix:
- Retry logic with multiple camera constraints (HD → SD → lowest)
- Auto-reconnect on stream end
- Watchdog that checks every 3s and restarts if needed
- Works even with permissions denied (graceful fallback)
- Both scanner-video and cam-video always stay in sync
"""
import pathlib

hf = pathlib.Path("static/index.html")
h = hf.read_text(encoding="utf-8")

OLD_CAMERA = """async function startAuth(){
  setAuthStatus('ACTIVANDO CÁMARA...',null,10);
  try{
    const stream=await navigator.mediaDevices.getUserMedia({video:{width:{ideal:640},height:{ideal:480},facingMode:'user'},audio:false});
    cameraStream=stream;
    document.getElementById('scanner-video').srcObject=stream;
    document.getElementById('cam-video').srcObject=stream;
    await document.getElementById('scanner-video').play();
    document.getElementById('cam-video').play().catch(()=>{});
    cameraActive=true;
    setAuthStatus('CÁMARA ACTIVA','Cargando inteligencia neural...',25);
    loadFaceApi();
  }catch(e){
    setAuthStatus('SIN ACCESO A CÁMARA',e.name+': '+e.message,0,'var(--r)');
    setTimeout(()=>activateMainUI('Invitado'),2500);
  }
}"""

NEW_CAMERA = """// ══════════════════════════════════════════════════
// CAMERA MANAGER — BULLETPROOF, NEVER FAILS
// ══════════════════════════════════════════════════
let camRetries = 0;
let camWatchdog = null;
const CAM_CONSTRAINTS = [
  // Best quality first
  {video:{width:{ideal:1280},height:{ideal:720},facingMode:'user'},audio:false},
  // HD fallback
  {video:{width:{ideal:640},height:{ideal:480},facingMode:'user'},audio:false},
  // SD fallback
  {video:{width:{ideal:320},height:{ideal:240}},         audio:false},
  // Any camera at all
  {video:true, audio:false},
];

async function startCamera(constraintIdx) {
  if (constraintIdx === undefined) constraintIdx = 0;
  if (constraintIdx >= CAM_CONSTRAINTS.length) {
    // Exhausted all constraints — run without camera
    console.warn('[CAM] All constraints failed — running in no-video mode');
    cameraActive = false;
    document.getElementById('mc-badge').textContent = '⚠ SIN CÁMARA';
    return null;
  }
  try {
    const stream = await navigator.mediaDevices.getUserMedia(CAM_CONSTRAINTS[constraintIdx]);
    return stream;
  } catch (e) {
    console.warn('[CAM] Constraint', constraintIdx, 'failed:', e.name);
    if (e.name === 'NotAllowedError' || e.name === 'PermissionDeniedError') {
      // User denied — don't retry, show message
      return 'DENIED';
    }
    // Hardware/format error — try next constraint
    return startCamera(constraintIdx + 1);
  }
}

function attachStream(stream) {
  if (!stream) return;
  cameraStream = stream;
  cameraActive = true;

  const sv = document.getElementById('scanner-video');
  const cv = document.getElementById('cam-video');

  [sv, cv].forEach(vid => {
    if (!vid) return;
    vid.srcObject = stream;
    vid.muted = true;
    vid.playsInline = true;
    // Force play with retry
    const tryPlay = () => vid.play().catch(() => setTimeout(tryPlay, 500));
    tryPlay();
  });

  // Monitor stream health — restart if tracks end
  stream.getTracks().forEach(track => {
    track.addEventListener('ended', () => {
      console.warn('[CAM] Track ended — restarting camera...');
      cameraActive = false;
      setTimeout(restartCamera, 1000);
    });
    track.addEventListener('mute', () => {
      console.warn('[CAM] Track muted — will monitor...');
    });
  });

  // Update badge
  const badge = document.getElementById('mc-badge');
  if (badge) badge.textContent = '● LIVE';
}

async function restartCamera() {
  camRetries++;
  console.log('[CAM] Restarting (attempt ' + camRetries + ')...');

  // Stop existing stream gracefully
  if (cameraStream) {
    try { cameraStream.getTracks().forEach(t => t.stop()); } catch(e) {}
    cameraStream = null;
  }
  cameraActive = false;

  const badge = document.getElementById('mc-badge');
  if (badge) badge.textContent = '↺ RECONECTANDO...';

  // Wait before retry (exponential backoff, max 5s)
  const wait = Math.min(500 * Math.pow(1.5, Math.min(camRetries - 1, 6)), 5000);
  await new Promise(r => setTimeout(r, wait));

  const stream = await startCamera(0);
  if (stream && stream !== 'DENIED') {
    attachStream(stream);
    console.log('[CAM] Restarted OK');
    camRetries = 0;
    // Resume face detection if it was active
    if (faceApiReady && !faceDetectionInterval) startFaceDetection();
    // Resume hands if active
    if (handsEnabled && !hDet) startHands();
  } else if (stream === 'DENIED') {
    if (badge) badge.textContent = '✕ PERMISO DENEGADO';
  } else {
    // Try again after 3s
    setTimeout(restartCamera, 3000);
  }
}

// Watchdog — checks camera health every 3 seconds
function startCameraWatchdog() {
  if (camWatchdog) clearInterval(camWatchdog);
  camWatchdog = setInterval(() => {
    if (!cameraActive || !cameraStream) return;
    const tracks = cameraStream.getTracks();
    const videoTrack = tracks.find(t => t.kind === 'video');
    if (!videoTrack || videoTrack.readyState === 'ended') {
      console.warn('[CAM] Watchdog: dead track detected');
      restartCamera();
    }
    // Also check video element is actually producing frames
    const cv = document.getElementById('cam-video');
    if (cv && cv.readyState < 2 && cameraActive) {
      console.warn('[CAM] Watchdog: video stalled');
      const tryPlay = () => cv.play().catch(() => {});
      tryPlay();
    }
  }, 3000);
}

async function startAuth(){
  setAuthStatus('ACTIVANDO CÁMARA...',null,10);

  // Check if getUserMedia is available
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    setAuthStatus('SIN SOPORTE DE CÁMARA','Navegador no compatible',0,'var(--r)');
    document.getElementById('auth-register-btn').style.display='flex';
    setTimeout(()=>activateMainUI('Invitado'),3000);
    return;
  }

  const stream = await startCamera(0);

  if (!stream) {
    // No camera available at all
    setAuthStatus('CÁMARA NO DISPONIBLE','Modo sin cámara activado',30,'var(--w)');
    cameraActive = false;
    document.getElementById('auth-register-btn').style.display='flex';
    setTimeout(()=>activateMainUI('Invitado'),3000);
    return;
  }

  if (stream === 'DENIED') {
    setAuthStatus('PERMISO DENEGADO','Accede a Configuración → Privacidad → Cámara y permite el acceso',0,'var(--r)');
    document.getElementById('auth-register-btn').style.display='flex';
    setTimeout(()=>activateMainUI('Invitado'),4000);
    return;
  }

  attachStream(stream);
  setAuthStatus('CÁMARA ACTIVA','Cargando inteligencia neural...',25);
  startCameraWatchdog();
  loadFaceApi();
}"""

if OLD_CAMERA in h:
    h = h.replace(OLD_CAMERA, NEW_CAMERA)
    print("startAuth replaced with bulletproof camera")
else:
    # Find and replace just the startAuth function
    s = h.find("async function startAuth(){")
    e = h.find("async function loadFaceApi(){")
    if s > 0 and e > s:
        h = h[:s] + NEW_CAMERA + "\n\n" + h[e:]
        print("startAuth replaced (boundary method)")
    else:
        print("ERROR: could not find startAuth boundaries")
        print("startAuth at:", h.find("async function startAuth"))
        print("loadFaceApi at:", h.find("async function loadFaceApi"))

hf.write_text(h, encoding="utf-8")
print(f"DONE: {len(h)} chars")
print("bulletproof:", "startCameraWatchdog" in h)
print("auto-retry:", "restartCamera" in h)
print("multi-constraint:", "CAM_CONSTRAINTS" in h)
