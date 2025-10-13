import os
from dominio.alumno import Alumno
from typing import List

class AlumnosMatriculados:
    """
    Clase que gestiona el fichero de alumnos matriculados.
    Todos los métodos son estáticos según el diagrama UML.
    """
    # Ruta por defecto del archivo (en la carpeta del proyecto)
    ruta_archivo: str = "alumnos_matriculados.txt"

    @staticmethod
    def matricular_alumno(alumno: Alumno) -> None:
        """
        Añade el nombre del alumno al archivo (una línea por alumno).
        Crea el archivo si no existe.
        """
        if not isinstance(alumno, Alumno):
            raise TypeError("Se esperaba un objeto Alumno.")
        try:
            with open(AlumnosMatriculados.ruta_archivo, "a", encoding="utf-8") as f:
                f.write(f"{alumno.nombre}\n")
        except OSError as e:
            raise RuntimeError(f"No se pudo escribir en el archivo: {e}")

    @staticmethod
    def listar_alumnos() -> List[Alumno]:
        """
        Lee el archivo y devuelve una lista de objetos Alumno.
        Si el archivo no existe, devuelve lista vacía.
        """
        alumnos = []
        if not os.path.exists(AlumnosMatriculados.ruta_archivo):
            return alumnos

        try:
            with open(AlumnosMatriculados.ruta_archivo, "r", encoding="utf-8") as f:
                for linea in f:
                    nombre = linea.strip()
                    if nombre:  # ignorar líneas vacías
                        try:
                            alumnos.append(Alumno(nombre))
                        except ValueError:
                            # Si hay una línea inválida, la saltamos
                            continue
            return alumnos
        except OSError as e:
            raise RuntimeError(f"No se pudo leer el archivo: {e}")

    @staticmethod
    def eliminar_alumnos() -> bool:
        """
        Elimina el archivo con los alumnos. Devuelve True si se eliminó, False si no existía.
        """
        if os.path.exists(AlumnosMatriculados.ruta_archivo):
            try:
                os.remove(AlumnosMatriculados.ruta_archivo)
                return True
            except OSError as e:
                raise RuntimeError(f"No se pudo eliminar el archivo: {e}")
        else:
            return False
