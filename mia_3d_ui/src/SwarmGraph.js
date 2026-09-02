import React, { useState, useEffect, useRef, useCallback } from 'react';
import ForceGraph3D from 'react-force-graph-3d';
import * as THREE from 'three';

const SwarmGraph = () => {
  const fgRef = useRef();
  const [logs, setLogs] = useState([]);
  
  // Nodos con estilo pixel/fantasma y posición central para el Master
  const initialData = {
    nodes: [
      { id: 'Master', name: 'GROK BOT', group: 1, val: 30, color: '#FFFFFF' },
      { id: 'Inbox', name: 'INBOX', group: 2, val: 15, color: '#FF5722' },
      { id: 'Daily', name: 'DAILY', group: 2, val: 15, color: '#2196F3' },
      { id: 'MOC', name: 'MOC', group: 2, val: 15, color: '#4CAF50' },
      { id: 'Tags', name: 'TAGS', group: 2, val: 15, color: '#9C27B0' },
      { id: 'Vault', name: 'VAULT', group: 3, val: 15, color: '#FFC107' }
    ],
    links: [
      { source: 'Inbox', target: 'Master' },
      { source: 'Daily', target: 'Master' },
      { source: 'MOC', target: 'Master' },
      { source: 'Tags', target: 'Master' },
      { source: 'Master', target: 'Vault' },
      { source: 'Vault', target: 'Master' }
    ]
  };

  const [graphData] = useState(initialData);
  const [activeNodes, setActiveNodes] = useState(new Set());

  useEffect(() => {
    // Conectar al WebSocket
    const ws = new WebSocket('ws://localhost:8000/ws');
    
    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        const { agent, action, data } = msg;
        
        // Agregar log a la terminal
        setLogs(prev => [...prev.slice(-10), `[${agent}] ${action.toUpperCase()}: ${data}`]);
        
        // Iluminar el nodo activo
        if (agent) {
          setActiveNodes(prev => {
            const next = new Set(prev);
            next.add(agent);
            // Apagar después de 3 segundos
            setTimeout(() => {
              setActiveNodes(current => {
                const updated = new Set(current);
                updated.delete(agent);
                return updated;
              });
            }, 3000);
            return next;
          });
        }
      } catch (e) {}
    };

    return () => ws.close();
  }, []);

  // Forzar que el Master esté en el centro (0,0,0) y los demás orbiten
  useEffect(() => {
    if (fgRef.current) {
      fgRef.current.d3Force('charge').strength(-200);
      fgRef.current.d3Force('radial', null);
      // Animacion rotatoria cinemática opcional
      let angle = 0;
      const distance = 300;
      const interval = setInterval(() => {
        if (fgRef.current) {
          fgRef.current.cameraPosition({
            x: distance * Math.sin(angle),
            z: distance * Math.cos(angle)
          });
          angle += Math.PI / 1000;
        }
      }, 10);
      return () => clearInterval(interval);
    }
  }, []);

  // Función para dibujar un sprite estilo fantasma
  const createGhostSprite = useCallback((node, isActive) => {
    const canvas = document.createElement('canvas');
    canvas.width = 128;
    canvas.height = 128;
    const ctx = canvas.getContext('2d');
    
    ctx.fillStyle = isActive ? '#FFFFFF' : node.color;
    
    // Cuerpo del fantasma pixelado (estilo Space Invaders/Pacman)
    const px = 8; // tamaño del pixel
    const offsetX = 32;
    const offsetY = 32;
    
    // Matriz simplificada de fantasma 8x8
    const ghostPixels = [
      "  xxxx  ",
      " xxxxxx ",
      "xxoxxoxx",
      "xxxxxxxx",
      "xxxxxxxx",
      "xx xx xx",
      "x  xx  x"
    ];
    
    ghostPixels.forEach((row, y) => {
      for (let x = 0; x < row.length; x++) {
        if (row[x] === 'x') {
          ctx.fillRect(offsetX + x*px, offsetY + y*px, px, px);
        } else if (row[x] === 'o') {
          ctx.fillStyle = '#000'; // Ojos negros
          ctx.fillRect(offsetX + x*px, offsetY + y*px, px, px);
          ctx.fillStyle = isActive ? '#FFFFFF' : node.color;
        }
      }
    });
    
    // Texto del nombre debajo
    ctx.fillStyle = isActive ? '#0ff' : '#FFF';
    ctx.font = 'bold 12px monospace';
    ctx.textAlign = 'center';
    ctx.fillText(node.name, 64, 110);

    const texture = new THREE.CanvasTexture(canvas);
    const material = new THREE.SpriteMaterial({ map: texture, transparent: true });
    const sprite = new THREE.Sprite(material);
    
    const size = isActive ? node.val * 1.5 : node.val;
    sprite.scale.set(size, size, 1);
    
    return sprite;
  }, []);

  return (
    <div style={{ position: 'relative', width: '100vw', height: '100vh', background: '#0a0a0f' }}>
      <div style={{ position: 'absolute', top: 20, left: 20, zIndex: 10, color: '#0ff', fontFamily: 'monospace' }}>
        <h2>GROK BOT / OBSIDIAN</h2>
        <p>Estado: {logs.length > 0 ? 'Sincronizando' : 'Esperando datos...'}</p>
      </div>

      {/* Terminal flotante */}
      <div style={{ 
        position: 'absolute', bottom: 20, left: 20, width: '400px',
        height: '200px', background: 'rgba(0,0,0,0.8)', border: '1px solid #333', 
        zIndex: 10, color: '#0f0', fontFamily: 'monospace', padding: '15px',
        overflowY: 'auto', borderRadius: '5px', boxShadow: '0 0 10px rgba(0,255,0,0.2)'
      }}>
        <h4 style={{ margin: '0 0 10px 0', color: '#888', borderBottom: '1px solid #333', paddingBottom: '5px' }}>&gt;_ SWARM_TERMINAL</h4>
        {logs.map((log, i) => (
          <div key={i} style={{ marginBottom: '6px', fontSize: '12px' }}>{log}</div>
        ))}
        {logs.length === 0 && <div style={{ color: '#555', fontStyle: 'italic' }}>Esperando ejecución del orquestador...</div>}
      </div>

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
            // Anclar Master al centro absoluto (0,0,0)
            const masterNode = graphData.nodes.find(n => n.id === 'Master');
            if (masterNode) {
              masterNode.fx = 0;
              masterNode.fy = 0;
              masterNode.fz = 0;
            }
          }
        }}
      />
    </div>
  );
};

export default SwarmGraph;
