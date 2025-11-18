import tkinter as tk
from tkinter import ttk, messagebox
from xml_utils import cargar_datos_bce

# Cargar datos al inicio
fecha, tasas = cargar_datos_bce()

def convertir():
    try:
        cantidad = float(entry_cantidad.get())
    except:
        messagebox.showerror("Error", "Introduce un número válido")
        return

    origen = combo_origen.get()
    destino = combo_destino.get()

    if origen not in tasas or destino not in tasas:
        messagebox.showerror("Error", "Selecciona monedas válidas")
        return

    tasa_origen = tasas[origen]
    tasa_destino = tasas[destino]

    euros = cantidad / tasa_origen
    resultado = euros * tasa_destino

    label_resultado.config(text=f"Resultado: {resultado:.4f} {destino}")

# Ventana
ventana = tk.Tk()
ventana.title("Conversión de Divisas")

# Cantidad
tk.Label(ventana, text="Cantidad:").pack()
entry_cantidad = tk.Entry(ventana)
entry_cantidad.pack()

# Monedas
monedas = list(tasas.keys())

tk.Label(ventana, text="Moneda Origen:").pack()
combo_origen = ttk.Combobox(ventana, values=monedas)
combo_origen.set("EUR")
combo_origen.pack()

tk.Label(ventana, text="Moneda Destino:").pack()
combo_destino = ttk.Combobox(ventana, values=monedas)
combo_destino.set("USD")
combo_destino.pack()

# Botón
boton = tk.Button(ventana, text="Convertir", command=convertir)
boton.pack()

# Resultado
label_resultado = tk.Label(ventana, text="Resultado:")
label_resultado.pack()

# Fecha de actualización
if fecha:
    tk.Label(ventana, text=f"Datos del BCE — Fecha: {fecha}").pack()
else:
    tk.Label(ventana, text="No se pudo cargar la fecha").pack()

ventana.mainloop()
