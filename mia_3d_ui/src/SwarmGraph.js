import React, { useState, useEffect, useRef, useCallback } from 'react';
import ForceGraph3D from 'react-force-graph-3d';
import * as THREE from 'three';

// ── Configuración ──────────────────────────────────────────────────────────────
// Proxy local: FastAPI en :8000 hace el fetch a Railway server-side (sin CORS)
const CACHE_API = 'http://localhost:8000/api/cache';
const WS_URL    = 'ws://localhost:8000/ws';

// Colores por agente para la terminal
const AGENT_COLORS = {
  Master:  '#e91e63',
  Inbox:   '#FF5722',
  Daily:   '#2196F3',
  MOC:     '#4CAF50',
  Tags:    '#9C27B0',
  Vault:   '#FFC107',
  RAILWAY: '#00bcd4',
};

// ── Nodos del Swarm ─────────────────────────────────────────────────────────────
const INITIAL_GRAPH = {
  nodes: [
    { id: 'Master', name: 'MIA BOT', group: 1, val: 32, color: '#e91e63' },
    { id: 'Inbox',  name: 'INBOX',   group: 2, val: 18, color: '#FF5722' },
    { id: 'Daily',  name: 'DAILY',   group: 2, val: 18, color: '#2196F3' },
    { id: 'MOC',    name: 'MOC',     group: 2, val: 18, color: '#4CAF50' },
    { id: 'Tags',   name: 'TAGS',    group: 2, val: 18, color: '#9C27B0' },
    { id: 'Vault',  name: 'VAULT',   group: 3, val: 18, color: '#FFC107' },
  ],
  links: [
    { source: 'Inbox',  target: 'Master' },
    { source: 'Daily',  target: 'Master' },
    { source: 'MOC',    target: 'Master' },
    { source: 'Tags',   target: 'Master' },
    { source: 'Master', target: 'Vault'  },
    { source: 'Vault',  target: 'Master' },
  ],
};

// ── Sprite: Pulpo pixel-art (Master) ───────────────────────────────────────────
function drawOctopus(ctx, color, px, ox, oy) {
  const rows = [
    '  xxxxx  ',
    ' xxxxxxx ',
    'xxoxxxoxx',
    'xxxxxxxxx',
    ' xxxxxxx ',
    'x x x x x',
    'x x x x x',
  ];
  rows.forEach((row, y) => {
    for (let x = 0; x < row.length; x++) {
      if (row[x] === 'x') {
        ctx.fillStyle = color;
        ctx.fillRect(ox + x * px, oy + y * px, px, px);
      } else if (row[x] === 'o') {
        ctx.fillStyle = '#111';
        ctx.fillRect(ox + x * px, oy + y * px, px, px);
      }
    }
  });
}

// ── Sprite: Fantasma pixel-art (Agentes) ───────────────────────────────────────
function drawGhost(ctx, color, px, ox, oy) {
  const rows = [
    '  xxxx  ',
    ' xxxxxx ',
    'xxoxxoxx',
    'xxxxxxxx',
    'xxxxxxxx',
    'xx xx xx',
    'x  xx  x',
  ];
  rows.forEach((row, y) => {
    for (let x = 0; x < row.length; x++) {
      if (row[x] === 'x') {
        ctx.fillStyle = color;
        ctx.fillRect(ox + x * px, oy + y * px, px, px);
      } else if (row[x] === 'o') {
        ctx.fillStyle = '#111';
        ctx.fillRect(ox + x * px, oy + y * px, px, px);
      }
    }
  });
}

// ── Componente Principal ────────────────────────────────────────────────────────
const SwarmGraph = () => {
  const fgRef = useRef();
  const [logs,       setLogs]       = useState([]);
  const [wsStatus,   setWsStatus]   = useState('Conectando al orquestador...');
  const [activeNodes,setActiveNodes]= useState(new Set());
  const [graphData]                 = useState(INITIAL_GRAPH);

  // ── WebSocket :8000 ───────────────────────────────────────────────────────────
  useEffect(() => {
    let ws, retryTimeout;

    const activate = (agent) => {
      setActiveNodes(prev => {
        const next = new Set(prev);
        next.add(agent);
        setTimeout(() => setActiveNodes(c => { const u = new Set(c); u.delete(agent); return u; }), 3000);
        return next;
      });
    };

    const connect = () => {
      ws = new WebSocket(WS_URL);
      ws.onopen  = () => setWsStatus('✅ Orquestador conectado — Puerto 8000');
      ws.onerror = () => setWsStatus('⚠️  Sin conexión — orquestador apagado');
      ws.onclose = () => { setWsStatus('🔄 Reconectando en 5s...'); retryTimeout = setTimeout(connect, 5000); };
      ws.onmessage = (e) => {
        try {
          const { agent, action, data } = JSON.parse(e.data);
          const ts = new Date().toLocaleTimeString('es-MX', { hour12: false });
          setLogs(prev => [...prev.slice(-40), { ts, agent, action: action.toUpperCase(), data }]);
          if (agent) activate(agent);
        } catch (_) {}
      };
    };

    connect();
    return () => { clearTimeout(retryTimeout); ws && ws.close(); };
  }, []);

  // ── Polling caché Railway vía proxy local cada 30s ───────────────────────────
  useEffect(() => {
    const pull = () => {
      fetch(CACHE_API)
        .then(r => r.json())
        .then(json => {
          if (json.status === 'success') {
            const ts  = new Date().toLocaleTimeString('es-MX', { hour12: false });
            const bal = json.data?.balance_actual?.toFixed(2) ?? '?';
            const eq  = json.data?.equity?.toFixed(2)         ?? '?';
            const fp  = json.data?.floating_pnl?.toFixed(2)   ?? '?';
            setLogs(prev => [...prev.slice(-40),
              { ts, agent: 'RAILWAY', action: 'SYNC',
                data: `Balance $${bal} | Equity $${eq} | Float PnL $${fp}` }
            ]);
          }
        })
        .catch(() => {
          const ts = new Date().toLocaleTimeString('es-MX', { hour12: false });
          setLogs(prev => [...prev.slice(-40),
            { ts, agent: 'RAILWAY', action: 'ERROR', data: 'Proxy local no disponible — reinicia :8000' }
          ]);
        });
    };
    pull();
    const id = setInterval(pull, 30000);
    return () => clearInterval(id);
  }, []);

  // ── Órbita circular real + ancla Master al centro ────────────────────────────
  useEffect(() => {
    if (!fgRef.current) return;

    // Desactivar todas las fuerzas para control total de posición
    fgRef.current.d3Force('charge', null);
    fgRef.current.d3Force('link',   null);
    fgRef.current.d3Force('center', null);

    const RADIUS = 120;
    const agents = ['Inbox', 'Daily', 'MOC', 'Tags', 'Vault'];
    const speeds  = [0.008, 0.006, 0.007, 0.009, 0.005];
    let angles    = agents.map((_, i) => (2 * Math.PI / agents.length) * i);

    // Posición inicial fija
    const master = graphData.nodes.find(n => n.id === 'Master');
    if (master) { master.fx = 0; master.fy = 0; master.fz = 0; }

    let camAngle = 0;
    const dist   = 320;
    const id = setInterval(() => {
      if (!fgRef.current) return;

      // Orbitar agentes
      agents.forEach((agentId, i) => {
        const node = graphData.nodes.find(n => n.id === agentId);
        if (node) {
          angles[i] += speeds[i];
          node.fx = RADIUS * Math.cos(angles[i]);
          node.fy = RADIUS * 0.3 * Math.sin(angles[i] * 2);
          node.fz = RADIUS * Math.sin(angles[i]);
        }
      });

      // Cámara rotatoria suave
      camAngle += 0.003;
      fgRef.current.cameraPosition({
        x: dist * Math.sin(camAngle),
        z: dist * Math.cos(camAngle),
        y: 80,
      });
    }, 16);

    return () => clearInterval(id);
  }, [graphData.nodes]);

  // ── Sprite canvas → THREE.Sprite ─────────────────────────────────────────────
  const createSprite = useCallback((node, isActive) => {
    const canvas = document.createElement('canvas');
    canvas.width = 144; canvas.height = 144;
    const ctx   = canvas.getContext('2d');
    const color = isActive ? '#FFFFFF' : node.color;
    const px = 8, ox = 28, oy = 28;

    if (node.id === 'Master') {
      drawOctopus(ctx, color, px, ox, oy);
    } else {
      drawGhost(ctx, color, px, ox, oy);
    }

    // Nombre
    ctx.fillStyle  = isActive ? '#0ff' : '#FFF';
    ctx.font       = 'bold 11px monospace';
    ctx.textAlign  = 'center';
    ctx.shadowColor   = isActive ? '#0ff' : node.color;
    ctx.shadowBlur    = isActive ? 12 : 0;
    ctx.fillText(node.name, 72, 126);

    const tex  = new THREE.CanvasTexture(canvas);
    const mat  = new THREE.SpriteMaterial({ map: tex, transparent: true });
    const spr  = new THREE.Sprite(mat);
    const size = isActive ? node.val * 1.6 : node.val;
    spr.scale.set(size, size, 1);
    return spr;
  }, []);

  // ── Render ────────────────────────────────────────────────────────────────────
  return (
    <div style={{ position: 'relative', width: '100vw', height: '100vh', background: '#0a0a0f', overflow: 'hidden' }}>

      {/* Título */}
      <div style={{ position: 'absolute', top: 20, left: 20, zIndex: 10, fontFamily: 'monospace', userSelect: 'none' }}>
        <h2 style={{ margin: 0, color: '#e91e63', letterSpacing: '3px', textShadow: '0 0 12px #e91e63' }}>
          MIA BOT / OBSIDIAN
        </h2>
        <p style={{ margin: '4px 0 0', fontSize: '12px', color: logs.length > 0 ? '#0f0' : '#555' }}>
          {logs.length > 0 ? '⚡ Enjambre activo' : wsStatus}
        </p>
      </div>



      {/* Terminal SWARM */}
      <div style={{
        position: 'absolute', bottom: 20, left: 20, width: '480px', maxHeight: '260px',
        background: 'rgba(0,0,0,0.9)', border: '1px solid #1a3a1a',
        zIndex: 10, fontFamily: 'monospace', padding: '14px',
        overflowY: 'auto', borderRadius: '8px',
        boxShadow: '0 0 16px rgba(0,255,0,0.1)'
      }}>
        <h4 style={{ margin: '0 0 8px', color: '#444', borderBottom: '1px solid #1a3a1a', paddingBottom: '5px', fontSize: '11px' }}>
          &gt;_ SWARM_TERMINAL — GROKTOPUS
        </h4>
        {logs.length === 0 && (
          <div style={{ color: '#333', fontStyle: 'italic', fontSize: '11px' }}>{wsStatus}</div>
        )}
        {logs.map((log, i) => {
          const color = AGENT_COLORS[log.agent] ?? '#0f0';
          return (
            <div key={i} style={{ marginBottom: '4px', fontSize: '11px', lineHeight: '1.4' }}>
              <span style={{ color: '#555' }}>[{log.ts}] </span>
              <span style={{ color, fontWeight: 'bold' }}>[{log.agent}]</span>
              <span style={{ color: '#888' }}> {log.action}: </span>
              <span style={{ color: log.action === 'ERROR' ? '#f44' : log.action === 'SUCCESS' ? '#0f0' : '#aaa' }}>
                {log.data}
              </span>
            </div>
          );
        })}
      </div>

      {/* Grafo 3D */}
      <ForceGraph3D
        ref={fgRef}
        graphData={graphData}
        nodeThreeObject={node => createSprite(node, activeNodes.has(node.id))}
        nodeThreeObjectExtend={false}
        linkDirectionalParticles={3}
        linkDirectionalParticleSpeed={d => activeNodes.has(
          typeof d.source === 'object' ? d.source.id : d.source
        ) ? 0.025 : 0.006}
        linkDirectionalParticleWidth={1.8}
        linkColor={() => 'rgba(233,30,99,0.25)'}
        linkWidth={0.5}
        backgroundColor="#0a0a0f"
        enableNodeDrag={false}
      />
    </div>
  );
};

export default SwarmGraph;
