# Reto 1 — Control de nivel de un tanque

Microcontroladores 2026-2 · Universidad Nacional de Colombia  
Ingeniería de Sistemas y Computación  
Nicolás Muñoz · Fredy Garcia

Una ESP32 con MicroPython mantiene el nivel de un tanque. Compara la altura medida con el nivel deseado y, según la diferencia, cambia la velocidad de una bomba. El programa de la exposición es el principal. El complemento cambia el sensor de nivel y la forma de mostrar la bomba; no es el montaje que se explica en detalle.

| Carpeta | Qué es |
| --- | --- |
| [principal](principal/README.md) | `reto1.py`. Potenciómetros, pulsador, LED y PWM. Incluye esquemático y diagramas. |
| [complemento](complemento/README.md) | `reto1_enhanced.py`. Nivel con HC-SR04 y bomba en una matriz 8×8. Solo el código y las conexiones. |

Los dos se ejecutan en Thonny, con el firmware de MicroPython en la ESP32. El archivo se copia a la placa como `main.py`, o se corre con Run. Lo que el programa imprime aparece en el shell de Thonny.
