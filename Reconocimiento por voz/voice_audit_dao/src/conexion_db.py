"""
conexion_db.py - Patrón Singleton
Responsabilidad: Garantizar una única conexión activa a la base de datos PostgreSQL.
"""
import psycopg2
from config import Config


class ConexionDB:
    """
    Singleton que gestiona la conexión única a PostgreSQL.
    Evita saturar el servidor con múltiples conexiones abiertas.
    """
    _instancia = None
    _conexion = None

    def __new__(cls):
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
        return cls._instancia

    def conectar(self):
        """Abre la conexión si no está activa o si fue cerrada."""
        if self._conexion is None or self._conexion.closed:
            try:
                self._conexion = psycopg2.connect(Config.get_dsn())
                self._conexion.autocommit = False
                print("[DB] Conexión establecida correctamente.")
            except psycopg2.OperationalError as e:
                print(f"[DB ERROR] No se pudo conectar: {e}")
                raise
        return self._conexion

    def obtener_conexion(self):
        """Devuelve la conexión activa, reconectando si es necesario."""
        return self.conectar()

    def cerrar(self):
        """Cierra la conexión de forma segura."""
        if self._conexion and not self._conexion.closed:
            self._conexion.close()
            print("[DB] Conexión cerrada.")
