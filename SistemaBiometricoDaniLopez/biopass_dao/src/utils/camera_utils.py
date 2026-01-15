import cv2
import numpy as np

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

def capturar_rostro():
    cap = cv2.VideoCapture(0)
    rostro_bytes = None

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        for (x, y, w, h) in faces:
            rostro = gray[y:y+h, x:x+w]
            _, buffer = cv2.imencode('.jpg', rostro)
            rostro_bytes = buffer.tobytes()
            cap.release()
            cv2.destroyAllWindows()
            return rostro_bytes

        cv2.imshow("Captura", frame)
        if cv2.waitKey(1) & 0xFF == 27: # Presionar ESC para salir
            break

    cap.release()
    cv2.destroyAllWindows()
    return None