"use client";

import { useState, useRef, useEffect, useCallback } from "react";

const PARTICLE_COUNT = 2800;
const SYNAPSE_COUNT = 400;
const BRAIN_RADIUS = 180;
const FACE_API_CDN = "https://cdn.jsdelivr.net/npm/@vladmandic/face-api@1.7.14/dist/face-api.js";
const MODEL_URL = "https://cdn.jsdelivr.net/npm/@vladmandic/face-api@1.7.14/model";
const MATCH_THRESHOLD = 0.45;
const OWNER_NAME = "DAVID MIQUEL";

export default function JarvisNeural() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [speakEnabled, setSpeakEnabled] = useState(true);
  const [showWelcome, setShowWelcome] = useState(true);
  const [neuralActivity, setNeuralActivity] = useState(0);
  const [panelOpen, setPanelOpen] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [continuousMode, setContinuousMode] = useState(false);
  const [cameraActive, setCameraActive] = useState(false);
  const [faceStatus, setFaceStatus] = useState("INICIANDO SISTEMAS...");
  const [identityVerified, setIdentityVerified] = useState(false);
  const [faceDetected, setFaceDetected] = useState(false);
  const [showRegister, setShowRegister] = useState(false);
  const [scanProgress, setScanProgress] = useState(0);
  const [biometrics, setBiometrics] = useState(null);

  const chatRef = useRef(null);
  const inputRef = useRef(null);
  const recognitionRef = useRef(null);
  const historyRef = useRef([]);
  const canvasRef = useRef(null);
  const animFrameRef = useRef(null);
  const brainStateRef = useRef({ thinking: false, intensity: 0 });
  const audioRef = useRef(null);
  const continuousModeRef = useRef(false);
  const speakEnabledRef = useRef(true);
  const videoRef = useRef(null);
  const faceCanvasRef = useRef(null);
  const faceIntervalRef = useRef(null);
  const identityVerifiedRef = useRef(false);
  const streamRef = useRef(null);

  useEffect(() => { continuousModeRef.current = continuousMode; }, [continuousMode]);
  useEffect(() => { speakEnabledRef.current = speakEnabled; }, [speakEnabled]);
  useEffect(() => { identityVerifiedRef.current = identityVerified; }, [identityVerified]);

  // ── FACE-API.JS LOADER ─────────────────────────────────
  useEffect(() => {
    let cancelled = false;
    async function initFaceSystem() {
      setFaceStatus("CARGANDO MODULOS BIOMETRICOS...");
      setScanProgress(10);
      try {
        if (!window.faceapi) {
          await new Promise((resolve, reject) => {
            const s = document.createElement("script");
            s.src = FACE_API_CDN;
            s.onload = resolve;
            s.onerror = reject;
            document.head.appendChild(s);
          });
        }
        if (cancelled) return;
        setScanProgress(30);
        setFaceStatus("CARGANDO REDES NEURONALES...");
        await window.faceapi.nets.tinyFaceDetector.loadFromUri(MODEL_URL);
        await window.faceapi.nets.faceLandmark68TinyNet.loadFromUri(MODEL_URL);
        await window.faceapi.nets.faceRecognitionNet.loadFromUri(MODEL_URL);
        if (cancelled) return;
        setScanProgress(60);
        setFaceStatus("ACTIVANDO CAMARA...");
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { width: 320, height: 240, facingMode: "user" },
          audio: false
        });
        if (cancelled) { stream.getTracks().forEach(t => t.stop()); return; }
        streamRef.current = stream;
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          await videoRef.current.play();
        }
        setCameraActive(true);
        setScanProgress(80);
        setFaceStatus("ESCANEANDO ROSTRO...");
        startFaceDetection();
      } catch (e) {
        console.error("Face init error:", e);
        setFaceStatus("CAMARA NO DISPONIBLE");
        setScanProgress(0);
        // Still allow voice without face
        setTimeout(() => {
          setContinuousMode(true);
          startListening();
        }, 2000);
      }
    }
    initFaceSystem();
    return () => {
      cancelled = true;
      if (faceIntervalRef.current) clearInterval(faceIntervalRef.current);
      if (streamRef.current) streamRef.current.getTracks().forEach(t => t.stop());
    };
  }, []);

  function startFaceDetection() {
    if (faceIntervalRef.current) clearInterval(faceIntervalRef.current);
    faceIntervalRef.current = setInterval(async () => {
      if (!videoRef.current || !window.faceapi || videoRef.current.readyState < 2) return;
      try {
        const detection = await window.faceapi
          .detectSingleFace(videoRef.current, new window.faceapi.TinyFaceDetectorOptions({ inputSize: 224, scoreThreshold: 0.4 }))
          .withFaceLandmarks(true)
          .withFaceDescriptor();
        if (detection) {
          setFaceDetected(true);
          drawFaceOverlay(detection);
          setBiometrics({
            confidence: Math.round(detection.detection.score * 100),
            landmarks: detection.landmarks.positions.length,
          });
          const stored = getStoredFace();
          if (stored) {
            const dist = window.faceapi.euclideanDistance(detection.descriptor, new Float32Array(stored));
            if (dist < MATCH_THRESHOLD) {
              if (!identityVerifiedRef.current) {
                setIdentityVerified(true);
                identityVerifiedRef.current = true;
                setFaceStatus("IDENTIDAD VERIFICADA");
                setScanProgress(100);
                brainStateRef.current = { thinking: true, intensity: 1 };
                setTimeout(() => {
                  brainStateRef.current = { thinking: false, intensity: 0.3 };
                  if (!continuousModeRef.current) {
                    setContinuousMode(true);
                    startListening();
                  }
                }, 2000);
              }
            } else {
              setFaceStatus("IDENTIDAD NO RECONOCIDA");
              setIdentityVerified(false);
              identityVerifiedRef.current = false;
            }
          } else {
            setFaceStatus("ROSTRO DETECTADO - REGISTRAR");
            setShowRegister(true);
          }
        } else {
          setFaceDetected(false);
          setBiometrics(null);
          clearFaceOverlay();
          if (identityVerifiedRef.current) {
            setFaceStatus("ROSTRO PERDIDO...");
          }
        }
      } catch (e) { /* silent */ }
    }, 600);
  }

  function drawFaceOverlay(detection) {
    const canvas = faceCanvasRef.current;
    const video = videoRef.current;
    if (!canvas || !video) return;
    const ctx = canvas.getContext("2d");
    canvas.width = video.videoWidth || 320;
    canvas.height = video.videoHeight || 240;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const box = detection.detection.box;
    const verified = identityVerifiedRef.current;
    const color = verified ? "#00ff88" : "#00d4ff";
    // Face frame corners
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.shadowColor = color;
    ctx.shadowBlur = 8;
    const cLen = 15;
    // Top-left
    ctx.beginPath(); ctx.moveTo(box.x, box.y + cLen); ctx.lineTo(box.x, box.y); ctx.lineTo(box.x + cLen, box.y); ctx.stroke();
    // Top-right
    ctx.beginPath(); ctx.moveTo(box.x + box.width - cLen, box.y); ctx.lineTo(box.x + box.width, box.y); ctx.lineTo(box.x + box.width, box.y + cLen); ctx.stroke();
    // Bottom-left
    ctx.beginPath(); ctx.moveTo(box.x, box.y + box.height - cLen); ctx.lineTo(box.x, box.y + box.height); ctx.lineTo(box.x + cLen, box.y + box.height); ctx.stroke();
    // Bottom-right
    ctx.beginPath(); ctx.moveTo(box.x + box.width - cLen, box.y + box.height); ctx.lineTo(box.x + box.width, box.y + box.height); ctx.lineTo(box.x + box.width, box.y + box.height - cLen); ctx.stroke();
    // Scan line animation
    ctx.shadowBlur = 0;
    const scanY = box.y + (Date.now() % 2000) / 2000 * box.height;
    ctx.strokeStyle = color;
    ctx.globalAlpha = 0.4;
    ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(box.x, scanY); ctx.lineTo(box.x + box.width, scanY); ctx.stroke();
    ctx.globalAlpha = 1;
    // Landmarks dots
    ctx.fillStyle = color;
    ctx.globalAlpha = 0.3;
    detection.landmarks.positions.forEach(p => {
      ctx.beginPath(); ctx.arc(p.x, p.y, 1, 0, Math.PI * 2); ctx.fill();
    });
    ctx.globalAlpha = 1;
    // Label
    ctx.font = "bold 10px Orbitron, monospace";
    ctx.fillStyle = color;
    ctx.fillText(verified ? OWNER_NAME : "ANALIZANDO...", box.x, box.y - 6);
  }

  function clearFaceOverlay() {
    const canvas = faceCanvasRef.current;
    if (canvas) {
      const ctx = canvas.getContext("2d");
      ctx.clearRect(0, 0, canvas.width, canvas.height);
    }
  }

  function getStoredFace() {
    try {
      const d = localStorage.getItem("jarvis_face");
      return d ? JSON.parse(d) : null;
    } catch { return null; }
  }

  async function registerFace() {
    if (!videoRef.current || !window.faceapi) return;
    setFaceStatus("REGISTRANDO IDENTIDAD...");
    setShowRegister(false);
    try {
      const detection = await window.faceapi
        .detectSingleFace(videoRef.current, new window.faceapi.TinyFaceDetectorOptions({ inputSize: 224 }))
        .withFaceLandmarks(true)
        .withFaceDescriptor();
      if (detection) {
        localStorage.setItem("jarvis_face", JSON.stringify(Array.from(detection.descriptor)));
        setIdentityVerified(true);
        identityVerifiedRef.current = true;
        setFaceStatus("IDENTIDAD REGISTRADA");
        setScanProgress(100);
        brainStateRef.current = { thinking: true, intensity: 1 };
        setTimeout(() => {
          brainStateRef.current = { thinking: false, intensity: 0.3 };
          setContinuousMode(true);
          startListening();
          speak("Identidad registrada correctamente, senor. Bienvenido al sistema JARVIS. Estoy a su disposicion.");
        }, 1500);
      }
    } catch (e) {
      setFaceStatus("ERROR EN REGISTRO");
    }
  }

  // ── BRAIN PARTICLE SYSTEM ──────────────────────────────
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    let width = canvas.parentElement.clientWidth;
    let height = canvas.parentElement.clientHeight;
    canvas.width = width; canvas.height = height;
    const particles = [];
    for (let i = 0; i < PARTICLE_COUNT; i++) {
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);
      let r = BRAIN_RADIUS * (0.6 + 0.4 * Math.random());
      const y = Math.cos(phi) * r;
      const flatY = y * 0.7;
      const sulcus = Math.sin(theta * 3 + phi * 2) * 12;
      r += sulcus;
      const x = Math.sin(phi) * Math.cos(theta) * r * 1.15;
      const z = Math.sin(phi) * Math.sin(theta) * r * 0.95;
      const fg = Math.abs(x) < 8 ? (8 - Math.abs(x)) * 0.5 : 0;
      particles.push({ x: x+(x>0?fg:-fg), y: flatY, z, ox: x+(x>0?fg:-fg), oy: flatY, oz: z, size: 0.8+Math.random()*1.8, brightness: 0.3+Math.random()*0.5, pulse: Math.random()*Math.PI*2, pulseSpeed: 0.01+Math.random()*0.03, region: Math.floor(Math.random()*6), active: false, activationTime: 0 });
    }
    const synapses = [];
    for (let i = 0; i < SYNAPSE_COUNT; i++) {
      const a = Math.floor(Math.random()*PARTICLE_COUNT), b = Math.floor(Math.random()*PARTICLE_COUNT);
      const dx = particles[a].ox-particles[b].ox, dy = particles[a].oy-particles[b].oy, dz = particles[a].oz-particles[b].oz;
      const dist = Math.sqrt(dx*dx+dy*dy+dz*dz);
      if (dist < 80 && dist > 10) synapses.push({ a, b, dist, signal: 0, signalSpeed: 0.005+Math.random()*0.02, active: false });
    }
    let rotY = 0, rotX = -0.15, tRY = 0, tRX = -0.15, time = 0;
    const onMM = (e) => { const r = canvas.getBoundingClientRect(); tRY = ((e.clientX-r.left)/r.width-0.5)*2*0.4; tRX = -0.15+((e.clientY-r.top)/r.height-0.5)*2*0.2; };
    const onRS = () => { width = canvas.parentElement.clientWidth; height = canvas.parentElement.clientHeight; canvas.width = width; canvas.height = height; };
    canvas.addEventListener("mousemove", onMM); window.addEventListener("resize", onRS);
    function actR(rid, int) { particles.forEach(p => { if (p.region===rid||Math.random()<int*0.1) { p.active=true; p.activationTime=time; } }); synapses.forEach(s => { if (particles[s.a].active||particles[s.b].active) { s.active=true; s.signal=0; } }); }
    function render() {
      time += 0.016; ctx.clearRect(0,0,width,height);
      const th = brainStateRef.current.thinking, int = brainStateRef.current.intensity;
      rotY += (tRY-rotY)*0.05; rotX += (tRX-rotX)*0.05; tRY += 0.001;
      if (th) { if (Math.random()<0.15) actR(Math.floor(Math.random()*6), int); } else { if (Math.random()<0.02) actR(Math.floor(Math.random()*6), 0.3); }
      const cY=Math.cos(rotY),sY=Math.sin(rotY),cX=Math.cos(rotX),sX=Math.sin(rotX);
      const cx=width/2,cy=height/2,sc=Math.min(width,height)/500;
      const proj = particles.map((p,i) => {
        const br=1+Math.sin(time*0.5)*0.008; let px=p.ox*br,py=p.oy*br,pz=p.oz*br;
        p.pulse+=p.pulseSpeed; const pm=Math.sin(p.pulse)*2,nx=px/BRAIN_RADIUS,ny=py/BRAIN_RADIUS,nz=pz/BRAIN_RADIUS;
        px+=nx*pm;py+=ny*pm;pz+=nz*pm;
        const rx1=px*cY-pz*sY,rz1=px*sY+pz*cY,ry2=py*cX-rz1*sX,rz2=py*sX+rz1*cX;
        if (p.active&&time-p.activationTime>1.5) p.active=false;
        return { x:cx+rx1*sc,y:cy+ry2*sc,z:rz2,size:p.size*sc,brightness:p.brightness,region:p.region,active:p.active,activationTime:p.activationTime,idx:i };
      });
      proj.sort((a,b)=>a.z-b.z);
      synapses.forEach(s => {
        const pa=proj.find(p=>p.idx===s.a),pb=proj.find(p=>p.idx===s.b);
        if (!pa||!pb) return;
        if (s.active) { s.signal+=s.signalSpeed; if(s.signal>1){s.active=false;s.signal=0;} const g=ctx.createLinearGradient(pa.x,pa.y,pb.x,pb.y); const gc=th?"0,210,255":"0,255,136"; g.addColorStop(Math.max(0,s.signal-0.15),`rgba(${gc},0)`); g.addColorStop(s.signal,`rgba(${gc},${0.6+int*0.4})`); g.addColorStop(Math.min(1,s.signal+0.15),`rgba(${gc},0)`); ctx.beginPath();ctx.moveTo(pa.x,pa.y);ctx.lineTo(pb.x,pb.y);ctx.strokeStyle=g;ctx.lineWidth=1.5*sc;ctx.stroke(); }
        else { const da=Math.max(0.02,Math.min(0.25,((pa.z+pb.z)/2+BRAIN_RADIUS)/(BRAIN_RADIUS*2)*0.3)); ctx.beginPath();ctx.moveTo(pa.x,pa.y);ctx.lineTo(pb.x,pb.y);ctx.strokeStyle=`rgba(0,180,220,${da})`;ctx.lineWidth=0.3*sc;ctx.stroke(); }
      });
      proj.forEach(p => {
        const df=(p.z+BRAIN_RADIUS)/(BRAIN_RADIUS*2),alpha=0.2+df*0.6;
        let r=0,g=150,b=200; const rg=[[0,200,255],[0,255,180],[100,150,255],[0,255,100],[150,100,255],[0,230,230]]; [r,g,b]=rg[p.region]||rg[0];
        if (p.active) { const fl=Math.max(0,1-(time-p.activationTime)/1.5); r=Math.min(255,r+155*fl);g=Math.min(255,g+105*fl);b=Math.min(255,b+55*fl); ctx.beginPath();ctx.arc(p.x,p.y,p.size*4,0,Math.PI*2);ctx.fillStyle=`rgba(${r},${g},${b},${fl*0.15})`;ctx.fill(); }
        ctx.beginPath();ctx.arc(p.x,p.y,p.size,0,Math.PI*2);ctx.fillStyle=`rgba(${r},${g},${b},${alpha*p.brightness})`;ctx.fill();
      });
      const cg=th?0.08+int*0.06:0.04; const cGr=ctx.createRadialGradient(cx,cy,0,cx,cy,BRAIN_RADIUS*sc);
      cGr.addColorStop(0,`rgba(0,212,255,${cg})`);cGr.addColorStop(0.5,`rgba(0,180,255,${cg*0.5})`);cGr.addColorStop(1,"rgba(0,100,200,0)");
      ctx.fillStyle=cGr;ctx.fillRect(0,0,width,height);
      animFrameRef.current=requestAnimationFrame(render);
    }
    render();
    return () => { canvas.removeEventListener("mousemove",onMM);window.removeEventListener("resize",onRS);if(animFrameRef.current) cancelAnimationFrame(animFrameRef.current); };
  }, []);

  // ── SPEECH RECOGNITION ──────────────────────────────────
  useEffect(() => {
    const SR = typeof window!=="undefined"&&(window.SpeechRecognition||window.webkitSpeechRecognition);
    if (!SR) return;
    const rec = new SR();
    rec.lang = "es-ES"; rec.continuous = false; rec.interimResults = true;
    rec.onresult = (ev) => {
      const t = Array.from(ev.results).map(r=>r[0].transcript).join("");
      setInput(t);
      if (ev.results[ev.results.length-1].isFinal) { setIsListening(false); if (t.trim()) sendMessage(t.trim(), true); }
    };
    rec.onerror = (e) => { setIsListening(false); if (continuousModeRef.current && e.error!=="aborted") setTimeout(()=>startListening(),500); };
    rec.onend = () => { setIsListening(false); if (continuousModeRef.current) setTimeout(()=>startListening(),300); };
    recognitionRef.current = rec;
  }, []);

  useEffect(() => { if (chatRef.current) chatRef.current.scrollTop = chatRef.current.scrollHeight; }, [messages]);

  function startListening() {
    if (!recognitionRef.current) return;
    try { setIsListening(true); recognitionRef.current.start(); window.speechSynthesis?.cancel(); if (audioRef.current) { audioRef.current.pause(); audioRef.current=null; } } catch(e) {}
  }
  function stopListening() { if (!recognitionRef.current) return; try { recognitionRef.current.stop(); } catch(e) {} setIsListening(false); }
  function toggleVoice() { if (isListening) { stopListening(); setContinuousMode(false); } else startListening(); }
  function toggleContinuous() { if (continuousMode) { setContinuousMode(false); stopListening(); } else { setContinuousMode(true); startListening(); } }

  // ── TTS WITH OPENAI ────────────────────────────────────
  async function speak(text) {
    if (!speakEnabledRef.current) return;
    const clean = text.replace(/[*#_`~>\[\]()!]/g,"").replace(/\n+/g,". ");
    setIsSpeaking(true); brainStateRef.current = { thinking: true, intensity: 0.5 };
    try {
      const res = await fetch("/api/tts", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ text: clean }) });
      if (!res.ok) throw new Error("TTS failed");
      const blob = await res.blob(); const url = URL.createObjectURL(blob);
      const audio = new Audio(url); audioRef.current = audio;
      audio.onended = () => { URL.revokeObjectURL(url); setIsSpeaking(false); audioRef.current=null; brainStateRef.current={thinking:false,intensity:0.2}; if(continuousModeRef.current) setTimeout(()=>startListening(),400); };
      audio.onerror = () => { setIsSpeaking(false); audioRef.current=null; brainStateRef.current={thinking:false,intensity:0.2}; fallbackSpeak(clean); };
      audio.play();
    } catch(e) { fallbackSpeak(clean); }
  }
  function fallbackSpeak(text) {
    if (!window.speechSynthesis) { setIsSpeaking(false); return; }
    const u = new SpeechSynthesisUtterance(text); u.lang="es-ES"; u.rate=1.05; u.pitch=0.95;
    const v = window.speechSynthesis.getVoices().find(v=>v.lang.startsWith("es")); if(v) u.voice=v;
    u.onend = () => { setIsSpeaking(false); brainStateRef.current={thinking:false,intensity:0.2}; if(continuousModeRef.current) setTimeout(()=>startListening(),400); };
    window.speechSynthesis.speak(u);
  }
  function stopSpeaking() { if(audioRef.current){audioRef.current.pause();audioRef.current=null;} window.speechSynthesis?.cancel(); setIsSpeaking(false); brainStateRef.current={thinking:false,intensity:0.2}; }

  // ── SEND MESSAGE ────────────────────────────────────────
  const sendMessage = useCallback(async (text, isVoice=false) => {
    const msg = text||input.trim(); if (!msg||isProcessing) return;
    stopSpeaking(); stopListening();
    setIsProcessing(true); setShowWelcome(false); setPanelOpen(true);
    setInput(""); setNeuralActivity(0.8); brainStateRef.current={thinking:true,intensity:0.8};
    const userMsg = { role:"user", content:msg }; setMessages(prev=>[...prev,userMsg]); historyRef.current.push(userMsg);
    setMessages(prev=>[...prev,{role:"typing"}]);
    try {
      const res = await fetch("/api/chat", { method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({message:msg,history:historyRef.current.slice(-40),isVoice}) });
      const data = await res.json();
      const aMsg = { role:"assistant", content:data.response };
      setMessages(prev=>prev.filter(m=>m.role!=="typing").concat(aMsg));
      historyRef.current.push(aMsg);
      speak(data.response);
    } catch {
      setMessages(prev=>prev.filter(m=>m.role!=="typing").concat({role:"assistant",content:"Error de conexion. Verificando sistemas..."}));
    }
    setNeuralActivity(0.2); setIsProcessing(false); inputRef.current?.focus();
  }, [input, isProcessing]);

  function clearChat() { fetch("/api/clear",{method:"POST"}).catch(()=>{}); setMessages([]); historyRef.current=[]; setShowWelcome(true); setPanelOpen(false); stopSpeaking(); }
  function handleKey(e) { if (e.key==="Enter"&&!e.shiftKey) { e.preventDefault(); sendMessage(); } }

  const suggestions = [
    { icon: "\u{1F9E0}", text: "Dime todas tus capacidades" },
    { icon: "\u{1F321}", text: "Que tiempo hace en Orihuela" },
    { icon: "\u{1F50D}", text: "Busca noticias de tecnologia" },
    { icon: "\u{1F4DD}", text: "Crea una nota importante" },
    { icon: "\u{2705}", text: "Crea tarea: reunion manana" },
    { icon: "\u{1F3E0}", text: "Enciende la luz del salon" },
    { icon: "\u{1F4E7}", text: "Redacta email profesional" },
    { icon: "\u{1F552}", text: "Que hora es ahora" },
  ];

  const statusColor = isSpeaking?"#00d4ff":isListening?"#ff4444":isProcessing?"#ff6b35":identityVerified?"#00ff88":"#4a6a8a";

  // ── RENDER ──────────────────────────────────────────────
  return (
    <div style={S.container}>
      <div style={S.canvasWrap}><canvas ref={canvasRef} style={S.canvas} /><div style={S.ambientOverlay} /></div>

      {/* CAMERA HUD */}
      <div style={S.cameraHud}>
        <div style={{...S.cameraFrame, borderColor: identityVerified?"#00ff88":faceDetected?"#00d4ff":"#1a3050", boxShadow: identityVerified?"0 0 20px rgba(0,255,136,.3)":faceDetected?"0 0 15px rgba(0,212,255,.2)":"none"}}>
          <video ref={videoRef} style={S.cameraVideo} muted playsInline />
          <canvas ref={faceCanvasRef} style={S.faceOverlay} />
          {!cameraActive && <div style={S.cameraPlaceholder}><div style={S.cameraLoader} /></div>}
          {/* Scan line */}
          <div style={{...S.cameraScanLine, animationPlayState: cameraActive?"running":"paused"}} />
          {/* Corner markers */}
          <div style={{...S.cornerMark, top:0,left:0, borderTop:"2px solid",borderLeft:"2px solid",borderColor:identityVerified?"#00ff88":"#00d4ff"}} />
          <div style={{...S.cornerMark, top:0,right:0, borderTop:"2px solid",borderRight:"2px solid",borderColor:identityVerified?"#00ff88":"#00d4ff"}} />
          <div style={{...S.cornerMark, bottom:0,left:0, borderBottom:"2px solid",borderLeft:"2px solid",borderColor:identityVerified?"#00ff88":"#00d4ff"}} />
          <div style={{...S.cornerMark, bottom:0,right:0, borderBottom:"2px solid",borderRight:"2px solid",borderColor:identityVerified?"#00ff88":"#00d4ff"}} />
        </div>
        {/* Biometric data */}
        <div style={S.bioData}>
          <div style={{...S.bioStatus, color: identityVerified?"#00ff88":faceDetected?"#00d4ff":"#4a6a8a"}}>
            <span style={{...S.bioDot, background: identityVerified?"#00ff88":faceDetected?"#00d4ff":"#4a6a8a"}} />
            {faceStatus}
          </div>
          {identityVerified && <div style={S.bioName}>{OWNER_NAME}</div>}
          {biometrics && (
            <div style={S.bioMetrics}>
              <span>MATCH: {biometrics.confidence}%</span>
              <span>POINTS: {biometrics.landmarks}</span>
            </div>
          )}
          {/* Progress bar */}
          <div style={S.bioProgress}>
            <div style={{...S.bioProgressFill, width: `${scanProgress}%`, background: identityVerified?"#00ff88":"#00d4ff"}} />
          </div>
          {showRegister && (
            <button onClick={registerFace} style={S.registerBtn}>REGISTRAR MI IDENTIDAD</button>
          )}
        </div>
      </div>

      {/* HEADER */}
      <header style={S.topBar}>
        <div style={S.brand}>
          <div style={{...S.statusDot, background:statusColor, boxShadow:`0 0 12px ${statusColor}`}} />
          <h1 style={S.title}>J.A.R.V.I.S.</h1>
          <span style={S.version}>NEURAL v3.0</span>
          {isSpeaking && <span style={{fontSize:11,color:"#00d4ff",marginLeft:8,animation:"pulse-glow 2s infinite"}}>HABLANDO</span>}
          {isListening && <span style={{fontSize:11,color:"#ff4444",marginLeft:8,animation:"pulse-red 1.5s infinite"}}>ESCUCHANDO</span>}
          {identityVerified && !isSpeaking && !isListening && <span style={{fontSize:11,color:"#00ff88",marginLeft:8}}>VERIFICADO</span>}
        </div>
        <div style={S.topRight}>
          <div style={S.neuralMeter}><span style={S.meterLabel}>Neural</span><div style={S.meterTrack}><div style={{...S.meterFill, width:`${neuralActivity*100}%`, background:neuralActivity>0.5?"#00d4ff":"#00ff88"}} /></div></div>
          <button onClick={toggleContinuous} style={{...S.iconBtn, color:continuousMode?"#ff4444":"#4a6a8a",position:"relative"}} title="Modo continuo">
            {continuousMode ? "\u{1F534}" : "\u{2B55}"}
            {continuousMode && <span style={{position:"absolute",top:-2,right:-2,width:6,height:6,borderRadius:"50%",background:"#ff4444",animation:"pulse-red 1s infinite"}} />}
          </button>
          <button onClick={()=>setSpeakEnabled(!speakEnabled)} style={{...S.iconBtn,color:speakEnabled?"#00d4ff":"#4a5568"}}>{speakEnabled?"\u{1F50A}":"\u{1F507}"}</button>
          <button onClick={clearChat} style={S.iconBtn}>{"\u{1F5D1}"}</button>
        </div>
      </header>

      {/* WELCOME */}
      {showWelcome && (
        <div style={S.welcomeOverlay}><div style={S.welcomeContent}>
          <div style={S.welcomeGlow} />
          <h2 style={S.welcomeTitle}>{identityVerified ? `Buenos dias, ${OWNER_NAME.split(" ")[0].toLowerCase()}` : "Identificacion requerida"}</h2>
          <p style={S.welcomeSub}>{identityVerified ? "Todos los sistemas operativos. Listo para asistirle." : "Posicione su rostro frente a la camara para verificar identidad."}</p>
          {identityVerified && <p style={S.welcomeHint}>Modo manos libres activado - solo hable</p>}
          {identityVerified && <div style={S.sugGrid}>
            {suggestions.map((s,i) => (
              <button key={i} style={S.sugBtn} onClick={()=>sendMessage(s.text)}
                onMouseEnter={e=>{e.target.style.borderColor="#00d4ff";e.target.style.background="rgba(0,212,255,0.08)";}}
                onMouseLeave={e=>{e.target.style.borderColor="rgba(0,212,255,0.15)";e.target.style.background="rgba(0,15,30,0.6)";}}>
                <span style={S.sugIcon}>{s.icon}</span><span style={S.sugText}>{s.text}</span>
              </button>
            ))}
          </div>}
        </div></div>
      )}

      {/* CHAT PANEL */}
      <div style={{...S.chatPanel, transform:panelOpen?"translateX(0)":"translateX(100%)", opacity:panelOpen?1:0}}>
        <div ref={chatRef} style={S.chatMessages}>
          {messages.map((msg,i) => {
            if (msg.role==="typing") return (<div key={i} style={S.msgRow}><div style={S.jarvisAvatar}>J</div><div style={S.bubbleJarvis}><div style={S.typingDots}><span style={{...S.tDot,animationDelay:"0s"}} /><span style={{...S.tDot,animationDelay:"0.2s"}} /><span style={{...S.tDot,animationDelay:"0.4s"}} /></div></div></div>);
            const isU = msg.role==="user";
            return (<div key={i} style={{...S.msgRow,justifyContent:isU?"flex-end":"flex-start"}}>
              {!isU&&<div style={S.jarvisAvatar}>J</div>}
              <div style={isU?S.bubbleUser:S.bubbleJarvis} dangerouslySetInnerHTML={isU?undefined:{__html:fmtMd(msg.content)}}>{isU?msg.content:undefined}</div>
              {isU&&<div style={S.userAvatar}>D</div>}
            </div>);
          })}
        </div>
      </div>

      {/* INPUT BAR */}
      <div style={S.inputBar}><div style={S.inputInner}>
        <button onClick={toggleVoice} style={isListening?{...S.voiceBtn,...S.voiceBtnActive}:S.voiceBtn}>{"\u{1F3A4}"}</button>
        {isSpeaking&&<button onClick={stopSpeaking} style={{...S.voiceBtn,borderColor:"#00d4ff",color:"#00d4ff"}}>{"\u23F9"}</button>}
        <textarea ref={inputRef} value={input} onChange={e=>setInput(e.target.value)} onKeyDown={handleKey}
          placeholder={isListening?"Escuchando...":isSpeaking?"JARVIS hablando...":"Habla con JARVIS..."} rows={1} style={S.textInput} />
        <button onClick={()=>sendMessage()} disabled={!input.trim()||isProcessing} style={{...S.sendBtn,opacity:!input.trim()||isProcessing?0.3:1}}>{"\u{27A4}"}</button>
      </div>
      <div style={S.inputHints}>
        <span style={S.hint}>{identityVerified ? "Manos libres activo | Habla directamente" : "Verificar identidad para modo automatico"}</span>
        {panelOpen&&<button onClick={()=>setPanelOpen(false)} style={S.minimizeBtn}>Minimizar</button>}
        {!panelOpen&&messages.length>0&&<button onClick={()=>setPanelOpen(true)} style={S.minimizeBtn}>Chat ({messages.filter(m=>m.role!=="typing").length})</button>}
      </div></div>

      <style>{`
        @keyframes typing-dot{0%,60%,100%{opacity:.3;transform:scale(.8)}30%{opacity:1;transform:scale(1)}}
        @keyframes pulse-glow{0%,100%{box-shadow:0 0 15px rgba(0,212,255,.15)}50%{box-shadow:0 0 30px rgba(0,212,255,.3)}}
        @keyframes pulse-red{0%,100%{box-shadow:0 0 0 0 rgba(255,68,68,.3)}50%{box-shadow:0 0 0 10px rgba(255,68,68,0)}}
        @keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-8px)}}
        @keyframes scanline{0%{top:0}100%{top:100%}}
        @keyframes cam-pulse{0%,100%{opacity:.3}50%{opacity:.8}}
        @keyframes border-glow{0%,100%{box-shadow:0 0 5px rgba(0,212,255,.2)}50%{box-shadow:0 0 20px rgba(0,212,255,.5)}}
        textarea:focus{outline:none}
        ::-webkit-scrollbar{width:4px}::-webkit-scrollbar-track{background:transparent}::-webkit-scrollbar-thumb{background:#1e2d42;border-radius:2px}
        *{box-sizing:border-box}
      `}</style>
    </div>
  );
}

function fmtMd(text) {
  if (!text) return "";
  return text.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")
    .replace(/```([\s\S]*?)```/g,'<pre style="background:#0a1628;border:1px solid #1a2d45;border-radius:8px;padding:12px;overflow-x:auto;margin:8px 0;font-size:13px"><code>$1</code></pre>')
    .replace(/`([^`]+)`/g,'<code style="background:rgba(0,212,255,.1);color:#00d4ff;padding:2px 6px;border-radius:4px;font-size:13px">$1</code>')
    .replace(/\*\*(.+?)\*\*/g,'<strong style="color:#00d4ff">$1</strong>')
    .replace(/\*(.+?)\*/g,'<em style="color:#00ff88">$1</em>')
    .replace(/\n/g,"<br>");
}

const S = {
  container:{fontFamily:"'Rajdhani',sans-serif",background:"#030810",color:"#e0e8f0",height:"100vh",display:"flex",flexDirection:"column",overflow:"hidden",position:"relative"},
  canvasWrap:{position:"absolute",inset:0,zIndex:0},
  canvas:{width:"100%",height:"100%",display:"block"},
  ambientOverlay:{position:"absolute",inset:0,background:"radial-gradient(ellipse at 50% 50%, transparent 30%, #030810 75%)",pointerEvents:"none"},
  // Camera HUD
  cameraHud:{position:"absolute",top:56,left:16,zIndex:15,display:"flex",gap:10,alignItems:"flex-start"},
  cameraFrame:{position:"relative",width:160,height:120,borderRadius:8,overflow:"hidden",border:"1px solid #1a3050",background:"#000",transition:"all .5s"},
  cameraVideo:{width:"100%",height:"100%",objectFit:"cover",transform:"scaleX(-1)"},
  faceOverlay:{position:"absolute",top:0,left:0,width:"100%",height:"100%",transform:"scaleX(-1)",pointerEvents:"none"},
  cameraPlaceholder:{position:"absolute",inset:0,display:"flex",alignItems:"center",justifyContent:"center",background:"rgba(0,10,20,.9)"},
  cameraLoader:{width:24,height:24,border:"2px solid #1a3050",borderTop:"2px solid #00d4ff",borderRadius:"50%",animation:"cam-pulse 1.5s linear infinite"},
  cameraScanLine:{position:"absolute",left:0,width:"100%",height:1,background:"linear-gradient(90deg,transparent,#00d4ff,transparent)",animation:"scanline 2s linear infinite",pointerEvents:"none",opacity:0.5},
  cornerMark:{position:"absolute",width:12,height:12,pointerEvents:"none"},
  // Bio data
  bioData:{display:"flex",flexDirection:"column",gap:4,minWidth:140},
  bioStatus:{fontSize:10,letterSpacing:1.5,fontWeight:700,display:"flex",alignItems:"center",gap:5,fontFamily:"'Orbitron',monospace"},
  bioDot:{width:6,height:6,borderRadius:"50%",flexShrink:0},
  bioName:{fontSize:13,color:"#00ff88",fontWeight:700,letterSpacing:2,fontFamily:"'Orbitron',monospace"},
  bioMetrics:{display:"flex",gap:10,fontSize:9,color:"#4a6a8a",letterSpacing:1,fontFamily:"monospace"},
  bioProgress:{width:"100%",height:2,background:"#0a1628",borderRadius:1,overflow:"hidden",marginTop:2},
  bioProgressFill:{height:"100%",borderRadius:1,transition:"all .8s ease"},
  registerBtn:{background:"rgba(0,212,255,.1)",border:"1px solid #00d4ff",borderRadius:6,color:"#00d4ff",fontSize:10,padding:"6px 12px",cursor:"pointer",fontFamily:"'Orbitron',monospace",letterSpacing:1,marginTop:4,transition:"all .2s"},
  // Header
  topBar:{position:"relative",zIndex:10,display:"flex",justifyContent:"space-between",alignItems:"center",padding:"10px 20px",background:"linear-gradient(180deg,rgba(3,8,16,.95),rgba(3,8,16,.6))",borderBottom:"1px solid rgba(0,212,255,.1)"},
  brand:{display:"flex",alignItems:"center",gap:10},
  statusDot:{width:10,height:10,borderRadius:"50%",transition:"all .3s"},
  title:{fontFamily:"'Orbitron',sans-serif",fontSize:16,fontWeight:700,color:"#00d4ff",letterSpacing:4,margin:0},
  version:{fontSize:10,color:"#4a6a8a",letterSpacing:2,textTransform:"uppercase"},
  topRight:{display:"flex",alignItems:"center",gap:12},
  neuralMeter:{display:"flex",alignItems:"center",gap:6},
  meterLabel:{fontSize:10,color:"#4a6a8a",letterSpacing:1,textTransform:"uppercase"},
  meterTrack:{width:60,height:4,background:"#0a1628",borderRadius:2,overflow:"hidden"},
  meterFill:{height:"100%",borderRadius:2,transition:"all .5s ease"},
  iconBtn:{background:"none",border:"none",color:"#4a6a8a",fontSize:16,cursor:"pointer",padding:4,transition:"color .2s"},
  // Welcome
  welcomeOverlay:{position:"absolute",inset:0,zIndex:5,display:"flex",alignItems:"center",justifyContent:"center",pointerEvents:"none"},
  welcomeContent:{pointerEvents:"auto",textAlign:"center",maxWidth:700,padding:"0 20px",position:"relative"},
  welcomeGlow:{position:"absolute",top:"-100px",left:"50%",transform:"translateX(-50%)",width:300,height:300,borderRadius:"50%",background:"radial-gradient(circle,rgba(0,212,255,.06),transparent 70%)",pointerEvents:"none"},
  welcomeTitle:{fontFamily:"'Orbitron',sans-serif",fontSize:28,color:"#00d4ff",marginBottom:8,letterSpacing:3,animation:"float 4s ease-in-out infinite"},
  welcomeSub:{fontSize:15,color:"#5a7a9a",marginBottom:10,letterSpacing:1},
  welcomeHint:{fontSize:12,color:"#00ff88",marginBottom:20,letterSpacing:0.5},
  sugGrid:{display:"grid",gridTemplateColumns:"repeat(auto-fill,minmax(200px,1fr))",gap:8,maxWidth:650,margin:"0 auto"},
  sugBtn:{background:"rgba(0,15,30,.6)",border:"1px solid rgba(0,212,255,.15)",borderRadius:10,padding:"10px 14px",cursor:"pointer",display:"flex",alignItems:"center",gap:8,transition:"all .2s",backdropFilter:"blur(10px)"},
  sugIcon:{fontSize:18,flexShrink:0},
  sugText:{fontSize:13,color:"#c0d0e0",fontFamily:"'Rajdhani',sans-serif",textAlign:"left"},
  // Chat
  chatPanel:{position:"absolute",right:0,top:48,bottom:80,width:"min(420px, 100vw)",zIndex:8,background:"linear-gradient(180deg,rgba(3,8,16,.92),rgba(5,12,24,.95))",borderLeft:"1px solid rgba(0,212,255,.1)",transition:"all .4s cubic-bezier(.4,0,.2,1)",display:"flex",flexDirection:"column",backdropFilter:"blur(20px)"},
  chatMessages:{flex:1,overflowY:"auto",padding:"16px 14px",display:"flex",flexDirection:"column",gap:12},
  msgRow:{display:"flex",gap:8,alignItems:"flex-end"},
  jarvisAvatar:{width:28,height:28,borderRadius:"50%",background:"linear-gradient(135deg,#0099cc,#00d4ff)",color:"#030810",display:"flex",alignItems:"center",justifyContent:"center",fontSize:12,fontWeight:700,flexShrink:0},
  userAvatar:{width:28,height:28,borderRadius:"50%",background:"linear-gradient(135deg,#6366f1,#8b5cf6)",color:"#fff",display:"flex",alignItems:"center",justifyContent:"center",fontSize:12,fontWeight:700,flexShrink:0},
  bubbleJarvis:{background:"rgba(0,20,40,.7)",border:"1px solid rgba(0,212,255,.12)",borderRadius:"14px 14px 14px 4px",padding:"10px 14px",fontSize:14,lineHeight:1.6,maxWidth:"85%",backdropFilter:"blur(10px)"},
  bubbleUser:{background:"rgba(99,102,241,.15)",border:"1px solid rgba(99,102,241,.2)",borderRadius:"14px 14px 4px 14px",padding:"10px 14px",fontSize:14,lineHeight:1.6,maxWidth:"85%"},
  typingDots:{display:"flex",gap:5,padding:"4px 0"},
  tDot:{width:6,height:6,background:"#00d4ff",borderRadius:"50%",animation:"typing-dot 1.4s ease-in-out infinite"},
  // Input
  inputBar:{position:"relative",zIndex:10,padding:"10px 20px 16px",background:"linear-gradient(0deg,rgba(3,8,16,.98),rgba(3,8,16,.7))",borderTop:"1px solid rgba(0,212,255,.08)"},
  inputInner:{display:"flex",gap:8,alignItems:"flex-end",maxWidth:800,margin:"0 auto"},
  voiceBtn:{width:40,height:40,borderRadius:12,border:"1px solid rgba(0,212,255,.15)",background:"rgba(0,15,30,.6)",color:"#5a7a9a",cursor:"pointer",fontSize:16,display:"flex",alignItems:"center",justifyContent:"center",flexShrink:0,transition:"all .2s"},
  voiceBtnActive:{background:"rgba(255,68,68,.15)",borderColor:"#ff4444",color:"#ff4444",animation:"pulse-red 1.5s ease-in-out infinite"},
  textInput:{flex:1,background:"rgba(0,15,30,.6)",border:"1px solid rgba(0,212,255,.12)",borderRadius:12,color:"#e0e8f0",fontFamily:"'Rajdhani',sans-serif",fontSize:15,padding:"10px 14px",resize:"none",maxHeight:100,lineHeight:1.4,backdropFilter:"blur(10px)"},
  sendBtn:{width:40,height:40,borderRadius:12,border:"none",background:"#00d4ff",color:"#030810",cursor:"pointer",fontSize:16,display:"flex",alignItems:"center",justifyContent:"center",flexShrink:0,fontWeight:700,transition:"all .2s"},
  inputHints:{display:"flex",justifyContent:"space-between",alignItems:"center",marginTop:6,padding:"0 4px"},
  hint:{fontSize:10,color:"#3a5a7a",letterSpacing:1},
  minimizeBtn:{background:"none",border:"1px solid rgba(0,212,255,.15)",borderRadius:6,color:"#5a7a9a",fontSize:11,padding:"3px 10px",cursor:"pointer",fontFamily:"'Rajdhani',sans-serif",transition:"all .2s"},
};
