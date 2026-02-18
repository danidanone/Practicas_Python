"""
auth_dao.py - Patrón DAO (Data Access Object)
Responsabilidad: Desacoplar la lógica de negocio del acceso a datos.
Gestiona todas las consultas SQL y el manejo de JSONB.
"""
import json
from datetime import datetime, timedelta
from conexion_db import ConexionDB

# Número máximo de intentos fallidos antes de bloquear
MAX_INTENTOS = 3
# Minutos de bloqueo tras agotar los intentos
MINUTOS_BLOQUEO = 5


class AuthDAO:
    """
    DAO que gestiona usuarios y logs de acceso con JSONB.
    Si cambia el esquema del JSON, solo se modifica este archivo.
    """

    def __init__(self):
        self._db = ConexionDB()

    def _get_conn(self):
        return self._db.obtener_conexion()

    # ─────────────────────────────────────────────
    # REGISTRO
    # ─────────────────────────────────────────────

    def registrar_usuario(self, username: str, passphrase: str, voz_info: dict) -> dict:
        """
        Inserta un nuevo usuario y su log de registro inicial.
        Returns: dict con 'ok' (bool) y 'mensaje' (str)
        """
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                # Verificar si ya existe
                cur.execute(
                    "SELECT id FROM usuarios_voz WHERE username = %s", (username,)
                )
                if cur.fetchone():
                    return {"ok": False, "mensaje": f"El usuario '{username}' ya existe."}

                # Insertar usuario
                cur.execute(
                    """
                    INSERT INTO usuarios_voz (username, passphrase_text)
                    VALUES (%s, %s) RETURNING id
                    """,
                    (username, passphrase),
                )
                usuario_id = cur.fetchone()[0]

                # Log de registro con JSONB
                if voz_info.get("error"):
                    log_json = {
                        "status": "ERROR",
                        "motivo": voz_info["error"],
                        "hardware_db": voz_info.get("hardware_db"),
                    }
                else:
                    log_json = {
                        "status": "REGISTRO",
                        "confianza": voz_info.get("confianza"),
                        "latencia": voz_info.get("latencia"),
                    }

                cur.execute(
                    """
                    INSERT INTO log_accesos_voz (usuario_id, resultado_json)
                    VALUES (%s, %s)
                    """,
                    (usuario_id, json.dumps(log_json)),
                )
                conn.commit()
                return {"ok": True, "mensaje": f"Usuario '{username}' registrado correctamente."}

        except Exception as e:
            conn.rollback()
            return {"ok": False, "mensaje": f"Error en BD: {e}"}

    # ─────────────────────────────────────────────
    # LOGIN
    # ─────────────────────────────────────────────

    def autenticar(self, username: str, frase_intentada: str, voz_info: dict) -> dict:
        """
        Valida la frase de paso del usuario y gestiona bloqueos.
        Returns: dict con 'ok' (bool), 'mensaje' (str), 'bloqueado' (bool)
        """
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, passphrase_text, intentos_fallidos, bloqueado_hasta
                    FROM usuarios_voz WHERE username = %s
                    """,
                    (username,),
                )
                fila = cur.fetchone()
                if not fila:
                    return {"ok": False, "mensaje": "Usuario no encontrado.", "bloqueado": False}

                uid, passphrase, intentos, bloqueado_hasta = fila

                # Comprobar bloqueo activo
                if bloqueado_hasta and datetime.now() < bloqueado_hasta:
                    restante = int((bloqueado_hasta - datetime.now()).total_seconds() / 60) + 1
                    return {
                        "ok": False,
                        "mensaje": f"Usuario bloqueado. Intenta en {restante} min.",
                        "bloqueado": True,
                    }

                # Comparar frase (case-insensitive, strip)
                acierto = frase_intentada.strip().lower() == passphrase.strip().lower()

                if acierto:
                    # Resetear intentos fallidos
                    cur.execute(
                        "UPDATE usuarios_voz SET intentos_fallidos=0, bloqueado_hasta=NULL WHERE id=%s",
                        (uid,),
                    )
                    log_json = {
                        "status": "OK",
                        "confianza": voz_info.get("confianza"),
                        "latencia": voz_info.get("latencia"),
                    }
                    cur.execute(
                        "INSERT INTO log_accesos_voz (usuario_id, resultado_json) VALUES (%s, %s)",
                        (uid, json.dumps(log_json)),
                    )
                    conn.commit()
                    return {"ok": True, "mensaje": "Acceso concedido ✓", "bloqueado": False}

                else:
                    # Incrementar intentos
                    nuevos_intentos = intentos + 1
                    intentos_restantes = MAX_INTENTOS - nuevos_intentos
                    nuevo_bloqueo = None

                    if intentos_restantes <= 0:
                        nuevo_bloqueo = datetime.now() + timedelta(minutes=MINUTOS_BLOQUEO)
                        cur.execute(
                            "UPDATE usuarios_voz SET intentos_fallidos=%s, bloqueado_hasta=%s WHERE id=%s",
                            (nuevos_intentos, nuevo_bloqueo, uid),
                        )
                        log_json = {
                            "status": "FAIL",
                            "frase_intentada": frase_intentada,
                            "intentos_restantes": 0,
                            "bloqueado_hasta": nuevo_bloqueo.isoformat(),
                        }
                        msg = f"Acceso denegado. Usuario bloqueado {MINUTOS_BLOQUEO} minutos."
                    else:
                        cur.execute(
                            "UPDATE usuarios_voz SET intentos_fallidos=%s WHERE id=%s",
                            (nuevos_intentos, uid),
                        )
                        log_json = {
                            "status": "FAIL",
                            "frase_intentada": frase_intentada,
                            "intentos_restantes": intentos_restantes,
                        }
                        msg = f"Frase incorrecta. Intentos restantes: {intentos_restantes}"

                    cur.execute(
                        "INSERT INTO log_accesos_voz (usuario_id, resultado_json) VALUES (%s, %s)",
                        (uid, json.dumps(log_json)),
                    )
                    conn.commit()
                    return {"ok": False, "mensaje": msg, "bloqueado": nuevo_bloqueo is not None}

        except Exception as e:
            conn.rollback()
            return {"ok": False, "mensaje": f"Error en BD: {e}", "bloqueado": False}

    # ─────────────────────────────────────────────
    # AUDITORÍA
    # ─────────────────────────────────────────────

    def obtener_logs_criticos(self) -> list:
        """
        Consulta avanzada que 'bucea' dentro del JSONB para encontrar
        registros críticos: fallos o confianza baja (< 0.6).
        """
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        u.username,
                        l.fecha_intento,
                        l.resultado_json->>'status' AS status,
                        l.resultado_json->>'confianza' AS confianza,
                        l.resultado_json->>'frase_intentada' AS frase_intentada,
                        l.resultado_json->>'intentos_restantes' AS intentos_restantes,
                        l.resultado_json->>'motivo' AS motivo
                    FROM log_accesos_voz l
                    JOIN usuarios_voz u ON l.usuario_id = u.id
                    WHERE l.resultado_json->>'status' = 'FAIL'
                       OR l.resultado_json->>'status' = 'ERROR'
                       OR (
                            l.resultado_json->>'confianza' IS NOT NULL
                            AND (l.resultado_json->>'confianza')::float < 0.6
                          )
                    ORDER BY l.fecha_intento DESC
                    """
                )
                columnas = [desc[0] for desc in cur.description]
                return [dict(zip(columnas, fila)) for fila in cur.fetchall()]
        except Exception as e:
            print(f"[DAO ERROR] {e}")
            return []

    def obtener_todos_los_logs(self) -> list:
        """Devuelve todos los logs de acceso para mostrar en el panel."""
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT u.username, l.fecha_intento, l.resultado_json
                    FROM log_accesos_voz l
                    JOIN usuarios_voz u ON l.usuario_id = u.id
                    ORDER BY l.fecha_intento DESC
                    LIMIT 100
                    """
                )
                return cur.fetchall()
        except Exception as e:
            print(f"[DAO ERROR] {e}")
            return []
