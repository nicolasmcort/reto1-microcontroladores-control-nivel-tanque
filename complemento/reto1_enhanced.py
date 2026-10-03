from machine import Pin, ADC, DAC, PWM, SPI, time_pulse_us
import time
import framebuf

# Driver MAX7219 (Matriz Led 8x8 SPI)
class Matrix8x8:
    def __init__(self, spi, cs, num=1):
        self.spi = spi
        self.cs = cs
        self.cs.init(Pin.OUT, value=1)
        self.num = num
        self.buffer = bytearray(8 * num)
        self.fb = framebuf.FrameBuffer(self.buffer, 8 * num, 8, framebuf.MONO_HLSB)
        self.init_display()

    def _write(self, command, data):
        self.cs.value(0)
        for _ in range(self.num):
            self.spi.write(bytearray([command, data]))
        self.cs.value(1)

    def init_display(self):
        for cmd, data in ((12, 1), (9, 0), (11, 7), (10, 3)):
            self._write(cmd, data)
        self.fill(0)
        self.show()

    def brightness(self, value):
        self._write(10, max(0, min(15, value)))

    def fill(self, val):
        self.fb.fill(val)

    def rect(self, x, y, w, h, col):
        self.fb.rect(x, y, w, h, col)

    def line(self, x0, y0, x1, y1, col):
        self.fb.line(x0, y0, x1, y1, col)

    def show(self):
        for y in range(8):
            self.cs.value(0)
            for i in range(self.num):
                self.spi.write(bytearray([y + 1, self.buffer[y * self.num + i]]))
            self.cs.value(1)

# Configuración de periféricos
# SPI para Matriz 8x8 MAX7219
spi = SPI(1, baudrate=10000000, polarity=0, phase=0, sck=Pin(18), mosi=Pin(23))
matriz = Matrix8x8(spi, Pin(5), 1)
matriz.brightness(3)

# Sensor Ultrasonido HC-SR04
trig = Pin(13, Pin.OUT)
echo = Pin(12, Pin.IN)

# ADC1 CH7 - Potenciómetro Setpoint (SP) -> GPIO 35
adc_SP = ADC(Pin(35))
adc_SP.atten(ADC.ATTN_11DB)

# Entradas / Salidas Digitales
btn = Pin(16, Pin.IN, Pin.PULL_UP)
led_r = Pin(2, Pin.OUT)  # Rojo -> Alarma (L > 190 cm)
led_v = Pin(4, Pin.OUT)  # Verde -> Habilitado

# DAC1 (GPIO 25) y PWM (GPIO 17 -> Bomba)
dac = DAC(Pin(25))
pwm_bomba = PWM(Pin(17), freq=5000)

# Funciones
def medir_nivel_ultrasonico():
    """Mide distancia con HC-SR04 y escala a Nivel L (0-200 cm)"""
    trig.value(0)
    time.sleep_us(2)
    trig.value(1)
    time.sleep_us(10)
    trig.value(0)
    
    try:
        duracion = time_pulse_us(echo, 1, 30000) # Timeout 30ms (~5 metros max)
        if duracion < 0:
            return 0.0
        dist_cm = (duracion / 2.0) / 29.1
        
        # Escalado de maqueta (Distancia 2 cm -> Tanque Lleno 200 cm | Distancia 20 cm -> Tanque Vacío 0 cm)
        nivel_L = (20.0 - dist_cm) * (200.0 / 18.0)
        return max(0.0, min(200.0, nivel_L))
    except:
        return 0.0

def dibujar_cuadro_bomba(frame):
    """Animación gráfica de la bomba rotando en la matriz 8x8"""
    matriz.fill(0)
    f = frame % 4
    if f == 0:
        matriz.line(0, 0, 7, 7, 1)
        matriz.line(0, 7, 7, 0, 1)
    elif f == 1:
        matriz.line(3, 0, 3, 7, 1)
        matriz.line(0, 3, 7, 3, 1)
    elif f == 2:
        matriz.line(7, 0, 0, 7, 1)
        matriz.line(0, 0, 7, 7, 1)
    elif f == 3:
        matriz.line(0, 3, 7, 3, 1)
        matriz.line(3, 0, 3, 7, 1)
    matriz.show()

# Bucle principal
sistema_habilitado = False
estado_btn_anterior = 1
ultimo_debounce = 0

ultimo_frame_matriz = 0
frame_count = 0

print("=" * 70)
print("SISTEMA DE CONTROL DE NIVEL CON ULTRASONIDO Y MATRIZ 8x8")
print("=" * 70)

while True:
    tiempo_actual = time.ticks_ms()
    lectura_btn = btn.value()

    # Antirrebote software para conmutación de estado
    if lectura_btn == 0 and estado_btn_anterior == 1:
        if time.ticks_diff(tiempo_actual, ultimo_debounce) > 200:
            sistema_habilitado = not sistema_habilitado
            ultimo_debounce = tiempo_actual
    estado_btn_anterior = lectura_btn

    # Lectura de sensores y escalamiento
    L = medir_nivel_ultrasonico()
    raw_SP = adc_SP.read()
    
    
    SP = 50.0 + (raw_SP / 4095.0) * 130.0  # Escala SP: 50 a 180 cm

    # Conversión y Salida DAC (GPIO 25: 0-200 cm -> 0-255)
    valor_dac = int((L / 200.0) * 255)
    valor_dac = max(0, min(255, valor_dac))
    dac.write(valor_dac)
    v_dac_teorico = (valor_dac / 255.0) * 3.3

    # Lógica de control
    duty_porcentaje = 0
    estado_led_v = 0
    estado_led_r = 0

    # Alarma Prioritaria (L > 190 cm). Detiene bomba e ilumina led rojo
    if L > 190.0:
        duty_porcentaje = 0
        estado_led_v = 1
        estado_led_r = 1  # SOLO AQUÍ ENCIENDE EL LED ROJO
        
    # Sistema Deshabilitado
    elif not sistema_habilitado:
        duty_porcentaje = 0
        estado_led_v = 0
        estado_led_r = 0
        
    # Tanque Lleno / Supera SP (L >= SP)
    elif L >= SP:
        duty_porcentaje = 0
        estado_led_v = 1
        estado_led_r = 0
        
    # Bomba a 25% (SP - 10 cm <= L < SP)
    elif (SP - 10.0) <= L < SP:
        duty_porcentaje = 25
        estado_led_v = 1
        estado_led_r = 0
        
    # Bomba a 50% (SP - 30 cm <= L < SP - 10 cm)
    elif (SP - 30.0) <= L < (SP - 10.0):
        duty_porcentaje = 50
        estado_led_v = 1
        estado_led_r = 0  
        
    # Bomba a 75% (SP - 60 cm <= L < SP - 30 cm)
    elif (SP - 60.0) <= L < (SP - 30.0):
        duty_porcentaje = 75
        estado_led_v = 1
        estado_led_r = 0
        
    # Bomba a 100% (L < SP - 60 cm)
    elif L < (SP - 60.0):
        duty_porcentaje = 100
        estado_led_v = 1
        estado_led_r = 0

    # Actualización de salidas físicas
    led_v.value(estado_led_v)
    led_r.value(estado_led_r)
    pwm_bomba.duty_u16(int((duty_porcentaje / 100.0) * 65535))

    # Actualización visual de la Matriz 8x8
    if duty_porcentaje == 0:
        matriz.fill(0)
        matriz.rect(2, 2, 4, 4, 1)  # Cuadro estático (Bomba detenida)
        matriz.show()
    else:
        if duty_porcentaje == 25:
            intervalo_ms = 350
        elif duty_porcentaje == 50:
            intervalo_ms = 180
        elif duty_porcentaje == 75:
            intervalo_ms = 90
        else: # 100%
            intervalo_ms = 35

        if time.ticks_diff(tiempo_actual, ultimo_frame_matriz) >= intervalo_ms:
            frame_count += 1
            dibujar_cuadro_bomba(frame_count)
            ultimo_frame_matriz = tiempo_actual

    # Monitoreo por consola serie
    estado_str = "HABILITADO" if sistema_habilitado else "DESHABILITADO"
    v_str = "ON" if estado_led_v else "OFF"
    r_str = "ON" if estado_led_r else "OFF"
    
    print(f"[{estado_str:<12}] | Nivel L: {L:5.1f} cm -> DAC: {valor_dac:3d} ({v_dac_teorico:4.2f}V) | SP: {SP:5.1f} cm | PWM: {duty_porcentaje:3d}% | LED_V: {v_str} | LED_R: {r_str}")

    time.sleep_ms(30)