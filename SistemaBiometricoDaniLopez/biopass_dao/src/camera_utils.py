import cv2
import numpy as np

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

def capturar_rostro(registro=False, retornar_imagen=False, frame=None):
    # Para registro: abre cámara si frame=None, espera 's' para guardar
    # Para login: usa frame recibido (ya está la cámara abierta)
    if frame is None:
        cap = cv2.VideoCapture(0)
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)
            rect = None
            for (x, y, w, h) in faces:
                rect = (x, y, w, h)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(frame, "Pulsa S para capturar", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.imshow("Registro", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('s') and rect is not None:
                (x, y, w, h) = rect
                rostro = gray[y:y+h, x:x+w]
                _, buffer = cv2.imencode('.jpg', rostro)
                cv2.destroyAllWindows()
                cap.release()
                return buffer.tobytes()
            elif key == ord('q'):
                break
        cap.release()
        cv2.destroyAllWindows()
        return None
    else:
        # frame ya entregado (para login)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        for (x, y, w, h) in faces:
            rostro = gray[y:y+h, x:x+w]
            if retornar_imagen:
                return rostro, (x, y, w, h)
        return None, None

def bytes_a_imagen(imagen_bytes):
    try:
        arr = np.frombuffer(imagen_bytes, np.uint8)
        return cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)
    except Exception:
        return None