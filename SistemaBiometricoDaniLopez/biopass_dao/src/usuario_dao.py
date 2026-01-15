import psycopg2
from src.conexion_db import DBConnection

class UsuarioDAO:
    def registrar_usuario(self, nombre, imagen_bytes):
        conn = DBConnection.get_connection()
        cursor = conn.cursor()
        query = "INSERT INTO usuarios (nombre, rostro) VALUES (%s, %s)"
        cursor.execute(query, (nombre, psycopg2.Binary(imagen_bytes)))
        conn.commit()
        cursor.close()

    def obtener_todos(self):
        conn = DBConnection.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre, rostro FROM usuarios")
        usuarios = cursor.fetchall()
        cursor.close()
        return usuarios