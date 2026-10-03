# Complemento

`reto1_enhanced.py` parte del control de nivel del programa principal. La altura la mide un HC-SR04 y la bomba se muestra en una matriz 8×8, en lugar del LED azul. El nivel deseado sigue en un potenciómetro. Este archivo no es el que se recorre en la exposición. Aquí la alarma se mira antes que el pulsador: si el nivel supera 190 cm, el LED rojo enciende aunque el sistema esté detenido.

Se corre igual que el principal: en Thonny, con MicroPython en la ESP32, guardado en la placa como `main.py` o con Run. Las lecturas salen en el shell.

El ultrasonido apunta al agua de una maqueta. Una distancia de 2 cm se toma como tanque lleno (200 cm) y una de 20 cm como tanque vacío (0 cm). La matriz enciende un cuadro fijo si la bomba está detenida y gira más rápido cuanto mayor es el porcentaje.

## Conexiones

| Señal | Dirección | GPIO | Función |
| --- | --- | --- | --- |
| HC-SR04 TRIG | Salida | 13 | Disparo del ultrasonido |
| HC-SR04 ECHO | Entrada | 12 | Eco. El tiempo de ida y vuelta pasa a centímetros |
| Nivel deseado SP | Entrada | 35 | ADC1, de 50 a 180 cm. Atenuación 11 dB |
| Pulsador | Entrada | 16 | Habilita o detiene. Pull-up, activo en bajo, antirrebote de 200 ms |
| LED verde | Salida | 4 | Sistema habilitado |
| LED rojo | Salida | 2 | Alarma de nivel alto |
| Nivel DAC | Salida | 25 | El nivel como cuenta de 0 a 255 |
| Bomba | Salida | 17 | PWM a 5 kHz. Ciclo útil con `duty_u16`, de 0 a 65535 |
| Matriz DIN | Salida | 23 | MOSI del SPI 1, hacia el MAX7219 |
| Matriz CLK | Salida | 18 | SCK del SPI 1 |
| Matriz CS | Salida | 5 | Chip select del MAX7219 |

El pulsador pasa a GPIO 16 porque GPIO 18 queda como reloj de la matriz. GND es común a todos los componentes. El potenciómetro de SP va entre 3V3 y GND.
