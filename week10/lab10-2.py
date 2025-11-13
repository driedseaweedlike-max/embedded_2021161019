import cv2
import numpy as np
import glob
import os

# 이미지 경로 지정
input_dir = "imgs"
output_dir = "results"
os.makedirs(output_dir, exist_ok=True)

# 노란색, 흰색 HSV 범위 정의
yellow_lower = np.array([15, 80, 80])
yellow_upper = np.array([40, 255, 255])
white_lower  = np.array([0, 0, 200])
white_upper  = np.array([180, 30, 255])

# imgs 폴더 내 모든 jpg 파일 불러오기
for file in sorted(glob.glob(os.path.join(input_dir, "*.jpg"))):
    img = cv2.imread(file)
    if img is None:
        continue

    # 크기 조정 (옵션)
    img = cv2.resize(img, (640, 480))

    # HSV 변환
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # 색상 마스크 생성
    mask_yellow = cv2.inRange(hsv, yellow_lower, yellow_upper)
    mask_white  = cv2.inRange(hsv, white_lower, white_upper)

    # 두 마스크 결합
    mask = cv2.bitwise_or(mask_yellow, mask_white)

    # 노이즈 제거 (morphology 연산)
    kernel = np.ones((5,5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

    # 마스크 적용 (선 부분만 보이게)
    result = cv2.bitwise_and(img, img, mask=mask)

    # 결과 저장
    base_name = os.path.basename(file)
    out_path = os.path.join(output_dir, f"detected_{base_name}")
    cv2.imwrite(out_path, result)

    print(f"✅ Saved: {out_path}")

