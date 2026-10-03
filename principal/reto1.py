from machine import Pin, ADC, DAC, PWM
import time

# Asignación de pines y configuración de periféricos
# ADC1 Potenciómetro Nivel L -> GPIO 34 
adc_L = ADC(Pin(34)) 
adc_L.atten(ADC.ATTN_11DB)  # Rango de entrada de 0 a 3.3V (0 a 4095)

# ADC2 Potenciómetro Setpoint SP -> GPIO 35 
adc_SP = ADC(Pin(35))
adc_SP.atten(ADC.ATTN_11DB) # Rango de entrada de 0 a 3.3V (0 a 4095)

# GPIO IN Pulsador Habilitar/Deshabilitar -> GPIO 18
btn = Pin(18, Pin.IN, Pin.PULL_UP)

# GPIO OUT Indicadores LED de Estado
led_r = Pin(2, Pin.OUT)   # LED Rojo -> GPIO 2 (Alarma de nivel alto)
led_v = Pin(4, Pin.OUT)   # LED Verde -> GPIO 4 (Sistema habilitado)

# DAC Salida Analógica que representa el Nivel L -> GPIO 25 
dac = DAC(Pin(25))

# PWM Actuador de Bomba Simulado (LED Azul) -> GPIO 17
pwm_bomba = PWM(Pin(17), freq=5000)

# Variables de control
sistema_habilitado = False
estado_btn_anterior = 1
ultimo_debounce_time = 0
debounce_delay = 200  # Tiempo antirrebote en milisegundos

# Bucle principal
while True:
    tiempo_actual = time.ticks_ms()
    lectura_btn = btn.value()

    # Detección de flanco de bajada del pulsador con antirrebote (Debounce)
    if lectura_btn == 0 and estado_btn_anterior == 1:
        if time.ticks_diff(tiempo_actual, ultimo_debounce_time) > debounce_delay:
            sistema_habilitado = not sistema_habilitado
            ultimo_debounce_time = tiempo_actual
    estado_btn_anterior = lectura_btn

    # Lectura de las entradas analógicas (ADC)
    raw_L = adc_L.read()
    raw_SP = adc_SP.read()

    # Escalamiento a variables de ingeniería según requerimientos
    L = (raw_L / 4095.0) * 200.0          # Escalado: 0 a 200 cm
    SP = 50.0 + (raw_SP / 4095.0) * 130.0 # Escalado: 50 a 180 cm

    # Conversión y salida DAC (8 bits: 0 a 255) ... 0 cm -> 0, 200 cm -> 255
    valor_dac = int((L / 200.0) * 255)
    valor_dac = max(0, min(255, valor_dac))  # Para evitar salirse del rango de 0 a 255
    dac.write(valor_dac)

    # Lógica de control y condiciones 
    duty_porcentaje = 0
    estado_led_v = 0
    estado_led_r = 0

    if not sistema_habilitado:
        duty_porcentaje = 0
        estado_led_v = 0
        estado_led_r = 0
    elif L > 190.0:
        # Alarma prioritaria de nivel alto (L > 190 cm)
        # Detiene la bomba independientemente del Setpoint
        duty_porcentaje = 0
        estado_led_v = 1
        estado_led_r = 1
    elif L >= SP:
        # Habilitado y L >= SP
        duty_porcentaje = 0
        estado_led_v = 1
        estado_led_r = 0
    elif (SP - 10.0) <= L < SP:
        # Habilitado y SP-10 cm <= L < SP
        duty_porcentaje = 25
        estado_led_v = 1
        estado_led_r = 0
    elif (SP - 30.0) <= L < (SP - 10.0):
        # Habilitado y SP-30 cm <= L < SP-10 cm
        duty_porcentaje = 50
        estado_led_v = 1
        estado_led_r = 0
    elif (SP - 60.0) <= L < (SP - 30.0):
        # Habilitado y SP-60 cm <= L < SP-30 cm
        duty_porcentaje = 75
        estado_led_v = 1
        estado_led_r = 0
    elif L < (SP - 60.0):
        # Habilitado y L < SP-60 cm
        duty_porcentaje = 100
        estado_led_v = 1
        estado_led_r = 0

    # Actualización de salidas digitales (GPIO OUT)
    led_v.value(estado_led_v)
    led_r.value(estado_led_r)

    # Salida PWM para la Bomba (Escala MicroPython de 16 bits... 0 a 65535)
    duty_16bit = int((duty_porcentaje / 100.0) * 65535)
    pwm_bomba.duty_u16(duty_16bit)

    # Monitoreo por consola serie
    estado_str = "HABILITADO" if sistema_habilitado else "DESHABILITADO"
    v_str = "ON" if estado_led_v else "OFF"
    r_str = "ON" if estado_led_r else "OFF"
    
    print(f"Estado: {estado_str:<12} | L: {L:5.1f} cm | SP: {SP:5.1f} cm | DAC: {valor_dac:3d} | PWM: {duty_porcentaje:3d}% | LED_V: {v_str} | LED_R: {r_str}")

    time.sleep_ms(150)