import csv

# Archivos de entrada
fichero_uf1 = 'notas_alumnos_UF1.csv'
fichero_uf2 = 'notas_alumnos_UF2.csv'
fichero_salida = 'notas_alumnos.csv'

# --- Leer las notas de UF1 ---
notas_uf1 = {}
with open(fichero_uf1, 'r', encoding='utf-8') as f1:
    lector1 = csv.DictReader(f1, delimiter=';')
    for fila in lector1:
        notas_uf1[fila['Id']] = {
            'Nombre': fila['Nombre'],
            'Apellido': fila['Apellido'],
            'Nota_UF1': fila['Nota']
        }

# --- Leer las notas de UF2 y combinar ---
with open(fichero_uf2, 'r', encoding='utf-8') as f2:
    lector2 = csv.DictReader(f2, delimiter=';')
    for fila in lector2:
        id_alumno = fila['Id']
        if id_alumno in notas_uf1:
            notas_uf1[id_alumno]['Nota_UF2'] = fila['Nota']
        else:
            notas_uf1[id_alumno] = {
                'Nombre': fila['Nombre'],
                'Apellido': fila['Apellido'],
                'Nota_UF1': '',
                'Nota_UF2': fila['Nota']
            }

# --- Escribir el fichero combinado ---
with open(fichero_salida, 'w', newline='', encoding='utf-8') as salida:
    campos = ['Id', 'Nombre', 'Apellido', 'Nota_UF1', 'Nota_UF2']
    escritor = csv.DictWriter(salida, fieldnames=campos, delimiter=';')
    escritor.writeheader()

    for id_alumno, datos in notas_uf1.items():
        fila = {'Id': id_alumno}
        fila.update(datos)
        escritor.writerow(fila)

print(f"Archivo '{fichero_salida}' generado correctamente.")
