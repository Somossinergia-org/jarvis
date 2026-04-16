"use client";
import { useState, useRef, useEffect } from "react";

export default function JarvisPage() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [speakEnabled, setSpeakEnabled] = useState(true);
  const [showWelcome, setShowWelcome] = useState(true);
  const chatRef = useRef(null);
  const inputRef = useRef(null);
  const recognitionRef = useRef(null);
  const historyRef = useRef([]);

  useEffect(() => { initSpeechRecognition(); inputRef.current?.focus(); }, []);
  useEffect(() => { if (chatRef.current) chatRef.current.scrollTop = chatRef.current.scrollHeight; }, [messages]);

  function initSpeechRecognition() {
    const SR = typeof window !== "undefined" && (window.SpeechRecognition || window.webkitSpeechRecognition);
    if (!SR) return;
    const recognition = new SR();
    recognition.lang = "es-ES";
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.onresult = (event) => {
      const transcript = Array.from(event.results).map((r) => r[0].transcript).join("");
      setInput(transcript);
      if (event.results[event.results.length - 1].isFinal) {
        setIsListening(false);
        if (transcript.trim()) sendMessage(transcript.trim(), true);
      }
    };
    recognition.onerror = () => setIsListening(false);
    recognition.onend = () => setIsListening(false);
    recognitionRef.current = recognition;
  }

  function toggleVoice() {
    if (!recognitionRef.current) return;
    if (isListening) { recognitionRef.current.stop(); }
    else { setIsListening(true); recognitionRef.current.start(); window.speechSynthesis?.cancel(); }
  }

  function speak(text) {
    if (!speakEnabled || typeof window === "undefined" || !window.speechSynthesis) return;
    const clean = text.replace(/[*#_\`~>\[\]()!]/g, "").replace(/\n+/g, ". ");
    const u = new SpeechSynthesisUtterance(clean);
    u.lang = "es-ES"; u.rate = 1.05; u.pitch = 0.95;
    const voices = window.speechSynthesis.getVoices();
    const esVoice = voices.find((v) => v.lang.startsWith("es"));
    if (esVoice) u.voice = esVoice;
    window.speechSynthesis.speak(u);
  }

  async function sendMessage(text, isVoice = false) {
    const msg = text || input.trim();
    if (!msg || isProcessing) return;
    setIsProcessing(true); setShowWelcome(false); setInput("");
    const userMsg = { role: "user", content: msg };
    setMessages((prev) => [...prev, userMsg]);
    historyRef.current.push(userMsg);
    setMessages((prev) => [...prev, { role: "typing" }]);
    try {
      const res = await fetch("/api/chat", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: msg, history: historyRef.current.slice(-40), isVoice }),
      });
      const data = await res.json();
      const assistantMsg = { role: "assistant", content: data.response };
      setMessages((prev) => prev.filter((m) => m.role !== "typing").concat(assistantMsg));
      historyRef.current.push(assistantMsg);
      if (isVoice || speakEnabled) speak(data.response);
    } catch {
      setMessages((prev) => prev.filter((m) => m.role !== "typing").concat({ role: "assistant", content: "Error de conexion." }));
    }
    setIsProcessing(false); inputRef.current?.focus();
  }

  function clearChat() {
    fetch("/api/clear", { method: "POST" }).catch(() => {});
    setMessages([]); historyRef.current = []; setShowWelcome(true);
    window.speechSynthesis?.cancel();
  }

  function handleKey(e) { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); } }

  function fmt(text) {
    if (!text) return "";
    return text.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")
      .replace(/\`\`\`([\s\S]*?)\`\`\`/g,'<pre style="background:#0d1117;border:1px solid #1e2d42;border-radius:8px;padding:12px;overflow-x:auto;margin:8px 0"><code>$1</code></pre>')
      .replace(/\`([^\`]+)\`/g,'<code style="background:rgba(0,212,255,0.1);color:#00d4ff;padding:2px 6px;border-radius:4px">$1</code>')
      .replace(/\*\*(.+?)\*\*/g,'<strong style="color:#00d4ff">$1</strong>')
      .replace(/\*(.+?)\*/g,'<em style="color:#00ff88">$1</em>')
      .replace(/\n/g,"<br>");
  }

  const sugs = ["Que hora es?", "Crea una lista de tareas", "Dame una idea de proyecto", "Resume las noticias tech"];

  return (
    <div style={{fontFamily:"'Rajdhani',sans-serif",background:"#0a0e17",color:"#e0e8f0",height:"100vh",display:"flex",flexDirection:"column",overflow:"hidden"}}>
      <header style={{display:"flex",alignItems:"center",justifyContent:"space-between",padding:"12px 24px",background:"linear-gradient(180deg,#0f1520,#0a0e17)",borderBottom:"1px solid #1e2d42",flexShrink:0}}>
        <div style={{display:"flex",alignItems:"center",gap:14}}>
          <div style={{width:44,height:44,borderRadius:"50%",background:"radial-gradient(circle,#00d4ff,transparent 70%)",display:"flex",alignItems:"center",justifyContent:"center"}}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="#00d4ff"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/></svg>
          </div>
          <div>
            <h1 style={{fontFamily:"'Orbitron',sans-serif",fontSize:18,fontWeight:700,color:"#00d4ff",letterSpacing:4,margin:0}}>J.A.R.V.I.S.</h1>
            <span style={{fontSize:11,color:"#7a8a9e",letterSpacing:1}}>Asistente Personal de IA</span>
          </div>
        </div>
        <div style={{display:"flex",gap:10,alignItems:"center"}}>
          <div style={{width:8,height:8,borderRadius:"50%",background:"#00ff88"}}/>
          <span style={{fontSize:12,color:"#00ff88"}}>En linea</span>
          <button onClick={clearChat} style={{background:"#1a2332",border:"1px solid #1e2d42",color:"#7a8a9e",width:36,height:36,borderRadius:8,cursor:"pointer",fontSize:16}}>x</button>
        </div>
      </header>

      <div ref={chatRef} style={{flex:1,overflowY:"auto",padding:"20px 24px",display:"flex",flexDirection:"column",gap:16,scrollBehavior:"smooth"}}>
        {showWelcome && (
          <div style={{textAlign:"center",padding:"60px 20px",color:"#7a8a9e"}}>
            <h2 style={{fontFamily:"'Orbitron',sans-serif",fontSize:28,color:"#00d4ff",marginBottom:8,letterSpacing:3}}>Bienvenido, senor</h2>
            <p style={{fontSize:16,marginBottom:30}}>Soy JARVIS, su asistente personal. En que puedo ayudarle hoy?</p>
            <div style={{display:"flex",flexWrap:"wrap",gap:10,justifyContent:"center",maxWidth:600,margin:"0 auto"}}>
              {sugs.map((s,i)=>(<button key={i} style={{background:"#111827",border:"1px solid #1e2d42",borderRadius:12,padding:"10px 16px",cursor:"pointer",fontSize:13,color:"#e0e8f0",fontFamily:"'Rajdhani',sans-serif"}} onClick={()=>{setInput(s);sendMessage(s);}}>{s}</button>))}
            </div>
          </div>
        )}
        {messages.map((msg,i)=>{
          if(msg.role==="typing") return (<div key={i} style={{display:"flex",gap:12,alignSelf:"flex-start"}}><div style={{width:36,height:36,borderRadius:"50%",background:"linear-gradient(135deg,#0099cc,#00d4ff)",color:"#0a0e17",display:"flex",alignItems:"center",justifyContent:"center",flexShrink:0,fontSize:14,fontWeight:700}}>J</div><div style={{background:"#111827",border:"1px solid #1e2d42",borderRadius:16,padding:"12px 16px",fontSize:15}}>...</div></div>);
          const isU=msg.role==="user";
          return (<div key={i} style={{display:"flex",gap:12,maxWidth:"85%",alignSelf:isU?"flex-end":"flex-start",flexDirection:isU?"row-reverse":"row"}}><div style={{width:36,height:36,borderRadius:"50%",background:isU?"linear-gradient(135deg,#6366f1,#8b5cf6)":"linear-gradient(135deg,#0099cc,#00d4ff)",color:isU?"white":"#0a0e17",display:"flex",alignItems:"center",justifyContent:"center",flexShrink:0,fontSize:14,fontWeight:700}}>{isU?"D":"J"}</div><div style={{background:isU?"#1a1f3d":"#111827",border:isU?"1px solid #2a2f5d":"1px solid #1e2d42",borderRadius:16,padding:"12px 16px",fontSize:15,lineHeight:1.6}} dangerouslySetInnerHTML={isU?undefined:{__html:fmt(msg.content)}}>{isU?msg.content:undefined}</div></div>);
        })}
      </div>

      <div style={{padding:"16px 24px 20px",background:"linear-gradient(0deg,#0f1520,#0a0e17)",borderTop:"1px solid #1e2d42",flexShrink:0}}>
        <div style={{display:"flex",gap:10,alignItems:"flex-end",maxWidth:900,margin:"0 auto"}}>
          <div style={{flex:1,background:"#1a2332",border:"1px solid #1e2d42",borderRadius:16,display:"flex",padding:4}}>
            <textarea ref={inputRef} value={input} onChange={(e)=>setInput(e.target.value)} onKeyDown={handleKey} placeholder={isListening?"Escuchando...":"Escribe un mensaje..."} rows={1} style={{flex:1,background:"none",border:"none",color:"#e0e8f0",fontFamily:"'Rajdhani',sans-serif",fontSize:15,padding:"10px 14px",resize:"none",maxHeight:120,lineHeight:1.5,outline:"none"}}/>
          </div>
          <button onClick={toggleVoice} style={{width:44,height:44,borderRadius:14,border:"1px solid "+(isListening?"#ff4444":"#1e2d42"),background:isListening?"rgba(255,68,68,0.15)":"#1a2332",color:isListening?"#ff4444":"#7a8a9e",cursor:"pointer",fontSize:18,display:"flex",alignItems:"center",justifyContent:"center",flexShrink:0}}>M</button>
          <button onClick={()=>sendMessage()} disabled={!input.trim()||isProcessing} style={{width:44,height:44,borderRadius:14,border:"none",background:"#00d4ff",color:"#0a0e17",cursor:"pointer",fontSize:18,display:"flex",alignItems:"center",justifyContent:"center",flexShrink:0,fontWeight:700,opacity:(!input.trim()||isProcessing)?0.4:1}}>{">"}</button>
        </div>
        <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginTop:8,padding:"0 4px"}}>
          <label style={{display:"flex",alignItems:"center",gap:6,fontSize:12,color:"#7a8a9e",cursor:"pointer"}}>
            <span>Voz</span>
            <input type="checkbox" checked={speakEnabled} onChange={(e)=>setSpeakEnabled(e.target.checked)} style={{display:"none"}}/>
            <div style={{width:32,height:18,background:speakEnabled?"#0099cc":"#1e2d42",borderRadius:9,position:"relative"}}>
              <div style={{width:14,height:14,background:"#e0e8f0",borderRadius:"50%",position:"absolute",top:2,left:2,transform:speakEnabled?"translateX(14px)":"none",transition:"transform 0.2s"}}/>
            </div>
          </label>
          <span style={{fontSize:11,color:"#7a8a9e"}}>Ctrl+Shift+Espacio = voz</span>
        </div>
      </div>
      <style>{"textarea:focus{outline:none} ::-webkit-scrollbar{width:6px} ::-webkit-scrollbar-track{background:transparent} ::-webkit-scrollbar-thumb{background:#1e2d42;border-radius:3px}"}</style>
    </div>
  );
  }
