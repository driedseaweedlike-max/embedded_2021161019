import cv2

# 얼굴 검출용 Haar Cascade 파일 로드
face_cascade = cv2.CascadeClassifier('/home/tjsghs69/.local/lib/python3.7/site-packages/cv2/data/haarcascade_frontalface_default.xml')

# 카메라 초기화 (0: 기본 카메라)
cap = cv2.VideoCapture(0)

# 카메라 프레임 크기 설정 (선택)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

while True:
    ret, frame = cap.read()
    if not ret:
        print("카메라에서 영상을 가져올 수 없습니다.")
        break

    # 영상을 흑백으로 변환
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # 얼굴 검출 (scaleFactor=1.3, minNeighbors=5)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)

    # 얼굴 주변에 사각형 박스 표시
    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

    # 영상 출력
    cv2.imshow("Face Detection", frame)

    # 'q' 키를 누르면 종료
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# 자원 해제
cap.release()
cv2.destroyAllWindows()
