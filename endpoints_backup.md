# Respaldo de Endpoints y Webhooks (Mia AI)

Este documento sirve como respaldo oficial de las rutas de conexión de Mia. En caso de que el servidor principal de Railway sufra una caída o se migre de cuenta, estos son los webhooks que debes actualizar en **TradingView** y **N8N**.

## 🌐 URL Principal (Master Endpoint)
**URL Actual:** `https://trading-production-927a.up.railway.app`

*(Si cambias de servidor, solo reemplaza esta URL base por la nueva).*

---

## 🔗 Webhooks de Alertas (TradingView)
Estas son las URLs que debes pegar en la caja de "URL del Webhook" al crear una alerta en TradingView.

### 1. Señales Técnicas (Estrategia Principal)
- **URL:** `https://trading-production-927a.up.railway.app/webhook_technical_update`
- **Uso:** Recibe las señales en formato JSON (Asset, Timeframe, Action, Price) desde los indicadores técnicos de PineScript.

### 2. Actualizaciones Fundamentales (N8N / Noticias)
- **URL:** `https://trading-production-927a.up.railway.app/webhook_fundamental_update`
- **Uso:** N8N o cualquier script de recolección de noticias envía un POST aquí con el nivel de volatilidad (High/Medium/Low) e impacto direccional.

---

## 📊 Endpoints de Interfaz y Análisis
Rutas para acceder al panel de control y descargar datos.

- **Dashboard Visual:**
  `https://trading-production-927a.up.railway.app/dashboard`
  *(Abre esto en tu navegador de PC o celular para ver el estado de Mia).*

- **Exportar Base de Datos (CSV):**
  `https://trading-production-927a.up.railway.app/api/export_audit_csv`
  *(Descarga el historial completo de los trades procesados).*

---

## ⚙️ Webhooks Internos (MetaTrader 5 -> Mia)
*(Estos no necesitas cambiarlos manualmente ya que el script de MT5 en la nube los lee de las variables de entorno, pero se documentan por seguridad).*

- **Confirmación de Ejecución:** `/webhook_marcar_ejecutado`
- **Reporte de Errores (Logs):** `/registrar_error_sistema`
- **Petición de Datos (Dashboard):** `/api/dashboard_data`
- **Petición de Gráficos (Velas):** `/api/chart_data/{symbol}`
