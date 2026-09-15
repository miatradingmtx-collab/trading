import urllib.request
import json

url = "https://trading-production-927a.up.railway.app/api/dashboard_data"
req = urllib.request.Request(url)
req.add_header('User-Agent', 'Mozilla/5.0')

try:
    with urllib.request.urlopen(req, timeout=15) as response:
        data = json.loads(response.read())
        
    dashboard = data.get("data", {})
    logs = dashboard.get("recent_logs", [])
    
    tickets = {}
    
    for l in logs:
        ticket = str(l.get("ticket", ""))
        if not ticket or ticket.startswith("EVAL_"): continue
        
        fecha = l.get("fecha", "")
        # Filtrar domingo (6), lunes (7), martes (8)
        if "2026-09-06" in fecha or "2026-09-07" in fecha or "2026-09-08" in fecha:
            acc = l.get("accion", "")
            pnl = float(l.get("pnl", 0.0))
            
            if acc in ["CIERRE_TOTAL", "CIERRE_PARCIAL", "CIERRE_PARCIAL_80", "PROTECCION_BE", "TRAILING_STOP"]:
                if ticket not in tickets:
                    tickets[ticket] = {
                        "pnl": 0.0, 
                        "activo": l.get("activo"), 
                        "fecha": fecha, 
                        "estrategia": l.get("detalle_setup", l.get("estrategia", "Desconocida")),
                        "sesion": l.get("sesion_killzone", "N/A"),
                        "parciales": 0,
                        "trailing": False
                    }
                tickets[ticket]["pnl"] += pnl
                if acc == "CIERRE_TOTAL":
                    tickets[ticket]["fecha"] = fecha
                if acc in ["CIERRE_PARCIAL", "CIERRE_PARCIAL_80"]:
                    tickets[ticket]["parciales"] += 1
                if acc == "TRAILING_STOP":
                    tickets[ticket]["trailing"] = True

    ganadoras = []
    perdedoras = []
    regla_3 = []
    total_pnl = 0.0

    for t, info in tickets.items():
        total_pnl += info["pnl"]
        
        hit_regla = info["parciales"] >= 2 or info["trailing"]
        if hit_regla:
            regla_3.append(info)
            
        if info["pnl"] > 0:
            ganadoras.append((t, info))
        elif info["pnl"] < 0:
            perdedoras.append((t, info))

    ganadoras.sort(key=lambda x: x[1]["pnl"], reverse=True)
    perdedoras.sort(key=lambda x: x[1]["pnl"])
    
    with open('reporte_post_fix_api.txt', 'w', encoding='utf-8') as f:
        f.write(f"PNL NETO DESDE EL DOMINGO: ${total_pnl:.2f}\\n")
        f.write(f"Total Operaciones Cerradas: {len(tickets)}\\n")
        f.write(f"Ganadoras: {len(ganadoras)} | Perdedoras: {len(perdedoras)}\\n\\n")
        
        f.write("--- REGLA DE 3 CUMPLIDA (Escalamiento Perfecto) ---\\n")
        if not regla_3:
            f.write("Aun no hay operaciones que hayan tocado 2 TPs consecutivos esta semana.\\n")
        for r in regla_3:
            f.write(f"Activo: {r['activo']} | PnL: ${r['pnl']:.2f} | Estrategia: {r['estrategia']}\\n")
            
        f.write("\\n--- RANKING POSITIVAS (Top 5) ---\\n")
        for t, info in ganadoras[:5]:
            f.write(f"{info['activo']} | ${info['pnl']:.2f} | Sesion: {info['sesion']} | Estrategia: {info['estrategia']}\\n")
            
        f.write("\\n--- RANKING NEGATIVAS (Top 5) ---\\n")
        for t, info in perdedoras[:5]:
            f.write(f"{info['activo']} | ${info['pnl']:.2f} | Sesion: {info['sesion']} | Estrategia: {info['estrategia']}\\n")
            
        f.write("\\n--- KPIS MACHINE LEARNING ---\\n")
        kpis = dashboard.get("kpis", {})
        f.write(f"Win Rate Global: {kpis.get('win_rate')}%\n")
        f.write(f"Patron Estrella: {kpis.get('patron_estrella')} (WR: {kpis.get('patron_estrella_wr')}%)\n")
        
    print("Reporte generado con exito.")

except Exception as e:
    print(f"Error fetching API: {e}")
