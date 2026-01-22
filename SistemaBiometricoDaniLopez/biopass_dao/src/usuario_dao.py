import psycopg2
from conexion_db import DBConnection

class UsuarioDAO:
    def registrar_usuario(self, nombre, imagen_bytes):
        conn = DBConnection.get_connection()
        if conn:
            try:
                with conn.cursor() as cursor:
                    # Prevenir mismo nombre dos veces (puedes eliminar esta sección si quieres duplicados)
                    cursor.execute("SELECT COUNT(*) FROM usuarios WHERE nombre=%s", (nombre,))
                    if cursor.fetchone()[0] > 0:
                        return False
                    query = "INSERT INTO usuarios (nombre, rostro) VALUES (%s, %s)"
                    cursor.execute(query, (nombre, psycopg2.Binary(imagen_bytes)))
                conn.commit()
                return True
            except Exception as e:
                print(f"Error al registrar: {e}")
                conn.rollback()
        return False

    def obtener_todos(self):
        conn = DBConnection.get_connection()
        usuarios = []
        if conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id, nombre, rostro FROM usuarios")
                for row in cursor.fetchall():
                    usuarios.append({'id': row[0], 'nombre': row[1], 'rostro': bytes(row[2])})
        return usuarios