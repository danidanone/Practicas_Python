from dominio.alumno import Alumno
from servicios.alumnos_matriculados import AlumnosMatriculados

def menu():
    print("=== GESTIÓN DE MATRÍCULAS ===")
    print("1) Matricular alumno")
    print("2) Listar alumnos")
    print("3) Eliminar archivo de alumnos")
    print("4) Salir")

def main():
    while True:
        menu()
        opcion = input("Elige una opción (1-4): ").strip()
        if opcion == "1":
            nombre = input("Nombre del alumno a matricular: ").strip()
            try:
                alumno = Alumno(nombre)
                AlumnosMatriculados.matricular_alumno(alumno)
                print(f"Alumno '{alumno}' matriculado correctamente.\n")
            except (TypeError, ValueError) as e:
                print(f"Error: {e}\n")
            except RuntimeError as e:
                print(f"Error de E/S: {e}\n")

        elif opcion == "2":
            try:
                lista = AlumnosMatriculados.listar_alumnos()
                if not lista:
                    print("No hay alumnos matriculados.\n")
                else:
                    print("Alumnos matriculados:")
                    for i, al in enumerate(lista, start=1):
                        print(f"{i}. {al}")
                    print()
            except RuntimeError as e:
                print(f"Error de E/S: {e}\n")

        elif opcion == "3":
            confirm = input("¿Estás seguro de eliminar el archivo? (s/n): ").strip().lower()
            if confirm == "s":
                try:
                    eliminado = AlumnosMatriculados.eliminar_alumnos()
                    if eliminado:
                        print("Archivo eliminado correctamente.\n")
                    else:
                        print("No existe archivo para eliminar.\n")
                except RuntimeError as e:
                    print(f"Error de E/S: {e}\n")
            else:
                print("Operación cancelada.\n")

        elif opcion == "4":
            print("Saliendo. ¡Hasta luego!")
            break
        else:
            print("Opción inválida. Intenta de nuevo.\n")

if __name__ == "__main__":
    main()
