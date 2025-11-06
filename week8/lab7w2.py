import RPi.GPIO as GPIO
import time

NOTES = {
    '도': 262, 
    '레': 294, 
    '미': 330, 
    '파': 349, 
    '솔': 392, 
    '라': 440, 
    '시': 494, 
    '높은도': 523
}

BUZZER_PIN = 12

SWITCHES = [
    {'pin': 5, 'name': 'SW1', 'note': '도'},
    {'pin': 6, 'name': 'SW2', 'note': '솔'},
    {'pin': 13, 'name': 'SW3', 'note': '라'},
    {'pin': 19, 'name': 'SW4', 'note': '높은도'},
]

prev_values = [0] * len(SWITCHES) 

is_playing = False 

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

GPIO.setup(BUZZER_PIN, GPIO.OUT)

for sw in SWITCHES:
    GPIO.setup(sw['pin'], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

buzzer_pwm = GPIO.PWM(BUZZER_PIN, 1)

def play_scale():
    print("1. '도레미파솔라시도'")
    buzzer_pwm.start(50)
    
    scale = ['도', '레', '미', '파', '솔', '라', '시', '높은도']
    for note in scale:
        freq = NOTES[note]
        buzzer_pwm.ChangeFrequency(freq)
        time.sleep(1.0)
    
    buzzer_pwm.stop()

def play_horn():
    global is_playing
    if is_playing:
        return
        
    is_playing = True
    print("2. 나만의 경적 소리 연주 시작!")
    
    horn_sequence = [
        (NOTES['라'], 0.5),
        (NOTES['파'], 0.5),
        (NOTES['라'], 0.5),
        (NOTES['파'], 0.5),
        (NOTES['라'], 1.0),
    ]

    buzzer_pwm.start(70)
    for freq, delay in horn_sequence:
        buzzer_pwm.ChangeFrequency(freq)
        time.sleep(delay)
        
    buzzer_pwm.stop()
    print("경적 소리 연주 종료")
    is_playing = False

def play_school_bell():
    global is_playing
    if is_playing:
        return
        
    is_playing = True
    print("4. '학교 종' 멜로디 연주 시작!")
    
    music_sequence = [
        (NOTES['솔'], 0.4), (NOTES['솔'], 0.4), (NOTES['라'], 0.4), (NOTES['라'], 0.4), 
        (NOTES['솔'], 0.4), (NOTES['솔'], 0.4), (NOTES['미'], 0.8),
        (NOTES['솔'], 0.4), (NOTES['솔'], 0.4), (NOTES['미'], 0.4), (NOTES['미'], 0.4), 
        (NOTES['레'], 1.2),
    ]

    buzzer_pwm.start(60)
    for freq, duration in music_sequence:
        buzzer_pwm.ChangeFrequency(freq)
        time.sleep(duration)
        
    buzzer_pwm.stop()
    print("'학교 종' 멜로디 연주 종료")
    is_playing = False

try:
    play_scale()
    
    print("SW1: 경적 소리 재생")
    print("SW2: '학교 종' ")
    print("SW3, SW4: 개별 음계 연주")
    
    while True:
        for i, sw in enumerate(SWITCHES):
            current_value = GPIO.input(sw['pin'])
            
            if current_value == 1 and prev_values[i] == 0:
                print(f"[{sw['name']} 눌림 감지]")
                
                if sw['name'] == 'SW1':
                    play_horn()
                elif sw['name'] == 'SW2':
                    play_school_bell()
                else:
                    freq = NOTES[sw['note']]
                    
                    buzzer_pwm.start(50)
                    buzzer_pwm.ChangeFrequency(freq)
                    time.sleep(0.15)
                    buzzer_pwm.stop()

            prev_values[i] = current_value
            
        time.sleep(0.05)

except KeyboardInterrupt:
    print("\n프로그램을 종료합니다.")
    pass

finally:
    buzzer_pwm.stop()
    GPIO.cleanup()