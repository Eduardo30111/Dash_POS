#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Archivo: login.py
Pantalla de inicio de sesión principal para VmPOS.
"""

import tkinter as tk
from tkinter import messagebox
from pantalla_carga import mostrar_carga
from menu_inicio import iniciar_dashboard

# Base de datos de usuarios simulada
# En un sistema real, esto se obtendría de una base de datos segura
USERS_DB = {
    'admin': {
        'password': 'admin',
        'usuario': 'Eduardo',
        'permisos': 'admin'
    },
    'vendedor': {
        'password': '123',
        'usuario': 'Andres',
        'permisos': 'vendedor'
    }
}

class VmPOSLogin(tk.Tk):
    """
    Clase para la ventana de inicio de sesión.
    """
    def __init__(self):
        super().__init__()
        self.title("VmPOS - Iniciar Sesión")
        self.geometry("400x300")
        self.resizable(False, False)
        self.configure(bg="#ffeaa7")
        self.update_idletasks()

        # Centrar ventana
        x = (self.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.winfo_screenheight() // 2) - (300 // 2)
        self.geometry(f"400x300+{x}+{y}")
        
        self.main_frame = tk.Frame(self, bg="#ffeaa7")
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        self._create_widgets()

    def _create_widgets(self):
        """Crea y empaqueta los widgets de la interfaz de inicio de sesión."""
        # Título
        tk.Label(self.main_frame, text="VmPOS", font=("Segoe UI", 24, "bold"), bg="#ffeaa7", fg="#e84393").pack(pady=(0, 5))
        tk.Label(self.main_frame, text="Centro de Copiado & Papelería", font=("Segoe UI", 10), bg="#ffeaa7", fg="#636e72").pack(pady=(0, 20))

        # Campo de usuario
        tk.Label(self.main_frame, text="Usuario:", font=("Segoe UI", 11), bg="#ffeaa7", fg="#2d3436").pack(anchor="w")
        self.user_entry = tk.Entry(self.main_frame, font=("Segoe UI", 11), relief="flat")
        self.user_entry.pack(fill="x", ipady=5, pady=(0, 10))
        self.user_entry.insert(0, "admin") # Rellenar para pruebas

        # Campo de contraseña
        tk.Label(self.main_frame, text="Contraseña:", font=("Segoe UI", 11), bg="#ffeaa7", fg="#2d3436").pack(anchor="w")
        self.pass_entry = tk.Entry(self.main_frame, font=("Segoe UI", 11), show="•", relief="flat")
        self.pass_entry.pack(fill="x", ipady=5, pady=(0, 15))
        self.pass_entry.insert(0, "admin") # Rellenar para pruebas

        # Botón de inicio de sesión
        login_btn = tk.Button(self.main_frame, text="Iniciar Sesión", font=("Segoe UI", 12, "bold"), 
                              bg="#e84393", fg="white", bd=0, relief="flat", padx=20, pady=10, 
                              cursor="hand2", command=self._login)
        login_btn.pack(fill="x")

        # Vincular la tecla Enter para el inicio de sesión
        self.bind('<Return>', lambda event=None: self._login())

    def _login(self):
        """
        Verifica las credenciales y, si son válidas, inicia el dashboard.
        """
        usuario = self.user_entry.get().lower()
        password = self.pass_entry.get()

        if usuario in USERS_DB and USERS_DB[usuario]['password'] == password:
            # Autenticación exitosa
            user_data = USERS_DB[usuario]
            
            # Cierra la ventana de login
            self.destroy()

            # Muestra la pantalla de carga y luego el dashboard
            # Se usa el diccionario de usuario para pasar toda la información necesaria.
            # Además se pasa la ventana de carga para poder destruirla después.
            user_data['ventana_carga'] = mostrar_carga(nombre=user_data['usuario'], usuario_info=user_data)
            iniciar_dashboard(user_data['usuario'], user_data)

        else:
            # Autenticación fallida
            messagebox.showerror("Error de Autenticación", "Usuario o contraseña incorrectos.")

if __name__ == "__main__":
    app = VmPOSLogin()
    app.mainloop()
