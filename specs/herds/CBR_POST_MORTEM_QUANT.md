# 🧠 CBR POST-MORTEM QUANT: APRENDIZAJE CBR, SCORE DE PREMIO Y CASTIGO (RL ENGINE)

## 1. MISIÓN Y RESPONSABILIDAD TÉCNICA
El CBR POST-MORTEM QUANT es el órgano cognitivo de autopsia y aprendizaje continuo de MIA Core.
Alineado con la Rama 1 de `GEMINI.md`, es gobernado por el **Agente Post-Mortem y Supervisor Quant** (motor Google Gemini 1.5 Pro).
Su misión exclusiva es analizar a profundidad los trades cerrados en MetaTrader 5, calcular la recompensa o penalización matemática (Score de Premio y Castigo), asignar crédito a los Herds que acertaron y penalizar a los que fallaron, archivando el caso normalizado para gobernar decisiones futuras en situaciones similares.

---

## 2. ESTRUCTURA CANÓNICA DEL CASO CBR LIGADO AL TICKET
Cada evento de trade cerrado genera un ticket de caso inmutable con nomenclatura:

$$\text{ID:} \quad \mathbf{TRADE\_CASE\_<ticket\_mt5>\_<timestamp>}$$

### Campos Estructurales Obligatorios:
```json
{
  "case_id": "TRADE_CASE_112472341_1761358900",
  "ticket_mt5": "112472341",
  "activo": "GBPUSD",
  "tipo_orden": "BUY",
  "volumen_lotes": 0.50,
  "pnl_usd": 145.20,
  "r_multiplo": 2.10,
  "mfe_max_favorable_r": 2.40,
  "mae_max_adverse_r": -0.35,
  "motivo_cierre": "CERRAR_TP_FASE_3",
  "timestamp_apertura": "2026-10-24T14:15:00Z",
  "timestamp_cierre": "2026-10-24T15:02:00Z",
  "contexto_mercado_entrada": {
    "sesion": "LONDRES_OVERLAP_NY",
    "regimen": "EXPANSION_POST_SWEEP",
    "sweep_macro_tf": "4H",
    "setup": "LUX_ALGO_OB_2H + RSI_EXTREMO + CVD_DELTA_POSITIVO",
    "cvol_energia": 1.82,
    "votos_iniciales_herds": {
      "tidal": "APROBADO",
      "noro": "APROBADO",
      "zephr": "APROBADO",
      "lumen": "APROBADO",
      "rune": "APROBADO",
      "tensorflow": "APROBADO",
      "atlas": "APROBADO"
    }
  },
  "score_premio_castigo": {
    "recompensa_neta_r": 2.58,
    "delta_weights_herds": {
      "herd_1_tidal": 0.05,
      "herd_2_noro": 0.08,
      "herd_3_zephr": 0.06,
      "herd_4_lumen": 0.15,
      "herd_5_rune": 0.10,
      "herd_6_tensorflow": 0.05,
      "herd_7_atlas": 0.12
    }
  },
  "diagnostico_gemini_pro": "Autopsia validada...",
  "solucion_aprendida": "En setups similares...",
  "veredicto_humano": "PENDIENTE_HITL"
}
```

---

## 3. FÓRMULA MATEMÁTICA DE PREMIO Y CASTIGO (REINFORCEMENT LEARNING)
El Score de Recompensa Neta ($R_{trade}$) se calcula con asimetría cuantitativa:

$$R_{trade} = \begin{cases} 
+1.0 \times \left(\frac{\text{PnL Real}}{\text{Riesgo Inicial}}\right) + 0.20 \times \left(\frac{\text{MFE}}{\text{Riesgo}}\right) & \text{si es GANADOR (Win)} \\
-1.5 \times \left(\frac{|\text{PnL Real}|}{\text{Riesgo Inicial}}\right) \times \left(1 + \frac{d}{1 - d}\right) & \text{si es PERDEDOR (Loss)} \\
+0.15 \times \text{Buffer Spread} & \text{si es BREAK-EVEN (BE)}
\end{cases}$$

### Asignación de Crédito por Herd ($\Delta W_i$):
- **Premio a la Confluencia Válida ($\text{Win}$):**
  $$\Delta W_i = +\eta \cdot R_{trade} \cdot V_i \quad (\text{con } \eta = 0.05)$$
  Los Herds que impulsaron la tesis ganadora (ej. LUMEN por Sweep AMD o ATLAS por CVD) reciben mayor peso en la memoria viva para ese par y régimen.
- **Castigo a la Trampa de Mercado ($\text{Loss}$):**
  $$\Delta W_i = -\eta \cdot |R_{trade}| \cdot V_i$$
  Los Herds que votaron "APROBADO" ignorando el peligro son penalizados en su factor de confianza, y se premia a los Herds que intentaron vetar.

---

## 4. CONSULTA Y REUTILIZACIÓN EN TIEMPO REAL (k-NN SIMILITUDE)
Antes de que los 7 Herds emitan su voto en un nuevo ciclo, el Master consulta `cache_trading_learning_kb`:
1. Compara el vector de setup actual contra los 50 casos históricos más recientes.
2. Si la distancia euclidiana / similitud coseno es $> 85\%$ con un caso **perdedor**:
   - Se inyecta una advertencia de veto directo al debate.
3. Si la similitud es $> 85\%$ con un caso **ganador probado**:
   - Se inyecta un multiplicador de confianza institucional que autoriza la entrada con ejecución rápida.
