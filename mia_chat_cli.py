#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
MIA CORE - CONSOLA DE DIÁLOGO INTERACTIVO CON MIA (SUPERVISOR CHAT)
================================================================================
Permite conversar directamente con Mia usando OpenRouter y telemetría viva de Upstash.
Activación: "Hola Mia" -> Mia responde: "Hola Padre".
"""

import sys
import os
import io

# Asegurar codificación UTF-8 universal en terminales
if sys.stdout and hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
if sys.stderr and hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace", line_buffering=True)

# Colores ANSI
C_RESET   = "\033[0m"
C_BOLD    = "\033[1m"
C_DIM     = "\033[2m"
C_CYAN    = "\033[96m"
C_YELLOW  = "\033[93m"
C_GREEN   = "\033[92m"
C_RED     = "\033[91m"
C_MAGENTA = "\033[95m"
C_WHITE   = "\033[97m"

if os.name == "nt":
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        pass

def main():
    os.system("cls" if os.name == "nt" else "clear")
    print(f"{C_BOLD}{C_MAGENTA}╔══════════════════════════════════════════════════════════════════════════╗{C_RESET}")
    print(f"{C_BOLD}{C_MAGENTA}║           MIA CORE - TERMINAL DE CONVERSACIÓN CON EL SUPERVISOR          ║{C_RESET}")
    print(f"{C_BOLD}{C_MAGENTA}║       Motor: OpenRouter (Claude 3.5 / DeepSeek V3 / Llama 3.3 70B)       ║{C_RESET}")
    print(f"{C_BOLD}{C_MAGENTA}║       Inicia saludando con: 'Hola Mia'                                   ║{C_RESET}")
    print(f"{C_BOLD}{C_MAGENTA}║       Escribe 'salir' para finalizar la sesión                           ║{C_RESET}")
    print(f"{C_BOLD}{C_MAGENTA}╚══════════════════════════════════════════════════════════════════════════╝{C_RESET}\n")

    from mia_supervisor_chat import chat_with_mia

    history = []
    
    while True:
        try:
            user_input = input(f"{C_BOLD}{C_CYAN}Tú: {C_RESET}").strip()
            if not user_input:
                continue
            if user_input.lower() in ["salir", "exit", "quit"]:
                print(f"\n{C_YELLOW}Cerrando sesión de diálogo con Mia. ¡Hasta pronto!{C_RESET}")
                break

            print(f"{C_DIM}Mia pensando (consultando OpenRouter & Upstash)...{C_RESET}", end="\r")
            reply = chat_with_mia(user_input, history)
            print(" " * 60, end="\r")  # Limpiar indicador de pensamiento

            print(f"{C_BOLD}{C_MAGENTA}Mia:{C_RESET} {reply}\n")

            history.append({"role": "user", "content": user_input})
            history.append({"role": "assistant", "content": reply})

        except KeyboardInterrupt:
            print(f"\n\n{C_YELLOW}Sesión interrumpida. ¡Hasta luego Padre!{C_RESET}")
            break
        except Exception as e:
            print(f"{C_RED}Error: {e}{C_RESET}\n")

if __name__ == "__main__":
    main()
