import cv2 as cv
import numpy as np
import threading, time

# SDcar 더미처리

try:
    import SDcar
except Exception:
    class DummyDrive:
        def __init__(self): print("[DummyDrive] initialized")
        def clean_GPIO(self): print("[DummyDrive] clean_GPIO")
        def motor_go(self, s): print(f"[DummyDrive] go {s}")
        def motor_back(self, s): print(f"[DummyDrive] back {s}")
        def motor_left(self, s): print(f"[DummyDrive] left {s}")
        def motor_right(self, s): print(f"[DummyDrive] right {s}")
        def motor_stop(self): print("[DummyDrive] stop")
    SDcar = type("m", (), {"Drive": DummyDrive})


# 파라미터
v_x = 320
v_y = 240
speed_base = 45             #  전진 속도 
Kp = 0.4                      # P 게인
roi_height = 60             # ROI 높이 
min_contour_area = 100      # 의미 있는 윤곽의 최소 면적
lost_threshold = 15         # 라인 소실시 처리 임계값
search_turn_time = 0.8      # (초) 소실 시 회전 탐색 시간

epsilon = 1e-6
v_x_grid = [int(v_x*i/10) for i in range(1, 10)]

# 전역 상태
is_running = False
enable_linetracing = True
last_cx = v_x // 2
lost_count = 0
last_time_lost = None

# 디버깅

def func_thread():
    while True:
        time.sleep(1)
        if not is_running:
            break


# 마스크 생성: 노란선에 집중
def make_mask(frame):
    hsv = cv.cvtColor(frame, cv.COLOR_BGR2HSV)
    
    # 노란색에 집중된 범위 (H: 20~40)
    mask_yellow = cv.inRange(hsv, (20, 100, 100), (40, 255, 255))
    
    # 노이즈 제거 및 구멍 메우기
    kernel = cv.getStructuringElement(cv.MORPH_RECT, (5,5))
    mask = cv.morphologyEx(mask_yellow, cv.MORPH_CLOSE, kernel, iterations=1)
    mask = cv.morphologyEx(mask, cv.MORPH_OPEN, kernel, iterations=1)
    
    return mask


# 윤곽에서 중심 구하기
def find_largest_contour_centroid(mask):
    # cv.RETR_EXTERNAL: 가장 외곽 윤곽선만 찾음
    contours, _ = cv.findContours(mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None, contours
    
    # 가장 면적이 큰 윤곽선 선택
    c = max(contours, key=cv.contourArea)
    area = cv.contourArea(c)
    if area < min_contour_area:
        return None, contours
    
    # 모멘트를 이용하여 무게 중심 계산
    M = cv.moments(c)
    if M['m00'] == 0:
        return None, contours
        
    cx = int(M['m10'] / (M['m00'] + epsilon))
    return (cx, int(area)), contours


# 간단한 조향: P 제어 

def control_by_error(err, car):
    # err: -1(left) .. 0(center) .. +1(right) (정규화된 에러)
    steer = Kp * err
    abs_steer = abs(steer)
    
    # 직진 구간: 오차가 0.20 미만일 때 직진 (떨림 최소화)
    if abs_steer < 0.20: 
        car.motor_go(speed_base)
    elif steer > 0:
        # 라인이 오른쪽으로 이탈 (err > 0) -> 오른쪽으로 회전하여 따라잡음
        turn_speed = int(speed_base * min(1.0, 0.6 + abs_steer))
        car.motor_right(turn_speed) 
    else:
        # 라인이 왼쪽으로 이탈 (err < 0) -> 왼쪽으로 회전하여 따라잡음
        turn_speed = int(speed_base * min(1.0, 0.6 + abs_steer))
        car.motor_left(turn_speed)   


# 메인: 카메라 루프
def main():
    # 전역 변수 선언 
    global last_cx, lost_count, last_time_lost, is_running, enable_linetracing
    
    camera = cv.VideoCapture(0)
    camera.set(cv.CAP_PROP_FRAME_WIDTH, v_x)
    camera.set(cv.CAP_PROP_FRAME_HEIGHT, v_y)

    try:
        while camera.isOpened() and is_running:
            ret, frame = camera.read()
            if not ret:
                print("camera read failed")
                break
            frame = cv.flip(frame, -1)

            # ROI 설정: 화면 하단 중앙 영역에 집중
            crop_y0 = int(v_y * 0.7)  # 화면 상단 70%는 자르고
            crop_img = frame[crop_y0:, :]

            # 마스크 생성
            mask_full = make_mask(crop_img)
            h_crop = crop_img.shape[0]
            
            # ROI: 마스크의 중앙 roi_height 픽셀만 사용
            roi_bot = mask_full[h_crop - roi_height : h_crop, :]

            # 중심 구하기 (Lookahead는 제외하고 근접 ROI만 사용)
            bot_centroid, _ = find_largest_contour_centroid(roi_bot)

            vis = crop_img.copy()
            # cv.imshow('mask_full', cv.resize(roi_bot, dsize=(0,0), fx=2, fy=2)) # ROI 마스크만 표시

            # 라인트레이싱 제어 로직
            if enable_linetracing:
                
                if bot_centroid is not None:
                    # 라인 발견 (안정적인 제어)
                    cx_rel = bot_centroid[0]
                    # 에러 계산: 중앙에서 얼마나 벗어났는지 (-1 ~ +1)
                    err = (cx_rel - (v_x/2)) / (v_x/2)
                    last_cx = cx_rel
                    lost_count = 0
                    last_time_lost = None

                    # control_by_error 호출
                    control_by_error(err, car) 

                    # 시각화
                    cy_abs = h_crop - roi_height // 2
                    cv.circle(vis, (int(cx_rel), cy_abs), 5, (0,0,255), -1)
                    cv.putText(vis, f'err:{err:.2f}', (5,20), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 1)

                else:
                    # 라인 소실 처리 (Lost Logic)
                    lost_count += 1
                    if last_time_lost is None: last_time_lost = time.time()
                    elapsed = time.time() - last_time_lost

                    if lost_count < lost_threshold:
                        # 짧은 소실: 이전 방향으로 저속 전진
                        car.motor_go(int(speed_base * 0.5))
                        if last_cx < (v_x/2): car.motor_left(int(speed_base * 0.4))
                        else: car.motor_right(int(speed_base * 0.4))
                    else:
                        # 오랜 소실: 탐색 모드 (양방향 회전 스윕)
                        if (elapsed % (search_turn_time*2)) < search_turn_time:
                            if last_cx < (v_x/2): car.motor_left(int(speed_base * 0.6))
                            else: car.motor_right(int(speed_base * 0.6))
                        else:
                            if last_cx < (v_x/2): car.motor_right(int(speed_base * 0.6))
                            else: car.motor_left(int(speed_base * 0.6))
                            
                    cv.putText(vis, f'LOST {lost_count}', (5,40), cv.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,255), 2)
            
            else:
                # 라인트레이싱 비활성화 상태: 정지
                car.motor_stop()
                cv.putText(vis, 'TRACING DISABLED', (5,20), cv.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)


            # 그리드/시각화
            for x in v_x_grid:
                cv.line(vis, (x, 0), (x, vis.shape[0]), (0,255,0), 1)
            cv.imshow('crop_vis', cv.resize(vis, dsize=(0,0), fx=2, fy=2))

            key = cv.waitKey(20)
            if key > 0:
                if key & 0xFF == ord('q'):
                    car.motor_stop()
                    is_running = False
                    break
                elif key & 0xFF == ord('e'):
                    print("enable tracing")
                    enable_linetracing = True
                elif key & 0xFF == ord('w'):
                    print("disable tracing")
                    enable_linetracing = False
                    car.motor_stop()

            # 안전: 강한 이상(마스크 전체가 거의 0)이면 속도 줄임
            if cv.countNonZero(mask_full) < 30:
                car.motor_go(int(speed_base * 0.4))
            # 루프 계속

    except Exception as ex:
        print("Exception:", ex)
    finally:
        camera.release()
        cv.destroyAllWindows()

# ------------------------------
# 실행부
# ------------------------------
if __name__ == '__main__':
    t = threading.Thread(target=func_thread)
    is_running = True
    t.start()

    car = SDcar.Drive()
    try:
        main()
    finally:
        is_running = False
        car.clean_GPIO()
        print("finished")