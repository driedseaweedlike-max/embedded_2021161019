import serial
import threading
import time
import RPi.GPIO as GPIO # 라즈베리파이 GPIO 제어 라이브러리

# =================================================================
# 1. 환경 설정 및 전역 변수
# =================================================================

# 시리얼 포트 설정: 라즈베리파이 UART 포트. raspi-config 설정이 선행되어야 함.
SERIAL_PORT = "/dev/ttyS0" 
BAUD_RATE = 9600

# GPIO 핀 설정: L298N 모터 드라이버를 가정 (BCM 모드 핀 번호)
# 실제 하드웨어 구성에 맞게 핀 번호를 수정하세요!
# Left Motor (A)
IN1 = 17 
IN2 = 18
ENA = 12 # PWM 핀 (속도 제어)

# Right Motor (B)
IN3 = 27
IN4 = 22
ENB = 13 # PWM 핀 (속도 제어)

# PWM 객체 (속도 제어용)
pwm_a = None
pwm_b = None
MOTOR_SPEED = 60 # 초기 속도 (Duty Cycle, 0~100)

# gData: 시리얼 통신으로 받은 명령을 저장하는 전역 변수
gData = "" 

# 시리얼 객체 초기화
try:
    bleSerial = serial.Serial(SERIAL_PORT, baudrate=BAUD_RATE, timeout=1.0)
    print(f"✅ 시리얼 포트 연결 성공: {SERIAL_PORT} @ {BAUD_RATE}bps")
except serial.SerialException as e:
    print(f"❌ 시리얼 포트 오류: {e}")
    print("  -> 포트 경로 및 라즈베리파이 시리얼 설정을 확인하세요.")
    exit()

# =================================================================
# 2. GPIO 및 모터 설정
# =================================================================

def setup_gpio():
    """GPIO 핀 모드 및 초기 상태 설정"""
    global pwm_a, pwm_b
    
    # BCM 모드로 핀 번호 사용
    GPIO.setmode(GPIO.BCM)
    
    # 모터 제어 핀들을 출력(OUT)으로 설정
    GPIO.setup([IN1, IN2, IN3, IN4], GPIO.OUT)
    
    # PWM 핀들을 출력으로 설정하고 PWM 객체 생성 (주파수 100Hz)
    GPIO.setup([ENA, ENB], GPIO.OUT)
    pwm_a = GPIO.PWM(ENA, 100)
    pwm_b = GPIO.PWM(ENB, 100)
    
    # PWM 시작 (초기 속도는 0)
    pwm_a.start(0)
    pwm_b.start(0)
    
    # 초기 정지 상태 설정
    stop()
    print("⚙️ GPIO 설정 완료 및 초기 정지")

def cleanup_gpio():
    """프로그램 종료 시 GPIO 리소스 해제"""
    stop()
    GPIO.cleanup()
    print("🧹 GPIO 리소스 해제 완료")

# =================================================================
# 3. 자동차 움직임 제어 함수
# =================================================================

def go():
    """전진: 두 모터를 같은 방향으로 구동"""
    print("🚗 [GO] 전진")
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.HIGH)
    GPIO.output(IN4, GPIO.LOW)
    pwm_a.ChangeDutyCycle(MOTOR_SPEED)
    pwm_b.ChangeDutyCycle(MOTOR_SPEED)

def back():
    """후진: 두 모터를 반대 방향으로 구동"""
    print("🚗 [BACK] 후진")
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.HIGH)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.HIGH)
    pwm_a.ChangeDutyCycle(MOTOR_SPEED)
    pwm_b.ChangeDutyCycle(MOTOR_SPEED)

def left():
    """좌회전: 왼쪽 모터는 후진, 오른쪽 모터는 전진 (제자리 회전)"""
    print("🚗 [LEFT] 좌회전")
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.HIGH)
    GPIO.output(IN3, GPIO.HIGH)
    GPIO.output(IN4, GPIO.LOW)
    pwm_a.ChangeDutyCycle(MOTOR_SPEED)
    pwm_b.ChangeDutyCycle(MOTOR_SPEED)

def right():
    """우회전: 왼쪽 모터는 전진, 오른쪽 모터는 후진 (제자리 회전)"""
    print("🚗 [RIGHT] 우회전")
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.HIGH)
    pwm_a.ChangeDutyCycle(MOTOR_SPEED)
    pwm_b.ChangeDutyCycle(MOTOR_SPEED)

def stop():
    """정지: 모든 모터의 ENA/ENB 핀을 0으로 설정"""
    print("🛑 [STOP] 정지")
    # PWM Duty Cycle을 0으로 설정하여 정지시키는 것이 모범적
    if pwm_a and pwm_b:
        pwm_a.ChangeDutyCycle(0)
        pwm_b.ChangeDutyCycle(0)
    
    # In case PWM is not used, setting IN pins to LOW might be necessary
    # GPIO.output([IN1, IN2, IN3, IN4], GPIO.LOW) 


# =================================================================
# 4. 블루투스 수신 쓰레드 함수
# =================================================================

def serial_thread():
    """BT 통신으로 받은 데이터를 gData 전역 변수에 할당"""
    global gData
    
    print("🔄 시리얼 수신 쓰레드 시작. 조이스틱 명령 대기 중...")
    
    while True:
        try:
            # 한 줄(\r\n이 포함된 데이터)씩 값을 읽습니다.
            data = bleSerial.readline()
            
            if data:
                # 바이트 데이터를 문자열로 변환 및 공백 제거
                decoded_data = data.decode('utf-8').strip()
                
                if decoded_data:
                    gData = decoded_data
                    # print(f"수신: {gData}") # 디버깅용
        
        except Exception as e:
            # print(f"Serial Read Error: {e}") 
            time.sleep(0.01)

# =================================================================
# 5. 메인 루프 (명령 처리)
# =================================================================

def main_loop():
    """조이스틱 명령을 처리하고 자동차 구동 함수를 호출"""
    global gData
    
    command_map = {
        "go": go,      # 전진 (Up)
        "back": back,  # 후진 (Down)
        "left": left,  # 좌회전 (Left)
        "right": right # 우회전 (Right)
        # 'stop'이 명령으로 오면 처리되지만, 조이스틱 제어에서는 보통 '누름 해제' 시 stop이 처리됨
    }
    
    current_command = ""
    print("🤖 자동차 제어 시스템 시작. 조이스틱 명령 확인 중...")
    
    try:
        # 1. 시리얼 수신 쓰레드 시작
        serial_t = threading.Thread(target = serial_thread)
        serial_t.daemon = True 
        serial_t.start()
        
        # 2. 메인 루프: gData의 명령을 지속적으로 확인
        while True:
            # 새로운 명령을 확인
            new_command = gData.lower()
            
            # 2-1. 명령이 유효하고 현재 명령과 다를 경우 (새로운 명령)
            if new_command in command_map and new_command != current_command:
                
                # 해당하는 함수 호출
                command_map[new_command]()
                
                # 현재 명령 업데이트
                current_command = new_command
            
            # 2-2. 명령이 비어있거나, 유효하지 않은 명령이 들어왔는데 
            #      현재 자동차가 움직이는 상태일 경우 (조이스틱을 놓은 경우)
            elif new_command == "" and current_command != "":
                stop()
                current_command = "" # 명령 초기화
                
            # 2-3. 명령이 계속 유지될 경우 (조이스틱을 계속 누르고 있는 경우)
            #      -> 별도 처리 없이 같은 상태 유지 (함수 재호출 불필요)
            
            # 명령 확인 주기 설정
            time.sleep(0.05) 

    except KeyboardInterrupt:
        print("\n프로그램 종료 요청...")
        
    finally:
        # 3. 프로그램 종료 시 정리 작업
        cleanup_gpio()
        if bleSerial.is_open:
            bleSerial.close()
        print("✅ 블루투스 포트 닫힘. 프로그램 종료.")


if __name__ == "__main__":
    try:
        setup_gpio() # GPIO 설정 먼저 수행
        main_loop()  # 메인 루프 실행
    except RuntimeError as e:
        print(f"❌ 초기화 오류: {e}")
        print("  -> 'sudo' 권한으로 실행했는지 확인하거나, GPIO 라이브러리 설치를 확인하세요.")