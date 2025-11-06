import serial
import time # time 모듈은 사용되지 않았지만, 일반적으로 시리얼 통신 코드에 포함되는 경우가 많아 참고용으로 남겨둡니다.

# 시리얼 포트 설정
# /dev/ttyS0는 예시 포트이며, 실제 환경에 맞게 수정해야 합니다.
bleSerial = serial.Serial("/dev/ttyS0", baudrate=9600, timeout=1.0)

try:
    # 무한 루프를 돌며 시리얼 데이터 읽기
    while True:
        # 시리얼 포트에서 1 바이트씩 데이터를 읽음 (read()는 기본 1바이트를 읽습니다)
        data = bleSerial.read()
        
        # 읽은 데이터를 출력
        # 출력 결과 'b''는 수신된 데이터가 바이트(bytes) 타입임을 나타냅니다.
        print(data)

except KeyboardInterrupt:
    # Ctrl+C 입력 시 루프를 빠져나오고 프로그램을 종료합니다.
    pass

# 프로그램 종료 시 시리얼 포트를 닫아줍니다.
bleSerial.close()