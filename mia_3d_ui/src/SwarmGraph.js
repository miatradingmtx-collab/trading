import React, { useState, useEffect, useRef } from 'react';
import { Canvas, useFrame, useLoader } from '@react-three/fiber';
import { OrbitControls, Stars } from '@react-three/drei';
import { Activity, Eye, Calculator, Map, ShieldCheck, Briefcase, Shield, Zap, CheckCircle, TerminalSquare, TrendingUp, BarChart2, Hash } from 'lucide-react';
import * as THREE from 'three';

const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const WS_URL = ${protocol}///ws;

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

          if (data.type === 'AGENT_STATUS') {
            const agentName = data.agent;
            setActiveAgent(agentName);
            
            const logEntry = {
              ts: new Date().toLocaleTimeString('en-US', { hour12: false }),
              agent: agentName,
              action: data.action || 'THINKING',
              msg: data.msg || data.data
            };

            setLogs(prev => [logEntry, ...prev].slice(0, 50));
            
            setTimeout(() => {
              setActiveAgent(curr => curr === agentName ? null : curr);
            }, 3000);
          }
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
    <div className="w-screen h-screen bg-[#06080c] text-slate-300 font-mono overflow-hidden flex flex-col">
      <div className="w-full flex justify-between items-center p-4 bg-[#0a0d14] border-b border-slate-800 shadow-lg shrink-0">
        <div className="flex items-center gap-4">
          <div className="text-2xl font-black text-[#ff6a00] tracking-widest drop-shadow-[0_0_8px_rgba(255,106,0,0.8)]">GROKTOPUS</div>
          <div className="text-[10px] text-slate-500 uppercase tracking-widest border-l border-slate-700 pl-4">Groq Bot - Autonomous Trading Floor / 8 Arms / 8 Agents</div>
        </div>
        <div className="flex items-center gap-6 text-[10px] font-bold tracking-widest text-slate-400">
          <div>CYCLE <span className="text-white">12</span></div>
          <div>UPTIME <span className="text-white">313h 25m</span></div>
          <div>MANDATE <span className="text-[#ff6a00]">SWARM</span></div>
          <div className="flex items-center gap-2">
            GRIP <div className={w-2 h-2 rounded-full animate-pulse }></div>
          </div>
        </div>
      </div>

      <div className="w-full grid grid-cols-4 gap-4 p-4 shrink-0">
        {[ 
          { label: "NET EQUITY", val: ",741.61", sub: "SEED ,000.00", color: "text-white" },
          { label: "TOTAL P&L", val: "+,741.61", sub: "+11.83% PEAK ,930", color: "text-[#00ffa3]" },
          { label: "24H VOLUME", val: ".24M", sub: "1,599 FILLS - 8 VENUES", color: "text-white" },
          { label: "HIT RATE", val: "76.1%", sub: "233W / 73L - SHARPE 2.41", color: "text-white" }
        ].map((m, i) => (
          <div key={i} className="bg-[#0a0d14] border border-slate-800 rounded-lg p-4 flex flex-col relative overflow-hidden">
            <div className="absolute top-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-[#ff6a00] to-transparent opacity-50"></div>
            <span className="text-[10px] text-slate-500 tracking-widest mb-1">{m.label}</span>
            <span className={	ext-2xl font-black tracking-wider }>{m.val}</span>
            <span className="text-[9px] text-slate-500 mt-1 uppercase">{m.sub}</span>
          </div>
        ))}
      </div>

      <div className="flex-1 w-full flex px-4 gap-4 overflow-hidden">
        <div className="w-[300px] shrink-0 bg-[#0a0d14] border border-slate-800 rounded-lg p-4 flex flex-col hidden md:flex">
          <div className="text-[10px] font-bold text-slate-500 tracking-widest mb-4 flex items-center gap-2"><BarChart2 size={12}/> BALANCE HISTORY</div>
          <div className="flex-1 relative flex items-center justify-center border border-slate-800/50 bg-[#06080c] rounded">
            <div className="absolute top-2 right-2 text-[#00ffa3] text-xs font-bold">,741.64</div>
            <div className="w-full h-full p-2 flex items-end">
              {[3,5,4,6,5,7,8,7,9,10,12,11,14,13,15].map((h, i) => (
                <div key={i} className="flex-1 bg-gradient-to-t from-transparent to-[#00ffa3]/50 mx-[1px] border-t border-[#00ffa3]" style={{height: ${h*5}%}}></div>
              ))}
            </div>
          </div>
        </div>

        <div className="flex-1 relative bg-[#0a0d14] border border-slate-800 rounded-lg overflow-hidden flex flex-col">
          <div className="absolute top-4 left-4 z-20 text-[10px] font-bold text-slate-500 tracking-widest flex items-center gap-2">
             THE REEF - SWARM CORE
          </div>
          <div className="absolute top-4 right-4 z-20 text-[9px] text-slate-600 tracking-widest">
             8 ARMS - 3 EXECUTING - 241 ops/s
          </div>

          <div className="absolute inset-0 z-0">
            <Canvas camera={{ position: [0, 0, 7] }}>
              <ambientLight intensity={0.1} />
              <Stars radius={50} depth={50} count={3000} factor={4} saturation={0} fade speed={1.5} />
              <GroktopusCore activeAgent={activeAgent} />
              <OrbitControls enableZoom={false} enablePan={false} autoRotate autoRotateSpeed={0.5} />
            </Canvas>
          </div>

          <div className="absolute inset-0 z-10 pointer-events-none">
            {agents.map((ag) => {
              const isActive = activeAgent === ag.name;
              return (
                <div 
                  key={ag.id} 
                  className={bsolute -translate-x-1/2 -translate-y-1/2 p-2 rounded border bg-[#06080c]/80 backdrop-blur-md transition-all duration-300
                    
                  }
                  style={{ top: ag.pos.top, left: ag.pos.left }}
                >
                  <div className="flex items-center gap-2 mb-1">
                    <div className={w-1.5 h-1.5 rounded-full }></div>
                    <span className={	ext-[10px] font-bold tracking-widest }>{ag.name}</span>
                  </div>
                  <div className="text-[8px] text-slate-500 uppercase px-1">{ag.desc}</div>
                </div>
              );
            })}
          </div>
        </div>

        <div className="w-[350px] shrink-0 bg-[#0a0d14] border border-slate-800 rounded-lg flex flex-col overflow-hidden hidden lg:flex">
          <div className="p-4 border-b border-slate-800 flex justify-between items-center bg-[#06080c]">
             <div className="text-[10px] font-bold text-slate-500 tracking-widest flex items-center gap-2"><TerminalSquare size={12}/> ACTIVITY LOG</div>
             <div className="text-[9px] text-slate-600">306 RESOLVED</div>
          </div>
          <div className="flex-1 overflow-y-auto p-2 scroll-smooth">
            {logs.length === 0 && <div className="text-slate-600 text-[10px] italic p-2">Awaiting stream...</div>}
            {logs.map((log, i) => (
              <div key={i} className="flex gap-2 text-[10px] p-2 hover:bg-white/5 border-b border-slate-800/50 items-start">
                <span className="text-slate-600 shrink-0">[{log.ts}]</span>
                <span className="text-[#ff6a00] font-bold shrink-0">{log.agent}</span>
                <span className="text-slate-300 line-clamp-2">{log.msg}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="w-full h-20 p-4 shrink-0 flex gap-2 overflow-x-auto">
        {agents.map((ag, i) => {
          const isActive = activeAgent === ag.name;
          return (
            <div key={i} className="min-w-[120px] flex-1 bg-[#0a0d14] border border-slate-800 rounded-lg p-2 flex flex-col justify-between relative overflow-hidden">
              <div className={bsolute top-0 left-0 w-full h-1 transition-colors duration-300 }></div>
              <div className="flex justify-between items-start mt-1">
                <div className="flex flex-col">
                  <span className="text-[10px] font-bold text-slate-300">{ag.name}</span>
                  <span className="text-[8px] text-slate-500">{ag.desc}</span>
                </div>
                {React.cloneElement(ag.icon, { size: 14, className: isActive ? 'text-[#00ffa3]' : 'text-slate-600' })}
              </div>
              <div className={	ext-[9px] tracking-widest mt-1 }>
                {isActive ? 'RUNNING' : 'STANDBY'}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default GroktopusDashboard;