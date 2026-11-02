# 🧭 TAXONOMÍA CANÓNICA DE CHATS Y ESPECIALIZACIÓN DE PROMPTS
## Ecosistema Mia Trading Core: Estructura de Conversaciones en Antigravity & IDE

Para evitar sobrecarga de contexto, contaminación de tokens (*Lost in the Middle*) y mezclas entre tareas de diseño visual, algoritmos de trading, infraestructura y despliegues, el ecosistema de Mia se divide en **7 Canales de Chat Especializados**.

---

## 🏛️ MAPA GENERAL DE LOS 7 CHATS ESPECIALIZADOS

| Chat # | Conversation ID | Nombre Oficial del Chat | Dominio / Alcance | Rama Git | Microservicio / Canal |
| :---: | :--- | :--- | :--- | :---: | :--- |
| **01** | `30cc37f2` | `01 - Supervisor Quant & Agente Post-Mortem (Cognición CBR & Slack Insights)` | Autopsias forenses de trades MT5, cálculo de premio/castigo, memoria CBR y Bóveda Obsidian. | `develop` | `0b51` / `#mia-trading-insights` |
| **02** | `2bd45cda` | `02 - Arquitectura Backend & Microservicios` | Lógica de `app.py`, `mt5_executor_cloud.py`, algoritmos SMC, Cascada RUNE y endpoints API. | `develop` | `927a` / Core API |
| **03** | `b456972a` | `03 - UI/UX Dashboard, Brain 3D, Mods & Mobile Responsive (Stitch/Figma/Flutter)` | Terminal Antopus 3D (`/`), Red Neuronal 3D (`/brain`), Módulos (`/mods`), flujo Bézier y Flutter. | `develop` | `1fd4` / WebSocket |
| **04** | `ba9096c1` | `04 - Producción Main Railway & Despliegues` | Releases estables, auditoría de capital real, aprobación HITL y sincronización de producción. | `main` | Railway Producción |
| **05** | `0abdbfa6` | `05 - Desarrollador Develop & Servidor MCP MT5` | Pruebas de integración, micro-lotes en demo, nuevo servidor `mia_server_mcp_mt5.py`. | `develop` | `a0b8` / MCP MT5 |
| **06** | `29c6e21a` | `06 - Infraestructura SRE & Watchdog Herds T1-T10` | Salud del cluster, latencias MGET sub-35ms, Upstash Redis, Docker y ChatOps Slack. | `develop` | `0b51` / `#back-office-y-backend` |
| **07** | `12664818` | `07 - Consultas Generales, Estrategia & Roadmap (Inalterable)` | Hub de consultas de mejoras, diseño cuantitativo, benchmarking y hojas de ruta. | `develop` | Control Plane / Hub |

---

## 📋 DETALLE, ALCANCE Y PROMPT INICIAL POR CHAT

### Chat 1: 🏛️ `01 - Supervisor Quant & Agente Post-Mortem (Cognición CBR & Slack Insights)`
* **Misión:** Dupla Cognitiva de la Rama 1: Autopsias forenses de cada trade cerrado en MT5 con Google Gemini 1.5 Pro, asignación de premio/castigo (+R / -R), enriquecimiento continuo de la memoria CBR (`system_memory/latest_cbr` y `cache_trading_learning_kb`), despacho interactivo a `#mia-trading-insights` y sincronización perpetua con la Bóveda de Obsidian.
* **Archivos Clave:** `specs/herds/*.md`, `specs/herds/CBR_POST_MORTEM_QUANT.md`, `mia_post_mortem_agent.py`, `mia_supervisor_quant.py`, `D:\obsidiana\Proyectos\Mia_Trading\`.
* **Prompt de Arranque (Copiar y Pegar al iniciar):**
  > *"Actúa como la Dupla Cognitiva de la Rama 1 de Mia Trading Core: el Agente Post-Mortem y el Supervisor Quant. Tu canal oficial es #mia-trading-insights (C0C6DUTQVEZ). Tu alcance exclusivo son las autopsias forenses de trades cerrados en MT5, cálculo de premio/castigo, memoria CBR post-mortem (system_memory/latest_cbr) y la sincronización con la Bóveda de Obsidian. Cero modificaciones de interfaz gráfica o servidores backend directos."*

---

### Chat 2: 💻 `[TRADING] Arquitectura de Código & Backend Core`
* **Misión:** Optimizar el rendimiento de la API en Python, lógica de ejecución en `mt5_executor_cloud.py`, Cascada RUNE de 4 fases, dimensionamiento de lotaje por riesgo en dólares y comunicación interna con FastAPI/Uvicorn.
* **Archivos Clave:** `app.py`, `mt5_executor_cloud.py`, `mia_master_swarm_rest.py`, `requirements.txt`.
* **Prompt de Arranque:**
  > *"Actúa como el Senior Backend Engineer de Mia Trading Core. Tu alcance es la arquitectura de código en Python, algoritmos de trading institucional (SMC/ICT), Cascada RUNE, optimización de endpoints FastAPI y cálculo determinista de riesgo. Mantén documentación estricta y código de alta velocidad."*

---

### Chat 3: 🎨 `[TRADING] UI/UX Dashboard, Brain 3D, Enjambres & Mods`
* **Misión:** Diseño y mejoras de la experiencia visual en el microservicio `1fd4`. Visualización tridimensional en Three.js / Canvas, terminal Antopus 3D, topología de 4 capas de red neuronal (`/brain`), catálogo de extensiones (`/mods`), KPIs y diseño responsive para Android y iOS.
* **Archivos Clave:** `templates/*.html`, `static/js/*.js`, `static/css/*.css`, `mia_websocket_server.py`.
* **Prompt de Arranque:**
  > *"Actúa como el Lead Frontend & 3D WebGL Designer de Mia. Tu alcance exclusivo son las interfaces de usuario del microservicio 1fd4: Terminal Antopus 3D (`/`), Visualizador Neuronal 3D (`/brain`), Módulos (`/mods`), gráficos de telemetría y adaptabilidad responsive para dispositivos móviles. Cero cambios en las fórmulas de trading o bases de datos."*

---

### Chat 4: 🚀 `[TRADING] Producción (Rama MAIN) & Despliegues Railway`
* **Misión:** Control estricto de despliegues a los microservicios en vivo de Railway. Verificación de commits antes de merge, validación de variables de entorno de producción, auditoría de drawdown vs capital base $5,000 USD y mandatos de Human-in-the-Loop (HITL).
* **Rama:** `main` (Despliegue automático a Railway Producción).
* **Prompt de Arranque:**
  > *"Actúa como el Release Manager y Custodio de Producción de Mia. Tu alcance es verificar la estabilidad de la rama `main`, auditar los merges procedentes de `develop`, supervisar los despliegues en Railway y velar por el cumplimiento del mandato HITL y la preservación del capital real."*

---

### Chat 5: 🧪 `[TRADING] Desarrollo (Rama DEVELOP), Staging & MCP MT5`
* **Misión:** Pruebas de nueva tecnología, calibración del servidor MCP nativo `mia_server_mcp_mt5.py` en el endpoint `a0b8`, ejecución de órdenes simuladas con micro-lotes en la cuenta demo oficial `112472341`, y validación antes de merge a `main`.
* **Rama:** `develop` (Despliegue automático al microservicio de pruebas `trading-production-a0b8`).
* **Prompt de Arranque:**
  > *"Actúa como el Ingeniero de Staging y Pruebas de Integración de Mia. Tu entorno de trabajo es la rama `develop` y el nuevo servidor MCP MT5 (`mia_server_mcp_mt5.py`). Tu objetivo es validar herramientas MCP, ejecutar pruebas de micro-lote en la cuenta demo 112472341 y preparar los paquetes listos para producción."*

---

### Chat 6: 🛠️ `[TRADING] Infraestructura Back-Office, SRE & Herds T1-T10`
* **Misión:** Monitoreo y estabilidad de la Tríada de Microservicios Railway, latencias de caché en Upstash Redis (MGET sub-35ms), Firebase pasivo, presupuesto Cloud (FinOps) y el canal de ChatOps Slack `#back-office-y-backend`.
* **Archivos Clave:** `mia_ops_service.py`, `mia_ops_mcp_server.py`, `mia_system_ops_swarm.py`, `mia_slack_bridge.py`.
* **Prompt de Arranque:**
  > *"Actúa como el Supervisor Watchdog y Líder SRE de los Herds T1 al T10. Tu alcance es la infraestructura técnica, latencia de base de datos, Docker, Uvicorn, presupuestos de nube y ChatOps en Slack. Tienes prohibida cualquier intervención en estrategias de mercado o pares de divisas."*

---

### Chat 7: 💡 `07 - Consultas Generales, Estrategia & Roadmap (Inalterable)`
* **Misión:** Hub permanente e inalterable de consultoría estratégica, análisis cuantitativo, benchmarking y diseño de mejoras. Nunca cambia de identidad. Cuando en este chat se aprueba una mejora para UI/UX, SRE o Backend, la solución se inyecta formalmente en el `.md` del prompt correspondiente declarando su Número, Nombre y Conversation ID.
* **Archivos Clave:** `.prompts/*.md`, `DOCS_TRADING_CORE.md`, `DOCS_OPS_CORE.md`.
* **Prompt de Arranque:**
  > *"Actúa como el Consultor Estratégico Cuantitativo y Hub de Consultas Generales de Mia. Tu identidad es inalterable. Analizaremos ideas conceptuales, hojas de ruta hacia el Modo Autónomo (Trust Mode), confirmaciones de la Regla de 3 (>= 50 trades) y mejoras sistémicas. Toda mejora diseñada aquí se inyectará en el prompt del chat correspondiente."*

---

## 🔄 PROTOCOLO DE TRABAJO DIARIO RECOMENDADO

1. **Para ideas o dudas:** Iniciar en **Chat 7 (Consultas)**.
2. **Para redactar reglas o memorias:** Trabajar en **Chat 1 (Cognición & .MD)**.
3. **Para programar código o probar MT5 MCP:** Trabajar en **Chat 5 (Develop & Staging)**.
4. **Para ajustar el visualizador 3D o terminal:** Trabajar en **Chat 3 (UI/UX & Brain)**.
5. **Para aplicar cambios en servidores de producción:** Pasar a **Chat 4 (Producción Main)** para merge y despliegue final.
