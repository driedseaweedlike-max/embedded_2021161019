# -*- coding: utf-8 -*-
import RPi.GPIO as GPIO
import time

PWMA = 18
AIN1 = 22
AIN2 = 27

PWMB = 23
BIN1 = 25
BIN2 = 24

SWITCHES = [
    {'pin': 5, 'name': 'SW1', 'direction': '앞'},
    {'pin': 6, 'name': 'SW2', 'direction': '오른쪽'},
    {'pin': 13, 'name': 'SW3', 'direction': '왼쪽'},
    {'pin': 19, 'name': 'SW4', 'direction': '뒤'},
]

SPEED = 50
prev_values = [0] * len(SWITCHES)

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

GPIO.setup([PWMA, AIN1, AIN2, PWMB, BIN1, BIN2], GPIO.OUT)

for sw in SWITCHES:
    GPIO.setup(sw['pin'], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

L_Motor = GPIO.PWM(PWMA, 500)
R_Motor = GPIO.PWM(PWMB, 500)
L_Motor.start(0)
R_Motor.start(0)


def stop_car():
    GPIO.output([AIN1, AIN2, BIN1, BIN2], GPIO.LOW)
    L_Motor.ChangeDutyCycle(0)
    R_Motor.ChangeDutyCycle(0)

def control_car(direction):
    
    if direction == '앞':
        GPIO.output(AIN1, GPIO.LOW)
        GPIO.output(AIN2, GPIO.HIGH)
        GPIO.output(BIN1, GPIO.LOW)
        GPIO.output(BIN2, GPIO.HIGH)
        
        L_Motor.ChangeDutyCycle(SPEED)
        R_Motor.ChangeDutyCycle(SPEED)
        print("자동차: 직진")

    elif direction == '뒤':
        GPIO.output(AIN1, GPIO.HIGH)
        GPIO.output(AIN2, GPIO.LOW)
        GPIO.output(BIN1, GPIO.HIGH)
        GPIO.output(BIN2, GPIO.LOW)
        
        L_Motor.ChangeDutyCycle(SPEED)
        R_Motor.ChangeDutyCycle(SPEED)
        print("자동차: 후진")

    elif direction == '왼쪽':
        GPIO.output(AIN1, GPIO.LOW)
        GPIO.output(AIN2, GPIO.LOW)
        GPIO.output(BIN1, GPIO.LOW)
        GPIO.output(BIN2, GPIO.HIGH)
        
        L_Motor.ChangeDutyCycle(0)
        R_Motor.ChangeDutyCycle(SPEED)
        print("자동차: 좌회전")

    elif direction == '오른쪽':
        GPIO.output(AIN1, GPIO.LOW)
        GPIO.output(AIN2, GPIO.HIGH)
        GPIO.output(BIN1, GPIO.LOW)
        GPIO.output(BIN2, GPIO.LOW)
        
        L_Motor.ChangeDutyCycle(SPEED)
        R_Motor.ChangeDutyCycle(0)
        print("자동차: 우회전")
    
    else:
        stop_car()

def test_right_motor():
    
    GPIO.output(BIN1, GPIO.LOW)
    GPIO.output(BIN2, GPIO.HIGH)
    
    R_Motor.ChangeDutyCycle(50)
    print("오른쪽 모터 동작 (50%)")
    time.sleep(1.0)
    
    R_Motor.ChangeDutyCycle(0)
    print("오른쪽 모터 정지")
    time.sleep(1.0)
    
    R_Motor.ChangeDutyCycle(50)
    print("오른쪽 모터 동작 (50%)")
    time.sleep(1.0)
    
    R_Motor.ChangeDutyCycle(0)
    print("오른쪽 모터 정지")
    time.sleep(1.0)
    

try:
    test_right_motor() 
    stop_car()
    
    print("SW1: 앞, SW2: 오른쪽, SW3: 왼쪽, SW4: 뒤")
    
    while True:
        for i, sw in enumerate(SWITCHES):
            current_value = GPIO.input(sw['pin'])
            
            if current_value == GPIO.HIGH and prev_values[i] == GPIO.LOW:
                print(f"[눌림] {sw['name']}: {sw['direction']} 동작 시작")
                control_car(sw['direction'])
                
            elif current_value == GPIO.LOW and prev_values[i] == GPIO.HIGH:
                print(f"[떼어짐] {sw['name']}: 동작 정지")
                stop_car()
            
            prev_values[i] = current_value
            
        time.sleep(0.02)

except KeyboardInterrupt:
    print("\n프로그램을 종료합니다.")
    pass

finally:
    stop_car()
    GPIO.cleanup()