import time
import micropython
import neopixel
from micropython import const
from machine import Pin, PWM, ADC, I2C, time_pulse_us
from ultrasonic_sensor import HCSR04

# Motors
M1_IN1 = 18
M1_IN2 = 19
M2_IN1 = 20
M2_IN2 = 21
M3_IN1 = 6
M3_IN2 = 7
M4_IN1 = 8
M4_IN2 = 9
# Servo
SERVO1 = 13
SERVO2 = 14
SERVO3 = 15
SERVO_MIN = 25
SERVO_MAX = 145
SERVO_CENTER = (SERVO_MIN + SERVO_MAX) // 2
#Tracking module
TRACK1 = 10
TRACK2 = 11
TRACK3 = 12
#I2C port/Ultrasonic module interface
SDA_TRIG = 4
SCL_ECHO = 5
# WS2812
WS2812 = 16
# Battery detection
A0 = 26
# Search light ADC port
A1 = 27
# Search light ADC port
A2 = 28
# Unused GPIO
GPIO22 = 22
GPIO17 = 17
# Infrared receiver port
IR = 3
# Buzzer port
BUZZER = 2
#Serial port
RX = 1
TX = 0

class Beep:
    # (freq, duration, volume)
    SHORT = (1000, 100, 100)
    LONG = (1000, 1000, 100)
    ERROR = [(1000, 50, 100), (1000, 50, 100), (1000, 50, 100)]

class Motor:
    def __init__(self, in1, in2):
        self.IN1 = Pin(in1, Pin.OUT)
        self.IN2 = Pin(in2, Pin.OUT)
        self.pwm1 = PWM(self.IN1)
        self.pwm2 = PWM(self.IN2)
        self.pwm1.freq(1000)
        self.pwm2.freq(1000)

    def forward(self, speed=65535):
        self.pwm1.duty_u16(speed)
        self.pwm2.duty_u16(0)

    def backward(self, speed=65535):
        self.pwm1.duty_u16(0)
        self.pwm2.duty_u16(speed)

    def stop(self):
        self.pwm1.duty_u16(0)
        self.pwm2.duty_u16(0)

class MotorController:
    def __init__(self):
        self.m1 = Motor(M1_IN1, M1_IN2)
        self.m2 = Motor(M2_IN2, M2_IN1)
        self.m3 = Motor(M3_IN2, M3_IN1)
        self.m4 = Motor(M4_IN2, M4_IN1)

    def test_motors(self):
        self.m1.forward()
        time.sleep(1)
        self.m1.stop()
        self.m2.forward()
        time.sleep(1)
        self.m2.stop()
        self.m3.forward()
        time.sleep(1)
        self.m3.stop()
        self.m4.forward()
        time.sleep(1)
        self.m4.stop()

    def left_forward(self, speed=65535):
        self.m1.forward(speed)
        self.m2.forward(speed)

    def left_stop(self):
        self.m1.stop()
        self.m2.stop()

    def left_back(self, speed=65535):
        self.m1.backward(speed)
        self.m2.backward(speed)
    
    def right_forward(self, speed=65535):
        self.m3.forward(speed)
        self.m4.forward(speed)

    def right_stop(self):
        self.m3.stop()
        self.m4.stop()
    
    def right_back(self, speed=65535):
        self.m3.backward(speed)
        self.m4.backward(speed)

    def forward(self, speed=65535):
        print("Moving forward")
        self.left_forward(speed)
        self.right_forward(speed)
        
    def back(self, speed=65535):
        self.left_back(speed)
        self.right_back(speed)

    def rotate_left(self, speed=65535):
        self.left_back(speed)
        self.right_forward(speed)
    
    def rotate_right(self, speed=65535):
        self.left_forward(speed)
        self.right_back(speed)

    def forward_left(self, speed=65535):
        self.left_stop()
        self.right_forward(speed)
        
    def forward_right(self, speed=65535):
        self.left_forward(speed)
        self.right_stop()

    def back_left(self, speed=65535):
        self.left_stop()
        self.right_back(speed)

    def back_right(self, speed=65535):
        self.left_back(speed)
        self.right_stop()
        
    def stop(self):
        self.left_stop()
        self.right_stop()

class HardwareInterface:
    def __init__(self):
        self.battery = ADC(Pin(A0))
        self.motor_control = MotorController()
        self.SERVO1 = PWM(Pin(SERVO1))
        self.buzzer = PWM(Pin(BUZZER, Pin.OUT))
        self.led = Pin('LED', Pin.OUT)
        self.np = neopixel.NeoPixel(Pin(WS2812), 1)
        self.i2c = HCSR04(SDA_TRIG, SCL_ECHO)
        self.track1 = Pin(TRACK1, Pin.IN)
        self.track2 = Pin(TRACK2, Pin.IN)
        self.track3 = Pin(TRACK3, Pin.IN)
        self.left_photoresistor = ADC(Pin(A1))
        self.right_photoresistor = ADC(Pin(A2))

    def get_left_light_intensity(self):
        return self.left_photoresistor.read_u16()

    def get_right_light_intensity(self):
        return self.right_photoresistor.read_u16()

    def get_battery_voltage(self):
        adc_value = self.battery.read_u16()
        voltage = (adc_value / 65535) * 3.3
        return voltage

    def read_track_sensors(self):
        return self.track1.value(), self.track2.value(), self.track3.value()

    def set_led(self, value):
        if value:
            self.led.on()
        else:
            self.led.off()

    def move(self, direction, speedf=1.0):
        speed = int(65535 * speedf)
        move_func = getattr(self.motor_control, direction, None)
        print(direction, speedf, speed, move_func)
        if callable(move_func):
            if direction == 'stop':
                move_func()
            else:
                move_func(speed)

    def set_np(self, r, g, b, duration=0):
        self.np[0] = (r, g, b)
        self.np.write()
        if duration != 0:
            time.sleep(duration)
            self.np[0] = (0, 0, 0)
            self.np.write()

    def move_servo(self, angle, freq=50):
        angle = max(SERVO_MIN, min(SERVO_MAX, angle))
        self.SERVO1.freq(freq)
        duty = int((angle/180) * 8000 + 1000)
        self.SERVO1.duty_u16(duty)
    
    def get_distance(self):
        value = self.i2c.distance_cm()
        print("Got distance: ", value)
        return value
    
    def play_song(self, notes):
        for freq, duration, volume in notes:
            self.beep(freq, duration, volume)

    def beep(self, frequency, duration, volume=100):
        volume = max(0, min(100, volume))
        duty_cycle = int((volume / 100) * 65535)
        self.buzzer.freq(frequency)
        self.buzzer.duty_u16(duty_cycle)
        time.sleep_ms(duration)
        self.buzzer.duty_u16(0)


        
    def scan(self, start_angle=SERVO_MIN, end_angle=SERVO_MAX, step=10):
        # TODO test if this actually works
        measurements_pass_1 = []
        measurements_pass_2 = []

        for angle in range(start_angle, end_angle + 1, step):
            self.move_servo(angle)
            time.sleep_ms(10)
            distance = self.get_distance()
            measurements_pass_1.append(distance)
        
        for angle in range(end_angle, start_angle - 1, -step):
            self.move_servo(angle)
            time.sleep_ms(10)
            distance = self.get_distance()
            measurements_pass_2.append(distance)
        self.move_servo(SERVO_CENTER)
        return measurements_pass_1, measurements_pass_2