import tkinter as tk
from tkinter import messagebox
from src.usuario_dao import UsuarioDAO
from src.utils.camera_utils import capturar_rostro

class BioPassApp:
    def __init__(self):
        self.dao = UsuarioDAO()
        self.root = tk.Tk()
        self.root.title("BioPass")

        tk.Label(self.root, text="Nombre:").pack()
        self.entry_nombre = tk.Entry(self.root)
        self.entry_nombre.pack()

        tk.Button(self.root, text="Registrar", command=self.registrar).pack()

        self.root.mainloop()

    def registrar(self):
        nombre = self.entry_nombre.get()
        if not nombre:
            messagebox.showerror("Error", "Nombre requerido")
            return

        imagen = capturar_rostro()
        if imagen is None:
            messagebox.showerror("Error", "No se capturó el rostro")
            return

        self.dao.registrar_usuario(nombre, imagen)
        messagebox.showinfo("OK", "Usuario registrado correctamente")

if __name__ == "__main__":
    BioPassApp()