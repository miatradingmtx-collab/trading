import React, { useState, useEffect, useRef, useCallback } from 'react';
import ForceGraph3D from 'react-force-graph-3d';
import * as THREE from 'three';

// ─── Constantes de configuración ──────────────────────────────────────────────
const RAILWAY_API = 'https://trading-production-927a.up.railway.app/api/dashboard_data';
const WS_URL      = 'ws://localhost:8000/ws';

const SwarmGraph = () => {
  const fgRef = useRef();

  // ─── Estado ───────────────────────────────────────────────────────────────
  const [logs, setLogs]           = useState([]);
  const [wsStatus, setWsStatus]   = useState('Conectando al orquestador...');
  const [activeNodes, setActiveNodes] = useState(new Set());
  const [railwayData, setRailwayData] = useState(null);

  // ─── 6 Agentes reales del Swarm ───────────────────────────────────────────
  const [graphData] = useState({
    nodes: [
      { id: 'Master', name: 'MIA BOT', group: 1, val: 30, color: '#e91e63' },
      { id: 'Inbox',  name: 'INBOX',   group: 2, val: 18, color: '#FF5722' },
      { id: 'Daily',  name: 'DAILY',   group: 2, val: 18, color: '#2196F3' },
      { id: 'MOC',    name: 'MOC',     group: 2, val: 18, color: '#4CAF50' },
      { id: 'Tags',   name: 'TAGS',    group: 2, val: 18, color: '#9C27B0' },
      { id: 'Vault',  name: 'VAULT',   group: 3, val: 18, color: '#FFC107' }
    ],
    links: [
      { source: 'Inbox',  target: 'Master' },
      { source: 'Daily',  target: 'Master' },
      { source: 'MOC',    target: 'Master' },
      { source: 'Tags',   target: 'Master' },
      { source: 'Master', target: 'Vault'  },
      { source: 'Vault',  target: 'Master' }
    ]
  });

  // ─── WebSocket — orquestador local :8000 ──────────────────────────────────
  useEffect(() => {
    let ws;
    let retryTimeout;

    const activateNode = (agent) => {
      setActiveNodes(prev => {
        const next = new Set(prev);
        next.add(agent);
        setTimeout(() => {
          setActiveNodes(cur => { const u = new Set(cur); u.delete(agent); return u; });
        }, 3000);
        return next;
      });
    };

    const connect = () => {
      ws = new WebSocket(WS_URL);

      ws.onopen = () => {
        setWsStatus('✅ Orquestador conectado — Puerto 8000');
      };

      ws.onmessage = (event) => {
        try {
          const { agent, action, data } = JSON.parse(event.data);
          const ts = new Date().toLocaleTimeString('es-MX', { hour12: false });
          setLogs(prev => [...prev.slice(-30), `[${ts}] [${agent}] ${action.toUpperCase()}: ${data}`]);
          if (agent) activateNode(agent);
        } catch (_) {}
      };

      ws.onerror = () => setWsStatus('⚠️ Sin conexión — orquestador apagado');
      ws.onclose = () => {
        setWsStatus('🔄 Reconectando en 5s...');
        retryTimeout = setTimeout(connect, 5000);
      };
    };

    connect();
    return () => { clearTimeout(retryTimeout); if (ws) ws.close(); };
  }, []);

  // ─── Polling a Railway — caché RAM (cada 30s) ─────────────────────────────
  useEffect(() => {
    const fetchRailway = () => {
      fetch(RAILWAY_API)
        .then(r => r.json())
        .then(json => {
          if (json.status === 'success') {
            setRailwayData(json.data);
            // Inyectar log automático con balance
            const ts = new Date().toLocaleTimeString('es-MX', { hour12: false });
            const bal = json.data.balance_actual?.toFixed(2) ?? '?';
            const eq  = json.data.equity?.toFixed(2) ?? '?';
            const fp  = json.data.floating_pnl?.toFixed(2) ?? '?';
            setLogs(prev => [
              ...prev.slice(-30),
              `[${ts}] [RAILWAY] SYNC: Balance $${bal} | Equity $${eq} | Floating PnL $${fp}`
            ]);
          }
        })
        .catch(() => {
          const ts = new Date().toLocaleTimeString('es-MX', { hour12: false });
          setLogs(prev => [...prev.slice(-30), `[${ts}] [RAILWAY] ERROR: No se pudo conectar al endpoint`]);
        });
    };

    fetchRailway(); // Llamada inmediata al montar
    const interval = setInterval(fetchRailway, 30000);
    return () => clearInterval(interval);
  }, []);

  // ─── Cámara rotatoria ─────────────────────────────────────────────────────
  useEffect(() => {
    if (!fgRef.current) return;
    fgRef.current.d3Force('charge').strength(-200);
    let angle = 0;
    const dist = 300;
    const id = setInterval(() => {
      if (fgRef.current) {
        fgRef.current.cameraPosition({ x: dist * Math.sin(angle), z: dist * Math.cos(angle) });
        angle += Math.PI / 1000;
      }
    }, 10);
    return () => clearInterval(id);
  }, []);

  // ─── Sprite estilo fantasma pixelado ──────────────────────────────────────
  const createGhostSprite = useCallback((node, isActive) => {
    const canvas = document.createElement('canvas');
    canvas.width = 128; canvas.height = 128;
    const ctx = canvas.getContext('2d');

    const bodyColor = isActive ? '#FFFFFF' : (node.id === 'Master' ? '#e91e63' : node.color);
    ctx.fillStyle = bodyColor;

    const px = 8, ox = 32, oy = 32;
    const pixels = node.id === 'Master' ? [
      "  xxxx  ",
      " xxxxxx ",
      "xxoxxoxx",
      "xxxxxxxx",
      "xx x xxx",
      "x x  x x",
      "x x  x x"
    ] : [
      "  xxxx  ",
      " xxxxxx ",
      "xxoxxoxx",
      "xxxxxxxx",
      "xxxxxxxx",
      "xx xx xx",
      "x  xx  x"
    ];

    pixels.forEach((row, y) => {
      for (let x = 0; x < row.length; x++) {
        if (row[x] === 'x') {
          ctx.fillStyle = bodyColor;
          ctx.fillRect(ox + x * px, oy + y * px, px, px);
        } else if (row[x] === 'o') {
          ctx.fillStyle = '#000';
          ctx.fillRect(ox + x * px, oy + y * px, px, px);
        }
      }
    });

    ctx.fillStyle = isActive ? '#0ff' : '#FFF';
    ctx.font = 'bold 11px monospace';
    ctx.textAlign = 'center';
    ctx.fillText(node.name, 64, 110);

    const texture  = new THREE.CanvasTexture(canvas);
    const material = new THREE.SpriteMaterial({ map: texture, transparent: true });
    const sprite   = new THREE.Sprite(material);
    const size     = isActive ? node.val * 1.5 : node.val;
    sprite.scale.set(size, size, 1);
    return sprite;
  }, []);

  // ─── Render ───────────────────────────────────────────────────────────────
  const kpis = railwayData?.kpis ?? {};
  const balance = railwayData?.balance_actual?.toFixed(2) ?? '—';
  const equity  = railwayData?.equity?.toFixed(2)         ?? '—';
  const fpnl    = railwayData?.floating_pnl?.toFixed(2)   ?? '—';
  const winRate = kpis?.win_rate ?? '—';

  return (
    <div style={{ position: 'relative', width: '100vw', height: '100vh', background: '#0a0a0f' }}>

      {/* ── Panel de título y estado ── */}
      <div style={{ position: 'absolute', top: 20, left: 20, zIndex: 10, color: '#0ff', fontFamily: 'monospace' }}>
        <h2 style={{ margin: 0 }}>MIA BOT / OBSIDIAN</h2>
        <p style={{ fontSize: '13px', margin: '4px 0 0', color: logs.length > 0 ? '#0f0' : '#888' }}>
          {logs.length > 0 ? '⚡ Sincronizando agentes...' : wsStatus}
        </p>
      </div>

      {/* ── Panel KPIs Railway (arriba derecha) ── */}
      <div style={{
        position: 'absolute', top: 20, right: 20, zIndex: 10,
        background: 'rgba(0,0,0,0.75)', border: '1px solid #1a1a2e',
        borderRadius: '6px', padding: '12px 18px', fontFamily: 'monospace',
        color: '#0ff', fontSize: '12px', minWidth: '200px',
        boxShadow: '0 0 12px rgba(0,200,255,0.15)'
      }}>
        <div style={{ color: '#555', borderBottom: '1px solid #1a1a2e', paddingBottom: '6px', marginBottom: '8px' }}>
          📡 RAILWAY — CACHE RAM
        </div>
        <div>💰 Balance: <span style={{ color: '#0f0' }}>${balance}</span></div>
        <div>📊 Equity:  <span style={{ color: '#0f0' }}>${equity}</span></div>
        <div>📈 Float PnL: <span style={{ color: parseFloat(fpnl) >= 0 ? '#0f0' : '#f44' }}>${fpnl}</span></div>
        <div>🎯 Win Rate: <span style={{ color: '#ff0' }}>{winRate}%</span></div>
      </div>

      {/* ── Terminal flotante ── */}
      <div style={{
        position: 'absolute', bottom: 20, left: 20, width: '460px',
        height: '230px', background: 'rgba(0,0,0,0.88)', border: '1px solid #1a3a1a',
        zIndex: 10, color: '#0f0', fontFamily: 'monospace', padding: '14px',
        overflowY: 'auto', borderRadius: '6px', boxShadow: '0 0 12px rgba(0,255,0,0.15)'
      }}>
        <h4 style={{ margin: '0 0 8px 0', color: '#555', borderBottom: '1px solid #1a3a1a', paddingBottom: '5px' }}>
          &gt;_ SWARM_TERMINAL
        </h4>
        {logs.map((log, i) => (
          <div key={i} style={{
            marginBottom: '5px', fontSize: '11px',
            color: log.includes('RAILWAY') ? '#0af' : log.includes('ERROR') ? '#f44' : '#0f0'
          }}>{log}</div>
        ))}
        {logs.length === 0 && (
          <div style={{ color: '#444', fontStyle: 'italic' }}>{wsStatus}</div>
        )}
      </div>

      {/* ── Grafo 3D ── */}
      <ForceGraph3D
        ref={fgRef}
        graphData={graphData}
        nodeThreeObject={node => createGhostSprite(node, activeNodes.has(node.id))}
        linkDirectionalParticles={2}
        linkDirectionalParticleSpeed={d => activeNodes.has(d.source.id) ? 0.02 : 0.005}
        linkDirectionalParticleWidth={1.5}
        linkColor={() => 'rgba(255,255,255,0.2)'}
        backgroundColor="#0a0a0f"
        onEngineTick={() => {
          if (fgRef.current) {
            const master = graphData.nodes.find(n => n.id === 'Master');
            if (master) { master.fx = 0; master.fy = 0; master.fz = 0; }
          }
        }}
      />
    </div>
  );
};

export default SwarmGraph;
