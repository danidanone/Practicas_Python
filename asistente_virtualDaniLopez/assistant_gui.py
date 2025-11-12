#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
assistant_gui.py
Asistente (Tkinter) que usa SOLO datos de Yahoo Finance a través de yfinance.
Soporta:
 - Consultar precio spot (ej.: "precio BTC" ó "precio BTC-USD")
 - Comprobar si un ticker devuelve datos en Yahoo (existencia/listado)
 - Consultar precios históricos simples (ej. "historial BTC 7d")
Reglas:
 - NO da consejos de inversión. Solo muestra datos obtenidos desde Yahoo via yfinance.
 - Si la petición no puede resolverse con datos de Yahoo, el asistente lo rechaza.
"""
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox
import json
import re
import traceback
import datetime
import time

# Dependencia: yfinance
import yfinance as yf
import pandas as pd

# --- Funciones que consultan Yahoo via yfinance ---

def normalize_symbol_user_input(symbol_candidate: str):
    """
    Normaliza entradas tipo 'btc', 'btc-usd', 'BTCUSD' -> 'BTC-USD'
    y devuelve la forma que Yahoo usa normalmente (ej. 'BTC-USD').
    """
    s = symbol_candidate.strip().upper()
    # Reemplazar espacios y barras por '-'
    s = s.replace(" ", "").replace("/", "-")
    # si ya contiene '-', devolver
    if "-" in s:
        return s
    # si termina en USD asumimos par crypto-USD
    # allow forms like BTCUSD -> BTC-USD
    m = re.match(r"^([A-Z]{2,6})(USD)$", s)
    if m:
        return f"{m.group(1)}-{m.group(2)}"
    # default: añadir -USD (comportamiento para criptos)
    if len(s) <= 5:
        return f"{s}-USD"
    return s

def get_spot_price_yf(symbol: str):
    """
    Obtiene precio 'spot' (último cierre o precio de mercado actual) con yfinance.
    Devuelve dict con keys: success, price, symbol, source
    """
    sym = normalize_symbol_user_input(symbol)
    try:
        ticker = yf.Ticker(sym)
        # Intentamos obtener precio en tiempo real mediante info['regularMarketPrice']
        info = {}
        try:
            info = ticker.fast_info if hasattr(ticker, "fast_info") else ticker.info
        except Exception:
            # fallback si no existe fast_info
            try:
                info = ticker.info
            except Exception:
                info = {}

        # Try multiple ways to get a price
        price = None
        # fast_info suele tener 'last_price' o 'last_price'
        if isinstance(info, dict):
            for key in ("last_price", "lastPrice", "regularMarketPrice", "currentPrice", "previousClose"):
                if key in info and info.get(key) is not None:
                    price = info.get(key)
                    break

        # fallback: usar history (último cierre)
        if price is None:
            hist = ticker.history(period="1d", interval="1m")
            if not hist.empty:
                # si hay datos intradía tomar la última fila "Close"
                price = float(hist["Close"].iloc[-1])
            else:
                hist2 = ticker.history(period="5d")
                if not hist2.empty:
                    price = float(hist2["Close"].iloc[-1])

        if price is None:
            return {"success": False, "error": "No hay datos de precio para ese ticker en Yahoo (yfinance)."}

        return {"success": True, "symbol": sym, "price": price, "source": "Yahoo Finance (yfinance)"}
    except Exception as e:
        return {"success": False, "error": f"Excepción al consultar yfinance: {e}"}

def ticker_exists_yf(symbol: str):
    """
    Comprueba si yfinance devuelve información útil para el ticker.
    Retorna True si existen datos básicos, False si no.
    """
    sym = normalize_symbol_user_input(symbol)
    try:
        ticker = yf.Ticker(sym)
        # Intentamos recuperar info mínima
        info = {}
        try:
            info = ticker.fast_info if hasattr(ticker, "fast_info") else ticker.info
        except Exception:
            try:
                info = ticker.info
            except Exception:
                info = {}

        # Si info es dict y no está vacío, asumimos que existe
        if isinstance(info, dict) and len(info) > 0:
            # chequeo adicional: si 'regularMarketPrice' o similares están presentes
            for k in ("regularMarketPrice", "lastPrice", "previousClose", "symbol"):
                if k in info and info.get(k) is not None:
                    return True
            # aún así, si info contiene keys, considerarlo existente
            return True

        # fallback: comprobar si history devuelve filas
        hist = ticker.history(period="5d")
        if not hist.empty:
            return True

        return False
    except Exception:
        return False

def get_history_yf(symbol: str, days: int=7):
    """
    Obtiene historial de precios de los últimos 'days' días (Close).
    Devuelve dict con success y dataframe convertido a lista de tuplas (fecha, close).
    """
    sym = normalize_symbol_user_input(symbol)
    try:
        ticker = yf.Ticker(sym)
        end = datetime.datetime.utcnow().date()
        start = end - datetime.timedelta(days=days+2)
        hist = ticker.history(start=start.isoformat(), end=end.isoformat())
        if hist.empty:
            return {"success": False, "error": "No hay datos históricos disponibles."}
        # Extraer fecha y cierre
        rows = []
        for idx, row in hist.iterrows():
            # idx -> Timestamp
            rows.append({"date": str(idx.date()), "close": float(row["Close"])})
        return {"success": True, "symbol": sym, "history": rows, "source": "Yahoo Finance (yfinance)"}
    except Exception as e:
        return {"success": False, "error": f"Error al obtener historial: {e}"}

# --- Procesador de texto (reglas simples) ---

def parse_and_answer(user_text: str):
    text = user_text.lower().strip()
    if not text:
        return "Escribe una consulta (ej.: 'precio BTC', 'historial BTC 7d', '¿está listado DOGE?')."

    # Rechazo de peticiones de inversión
    if re.search(r"\b(invertir|en qué tengo que invertir|recomienda|consejo de inversión|comprar|vender)\b", text):
        return ("No doy consejos de inversión. Puedo mostrar datos (precios y historiales) "
                "obtenidos exclusivamente desde Yahoo Finance. Ejemplos: 'precio BTC', 'historial BTC 7d'.")

    # Precio: buscar tokens tipo BTC, BTC-USD, ETH
    m = re.search(r"(precio|cotiz|valor|¿a cuánto|¿cuánto).*?([a-zA-Z]{2,6}(?:-[A-Z]{2,6})?)", user_text, re.IGNORECASE)
    if m:
        # extraer último token válido del input
        tokens = re.findall(r"[A-Za-z]{2,6}(?:-[A-Za-z]{2,6})?", user_text.upper())
        if tokens:
            sym = tokens[-1]
        else:
            # fallback: buscar palabras comunes
            sym = "BTC"
        res = get_spot_price_yf(sym)
        if res.get("success"):
            price = res["price"]
            symbol = res["symbol"]
            return f"Precio (Yahoo) para {symbol}: {price} (fuente: Yahoo Finance vía yfinance)."
        else:
            return f"Error al obtener precio desde Yahoo: {res.get('error')}"

    # Historial: e.g. "historial BTC 7d" or "historial ETH 30d"
    m2 = re.search(r"(historial|historia|histórico).*?([A-Za-z]{2,6}(?:-[A-Za-z]{2,6})?)\s*(\d+)?\s*(d|days|dias)?", user_text, re.IGNORECASE)
    if m2:
        sym = m2.group(2).upper()
        days = int(m2.group(3)) if m2.group(3) else 7
        res = get_history_yf(sym, days=days)
        if res.get("success"):
            rows = res["history"]
            # Construir pequeño resumen + 5 primeras/últimas entradas
            summary_lines = [f"Historial {sym} (últimos {days} días) — fuente: Yahoo Finance (yfinance):"]
            # mostrar hasta 8 entradas (si hay muchas)
            for r in rows[-min(len(rows), 8):]:
                summary_lines.append(f" - {r['date']}: {r['close']}")
            return "\n".join(summary_lines)
        else:
            return f"No se pudo obtener historial desde Yahoo: {res.get('error')}"

    # Comprobar si ticker existe (listado)
    m3 = re.search(r"(está|listado|listado en yahoo|disponible|¿está).*?([A-Za-z]{2,6})", user_text, re.IGNORECASE)
    if m3:
        sym = m3.group(2).upper()
        exists = ticker_exists_yf(sym)
        if exists:
            return f"{sym} parece estar listado / tener datos en Yahoo Finance (consulta vía yfinance)."
        else:
            return f"No se han encontrado datos para {sym} en Yahoo Finance (yfinance)."

    # Si no entra en casos anteriores, responder de forma orientativa
    return ("No reconozco esa petición. Este asistente responde a consultas sobre precios, historiales o si un ticker "
            "tiene datos en Yahoo Finance (vía la librería yfinance). Ejemplos: 'precio BTC', 'historial BTC 7d', '¿está listado DOGE?'.")

# --- Interfaz gráfica (Tkinter) ---

class CryptoAssistantGUI:
    def __init__(self, root):
        self.root = root
        root.title("Asistente (Yahoo Finance via yfinance)")
        root.geometry("760x540")

        lbl = tk.Label(root, text="Pregunta (ej.: 'precio BTC', 'historial BTC 7d'):", font=("Arial", 11))
        lbl.pack(padx=8, pady=(8,0), anchor="w")

        self.entry = tk.Entry(root, font=("Arial", 12))
        self.entry.pack(fill="x", padx=8, pady=(0,6))
        self.entry.bind("<Return>", self.on_send)

        btn_frame = tk.Frame(root)
        btn_frame.pack(fill="x", padx=8, pady=(0,6))
        send_btn = tk.Button(btn_frame, text="Enviar", command=self.on_send, width=12)
        send_btn.pack(side="left")
        clear_btn = tk.Button(btn_frame, text="Limpiar salida", command=self.clear_output, width=12)
        clear_btn.pack(side="left", padx=(6,0))

        note = ("Nota: todas las respuestas provienen exclusivamente de Yahoo Finance usando la librería yfinance.\n"
                "No se emiten recomendaciones de inversión.")
        note_lbl = tk.Label(root, text=note, font=("Arial", 9), fg="gray")
        note_lbl.pack(padx=8, anchor="w")

        self.output = scrolledtext.ScrolledText(root, wrap=tk.WORD, font=("Arial", 11))
        self.output.pack(fill="both", expand=True, padx=8, pady=8)
        self.output.insert(tk.END, "Bienvenido. Escribe tu consulta y pulsa Enviar.\n")
        self.output.configure(state=tk.DISABLED)

    def append_output(self, text):
        self.output.configure(state=tk.NORMAL)
        self.output.insert(tk.END, text + "\n\n")
        self.output.see(tk.END)
        self.output.configure(state=tk.DISABLED)

    def clear_output(self):
        self.output.configure(state=tk.NORMAL)
        self.output.delete("1.0", tk.END)
        self.output.configure(state=tk.DISABLED)

    def on_send(self, event=None):
        query = self.entry.get().strip()
        if not query:
            messagebox.showinfo("Info", "Escribe una pregunta primero.")
            return
        threading.Thread(target=self.handle_query, args=(query,), daemon=True).start()
        self.entry.delete(0, tk.END)

    def handle_query(self, query):
        self.append_output(f"> {query}")
        try:
            resp = parse_and_answer(query)
            self.append_output(resp)
        except Exception as e:
            tb = traceback.format_exc()
            self.append_output(f"Error interno: {e}\n{tb}")

def main():
    root = tk.Tk()
    app = CryptoAssistantGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
