class Alumno:
    """
    Representa un alumno con un único atributo: nombre.
    """
    def __init__(self, nombre: str):
        if not isinstance(nombre, str):
            raise TypeError("El nombre debe ser una cadena.")
        nombre = nombre.strip()
        if not nombre:
            raise ValueError("El nombre no puede estar vacío.")
        self.nombre = nombre

    def __str__(self):
        return self.nombre

    def __repr__(self):
        return f"Alumno(nombre={self.nombre!r})"
