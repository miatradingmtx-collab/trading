import React, { useState, useEffect, useRef } from 'react';
import { Canvas, useFrame, useLoader } from '@react-three/fiber';
import { OrbitControls, Stars } from '@react-three/drei';
import { Activity, Eye, Calculator, Map, ShieldCheck, Briefcase, Shield, Zap, TerminalSquare } from 'lucide-react';
import * as THREE from 'three';

const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const WS_URL = `${protocol}//${window.location.host}/ws`;

const AntopusCore = ({ activeAgent }) => {
  const meshRef = useRef();
  const texture = useLoader(THREE.TextureLoader, '/pro_octopus.jpg');
  
  useFrame((state) => {
    if (meshRef.current) {
      const isMobile = window.innerWidth < 768;
      const scaleBase = isMobile ? 5 : 8;
      const pulse = Math.sin(state.clock.getElapsedTime() * 2) * 0.25;
      meshRef.current.scale.set(scaleBase + pulse, scaleBase + pulse, 1);
    }
  });

  const isThinking = activeAgent && activeAgent !== 'Master' && activeAgent !== 'VESKA' && activeAgent !== 'RUNE';
  const isExecuting = activeAgent === 'Master' || activeAgent === 'VESKA' || activeAgent === 'RUNE';

  let color = "#ffffff";
  if (isThinking) color = "#aaffaa"; 
  if (isExecuting) color = "#ffffaa"; 

  return (
    <sprite ref={meshRef}>
      <spriteMaterial map={texture} color={color} transparent={true} opacity={1} blending={THREE.AdditiveBlending} depthWrite={false} />
    </sprite>
  );
};

const AntopusDashboard = () => {
  const [logs, setLogs] = useState([]);
  const [wsStatus, setWsStatus] = useState('CONNECTING...');
  const [activeAgent, setActiveAgent] = useState(null);
  const logsEndRef = useRef(null);

  useEffect(() => {
    let ws, retryTimeout;

    const connect = () => {
      ws = new WebSocket(WS_URL);

      ws.onopen = () => {
        setWsStatus('CONNECTED / LIVE FLOOR');
        clearTimeout(retryTimeout);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'HEARTBEAT') return;

          const agentName = data.agent || 'SYSTEM';
          setActiveAgent(agentName);
          
          const logEntry = {
            ts: new Date().toLocaleTimeString('en-US', { hour12: false }),
            agent: agentName,
            action: data.action || data.type || 'LOG',
            msg: data.msg || data.data || data.texto || JSON.stringify(data)
          };

          setLogs(prev => [...prev, logEntry].slice(-100));
          
          setTimeout(() => {
            setActiveAgent(curr => curr === agentName ? null : curr);
          }, 3000);
        } catch (e) {
          console.error("WS parse error", e);
        }
      };

      ws.onclose = () => {
        setWsStatus('DISCONNECTED - RETRYING...');
        retryTimeout = setTimeout(connect, 3000);
      };
    };

    connect();

    return () => {
      if (ws) ws.close();
      clearTimeout(retryTimeout);
    };
  }, []);

  useEffect(() => {
    if (logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [logs]);

  // Posiciones aseguradas dentro del contenedor de 100% de alto y ancho (Ellipse instead of perfect circle to fit landscape screens)
  const agents = [
    { id: 'NORO', name: 'NORO', desc: 'PRICING', color: 'text-[#ff6a00]', border: 'border-[#ff6a00]', icon: <Calculator size={18}/>, pos: { top: '10%', left: '50%' } },
    { id: 'LUMEN', name: 'LUMEN', desc: 'SENTIMENT', color: 'text-yellow-400', border: 'border-yellow-400', icon: <Eye size={18}/>, pos: { top: '25%', left: '80%' } },
    { id: 'TIDAL', name: 'TIDAL', desc: 'SCANNER', color: 'text-[#00ffa3]', border: 'border-[#00ffa3]', icon: <Activity size={18}/>, pos: { top: '50%', left: '90%' } },
    { id: 'ZEPHR', name: 'ZEPHR', desc: 'LIQUIDITY', color: 'text-emerald-400', border: 'border-emerald-400', icon: <Map size={18}/>, pos: { top: '75%', left: '80%' } },
    { id: 'MARIN', name: 'MARIN', desc: 'SETTLEMENT', color: 'text-purple-400', border: 'border-purple-400', icon: <Briefcase size={18}/>, pos: { top: '90%', left: '50%' } },
    { id: 'OKAPI', name: 'OKAPI', desc: 'HEDGING', color: 'text-orange-400', border: 'border-orange-400', icon: <ShieldCheck size={18}/>, pos: { top: '75%', left: '20%' } },
    { id: 'RUNE', name: 'RUNE', desc: 'RISK', color: 'text-red-500', border: 'border-red-500', icon: <Shield size={18}/>, pos: { top: '50%', left: '10%' } },
    { id: 'VESKA', name: 'VESKA', desc: 'EXECUTION', color: 'text-blue-400', border: 'border-blue-400', icon: <Zap size={18}/>, pos: { top: '25%', left: '20%' } }
  ];

  return (
    <div className="w-screen h-[100dvh] bg-[#06080c] text-slate-300 font-mono flex flex-col relative overflow-hidden">
      
      {/* HEADER */}
      <div className="w-full p-4 md:p-6 z-20 flex flex-col md:flex-row justify-between items-center md:items-start shrink-0 pointer-events-none bg-gradient-to-b from-[#06080c] to-transparent absolute top-0">
        <div className="text-center md:text-left mb-2 md:mb-0">
          <h1 className="text-xl md:text-3xl font-bold tracking-[0.2em] text-[#ff6a00] drop-shadow-[0_0_10px_rgba(255,106,0,0.8)]">
              ANTOPUS
            </h1>
            <h2 className="text-sm md:text-md font-bold text-[#00ffa3] tracking-widest mt-1 drop-shadow-[0_0_5px_rgba(0,255,163,0.8)]">
              MIA IA
            </h2>
            <p className="text-[10px] md:text-xs text-slate-500 uppercase tracking-widest mt-1">
              MODO: SHADOW TRADING (TESTING)
          </p>
        </div>
        <div className="text-center md:text-right flex flex-col items-center md:items-end">
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 md:w-3 md:h-3 rounded-full animate-pulse ${wsStatus.includes('LIVE') ? 'bg-[#00ffa3] shadow-[0_0_8px_#00ffa3]' : 'bg-red-500'}`}></div>
            <span className="text-xs md:text-sm font-bold tracking-widest text-slate-400">{wsStatus}</span>
          </div>
          <p className="text-[9px] md:text-xs text-slate-600 mt-1">CONSENSUS THRESHOLD: 70%</p>
        </div>
      </div>

      {/* TOP SECTION: 3D SCENE & ORBIT */}
      <div className="relative w-full flex-1 pt-20 pb-4">
        <div className="absolute inset-0 z-0">
          <Canvas camera={{ position: [0, 0, 7] }}>
            <ambientLight intensity={0.1} />
            <Stars radius={100} depth={50} count={4000} factor={4} saturation={0} fade speed={1.5} />
            <AntopusCore activeAgent={activeAgent} />
            <OrbitControls enableZoom={false} enablePan={false} autoRotate autoRotateSpeed={0.5} />
          </Canvas>
        </div>

        {/* Orbit HTML Overlays (w-full h-full to prevent clipping) */}
        <div className="absolute inset-0 z-10 pointer-events-none mt-20 md:mt-10">
          <div className="relative w-full h-full max-w-5xl mx-auto">
            {agents.map((ag) => {
              const isActive = activeAgent === ag.name;
              return (
                <div 
                  key={ag.id} 
                  className={`absolute -translate-x-1/2 -translate-y-1/2 p-2 md:p-3 rounded-xl border backdrop-blur-md transition-all duration-700 flex flex-col items-center md:items-start
                    ${isActive ? 'bg-slate-900/90 border-[#00ffa3] scale-110 md:scale-125 z-50 shadow-[0_0_15px_rgba(0,255,163,0.3)]' : 'bg-slate-900/60 border-slate-800 scale-90 md:scale-100 opacity-80'}
                  `}
                  style={{ top: ag.pos.top, left: ag.pos.left }}
                >
                  <div className={`flex items-center justify-center md:justify-start gap-1 md:gap-2 mb-1 ${isActive ? 'text-[#00ffa3]' : 'text-slate-400'}`}>
                    <div className="hidden md:block">{ag.icon}</div>
                    <span className="font-bold text-[10px] md:text-sm tracking-wider">{ag.name}</span>
                  </div>
                  <div className="text-[8px] md:text-xs text-slate-400 font-sans tracking-wide uppercase hidden sm:block">{ag.desc}</div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* BOTTOM SECTION: SWARM TERMINAL */}
      <div className="w-full h-[40vh] md:h-[35vh] px-2 md:px-8 pb-4 md:pb-8 z-30 flex justify-center shrink-0">
        <div className="w-full max-w-6xl h-full bg-[#08080c]/90 backdrop-blur-xl border border-[#ff6a00]/30 rounded-xl flex flex-col shadow-[0_0_30px_rgba(255,106,0,0.1)] overflow-hidden pointer-events-auto">
          <div className="flex items-center gap-2 p-2 md:p-3 border-b border-[#ff6a00]/30 bg-black/60 shrink-0">
            <TerminalSquare size={14} className="text-[#ff6a00]" />
            <span className="text-[10px] md:text-xs font-bold text-[#ff6a00] tracking-widest">SWARM_TERMINAL // INTER-AGENT COMMS</span>
          </div>
          
          <div className="flex-1 overflow-y-auto p-2 md:p-4 space-y-2 md:space-y-3 scroll-smooth">
            {logs.length === 0 && (
              <div className="text-slate-600 text-[10px] md:text-sm italic">Awaiting telemetry stream from Swarm...</div>
            )}
            {logs.map((log, i) => {
               let agentColor = 'text-[#00ffa3]';
               if (log.agent === 'Vault' || log.agent === 'MARIN') agentColor = 'text-purple-400';
               if (log.agent === 'RUNE') agentColor = 'text-red-500';
               if (log.agent === 'NORO') agentColor = 'text-[#ff6a00]';

               return (
                 <div key={i} className="flex flex-col md:flex-row md:items-start gap-1 md:gap-2 border-l-2 border-slate-800 pl-2 hover:bg-white/5 p-1 transition-colors">
                   <div className="flex gap-2 shrink-0 text-[10px] md:text-xs mt-[2px]">
                     <span className="text-slate-600">[{log.ts}]</span>
                     <span className={`font-bold uppercase tracking-wider ${agentColor}`}>
                       [{log.agent || 'SYSTEM'}]
                     </span>
                   </div>
                   <div className="text-[11px] md:text-sm text-slate-300 leading-relaxed font-sans flex-1 break-words">
                     <span className="text-slate-500 mr-2 uppercase text-[8px] md:text-[10px] tracking-widest border border-slate-700 rounded px-1">
                       {log.action}
                     </span>
                     {log.msg}
                   </div>
                 </div>
               );
            })}
            <div ref={logsEndRef} />
          </div>
        </div>
      </div>
    </div>
  );
};

export default AntopusDashboard;
