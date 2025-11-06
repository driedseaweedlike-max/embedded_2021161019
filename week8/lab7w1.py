import RPi.GPIO as GPIO
import time
import sys

SWITCHES = [
    {'pin': 5, 'name': 'SW1'},
    {'pin': 6, 'name': 'SW2'},
    {'pin': 13, 'name': 'SW3'},
    {'pin': 19, 'name': 'SW4'},
]

click_count = [0] * len(SWITCHES) 

prev_values = [0] * len(SWITCHES) 

GPIO.setwarnings(False) 
GPIO.setmode(GPIO.BCM)


for sw in SWITCHES:
    GPIO.setup(sw['pin'], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

try:
    while True:
        for i, sw in enumerate(SWITCHES):
            current_value = GPIO.input(sw['pin'])
            
            if current_value == 1 and prev_values[i] == 0:
                
                click_count[i] += 1
                
                print(f"('{sw['name']} click', {click_count[i]})")
            
            prev_values[i] = current_value
            
        time.sleep(0.05) 

except KeyboardInterrupt:
    print("\n프로그램을 종료합니다.")
    pass

finally:
    GPIO.cleanup()