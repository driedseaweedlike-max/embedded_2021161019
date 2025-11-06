# -*- coding: utf-8 -*-
import RPi.GPIO as GPIO
import time
import threading
import serial

# --- GPIO 핀 설정 (생략, 기존과 동일) ---
PWMA = 18
AIN1 = 22
AIN2 = 27
PWMB = 23
BIN1 = 25
BIN2 = 24

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup([PWMA, AIN1, AIN2, PWMB, BIN1, BIN2], GPIO.OUT)

# PWM 설정 (Frequency 500Hz)
L_Motor = GPIO.PWM(PWMA, 500)
R_Motor = GPIO.PWM(PWMB, 500)
L_Motor.start(0)
R_Motor.start(0)

# --- 블루투스 통신 설정 및 전역 변수 (생략, 기존과 동일) ---
try:
    bleSerial = serial.Serial("/dev/ttyS0", baudrate=9600, timeout=1.0) 
    print("블루투스 시리얼 포트 초기화 성공")
except serial.SerialException:
    class DummySerial:
        def readline(self): return b''
        def close(self): pass
    bleSerial = DummySerial()

gData = "" # 블루투스로 수신된 데이터 저장

# --- 자동차 제어 함수 수정 (속도를 인자로 받도록) ---

def stop_car():
    GPIO.output([AIN1, AIN2, BIN1, BIN2], GPIO.LOW)
    L_Motor.ChangeDutyCycle(0)
    R_Motor.ChangeDutyCycle(0)
    # print("자동차: 정지") # 조이스틱은 정지 메시지가 너무 많이 나와서 주석 처리

# control_car 함수를 방향과 속도를 인자로 받도록 수정
def control_car(direction, speed_percent):
    
    # PWM 듀티 사이클 설정
    duty_cycle = min(max(int(speed_percent), 0), 100) # 0~100 사이로 제한
    
    # 정지
    if duty_cycle == 0:
        stop_car()
        return

    # 앞 (go)
    if direction == 'go':
        GPIO.output(AIN1, GPIO.LOW)
        GPIO.output(AIN2, GPIO.HIGH)
        GPIO.output(BIN1, GPIO.LOW)
        GPIO.output(BIN2, GPIO.HIGH)
        
        L_Motor.ChangeDutyCycle(duty_cycle)
        R_Motor.ChangeDutyCycle(duty_cycle)
        # print(f"자동차: 직진 ({duty_cycle}%)")

    # 뒤 (back)
    elif direction == 'back':
        GPIO.output(AIN1, GPIO.HIGH)
        GPIO.output(AIN2, GPIO.LOW)
        GPIO.output(BIN1, GPIO.HIGH)
        GPIO.output(BIN2, GPIO.LOW)
        
        L_Motor.ChangeDutyCycle(duty_cycle)
        R_Motor.ChangeDutyCycle(duty_cycle)
        # print(f"자동차: 후진 ({duty_cycle}%)")

    # 왼쪽 (left) - 제자리 회전이 아닌 한쪽 바퀴 정지
    elif direction == 'left':
        GPIO.output(AIN1, GPIO.LOW)
        GPIO.output(AIN2, GPIO.LOW) # 왼쪽 바퀴 정지
        GPIO.output(BIN1, GPIO.LOW)
        GPIO.output(BIN2, GPIO.HIGH) # 오른쪽 바퀴 전진
        
        L_Motor.ChangeDutyCycle(0)
        R_Motor.ChangeDutyCycle(duty_cycle)
        # print(f"자동차: 좌회전 ({duty_cycle}%)")

    # 오른쪽 (right) - 한쪽 바퀴 정지
    elif direction == 'right':
        GPIO.output(AIN1, GPIO.LOW)
        GPIO.output(AIN2, GPIO.HIGH) # 왼쪽 바퀴 전진
        GPIO.output(BIN1, GPIO.LOW)
        GPIO.output(BIN2, GPIO.LOW) # 오른쪽 바퀴 정지
        
        L_Motor.ChangeDutyCycle(duty_cycle)
        R_Motor.ChangeDutyCycle(0)
        # print(f"자동차: 우회전 ({duty_cycle}%)")
    
    # 조이스틱 데이터로 미세 조정하는 로직은 나중에 추가 가능 (Differential Drive)
    # 현재는 기본 4방향만 처리

# --- 통신 스레드 함수 (생략, 기존과 동일) ---
def serial_thread():
    global gData
    # print("serial_thread 시작...")
    while True:
        try:
            data = bleSerial.readline() 
            if data:
                # 조이스틱 명령은 연속으로 들어오므로, 이전 명령과 동일해도 업데이트
                gData = data.decode('utf-8').strip() 
        except Exception:
            time.sleep(1)

# --- 메인 제어 루프 함수 수정 (핵심) ---
def main():
    global gData
    
    stop_car()
    print("메인 제어 루프 시작. 조이스틱(J0:각도,크기) 및 버튼(go, stop 등) 명령어 대기.")
    
    # 버튼 명령어를 위한 이전 데이터 추적 (조이스틱 데이터는 너무 많아서 추적 안 함)
    prev_button_command = "" 

    try:
        while True:
            command = gData
            
            if command.startswith("J0:"):
                # 1. 조이스틱 명령어 처리 로직
                try:
                    # J0:Angle,Magnitude 형식 파싱
                    parts = command[3:].split(',')
                    angle = float(parts[0])
                    magnitude = float(parts[1])
                    
                    # Magnitude를 PWM Duty Cycle로 변환 (예: 1.0 -> 100%)
                    motor_speed = magnitude * 100 
                    
                    direction = 'stop'
                    
                    # 4방향 (앞/뒤/왼/오른쪽) 결정
                    if magnitude > 0.1: # 정지 상태 무시 (데드존 설정)
                        
                        # 45도 ~ 135도: 앞 (go)
                        if 45 <= angle < 135:
                            direction = 'go'
                        # 225도 ~ 315도: 뒤 (back)
                        elif 225 <= angle < 315:
                            direction = 'back'
                        # 135도 ~ 225도: 왼쪽 (left)
                        elif 135 <= angle < 225:
                            direction = 'left'
                        # 315도 ~ 45도: 오른쪽 (right) (0도 주변 처리)
                        else:
                            direction = 'right'

                    control_car(direction, motor_speed)
                    
                except ValueError as e:
                    # print(f"조이스틱 데이터 파싱 오류: {command}, {e}")
                    pass # 연속 데이터이므로 오류는 무시하고 다음 데이터 기다림

            # 2. 버튼 명령어 처리 로직 (기존 로직 유지)
            elif command and not command.startswith("J0:"):
                
                # 새로운 버튼 명령이 들어왔을 때만 실행
                if command != prev_button_command:
                    command_lower = command.lower()
                    
                    if "go" in command_lower:
                        control_car('go', 50) # 버튼 명령은 고정 속도 (50%)
                        prev_button_command = "go"
                    elif "back" in command_lower:
                        control_car('back', 50)
                        prev_button_command = "back"
                    elif "left" in command_lower:
                        control_car('left', 50)
                        prev_button_command = "left"
                    elif "right" in command_lower:
                        control_car('right', 50)
                        prev_button_command = "right"
                    elif "stop" in command_lower or not command_lower:
                        control_car('stop', 0)
                        prev_button_command = "stop"
                    else:
                        print(f"수신된 버튼 명령어: {command} (처리하지 않음)")
                
                # 버튼 명령 수신 후 다음 명령 대기를 위해 gData 초기화 (조이스틱 데이터와 구분)
                # gData = "" 
                
            time.sleep(0.02) # 루프 지연

    except KeyboardInterrupt:
        pass

# --- 프로그램 실행 시작 (생략, 기존과 동일) ---
if __name__ == '__main__':
    try:
        task1 = threading.Thread(target=serial_thread)
        task1.daemon = True
        task1.start()
        main()
    except Exception as e:
        print(f"메인 실행 중 오류 발생: {e}")
    finally:
        stop_car()
        bleSerial.close()
        GPIO.cleanup()
        print("GPIO 및 통신 정리 완료.")