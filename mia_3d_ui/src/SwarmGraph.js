import React, { useState, useEffect, useRef } from 'react';
import { Canvas, useFrame, useLoader } from '@react-three/fiber';
import { OrbitControls, Stars } from '@react-three/drei';
import { Activity, Eye, Calculator, Map, ShieldCheck, Briefcase, Shield, Zap, TerminalSquare } from 'lucide-react';
import * as THREE from 'three';

const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const WS_URL = `${protocol}//${window.location.host}/ws`;

const GroktopusCore = ({ activeAgent }) => {
  const meshRef = useRef();
  const texture = useLoader(THREE.TextureLoader, '/logo512.png');
  
  useFrame((state) => {
    if (meshRef.current) {
      const scaleBase = 4;
      const pulse = Math.sin(state.clock.getElapsedTime() * 2) * 0.15;
      meshRef.current.scale.set(scaleBase + pulse, scaleBase + pulse, 1);
    }
  });

  const isThinking = activeAgent && activeAgent !== 'Master' && activeAgent !== 'VESKA' && activeAgent !== 'RUNE';
  const isExecuting = activeAgent === 'Master' || activeAgent === 'VESKA' || activeAgent === 'RUNE';

  let color = "#ff6a00";
  if (isThinking) color = "#00ffa3";
  if (isExecuting) color = "#ffeb3b";

  return (
    <sprite ref={meshRef}>
      <spriteMaterial map={texture} color={color} transparent={true} opacity={0.9} blending={THREE.AdditiveBlending} depthWrite={false} />
    </sprite>
  );
};

const GroktopusDashboard = () => {
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

  // Auto-scroll para la terminal
  useEffect(() => {
    if (logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [logs]);

  const agents = [
    { id: 'TIDAL', name: 'TIDAL', desc: 'SCANNER', color: 'text-[#00ffa3]', border: 'border-[#00ffa3]', icon: <Activity size={24}/>, pos: { top: '30%', left: '85%' } },
    { id: 'RUNE', name: 'RUNE', desc: 'RISK', color: 'text-red-500', border: 'border-red-500', icon: <Shield size={24}/>, pos: { top: '70%', left: '15%' } },
    { id: 'LUMEN', name: 'LUMEN', desc: 'SENTIMENT', color: 'text-yellow-400', border: 'border-yellow-400', icon: <Eye size={24}/>, pos: { top: '25%', left: '65%' } },
    { id: 'MARIN', name: 'MARIN', desc: 'SETTLEMENT', color: 'text-purple-400', border: 'border-purple-400', icon: <Briefcase size={24}/>, pos: { top: '75%', left: '60%' } },
    { id: 'NORO', name: 'NORO', desc: 'PRICING', color: 'text-[#ff6a00]', border: 'border-[#ff6a00]', icon: <Calculator size={24}/>, pos: { top: '25%', left: '35%' } },
    { id: 'OKAPI', name: 'OKAPI', desc: 'HEDGING', color: 'text-orange-400', border: 'border-orange-400', icon: <ShieldCheck size={24}/>, pos: { top: '75%', left: '40%' } },
    { id: 'ZEPHR', name: 'ZEPHR', desc: 'LIQUIDITY', color: 'text-emerald-400', border: 'border-emerald-400', icon: <Map size={24}/>, pos: { top: '70%', left: '85%' } },
    { id: 'VESKA', name: 'VESKA', desc: 'EXECUTION', color: 'text-blue-400', border: 'border-blue-400', icon: <Zap size={24}/>, pos: { top: '30%', left: '15%' } }
  ];

  return (
    <div className="w-screen h-screen bg-[#06080c] text-slate-300 font-mono overflow-hidden flex flex-col relative">
      
      {/* HEADER ABSOLUTO (Para no romper el 3D) */}
      <div className="absolute top-0 left-0 w-full p-6 z-20 flex justify-between items-start pointer-events-none">
        <div>
          <h1 className="text-3xl font-bold tracking-[0.2em] text-[#ff6a00] drop-shadow-[0_0_10px_rgba(255,106,0,0.8)]">
            GROKTOPUS
          </h1>
          <p className="text-xs text-slate-500 uppercase tracking-widest mt-1">
            MODO: SHADOW TRADING (TESTING)
          </p>
        </div>
        <div className="text-right">
          <div className="flex items-center gap-2 justify-end">
            <div className={`w-3 h-3 rounded-full animate-pulse ${wsStatus.includes('LIVE') ? 'bg-[#00ffa3] shadow-[0_0_8px_#00ffa3]' : 'bg-red-500'}`}></div>
            <span className="text-sm font-bold tracking-widest text-slate-400">{wsStatus}</span>
          </div>
          <p className="text-xs text-slate-600 mt-1">CONSENSUS THRESHOLD: 70%</p>
        </div>
      </div>

      {/* TOP SECTION: 3D SCENE & ORBIT */}
      <div className="relative w-full h-[65vh]">
        <div className="absolute inset-0 z-0">
          <Canvas camera={{ position: [0, 0, 7] }}>
            <ambientLight intensity={0.1} />
            <Stars radius={100} depth={50} count={4000} factor={4} saturation={0} fade speed={1.5} />
            <GroktopusCore activeAgent={activeAgent} />
            <OrbitControls enableZoom={false} enablePan={false} autoRotate autoRotateSpeed={0.5} />
          </Canvas>
        </div>

        {/* Orbit HTML Overlays */}
        <div className="absolute inset-0 z-10 pointer-events-none flex items-center justify-center">
          <div className="relative w-[800px] h-[800px] scale-[0.5] md:scale-75 lg:scale-100 mt-10 md:mt-0">
            {agents.map((ag) => {
              const isActive = activeAgent === ag.name;
              return (
                <div 
                  key={ag.id} 
                  className={`absolute -translate-x-1/2 -translate-y-1/2 p-4 rounded-xl border backdrop-blur-md transition-all duration-700
                    ${isActive ? 'bg-slate-900/90 border-[#00ffa3] scale-125 z-50 shadow-[0_0_20px_rgba(0,255,163,0.3)]' : 'bg-slate-900/40 border-slate-800 scale-100 opacity-60'}
                  `}
                  style={{ top: ag.pos.top, left: ag.pos.left }}
                >
                  <div className={`flex items-center gap-3 mb-2 ${isActive ? 'text-[#00ffa3]' : 'text-slate-400'}`}>
                    {ag.icon}
                    <span className="font-bold text-lg tracking-wider">{ag.name}</span>
                  </div>
                  <div className="text-xs text-slate-400 font-sans tracking-wide uppercase">{ag.desc}</div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* BOTTOM SECTION: SWARM TERMINAL */}
      <div className="w-full h-[35vh] px-8 pb-8 z-30 flex justify-center">
        <div className="w-full max-w-6xl h-full bg-[#08080c]/80 backdrop-blur-xl border border-[#ff6a00]/30 rounded-xl flex flex-col shadow-[0_0_30px_rgba(255,106,0,0.05)] overflow-hidden">
          <div className="flex items-center gap-2 p-3 border-b border-[#ff6a00]/30 bg-black/60 shrink-0">
            <TerminalSquare size={16} className="text-[#ff6a00]" />
            <span className="text-xs font-bold text-[#ff6a00] tracking-widest">SWARM_TERMINAL // INTER-AGENT COMMS</span>
          </div>
          
          <div className="flex-1 overflow-y-auto p-4 space-y-3 scroll-smooth">
            {logs.length === 0 && (
              <div className="text-slate-600 text-sm italic">Awaiting telemetry stream from Swarm...</div>
            )}
            {logs.map((log, i) => {
               let agentColor = 'text-[#00ffa3]';
               if (log.agent === 'Vault' || log.agent === 'MARIN') agentColor = 'text-purple-400';
               if (log.agent === 'RUNE') agentColor = 'text-red-500';
               if (log.agent === 'NORO') agentColor = 'text-[#ff6a00]';

               return (
                 <div key={i} className="flex flex-col md:flex-row md:items-start gap-2 border-l-2 border-slate-800 pl-3 hover:bg-white/5 p-1 transition-colors">
                   <div className="flex gap-2 shrink-0 text-xs mt-[2px]">
                     <span className="text-slate-600">[{log.ts}]</span>
                     <span className={`font-bold uppercase tracking-wider ${agentColor}`}>
                       [{log.agent || 'SYSTEM'}]
                     </span>
                   </div>
                   <div className="text-sm text-slate-300 leading-relaxed font-sans flex-1 break-words">
                     <span className="text-slate-500 mr-2 uppercase text-[10px] tracking-widest border border-slate-700 rounded px-1">
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

export default GroktopusDashboard;
