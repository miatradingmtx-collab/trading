import React, { useState, useEffect, useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Sphere, MeshDistortMaterial, OrbitControls, Stars } from '@react-three/drei';
import { Activity, Eye, Calculator, Map, ShieldCheck, Briefcase, Shield, Zap, CheckCircle, TerminalSquare } from 'lucide-react';

const CACHE_API = 'http://localhost:8000/api/cache';
const WS_URL    = 'ws://localhost:8000/ws';

// ── 3D Groktopus Core ──────────────────────────────────────────────────────────
const GroktopusCore = ({ activeAgent }) => {
  const meshRef = useRef();
  
  useFrame((state) => {
    if (meshRef.current) {
      meshRef.current.rotation.x = state.clock.getElapsedTime() * 0.15;
      meshRef.current.rotation.y = state.clock.getElapsedTime() * 0.25;
      // Respiración sutil
      meshRef.current.scale.setScalar(1 + Math.sin(state.clock.getElapsedTime() * 2) * 0.04);
    }
  });

  const isThinking = activeAgent && activeAgent !== 'Master' && activeAgent !== 'VESKA';
  const isExecuting = activeAgent === 'Master' || activeAgent === 'VESKA';

  let color = "#e91e63"; // Magenta (Idle)
  if (isThinking) color = "#00ffa3"; // Cian (Analizando)
  if (isExecuting) color = "#ffeb3b"; // Dorado (Consenso/Ejecutando)

  return (
    <mesh ref={meshRef}>
      <Sphere args={[1.5, 64, 64]}>
        <MeshDistortMaterial
          color={color}
          attach="material"
          distort={isThinking ? 0.5 : 0.3}
          speed={isThinking ? 3 : 1}
          roughness={0.2}
          metalness={0.6}
          emissive={color}
          emissiveIntensity={0.6}
        />
      </Sphere>
      <pointLight color={color} intensity={15} distance={20} />
    </mesh>
  );
};

// ── Dashboard Principal ────────────────────────────────────────────────────────
const GroktopusDashboard = () => {
  const [logs, setLogs] = useState([]);
  const [wsStatus, setWsStatus] = useState('CONNECTING...');
  const [activeAgent, setActiveAgent] = useState(null);

  // ── Conexión WebSocket (Misma Caché, Mismo Bot) ─────────────────────────────
  useEffect(() => {
    let ws, retryTimeout;

    const connect = () => {
      ws = new WebSocket(WS_URL);
      ws.onopen  = () => setWsStatus('CONNECTED / LIVE FLOOR');
      ws.onerror = () => setWsStatus('OFFLINE');
      ws.onclose = () => { setWsStatus('RECONNECTING...'); retryTimeout = setTimeout(connect, 5000); };
      
      ws.onmessage = (e) => {
        try {
          const msg = JSON.parse(e.data);
          const ts = new Date().toLocaleTimeString('es-MX', { hour12: false });
          
          setLogs(prev => [...prev.slice(-25), { ts, ...msg }]);
          
          // Mapeamos los nombres del backend a los 8 agentes del lore si es posible
          // O iluminamos por acción.
          if (msg.agent) {
            setActiveAgent(msg.agent);
            setTimeout(() => setActiveAgent(null), 4000); 
          }
        } catch (_) {}
      };
    };

    connect();
    return () => { clearTimeout(retryTimeout); ws && ws.close(); };
  }, []);

  // ── Los 8 Agentes del Piso de Trading ───────────────────────────────────────
  const agents = [
    { id: 'TIDAL', icon: <Activity size={20}/>, name: 'TIDAL', desc: 'Order Book Scanner', color: 'text-cyan-400', border: 'border-cyan-400/50' },
    { id: 'LUMEN', icon: <Eye size={20}/>, name: 'LUMEN', desc: 'Sentiment Engine', color: 'text-yellow-400', border: 'border-yellow-400/50' },
    { id: 'NORO',  icon: <Calculator size={20}/>, name: 'NORO', desc: 'Fair Value / Math', color: 'text-blue-400', border: 'border-blue-400/50' },
    { id: 'ZEPHR', icon: <Map size={20}/>, name: 'ZEPHR', desc: 'Liquidity Mapper', color: 'text-green-400', border: 'border-green-400/50' },
    { id: 'VESKA', icon: <Zap size={20}/>, name: 'VESKA', desc: 'Execution Specialist', color: 'text-mia-magenta', border: 'border-mia-magenta/50' },
    { id: 'OKAPI', icon: <ShieldCheck size={20}/>, name: 'OKAPI', desc: 'Hedge Exposure', color: 'text-orange-400', border: 'border-orange-400/50' },
    { id: 'MARIN', icon: <Briefcase size={20}/>, name: 'MARIN', desc: 'Settlement Desk', color: 'text-purple-400', border: 'border-purple-400/50' },
    { id: 'RUNE',  icon: <Shield size={20}/>, name: 'RUNE', desc: 'Risk Control (Veto)', color: 'text-red-500', border: 'border-red-500/50' }
  ];

  return (
    <div className="w-screen h-screen bg-[#050505] text-slate-300 font-mono overflow-hidden relative flex flex-col">
      
      {/* ── HEADER ──────────────────────────────────────────────────────────── */}
      <div className="absolute top-0 left-0 w-full p-6 z-20 flex justify-between items-start pointer-events-none">
        <div>
          <h1 className="text-3xl font-bold tracking-[0.2em] text-mia-magenta drop-shadow-[0_0_10px_rgba(233,30,99,0.8)]">
            GROKTOPUS
          </h1>
          <p className="text-sm tracking-widest text-slate-500 mt-1">AI TRADING FLOOR / MIA BOT</p>
        </div>
        <div className="text-right">
          <div className="flex items-center gap-2 justify-end">
            <div className={`w-3 h-3 rounded-full animate-pulse ${wsStatus.includes('LIVE') ? 'bg-mia-cyan shadow-[0_0_8px_#00ffa3]' : 'bg-red-500'}`}></div>
            <span className="text-sm font-bold tracking-widest text-slate-400">{wsStatus}</span>
          </div>
          <p className="text-xs text-slate-600 mt-1">CONSENSUS THRESHOLD: 70%</p>
        </div>
      </div>

      {/* ── 3D SCENE & ORBITING AGENTS ──────────────────────────────────────── */}
      <div className="absolute inset-0 z-0">
        <Canvas camera={{ position: [0, 0, 7] }}>
          <ambientLight intensity={0.1} />
          <Stars radius={100} depth={50} count={4000} factor={4} saturation={0} fade speed={1.5} />
          <GroktopusCore activeAgent={activeAgent} />
          <OrbitControls enableZoom={false} autoRotate autoRotateSpeed={0.8} />
        </Canvas>
      </div>

      {/* ── AGENT HTML OVERLAYS ─────────────────────────────────────────────── */}
      <div className="absolute inset-0 z-10 pointer-events-none flex items-center justify-center">
        <div className="relative w-[800px] h-[800px]">
          {agents.map((ag, i) => {
            const angle = (i / agents.length) * Math.PI * 2 - Math.PI / 2;
            const radius = 42; // Porcentaje de distancia desde el centro
            const top = `${50 + Math.sin(angle) * radius}%`;
            const left = `${50 + Math.cos(angle) * radius}%`;
            
            // Map incoming backend agent names to these 8 lore agents conceptually if possible
            // For now, it glows if the ID matches loosely.
            const isMatch = activeAgent && (
                ag.id.toLowerCase() === activeAgent.toLowerCase() ||
                (activeAgent === 'Master' && ag.id === 'RUNE') ||
                (activeAgent === 'Inbox' && ag.id === 'TIDAL') ||
                (activeAgent === 'Daily' && ag.id === 'NORO') ||
                (activeAgent === 'MOC' && ag.id === 'ZEPHR') ||
                (activeAgent === 'Tags' && ag.id === 'LUMEN') ||
                (activeAgent === 'Vault' && ag.id === 'MARIN')
            );

            return (
              <div 
                key={ag.id} 
                className={`absolute -translate-x-1/2 -translate-y-1/2 p-4 rounded-xl border backdrop-blur-md transition-all duration-700
                  ${isMatch ? `bg-slate-900/90 ${ag.border} scale-125 z-50 shadow-[0_0_20px_rgba(255,255,255,0.1)]` : 'bg-slate-900/40 border-slate-800 scale-100 opacity-60'}
                `}
                style={{ top, left }}
              >
                <div className={`flex items-center gap-3 mb-2 ${ag.color}`}>
                  {ag.icon}
                  <span className="font-bold text-lg tracking-wider">{ag.name}</span>
                  {isMatch && <CheckCircle size={16} className="ml-2 animate-pulse" />}
                </div>
                <div className="text-xs text-slate-400 font-sans tracking-wide uppercase">{ag.desc}</div>
              </div>
            );
          })}
        </div>
      </div>

      {/* ── SWARM TERMINAL ──────────────────────────────────────────────────── */}
      <div className="absolute bottom-6 left-1/2 -translate-x-1/2 w-[80%] max-w-4xl h-[30vh] bg-[#08080c]/80 backdrop-blur-xl border border-slate-800/80 rounded-xl z-30 flex flex-col shadow-2xl">
        <div className="flex items-center gap-2 p-3 border-b border-slate-800/80 bg-black/40 rounded-t-xl">
          <TerminalSquare size={16} className="text-slate-500" />
          <span className="text-xs font-bold text-slate-500 tracking-widest">SWARM_TERMINAL // INTER-AGENT COMMS</span>
        </div>
        
        <div className="flex-1 overflow-y-auto p-4 space-y-3 scroll-smooth">
          {logs.length === 0 && (
            <div className="text-slate-600 text-sm italic">Esperando inicialización del piso de trading...</div>
          )}
          {logs.map((log, i) => {
             // Determinar color de agente dinámicamente o por defecto cian
             let agentColor = 'text-mia-cyan';
             if (log.agent === 'Master') agentColor = 'text-mia-magenta';
             if (log.agent === 'Inbox' || log.agent === 'TIDAL') agentColor = 'text-orange-400';
             if (log.agent === 'Daily' || log.agent === 'NORO') agentColor = 'text-blue-400';
             if (log.agent === 'MOC' || log.agent === 'ZEPHR') agentColor = 'text-green-400';
             if (log.agent === 'Tags' || log.agent === 'LUMEN') agentColor = 'text-yellow-400';
             if (log.agent === 'Vault' || log.agent === 'MARIN') agentColor = 'text-purple-400';

             return (
               <div key={i} className="flex flex-col md:flex-row md:items-start gap-2 border-l-2 border-slate-800 pl-3">
                 <div className="flex gap-2 shrink-0 text-xs mt-[2px]">
                   <span className="text-slate-600">[{log.ts}]</span>
                   <span className={`font-bold uppercase tracking-wider ${agentColor}`}>
                     [{log.agent || 'SYSTEM'}]
                   </span>
                 </div>
                 <div className="text-sm text-slate-300 leading-relaxed font-sans">
                   <span className="text-slate-500 mr-2 uppercase text-[10px] tracking-widest border border-slate-700 rounded px-1">
                     {log.action}
                   </span>
                   {log.data}
                 </div>
               </div>
             );
          })}
        </div>
      </div>

    </div>
  );
};

export default GroktopusDashboard;
