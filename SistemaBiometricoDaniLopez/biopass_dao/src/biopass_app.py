import tkinter as tk
from tkinter import messagebox, simpledialog
from usuario_dao import UsuarioDAO
from camera_utils import capturar_rostro, bytes_a_imagen
import cv2
import numpy as np

class BioPassApp:
    def __init__(self):
        self.dao = UsuarioDAO()
        self.root = tk.Tk()
        self.root.title("BioPass")
        self.root.geometry("400x250")
        tk.Label(self.root, text="BioPass Facial Login", font=("Arial", 16)).pack(pady=20)
        tk.Button(self.root, text="Registrar usuario", width=20, height=2, command=self.registrar).pack(pady=8)
        tk.Button(self.root, text="Entrar (Login)", width=20, height=2, command=self.login).pack(pady=8)
        self.root.mainloop()

    def registrar(self):
        nombre = simpledialog.askstring("Registro", "Introduce tu nombre:")
        if not nombre:
            return
        messagebox.showinfo("Captura", "Se abrirá la cámara.\nCuando veas tu rostro en recuadro verde, pulsa S para guardar o Q para cancelar.")
        rostro_bytes = capturar_rostro(registro=True)
        if rostro_bytes is None:
            messagebox.showerror("Error", "No se capturó el rostro.")
            return
        if self.dao.registrar_usuario(nombre, rostro_bytes):
            messagebox.showinfo("¡OK!", f"Usuario {nombre} registrado exitosamente.")
        else:
            messagebox.showerror("Error", "No se pudo registrar el usuario (¿Duplicado?)")

    def entrenar_modelo(self):
        usuarios = self.dao.obtener_todos()
        if not usuarios:
            return None, None
        faces, labels, nombres_id = [], [], {}
        for user in usuarios:
            img = bytes_a_imagen(user['rostro'])
            if img is not None:
                faces.append(img)
                labels.append(user['id'])
                nombres_id[user['id']] = user['nombre']
        if not faces:
            return None, None
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        recognizer.train(faces, np.array(labels))
        return recognizer, nombres_id

    def login(self):
        recognizer, nom_id = self.entrenar_modelo()
        if recognizer is None:
            messagebox.showerror("Error", "Debes registrar algún usuario primero.")
            return
        messagebox.showinfo("Login", "Se abrirá la cámara.\nMira al objetivo.\nPulsa Q para salir.")
        cap = cv2.VideoCapture(0)
        ok = False
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            img_face, rect = capturar_rostro(retornar_imagen=True, frame=frame)
            if rect is not None and img_face is not None:
                (x, y, w, h) = rect
                pred_id, conf = recognizer.predict(img_face)
                match_pct = max(0, 100 - round(conf))
                color = (0, 255, 0) if match_pct > 70 else (0, 0, 255)
                label = f"{nom_id.get(pred_id, 'Desconocido') if match_pct > 70 else 'Desconocido'} ({match_pct}%)"
                cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
                cv2.putText(frame, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
                cv2.imshow("Login", frame)
                if match_pct > 70:
                    nombre = nom_id.get(pred_id, "Desconocido")
                    messagebox.showinfo("Bienvenido", f"Hola {nombre}")
                    ok = True
                    break
            else:
                cv2.imshow("Login", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        cap.release()
        cv2.destroyAllWindows()
        if not ok:
            messagebox.showwarning("No encontrado", "No te reconocimos. Intenta registrarte.")

if __name__ == '__main__':
    BioPassApp()