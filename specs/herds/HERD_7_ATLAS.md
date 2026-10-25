# 🛰️ HERD 7 (ATLAS): MICROESTRUCTURA DOM CME, CVD DELTA & SERVIDOR MCP

## 1. MISIÓN Y RESPONSABILIDAD TÉCNICA
HERD 7 (ATLAS) es el sensor de microestructura de alta frecuencia y flujo de órdenes de MIA Core.
Su misión es auditar el libro de órdenes profundo (Depth of Market - DOM L2/L3), monitorear el Cumulative Volume Delta (CVD Delta) en contratos de futuros de Chicago Mercantile Exchange (CME) y OANDA, y detectar trampas de liquidez tóxica (*Resting Liquidity Traps*) mediante su servidor MCP dedicado.

---

## 2. ARQUITECTURA DE DATOS DOM CME VS SPOT
ATLAS mapea los pares oficiales de Forex y Commodities contra sus contratos de futuros CME Tape+:
- `EURUSD` $\longleftrightarrow$ Contrato CME Euro FX (`6E`).
- `GBPUSD` $\longleftrightarrow$ Contrato CME British Pound (`6B`).
- `GBPJPY` $\longleftrightarrow$ Contrato CME Japanese Yen (`6J`) sintetizado con Libra.
- `AUDUSD` $\longleftrightarrow$ Contrato CME Australian Dollar (`6A`).
- `XAUUSD` $\longleftrightarrow$ Contrato CME Gold Futures (`GC`).
- `NZDCAD` $\longleftrightarrow$ Contratos CME Kiwi (`6N`) y Canadian Dollar (`6C`) [Sandbox].

---

## 3. CUMULATIVE VOLUME DELTA (CVD DELTA) Y ABSORCIONES
1. **Presión Agresiva vs Pasiva:**
   $$\text{Delta} = \text{Volumen Ejecutado en Ask (Compradores Agresivos)} - \text{Volumen Ejecutado en Bid (Vendedores Agresivos)}$$
2. **Absorción Institucional Pasiva:**
   - Si el precio intenta romper un nivel de resistencia pero el CVD Delta sube fuertemente sin que el precio avance, ATLAS detecta **Absorción de Ventas Pasivas** (órdenes límite institucionales conteniendo el precio).
   - Esta divergencia indica un giro bajista inminente y veta cualquier compra retail de ruptura.

---

## 4. MAPA DE CALOR DE TRAMPAS DE LIQUIDEZ (HEATMAP)
ATLAS escanea los pools de órdenes descansando (*Resting Liquidity*):
- **Buy Stops Resting (Zona Trampa Alcista):** Grandes acumulaciones de compras retail por encima de máximos recientes. Si el mercado sube solo a tocarlas y el delta no expande, se clasifica como *Caza de Liquidez*.
- **Sell Stops Resting (Zona Trampa Bajista):** Grandes acumulaciones de ventas retail por debajo de mínimos recientes.

---

## 5. CONDICIONES DE VETO Y APROBACIÓN
- **VETO ABSOLUTO (⛔):**
  - El trade propuesto compra directamente contra una barrera de absorción institucional pasiva masiva en el DOM de CME.
  - El CVD Delta diverge negativamente con la acción del precio (ej. precio subiendo con delta cayendo en picada).
  - Detección de trampa de liquidez tóxica en el libro de órdenes.
- **APROBADO (✅):**
  - Desequilibrio del DOM institucional a favor de la dirección del trade ($> 60\%$ a favor) + CVD Delta confirmando la presión agresiva sin absorciones hostiles.
