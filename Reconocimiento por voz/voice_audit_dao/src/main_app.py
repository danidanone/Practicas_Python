import warnings
warnings.filterwarnings("ignore")

import threading
import tkinter as tk
from tkinter import ttk, messagebox
import json

from conexion_db import ConexionDB
from auth_dao import AuthDAO
from voice_service import VoiceService


# ─── Paleta de colores ───────────────────────────────────────────────────────
BG_DARK    = "#0f1117"
BG_CARD    = "#1a1d2e"
BG_INPUT   = "#252840"
ACCENT     = "#6c63ff"
ACCENT2    = "#a78bfa"
SUCCESS    = "#22c55e"
DANGER     = "#ef4444"
WARNING    = "#f59e0b"
TEXT_MAIN  = "#e2e8f0"
TEXT_MUTED = "#94a3b8"
FONT_MAIN  = ("Segoe UI", 10)
FONT_TITLE = ("Segoe UI", 18, "bold")
FONT_LABEL = ("Segoe UI", 9)
FONT_MONO  = ("Consolas", 9)


class VoiceAuditApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("VoiceAudit Login  |  DAM M6")
        self.geometry("820x680")
        self.resizable(True, True)
        self.configure(bg=BG_DARK)

        self.dao   = AuthDAO()
        self.voice = VoiceService()

        self._build_ui()

    # ─── Construcción de la UI ────────────────────────────────────────────────

    def _build_ui(self):
        # Barra de color superior
        tk.Frame(self, bg=ACCENT, height=4).pack(fill="x")

        # Título
        title_frame = tk.Frame(self, bg=BG_DARK, pady=16)
        title_frame.pack(fill="x")
        tk.Label(title_frame, text="🎙 VoiceAudit Login",
                 font=FONT_TITLE, bg=BG_DARK, fg=ACCENT2).pack()
        tk.Label(title_frame,
                 text="Sistema de autenticación por voz con auditoría JSONB",
                 font=FONT_LABEL, bg=BG_DARK, fg=TEXT_MUTED).pack()

        # Estilos del Notebook
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TNotebook", background=BG_DARK, borderwidth=0)
        style.configure("TNotebook.Tab", background=BG_CARD,
                        foreground=TEXT_MUTED, padding=[16, 8], font=FONT_MAIN)
        style.map("TNotebook.Tab",
                  background=[("selected", ACCENT)],
                  foreground=[("selected", "white")])

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.tab_registro  = tk.Frame(self.notebook, bg=BG_DARK)
        self.tab_login     = tk.Frame(self.notebook, bg=BG_DARK)
        self.tab_auditoria = tk.Frame(self.notebook, bg=BG_DARK)

        self.notebook.add(self.tab_registro,  text="  📝 Registro  ")
        self.notebook.add(self.tab_login,     text="  🔐 Login  ")
        self.notebook.add(self.tab_auditoria, text="  🔍 Auditoría  ")

        self._build_tab_registro()
        self._build_tab_login()
        self._build_tab_auditoria()

    # ─── TAB REGISTRO ─────────────────────────────────────────────────────────

    def _build_tab_registro(self):
        card = self._card(self.tab_registro)

        tk.Label(card, text="Nombre de usuario", font=FONT_LABEL,
                 bg=BG_CARD, fg=TEXT_MUTED).pack(anchor="w", pady=(0, 4))
        self.reg_username = self._entry(card)

        tk.Label(card, text="Frase de paso (se capturará por voz)",
                 font=FONT_LABEL, bg=BG_CARD, fg=TEXT_MUTED).pack(anchor="w", pady=(12, 4))

        # Área de resultado de voz
        self.reg_frase_var = tk.StringVar(value="— Pulsa el botón para grabar —")
        tk.Label(card, textvariable=self.reg_frase_var,
                 font=("Segoe UI", 11, "italic"),
                 bg=BG_INPUT, fg=ACCENT2,
                 wraplength=480, justify="center",
                 pady=14, padx=10).pack(fill="x", pady=(0, 8))

        # Confianza
        self.reg_confianza_var = tk.StringVar(value="")
        tk.Label(card, textvariable=self.reg_confianza_var,
                 font=FONT_LABEL, bg=BG_CARD, fg=TEXT_MUTED).pack()

        btn_frame = tk.Frame(card, bg=BG_CARD)
        btn_frame.pack(pady=16)
        self._btn(btn_frame, "🎙 Grabar frase", ACCENT,
                  self._grabar_registro).pack(side="left", padx=6)
        self._btn(btn_frame, "✅ Confirmar registro", SUCCESS,
                  self._confirmar_registro).pack(side="left", padx=6)

        # Estado
        self.reg_estado_var = tk.StringVar(value="")
        self.reg_estado_lbl = tk.Label(card, textvariable=self.reg_estado_var,
                                       font=FONT_MAIN, bg=BG_CARD, fg=TEXT_MAIN,
                                       wraplength=480)
        self.reg_estado_lbl.pack(pady=(8, 0))

        self._voz_info_registro = None

    def _grabar_registro(self):
        self.reg_frase_var.set("⏳ Escuchando... habla ahora")
        self.reg_confianza_var.set("")
        self.reg_estado_var.set("")
        self.update()
        threading.Thread(target=self._hilo_grabar_registro, daemon=True).start()

    def _hilo_grabar_registro(self):
        info = self.voice.capturar_frase()
        self._voz_info_registro = info
        if info["error"]:
            self.reg_frase_var.set(f"❌ Error: {info['error']}")
            self.reg_estado_var.set("Grabación fallida. Inténtalo de nuevo.")
            self.reg_estado_lbl.configure(fg=DANGER)
        else:
            self.reg_frase_var.set(f'"{info["texto"]}"')
            conf = info["confianza"]
            self.reg_confianza_var.set(
                f"Confianza IA: {conf:.0%}" if conf else "Confianza: N/D"
            )
            color = SUCCESS if conf and conf >= 0.6 else WARNING
            self.reg_estado_lbl.configure(fg=color)
            self.reg_estado_var.set("Frase capturada. Pulsa 'Confirmar registro' para guardar.")

    def _confirmar_registro(self):
        username = self.reg_username.get().strip()
        if not username:
            messagebox.showwarning("Campo vacío", "Introduce un nombre de usuario.")
            return
        if not self._voz_info_registro:
            messagebox.showwarning("Sin frase", "Graba primero tu frase de paso.")
            return
        if self._voz_info_registro.get("error"):
            messagebox.showerror("Error de voz", "La grabación falló. Inténtalo de nuevo.")
            return

        frase = self._voz_info_registro["texto"]
        resultado = self.dao.registrar_usuario(username, frase, self._voz_info_registro)

        color = SUCCESS if resultado["ok"] else DANGER
        self.reg_estado_var.set(resultado["mensaje"])
        self.reg_estado_lbl.configure(fg=color)

        if resultado["ok"]:
            self._voz_info_registro = None
            self.reg_frase_var.set("— Pulsa el botón para grabar —")
            self.reg_confianza_var.set("")
            self.reg_username.delete(0, tk.END)

    # ─── TAB LOGIN ────────────────────────────────────────────────────────────

    def _build_tab_login(self):
        card = self._card(self.tab_login)

        tk.Label(card, text="Nombre de usuario", font=FONT_LABEL,
                 bg=BG_CARD, fg=TEXT_MUTED).pack(anchor="w", pady=(0, 4))
        self.login_username = self._entry(card)

        tk.Label(card, text="Frase reconocida",
                 font=FONT_LABEL, bg=BG_CARD, fg=TEXT_MUTED).pack(anchor="w", pady=(12, 4))

        self.login_frase_var = tk.StringVar(value="— Pulsa el botón para autenticarte —")
        tk.Label(card, textvariable=self.login_frase_var,
                 font=("Segoe UI", 11, "italic"),
                 bg=BG_INPUT, fg=ACCENT2,
                 wraplength=480, justify="center",
                 pady=14, padx=10).pack(fill="x", pady=(0, 8))

        self.login_confianza_var = tk.StringVar(value="")
        tk.Label(card, textvariable=self.login_confianza_var,
                 font=FONT_LABEL, bg=BG_CARD, fg=TEXT_MUTED).pack()

        btn_frame = tk.Frame(card, bg=BG_CARD)
        btn_frame.pack(pady=16)
        self._btn(btn_frame, "🎙 Autenticar por voz", ACCENT,
                  self._autenticar_voz).pack(side="left", padx=6)

        # Estado del login  ← este bloque faltaba / estaba truncado en el original
        self.login_estado_var = tk.StringVar(value="")
        self.login_estado_lbl = tk.Label(card, textvariable=self.login_estado_var,
                                         font=("Segoe UI", 12, "bold"),
                                         bg=BG_CARD, fg=TEXT_MAIN,
                                         wraplength=480)
        self.login_estado_lbl.pack(pady=(8, 0))

        # Barra de progreso de confianza
        tk.Label(card, text="Nivel de confianza IA",
                 font=FONT_LABEL, bg=BG_CARD, fg=TEXT_MUTED).pack(anchor="w", pady=(16, 2))
        self.conf_bar = ttk.Progressbar(card, length=480, maximum=100)
        self.conf_bar.pack(fill="x")

        self._voz_info_login = None

    def _autenticar_voz(self):
        username = self.login_username.get().strip()
        if not username:
            messagebox.showwarning("Campo vacío", "Introduce tu nombre de usuario.")
            return
        self.login_frase_var.set("⏳ Escuchando... habla ahora")
        self.login_confianza_var.set("")
        self.login_estado_var.set("")
        self.conf_bar["value"] = 0
        self.update()
        threading.Thread(target=self._hilo_autenticar, args=(username,), daemon=True).start()

    def _hilo_autenticar(self, username: str):
        info = self.voice.capturar_frase()
        self._voz_info_login = info

        if info["error"]:
            self.login_frase_var.set(f"❌ Error: {info['error']}")
            self.login_estado_var.set(f"Error de captura: {info['error']}")
            self.login_estado_lbl.configure(fg=DANGER)
            # Registrar error en log aunque no haya frase
            self.dao.autenticar(username, "", info)
            return

        frase = info["texto"]
        self.login_frase_var.set(f'"{frase}"')
        conf = info["confianza"] or 0.0
        self.login_confianza_var.set(
            f"Confianza IA: {conf:.0%}  |  Latencia: {info.get('latencia', 'N/D')}"
        )
        self.conf_bar["value"] = int(conf * 100)

        resultado = self.dao.autenticar(username, frase, info)

        if resultado["ok"]:
            self.login_estado_var.set(f"✅ {resultado['mensaje']}")
            self.login_estado_lbl.configure(fg=SUCCESS)
        elif resultado.get("bloqueado"):
            self.login_estado_var.set(f"🔒 {resultado['mensaje']}")
            self.login_estado_lbl.configure(fg=DANGER)
        else:
            self.login_estado_var.set(f"❌ {resultado['mensaje']}")
            self.login_estado_lbl.configure(fg=WARNING)

    # ─── TAB AUDITORÍA ────────────────────────────────────────────────────────

    def _build_tab_auditoria(self):
        card = self._card(self.tab_auditoria, expand=True)

        btn_frame = tk.Frame(card, bg=BG_CARD)
        btn_frame.pack(fill="x", pady=(0, 12))
        self._btn(btn_frame,
                  "🔍 Ver logs críticos (FAIL / ERROR / Confianza < 60%)",
                  DANGER, self._cargar_logs_criticos).pack(side="left", padx=(0, 8))
        self._btn(btn_frame, "📋 Ver todos los logs",
                  ACCENT, self._cargar_todos_logs).pack(side="left")

        # Tabla
        cols = ("Usuario", "Fecha", "Status", "Confianza", "Frase intentada", "Motivo")
        self.tree = ttk.Treeview(card, columns=cols, show="headings", height=16)

        style = ttk.Style()
        style.configure("Treeview",
                        background=BG_INPUT, foreground=TEXT_MAIN,
                        fieldbackground=BG_INPUT, rowheight=26, font=FONT_MONO)
        style.configure("Treeview.Heading",
                        background=BG_CARD, foreground=ACCENT2,
                        font=("Segoe UI", 9, "bold"))
        style.map("Treeview", background=[("selected", ACCENT)])

        anchos = [100, 140, 70, 80, 160, 120]
        for col, ancho in zip(cols, anchos):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=ancho, anchor="center")

        scrollbar = ttk.Scrollbar(card, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Contador de registros
        self.audit_count_var = tk.StringVar(value="")
        tk.Label(self.tab_auditoria, textvariable=self.audit_count_var,
                 font=FONT_LABEL, bg=BG_DARK, fg=TEXT_MUTED).pack(pady=4)

    def _cargar_logs_criticos(self):
        logs = self.dao.obtener_logs_criticos()
        self._poblar_tabla(logs)
        self.audit_count_var.set(f"{len(logs)} registros críticos encontrados")

    def _cargar_todos_logs(self):
        filas = self.dao.obtener_todos_los_logs()
        logs = []
        for username, fecha, resultado_json in filas:
            d = resultado_json if isinstance(resultado_json, dict) else json.loads(resultado_json)
            logs.append({
                "username": username,
                "fecha_intento": fecha,
                "status": d.get("status", ""),
                "confianza": d.get("confianza"),
                "frase_intentada": d.get("frase_intentada", ""),
                "motivo": d.get("motivo", ""),
            })
        self._poblar_tabla(logs)
        self.audit_count_var.set(f"{len(logs)} registros totales")

    def _poblar_tabla(self, logs: list):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for log in logs:
            status = log.get("status", "")
            conf   = log.get("confianza")
            conf_str = f"{float(conf):.0%}" if conf is not None else "—"
            fecha  = log.get("fecha_intento", "")
            if hasattr(fecha, "strftime"):
                fecha = fecha.strftime("%Y-%m-%d %H:%M:%S")

            if status == "FAIL":
                tag = "fail"
            elif status == "ERROR":
                tag = "error"
            elif conf and float(conf) < 0.6:
                tag = "warn"
            else:
                tag = "ok"

            self.tree.insert("", "end", values=(
                log.get("username", ""),
                fecha,
                status,
                conf_str,
                log.get("frase_intentada") or "—",
                log.get("motivo") or "—",
            ), tags=(tag,))

        self.tree.tag_configure("ok",    background="#1a2e1a", foreground=SUCCESS)
        self.tree.tag_configure("fail",  background="#2e1a1a", foreground=DANGER)
        self.tree.tag_configure("error", background="#2e2a1a", foreground=WARNING)
        self.tree.tag_configure("warn",  background="#2e2a1a", foreground=WARNING)

    # ─── Helpers de UI ────────────────────────────────────────────────────────

    def _card(self, parent, expand=False):
        outer = tk.Frame(parent, bg=BG_DARK)
        outer.pack(fill="both", expand=expand, padx=30, pady=20)
        card = tk.Frame(outer, bg=BG_CARD, padx=28, pady=24, relief="flat", bd=0)
        card.pack(fill="both", expand=expand)
        return card

    def _entry(self, parent) -> tk.Entry:
        e = tk.Entry(parent, font=("Segoe UI", 12),
                     bg=BG_INPUT, fg=TEXT_MAIN,
                     insertbackground=TEXT_MAIN,
                     relief="flat", bd=0)
        e.pack(fill="x", ipady=8, pady=(0, 4))
        return e

    def _btn(self, parent, text, color, command) -> tk.Button:
        return tk.Button(
            parent, text=text, command=command,
            bg=color, fg="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat", bd=0,
            padx=16, pady=8,
            cursor="hand2",
            activebackground=ACCENT2,
            activeforeground="white",
        )


# ─── Punto de entrada ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    db = ConexionDB()
    try:
        db.conectar()
    except Exception as e:
        import tkinter.messagebox as mb
        root = tk.Tk()
        root.withdraw()
        mb.showerror(
            "Error de conexión",
            f"No se pudo conectar a PostgreSQL.\n\n{e}\n\n"
            "Comprueba el archivo .env y que el servidor esté activo."
        )
        root.destroy()
        exit(1)

    app = VoiceAuditApp()
    app.mainloop()
    db.cerrar()