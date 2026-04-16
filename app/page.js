"use client";

import { useState, useRef, useEffect, useCallback } from "react";

const PARTICLE_COUNT = 2800;
const SYNAPSE_COUNT = 400;
const BRAIN_RADIUS = 180;

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

  useEffect(() => { continuousModeRef.current = continuousMode; }, [continuousMode]);
  useEffect(() => { speakEnabledRef.current = speakEnabled; }, [speakEnabled]);

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
      const fissureGap = Math.abs(x) < 8 ? (8 - Math.abs(x)) * 0.5 : 0;
      particles.push({
        x: x + (x > 0 ? fissureGap : -fissureGap), y: flatY, z,
        ox: x + (x > 0 ? fissureGap : -fissureGap), oy: flatY, oz: z,
        size: 0.8 + Math.random() * 1.8,
        brightness: 0.3 + Math.random() * 0.5,
        pulse: Math.random() * Math.PI * 2,
        pulseSpeed: 0.01 + Math.random() * 0.03,
        region: Math.floor(Math.random() * 6),
        active: false, activationTime: 0,
      });
    }
    const synapses = [];
    for (let i = 0; i < SYNAPSE_COUNT; i++) {
      const a = Math.floor(Math.random() * PARTICLE_COUNT);
      const b = Math.floor(Math.random() * PARTICLE_COUNT);
      const dx = particles[a].ox - particles[b].ox;
      const dy = particles[a].oy - particles[b].oy;
      const dz = particles[a].oz - particles[b].oz;
      const dist = Math.sqrt(dx*dx + dy*dy + dz*dz);
      if (dist < 80 && dist > 10) {
        synapses.push({ a, b, dist, signal: 0, signalSpeed: 0.005 + Math.random() * 0.02, active: false });
      }
    }
    let rotY = 0, rotX = -0.15, targetRotY = 0, targetRotX = -0.15, time = 0;
    const handleMouseMove = (e) => {
      const rect = canvas.getBoundingClientRect();
      const mx = ((e.clientX - rect.left) / rect.width - 0.5) * 2;
      const my = ((e.clientY - rect.top) / rect.height - 0.5) * 2;
      targetRotY = mx * 0.4; targetRotX = -0.15 + my * 0.2;
    };
    const handleResize = () => { width = canvas.parentElement.clientWidth; height = canvas.parentElement.clientHeight; canvas.width = width; canvas.height = height; };
    canvas.addEventListener("mousemove", handleMouseMove);
    window.addEventListener("resize", handleResize);
    function activateRegion(regionId, intensity) {
      particles.forEach(p => { if (p.region === regionId || Math.random() < intensity * 0.1) { p.active = true; p.activationTime = time; } });
      synapses.forEach(s => { if (particles[s.a].active || particles[s.b].active) { s.active = true; s.signal = 0; } });
    }
    function render() {
      time += 0.016; ctx.clearRect(0, 0, width, height);
      const thinking = brainStateRef.current.thinking;
      const intensity = brainStateRef.current.intensity;
      rotY += (targetRotY - rotY) * 0.05; rotX += (targetRotX - rotX) * 0.05;
      targetRotY += 0.001;
      if (thinking) { if (Math.random() < 0.15) activateRegion(Math.floor(Math.random() * 6), intensity); }
      else { if (Math.random() < 0.02) activateRegion(Math.floor(Math.random() * 6), 0.3); }
      const cosY = Math.cos(rotY), sinY = Math.sin(rotY), cosX = Math.cos(rotX), sinX = Math.sin(rotX);
      const cx = width / 2, cy = height / 2, scale = Math.min(width, height) / 500;
      const projected = particles.map((p, i) => {
        const breathe = 1 + Math.sin(time * 0.5) * 0.008;
        let px = p.ox * breathe, py = p.oy * breathe, pz = p.oz * breathe;
        p.pulse += p.pulseSpeed;
        const pm = Math.sin(p.pulse) * 2, nx = px/BRAIN_RADIUS, ny = py/BRAIN_RADIUS, nz = pz/BRAIN_RADIUS;
        px += nx*pm; py += ny*pm; pz += nz*pm;
        const rx1 = px*cosY - pz*sinY, rz1 = px*sinY + pz*cosY;
        const ry2 = py*cosX - rz1*sinX, rz2 = py*sinX + rz1*cosX;
        if (p.active && time - p.activationTime > 1.5) p.active = false;
        return { x: cx+rx1*scale, y: cy+ry2*scale, z: rz2, size: p.size*scale, brightness: p.brightness, region: p.region, active: p.active, activationTime: p.activationTime, idx: i };
      });
      projected.sort((a, b) => a.z - b.z);
      synapses.forEach(s => {
        const pa = projected.find(p => p.idx === s.a), pb = projected.find(p => p.idx === s.b);
        if (!pa || !pb) return;
        if (s.active) {
          s.signal += s.signalSpeed; if (s.signal > 1) { s.active = false; s.signal = 0; }
          const g = ctx.createLinearGradient(pa.x, pa.y, pb.x, pb.y);
          const gc = thinking ? "0,210,255" : "0,255,136";
          g.addColorStop(Math.max(0, s.signal-0.15), `rgba(${gc},0)`);
          g.addColorStop(s.signal, `rgba(${gc},${0.6+intensity*0.4})`);
          g.addColorStop(Math.min(1, s.signal+0.15), `rgba(${gc},0)`);
          ctx.beginPath(); ctx.moveTo(pa.x, pa.y); ctx.lineTo(pb.x, pb.y);
          ctx.strokeStyle = g; ctx.lineWidth = 1.5*scale; ctx.stroke();
        } else {
          const da = Math.max(0.02, Math.min(0.25, ((pa.z+pb.z)/2 + BRAIN_RADIUS)/(BRAIN_RADIUS*2)*0.3));
          ctx.beginPath(); ctx.moveTo(pa.x, pa.y); ctx.lineTo(pb.x, pb.y);
          ctx.strokeStyle = `rgba(0,180,220,${da})`; ctx.lineWidth = 0.3*scale; ctx.stroke();
        }
      });
      projected.forEach(p => {
        const df = (p.z+BRAIN_RADIUS)/(BRAIN_RADIUS*2), alpha = 0.2+df*0.6;
        let r=0,g=150,b=200;
        const regions = [[0,200,255],[0,255,180],[100,150,255],[0,255,100],[150,100,255],[0,230,230]];
        [r,g,b] = regions[p.region]||regions[0];
        if (p.active) {
          const flash = Math.max(0, 1-(time-p.activationTime)/1.5);
          r=Math.min(255,r+155*flash); g=Math.min(255,g+105*flash); b=Math.min(255,b+55*flash);
          ctx.beginPath(); ctx.arc(p.x,p.y,p.size*4,0,Math.PI*2);
          ctx.fillStyle = `rgba(${r},${g},${b},${flash*0.15})`; ctx.fill();
        }
        ctx.beginPath(); ctx.arc(p.x,p.y,p.size,0,Math.PI*2);
        ctx.fillStyle = `rgba(${r},${g},${b},${alpha*p.brightness})`; ctx.fill();
      });
      const cg = thinking ? 0.08+intensity*0.06 : 0.04;
      const cGrad = ctx.createRadialGradient(cx,cy,0,cx,cy,BRAIN_RADIUS*scale);
      cGrad.addColorStop(0, `rgba(0,212,255,${cg})`); cGrad.addColorStop(0.5, `rgba(0,180,255,${cg*0.5})`); cGrad.addColorStop(1, "rgba(0,100,200,0)");
      ctx.fillStyle = cGrad; ctx.fillRect(0,0,width,height);
      animFrameRef.current = requestAnimationFrame(render);
    }
    render();
    return () => { canvas.removeEventListener("mousemove", handleMouseMove); window.removeEventListener("resize", handleResize); if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current); };
  }, []);

  // ── SPEECH RECOGNITION ──────────────────────────────────
  useEffect(() => {
    const SR = typeof window !== "undefined" && (window.SpeechRecognition || window.webkitSpeechRecognition);
    if (!SR) return;
    const recognition = new SR();
    recognition.lang = "es-ES";
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.onresult = (event) => {
      const transcript = Array.from(event.results).map(r => r[0].transcript).join("");
      setInput(transcript);
      if (event.results[event.results.length - 1].isFinal) {
        setIsListening(false);
        if (transcript.trim()) sendMessage(transcript.trim(), true);
      }
    };
    recognition.onerror = (e) => {
      setIsListening(false);
      if (continuousModeRef.current && e.error !== "aborted") {
        setTimeout(() => startListening(), 500);
      }
    };
    recognition.onend = () => {
      setIsListening(false);
      if (continuousModeRef.current) {
        setTimeout(() => startListening(), 300);
      }
    };
    recognitionRef.current = recognition;
  }, []);

  useEffect(() => { if (chatRef.current) chatRef.current.scrollTop = chatRef.current.scrollHeight; }, [messages]);
  useEffect(() => {
    const handleKey = (e) => {
      if (e.ctrlKey && e.shiftKey && e.code === "Space") { e.preventDefault(); toggleVoice(); }
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, []);

  function startListening() {
    if (!recognitionRef.current) return;
    try {
      setIsListening(true);
      recognitionRef.current.start();
      window.speechSynthesis?.cancel();
      if (audioRef.current) { audioRef.current.pause(); audioRef.current = null; }
    } catch(e) { console.log("Recognition start error:", e); }
  }

  function stopListening() {
    if (!recognitionRef.current) return;
    try { recognitionRef.current.stop(); } catch(e) {}
    setIsListening(false);
  }

  function toggleVoice() {
    if (isListening) { stopListening(); setContinuousMode(false); }
    else { startListening(); }
  }

  function toggleContinuous() {
    if (continuousMode) {
      setContinuousMode(false);
      stopListening();
    } else {
      setContinuousMode(true);
      startListening();
    }
  }

  // ── TTS WITH OPENAI ────────────────────────────────────
  async function speak(text) {
    if (!speakEnabledRef.current) return;
    const clean = text.replace(/[*#_\`~>\[\]()!]/g, "").replace(/\n+/g, ". ");
    setIsSpeaking(true);
    brainStateRef.current = { thinking: true, intensity: 0.5 };

    try {
      const res = await fetch("/api/tts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: clean }),
      });
      if (!res.ok) throw new Error("TTS API failed");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      audioRef.current = audio;

      audio.onended = () => {
        URL.revokeObjectURL(url);
        setIsSpeaking(false);
        audioRef.current = null;
        brainStateRef.current = { thinking: false, intensity: 0.2 };
        if (continuousModeRef.current) {
          setTimeout(() => startListening(), 400);
        }
      };
      audio.onerror = () => {
        setIsSpeaking(false);
        audioRef.current = null;
        brainStateRef.current = { thinking: false, intensity: 0.2 };
        fallbackSpeak(clean);
      };
      audio.play();
    } catch (e) {
      console.error("TTS error, using fallback:", e);
      fallbackSpeak(clean);
    }
  }

  function fallbackSpeak(text) {
    if (!window.speechSynthesis) { setIsSpeaking(false); return; }
    const u = new SpeechSynthesisUtterance(text);
    u.lang = "es-ES"; u.rate = 1.05; u.pitch = 0.95;
    const voices = window.speechSynthesis.getVoices();
    const esVoice = voices.find(v => v.lang.startsWith("es"));
    if (esVoice) u.voice = esVoice;
    u.onend = () => {
      setIsSpeaking(false);
      brainStateRef.current = { thinking: false, intensity: 0.2 };
      if (continuousModeRef.current) setTimeout(() => startListening(), 400);
    };
    window.speechSynthesis.speak(u);
  }

  function stopSpeaking() {
    if (audioRef.current) { audioRef.current.pause(); audioRef.current = null; }
    window.speechSynthesis?.cancel();
    setIsSpeaking(false);
    brainStateRef.current = { thinking: false, intensity: 0.2 };
  }

  // ── SEND MESSAGE ────────────────────────────────────────
  const sendMessage = useCallback(async (text, isVoice = false) => {
    const msg = text || input.trim();
    if (!msg || isProcessing) return;
    stopSpeaking();
    stopListening();
    setIsProcessing(true); setShowWelcome(false); setPanelOpen(true);
    setInput(""); setNeuralActivity(0.8);
    brainStateRef.current = { thinking: true, intensity: 0.8 };
    const userMsg = { role: "user", content: msg };
    setMessages(prev => [...prev, userMsg]);
    historyRef.current.push(userMsg);
    setMessages(prev => [...prev, { role: "typing" }]);
    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: msg, history: historyRef.current.slice(-40), isVoice }),
      });
      const data = await res.json();
      const assistantMsg = { role: "assistant", content: data.response };
      setMessages(prev => prev.filter(m => m.role !== "typing").concat(assistantMsg));
      historyRef.current.push(assistantMsg);
      speak(data.response);
    } catch {
      const errMsg = { role: "assistant", content: "Error de conexion. Verificando sistemas..." };
      setMessages(prev => prev.filter(m => m.role !== "typing").concat(errMsg));
    }
    setNeuralActivity(0.2); setIsProcessing(false);
    inputRef.current?.focus();
  }, [input, isProcessing]);

  function clearChat() {
    fetch("/api/clear", { method: "POST" }).catch(() => {});
    setMessages([]); historyRef.current = [];
    setShowWelcome(true); setPanelOpen(false);
    stopSpeaking();
  }

  function handleKey(e) { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); } }

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

  // ── RENDER ──────────────────────────────────────────────
  return (
    <div style={S.container}>
      <div style={S.canvasWrap}>
        <canvas ref={canvasRef} style={S.canvas} />
        <div style={S.ambientOverlay} />
      </div>
      <header style={S.topBar}>
        <div style={S.brand}>
          <div style={{...S.statusDot, background: isSpeaking ? "#00d4ff" : isListening ? "#ff4444" : isProcessing ? "#ff6b35" : "#00ff88", boxShadow: `0 0 12px ${isSpeaking ? "#00d4ff" : isListening ? "#ff4444" : isProcessing ? "#ff6b35" : "#00ff88"}`}} />
          <h1 style={S.title}>J.A.R.V.I.S.</h1>
          <span style={S.version}>NEURAL v2.0</span>
          {isSpeaking && <span style={{fontSize:11,color:"#00d4ff",marginLeft:8,animation:"pulse-glow 2s infinite"}}>HABLANDO</span>}
          {isListening && <span style={{fontSize:11,color:"#ff4444",marginLeft:8,animation:"pulse-red 1.5s infinite"}}>ESCUCHANDO</span>}
        </div>
        <div style={S.topRight}>
          <div style={S.neuralMeter}>
            <span style={S.meterLabel}>Neural</span>
            <div style={S.meterTrack}>
              <div style={{...S.meterFill, width: `${neuralActivity * 100}%`, background: neuralActivity > 0.5 ? "#00d4ff" : "#00ff88"}} />
            </div>
          </div>
          <button onClick={toggleContinuous} style={{...S.iconBtn, color: continuousMode ? "#ff4444" : "#4a6a8a", position:"relative"}} title="Modo continuo">
            {continuousMode ? "\u{1F534}" : "\u{2B55}"}
            {continuousMode && <span style={{position:"absolute",top:-2,right:-2,width:6,height:6,borderRadius:"50%",background:"#ff4444",animation:"pulse-red 1s infinite"}} />}
          </button>
          <button onClick={() => setSpeakEnabled(!speakEnabled)} style={{...S.iconBtn, color: speakEnabled ? "#00d4ff" : "#4a5568"}}>
            {speakEnabled ? "\u{1F50A}" : "\u{1F507}"}
          </button>
          <button onClick={clearChat} style={S.iconBtn}>{"\u{1F5D1}"}</button>
        </div>
      </header>
      {showWelcome && (
        <div style={S.welcomeOverlay}>
          <div style={S.welcomeContent}>
            <div style={S.welcomeGlow} />
            <h2 style={S.welcomeTitle}>Buenos dias, senor</h2>
            <p style={S.welcomeSub}>Todos los sistemas operativos. Listo para asistirle.</p>
            <p style={S.welcomeHint}>Pulse el boton rojo {"\ud83d\udd34"} para modo continuo de voz</p>
            <div style={S.sugGrid}>
              {suggestions.map((s, i) => (
                <button key={i} style={S.sugBtn}
                  onClick={() => sendMessage(s.text)}
                  onMouseEnter={e => { e.target.style.borderColor = "#00d4ff"; e.target.style.background = "rgba(0,212,255,0.08)"; }}
                  onMouseLeave={e => { e.target.style.borderColor = "rgba(0,212,255,0.15)"; e.target.style.background = "rgba(0,15,30,0.6)"; }}
                >
                  <span style={S.sugIcon}>{s.icon}</span>
                  <span style={S.sugText}>{s.text}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
      <div style={{...S.chatPanel, transform: panelOpen ? "translateX(0)" : "translateX(100%)", opacity: panelOpen ? 1 : 0}}>
        <div ref={chatRef} style={S.chatMessages}>
          {messages.map((msg, i) => {
            if (msg.role === "typing") return (
              <div key={i} style={S.msgRow}><div style={S.jarvisAvatar}>J</div><div style={S.bubbleJarvis}><div style={S.typingDots}><span style={{...S.tDot, animationDelay:"0s"}} /><span style={{...S.tDot, animationDelay:"0.2s"}} /><span style={{...S.tDot, animationDelay:"0.4s"}} /></div></div></div>
            );
            const isUser = msg.role === "user";
            return (
              <div key={i} style={{...S.msgRow, justifyContent: isUser ? "flex-end" : "flex-start"}}>
                {!isUser && <div style={S.jarvisAvatar}>J</div>}
                <div style={isUser ? S.bubbleUser : S.bubbleJarvis} dangerouslySetInnerHTML={isUser ? undefined : { __html: fmtMd(msg.content) }}>{isUser ? msg.content : undefined}</div>
                {isUser && <div style={S.userAvatar}>D</div>}
              </div>
            );
          })}
        </div>
      </div>
      <div style={S.inputBar}>
        <div style={S.inputInner}>
          <button onClick={toggleVoice} style={isListening ? {...S.voiceBtn, ...S.voiceBtnActive} : S.voiceBtn}>{"\u{1F3A4}"}</button>
          {isSpeaking && <button onClick={stopSpeaking} style={{...S.voiceBtn, borderColor:"#00d4ff", color:"#00d4ff"}}>{"\u23F9"}</button>}
          <textarea ref={inputRef} value={input} onChange={e => setInput(e.target.value)} onKeyDown={handleKey}
            placeholder={isListening ? "Escuchando..." : isSpeaking ? "JARVIS hablando..." : "Habla con JARVIS..."}
            rows={1} style={S.textInput} />
          <button onClick={() => sendMessage()} disabled={!input.trim() || isProcessing}
            style={{...S.sendBtn, opacity: !input.trim() || isProcessing ? 0.3 : 1}}>{"\u{27A4}"}</button>
        </div>
        <div style={S.inputHints}>
          <span style={S.hint}>Ctrl+Shift+Espacio = voz | {"\ud83d\udd34"} = modo continuo</span>
          {panelOpen && <button onClick={() => setPanelOpen(false)} style={S.minimizeBtn}>Minimizar chat</button>}
          {!panelOpen && messages.length > 0 && <button onClick={() => setPanelOpen(true)} style={S.minimizeBtn}>Abrir chat ({messages.filter(m=>m.role!=="typing").length})</button>}
        </div>
      </div>
      <style>{`
        @keyframes typing-dot { 0%,60%,100%{opacity:.3;transform:scale(.8)} 30%{opacity:1;transform:scale(1)} }
        @keyframes pulse-glow { 0%,100%{box-shadow:0 0 15px rgba(0,212,255,.15)} 50%{box-shadow:0 0 30px rgba(0,212,255,.3)} }
        @keyframes pulse-red { 0%,100%{box-shadow:0 0 0 0 rgba(255,68,68,.3)} 50%{box-shadow:0 0 0 10px rgba(255,68,68,0)} }
        @keyframes float { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-8px)} }
        textarea:focus{outline:none}
        ::-webkit-scrollbar{width:4px} ::-webkit-scrollbar-track{background:transparent} ::-webkit-scrollbar-thumb{background:#1e2d42;border-radius:2px}
        *{box-sizing:border-box}
      `}</style>
    </div>
  );
}

function fmtMd(text) {
  if (!text) return "";
  return text.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")
    .replace(/\`\`\`([\s\S]*?)\`\`\`/g, '<pre style="background:#0a1628;border:1px solid #1a2d45;border-radius:8px;padding:12px;overflow-x:auto;margin:8px 0;font-size:13px"><code>$1</code></pre>')
    .replace(/\`([^\`]+)\`/g, '<code style="background:rgba(0,212,255,.1);color:#00d4ff;padding:2px 6px;border-radius:4px;font-size:13px">$1</code>')
    .replace(/\*\*(.+?)\*\*/g, '<strong style="color:#00d4ff">$1</strong>')
    .replace(/\*(.+?)\*/g, '<em style="color:#00ff88">$1</em>')
    .replace(/\n/g, "<br>");
}

const S = {
  container: { fontFamily: "'Rajdhani',sans-serif", background: "#030810", color: "#e0e8f0", height: "100vh", display: "flex", flexDirection: "column", overflow: "hidden", position: "relative" },
  canvasWrap: { position: "absolute", inset: 0, zIndex: 0 },
  canvas: { width: "100%", height: "100%", display: "block" },
  ambientOverlay: { position: "absolute", inset: 0, background: "radial-gradient(ellipse at 50% 50%, transparent 30%, #030810 75%)", pointerEvents: "none" },
  topBar: { position: "relative", zIndex: 10, display: "flex", justifyContent: "space-between", alignItems: "center", padding: "10px 20px", background: "linear-gradient(180deg,rgba(3,8,16,.95),rgba(3,8,16,.6))", borderBottom: "1px solid rgba(0,212,255,.1)" },
  brand: { display: "flex", alignItems: "center", gap: 10 },
  statusDot: { width: 10, height: 10, borderRadius: "50%", transition: "all .3s" },
  title: { fontFamily: "'Orbitron',sans-serif", fontSize: 16, fontWeight: 700, color: "#00d4ff", letterSpacing: 4, margin: 0 },
  version: { fontSize: 10, color: "#4a6a8a", letterSpacing: 2, textTransform: "uppercase" },
  topRight: { display: "flex", alignItems: "center", gap: 12 },
  neuralMeter: { display: "flex", alignItems: "center", gap: 6 },
  meterLabel: { fontSize: 10, color: "#4a6a8a", letterSpacing: 1, textTransform: "uppercase" },
  meterTrack: { width: 60, height: 4, background: "#0a1628", borderRadius: 2, overflow: "hidden" },
  meterFill: { height: "100%", borderRadius: 2, transition: "all .5s ease" },
  iconBtn: { background: "none", border: "none", color: "#4a6a8a", fontSize: 16, cursor: "pointer", padding: 4, transition: "color .2s" },
  welcomeOverlay: { position: "absolute", inset: 0, zIndex: 5, display: "flex", alignItems: "center", justifyContent: "center", pointerEvents: "none" },
  welcomeContent: { pointerEvents: "auto", textAlign: "center", maxWidth: 700, padding: "0 20px", position: "relative" },
  welcomeGlow: { position: "absolute", top: "-100px", left: "50%", transform: "translateX(-50%)", width: 300, height: 300, borderRadius: "50%", background: "radial-gradient(circle,rgba(0,212,255,.06),transparent 70%)", pointerEvents: "none" },
  welcomeTitle: { fontFamily: "'Orbitron',sans-serif", fontSize: 28, color: "#00d4ff", marginBottom: 8, letterSpacing: 3, animation: "float 4s ease-in-out infinite" },
  welcomeSub: { fontSize: 15, color: "#5a7a9a", marginBottom: 10, letterSpacing: 1 },
  welcomeHint: { fontSize: 12, color: "#ff6b6b", marginBottom: 20, letterSpacing: 0.5 },
  sugGrid: { display: "grid", gridTemplateColumns: "repeat(auto-fill,minmax(200px,1fr))", gap: 8, maxWidth: 650, margin: "0 auto" },
  sugBtn: { background: "rgba(0,15,30,.6)", border: "1px solid rgba(0,212,255,.15)", borderRadius: 10, padding: "10px 14px", cursor: "pointer", display: "flex", alignItems: "center", gap: 8, transition: "all .2s", backdropFilter: "blur(10px)" },
  sugIcon: { fontSize: 18, flexShrink: 0 },
  sugText: { fontSize: 13, color: "#c0d0e0", fontFamily: "'Rajdhani',sans-serif", textAlign: "left" },
  chatPanel: { position: "absolute", right: 0, top: 48, bottom: 80, width: "min(420px, 100vw)", zIndex: 8, background: "linear-gradient(180deg,rgba(3,8,16,.92),rgba(5,12,24,.95))", borderLeft: "1px solid rgba(0,212,255,.1)", transition: "all .4s cubic-bezier(.4,0,.2,1)", display: "flex", flexDirection: "column", backdropFilter: "blur(20px)" },
  chatMessages: { flex: 1, overflowY: "auto", padding: "16px 14px", display: "flex", flexDirection: "column", gap: 12 },
  msgRow: { display: "flex", gap: 8, alignItems: "flex-end" },
  jarvisAvatar: { width: 28, height: 28, borderRadius: "50%", background: "linear-gradient(135deg,#0099cc,#00d4ff)", color: "#030810", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 12, fontWeight: 700, flexShrink: 0 },
  userAvatar: { width: 28, height: 28, borderRadius: "50%", background: "linear-gradient(135deg,#6366f1,#8b5cf6)", color: "#fff", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 12, fontWeight: 700, flexShrink: 0 },
  bubbleJarvis: { background: "rgba(0,20,40,.7)", border: "1px solid rgba(0,212,255,.12)", borderRadius: "14px 14px 14px 4px", padding: "10px 14px", fontSize: 14, lineHeight: 1.6, maxWidth: "85%", backdropFilter: "blur(10px)" },
  bubbleUser: { background: "rgba(99,102,241,.15)", border: "1px solid rgba(99,102,241,.2)", borderRadius: "14px 14px 4px 14px", padding: "10px 14px", fontSize: 14, lineHeight: 1.6, maxWidth: "85%" },
  typingDots: { display: "flex", gap: 5, padding: "4px 0" },
  tDot: { width: 6, height: 6, background: "#00d4ff", borderRadius: "50%", animation: "typing-dot 1.4s ease-in-out infinite" },
  inputBar: { position: "relative", zIndex: 10, padding: "10px 20px 16px", background: "linear-gradient(0deg,rgba(3,8,16,.98),rgba(3,8,16,.7))", borderTop: "1px solid rgba(0,212,255,.08)" },
  inputInner: { display: "flex", gap: 8, alignItems: "flex-end", maxWidth: 800, margin: "0 auto" },
  voiceBtn: { width: 40, height: 40, borderRadius: 12, border: "1px solid rgba(0,212,255,.15)", background: "rgba(0,15,30,.6)", color: "#5a7a9a", cursor: "pointer", fontSize: 16, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0, transition: "all .2s" },
  voiceBtnActive: { background: "rgba(255,68,68,.15)", borderColor: "#ff4444", color: "#ff4444", animation: "pulse-red 1.5s ease-in-out infinite" },
  textInput: { flex: 1, background: "rgba(0,15,30,.6)", border: "1px solid rgba(0,212,255,.12)", borderRadius: 12, color: "#e0e8f0", fontFamily: "'Rajdhani',sans-serif", fontSize: 15, padding: "10px 14px", resize: "none", maxHeight: 100, lineHeight: 1.4, backdropFilter: "blur(10px)" },
  sendBtn: { width: 40, height: 40, borderRadius: 12, border: "none", background: "#00d4ff", color: "#030810", cursor: "pointer", fontSize: 16, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0, fontWeight: 700, transition: "all .2s" },
  inputHints: { display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 6, padding: "0 4px" },
  hint: { fontSize: 10, color: "#3a5a7a", letterSpacing: 1 },
  minimizeBtn: { background: "none", border: "1px solid rgba(0,212,255,.15)", borderRadius: 6, color: "#5a7a9a", fontSize: 11, padding: "3px 10px", cursor: "pointer", fontFamily: "'Rajdhani',sans-serif", transition: "all .2s" },
};
