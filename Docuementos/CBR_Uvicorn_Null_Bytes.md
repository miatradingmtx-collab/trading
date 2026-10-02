# CBR Entry: Uvicorn Null Byte Crash
## Error Signature
```python
File "<frozen importlib._bootstrap_external>", line 947, in source_to_code
ValueError: source code string cannot contain null bytes
```

## Diagnóstico
Este error ocurre cuando un archivo de código fuente de Python (ej. `app.py`) se corrompe al insertarse bytes nulos (`\x00`). Esto es común cuando se usan scripts de reemplazo de texto (`regex`, `codecs`) en entornos cruzados (Windows PowerShell a Linux) sin sanear el formato binario.
Como resultado, el servidor Uvicorn / FastAPI entra en un ciclo de "Crash Loop" fatal, pero los monitores de estado HTTP o Docker podrían marcarlo como "Online" falsamente si solo hacen ping al contenedor.

## Falso Positivo del Watchdog
El Watchdog AI falló en su reporte inicial ("Cero cambios críticos pendientes") porque estaba midiendo la disponibilidad de la memoria y la CPU del contenedor (que estaban bien), pero no estaba haciendo una lectura en vivo del `stderr` (Standard Error) de Uvicorn en el puerto 8000. 

## Solución Inmediata (Playbook de Mitigación)
Cuando el Enjambre o el Watchdog detecte este error en los logs de Railway, debe ejecutar inmediatamente el siguiente script de saneamiento binario sobre el archivo corrupto:

```python
# Script de Reparación CBR para Watchdog
import os
archivo_corrupto = 'app.py'

with open(archivo_corrupto, 'rb') as f:
    content = f.read()

if b'\x00' in content:
    content = content.replace(b'\x00', b'')
    with open(archivo_corrupto, 'wb') as f:
        f.write(content)
    print(f"Saneamiento exitoso: Bytes nulos removidos de {archivo_corrupto}.")
```

## Homologación (Mirroring)
Todos los agentes (T1-T10, Watchdog, y Slack Bot) deben incorporar esta firma en sus matrices de riesgo. Si Uvicorn no levanta, el primer paso es escanear por `\x00` antes de asumir fallas lógicas o de dependencias.
