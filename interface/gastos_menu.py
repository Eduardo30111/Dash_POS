import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import sqlite3
import os

# Lista para almacenar gastos en memoria
gastos_registrados = []

def iniciar_gastos():
    ventana = tk.Tk()
    ventana.title("💸 Control de Gastos - VmPOS")
    ventana.geometry("1100x700")
    ventana.resizable(False, False)
    ventana.configure(bg="#FFE4F1")
    
    # Centrar ventana
    ventana.update_idletasks()
    x = (ventana.winfo_screenwidth() // 2) - (550)
    y = (ventana.winfo_screenheight() // 2) - (350)
    ventana.geometry(f"1100x700+{x}+{y}")

    # Variables globales para los campos
    global concepto_var, valor_var, fecha_var, tabla
    concepto_var = tk.StringVar()
    valor_var = tk.StringVar()
    fecha_var = tk.StringVar(value=datetime.now().strftime("%d-%m-%Y"))

    # 🌸 Header principal
    header_frame = tk.Frame(ventana, bg="#FF1493", height=100)
    header_frame.pack(fill="x")
    header_frame.pack_propagate(False)

    header_content = tk.Frame(header_frame, bg="#FF1493")
    header_content.pack(expand=True, fill="both")

    title_container = tk.Frame(header_content, bg="#FF1493")
    title_container.pack(expand=True)

    tk.Label(title_container, text="💸", font=("Segoe UI Emoji", 40), 
             bg="#FF1493", fg="white").pack(side="left", pady=25, padx=(50, 15))
    tk.Label(title_container, text="CONTROL DE GASTOS", font=("Segoe UI", 22, "bold"), 
             bg="#FF1493", fg="white").pack(side="left", pady=30)
    tk.Label(title_container, text="📊", font=("Segoe UI Emoji", 40), 
             bg="#FF1493", fg="white").pack(side="left", pady=25, padx=(15, 50))

    # 🕒 Panel de fecha y hora
    def actualizar_tiempo():
        ahora = datetime.now()
        lbl_fecha.config(text=f"📅 {ahora.strftime('%d-%m-%Y')}")
        lbl_hora.config(text=f"⏰ {ahora.strftime('%H:%M:%S')}")
        fecha_var.set(ahora.strftime("%d-%m-%Y"))  # Actualizar fecha automáticamente
        ventana.after(1000, actualizar_tiempo)

    panel_superior = tk.Frame(ventana, bg="#FFDDEE", relief="raised", bd=2)
    panel_superior.pack(fill="x", pady=5, padx=10)

    time_container = tk.Frame(panel_superior, bg="#FFDDEE")
    time_container.pack(pady=15)

    lbl_fecha = tk.Label(time_container, text="", font=("Segoe UI", 12, "bold"), 
                        bg="#FFDDEE", fg="#C71585")
    lbl_fecha.pack(side="left", padx=20)

    tk.Label(time_container, text="✨", font=("Segoe UI Emoji", 16), 
             bg="#FFDDEE").pack(side="left", padx=10)

    lbl_hora = tk.Label(time_container, text="", font=("Segoe UI", 12, "bold"), 
                       bg="#FFDDEE", fg="#C71585")
    lbl_hora.pack(side="left", padx=20)

    actualizar_tiempo()

    # 💖 Panel de estadísticas rápidas
    stats_frame = tk.Frame(ventana, bg="#FFE4F1")
    stats_frame.pack(fill="x", pady=15, padx=10)

    stats_container = tk.Frame(stats_frame, bg="#FFE4F1")
    stats_container.pack()

    # Calcular estadísticas
    def calcular_estadisticas():
        total_gastos = sum(float(gasto.get('valor', 0)) for gasto in gastos_registrados)
        gastos_hoy = len([g for g in gastos_registrados 
                         if g.get('fecha') == datetime.now().strftime("%d-%m-%Y")])
        return total_gastos, gastos_hoy, len(gastos_registrados)

    total_gastos, gastos_hoy, total_registros = calcular_estadisticas()

    stats_data = [
        ("💰", "Total Gastos", f"${total_gastos:,.0f}", "#FF6B6B"),
        ("📅", "Gastos Hoy", str(gastos_hoy), "#4ECDC4"),
        ("📋", "Total Registros", str(total_registros), "#45B7D1"),
        ("📊", "Promedio Diario", f"${total_gastos/max(1, total_registros):,.0f}", "#96CEB4")
    ]

    for i, (icono, titulo, valor, color) in enumerate(stats_data):
        card = tk.Frame(stats_container, bg="white", relief="raised", bd=2, width=200, height=100)
        card.pack(side="left", padx=15, pady=5)
        card.pack_propagate(False)

        card_header = tk.Frame(card, bg=color, height=25)
        card_header.pack(fill="x")

        card_content = tk.Frame(card, bg="white")
        card_content.pack(fill="both", expand=True, padx=10, pady=10)

        tk.Label(card_content, text=icono, font=("Segoe UI Emoji", 20), bg="white").pack()
        tk.Label(card_content, text=titulo, font=("Segoe UI", 9, "bold"), 
                bg="white", fg="#666").pack()
        tk.Label(card_content, text=valor, font=("Segoe UI", 12, "bold"), 
                bg="white", fg=color).pack()

    # 🎀 Panel de formulario
    form_frame = tk.Frame(ventana, bg="#FFC0CB", relief="raised", bd=2)
    form_frame.pack(fill="x", pady=15, padx=10)

    tk.Label(form_frame, text="✏️ Registrar Nuevo Gasto", font=("Segoe UI", 14, "bold"), 
             bg="#FFC0CB", fg="#8B0054").pack(pady=15)

    # Contenedor del formulario
    form_container = tk.Frame(form_frame, bg="#FFC0CB")
    form_container.pack(pady=10, padx=30)

    # Primera fila - Concepto y Valor
    row1 = tk.Frame(form_container, bg="#FFC0CB")
    row1.pack(fill="x", pady=10)

    tk.Label(row1, text="📝 Concepto:", font=("Segoe UI", 11, "bold"), 
             bg="#FFC0CB", fg="#8B0054").pack(side="left", padx=(0, 10))
    concepto_entry = tk.Entry(row1, textvariable=concepto_var, font=("Segoe UI", 11), 
                             width=25, relief="solid", bd=1)
    concepto_entry.pack(side="left", padx=(0, 30))

    tk.Label(row1, text="💰 Valor:", font=("Segoe UI", 11, "bold"), 
             bg="#FFC0CB", fg="#8B0054").pack(side="left", padx=(0, 10))
    valor_entry = tk.Entry(row1, textvariable=valor_var, font=("Segoe UI", 11), 
                          width=20, relief="solid", bd=1)
    valor_entry.pack(side="left")

    # Segunda fila - Fecha y botones
    row2 = tk.Frame(form_container, bg="#FFC0CB")
    row2.pack(fill="x", pady=15)

    tk.Label(row2, text="📅 Fecha:", font=("Segoe UI", 11, "bold"), 
             bg="#FFC0CB", fg="#8B0054").pack(side="left", padx=(0, 10))
    fecha_entry = tk.Entry(row2, textvariable=fecha_var, font=("Segoe UI", 11), 
                          width=15, state="readonly", relief="solid", bd=1)
    fecha_entry.pack(side="left", padx=(0, 50))

    # Botones de acción
    def ingresar_gasto():
        if not concepto_var.get().strip():
            messagebox.showwarning("⚠️ Campo Vacío", "💖 Por favor ingresa un concepto para el gasto")
            concepto_entry.focus()
            return
        
        try:
            valor = float(valor_var.get().replace(',', '').replace('$', ''))
            if valor <= 0:
                raise ValueError("El valor debe ser mayor a 0")
        except ValueError:
            messagebox.showwarning("⚠️ Valor Inválido", "💖 Por favor ingresa un valor numérico válido")
            valor_entry.focus()
            return

        # Agregar gasto
        nuevo_gasto = {
            'concepto': concepto_var.get().strip(),
            'valor': valor,
            'fecha': fecha_var.get(),
            'hora': datetime.now().strftime("%H:%M:%S")
        }
        gastos_registrados.append(nuevo_gasto)
        
        # Actualizar tabla
        actualizar_tabla()
        
        # Limpiar campos
        concepto_var.set("")
        valor_var.set("")
        concepto_entry.focus()
        
        messagebox.showinfo("✅ Éxito", f"💎 Gasto registrado exitosamente!\n\n"
                                      f"📝 Concepto: {nuevo_gasto['concepto']}\n"
                                      f"💰 Valor: ${nuevo_gasto['valor']:,.0f}")

    def eliminar_gasto():
        seleccionado = tabla.focus()
        if not seleccionado:
            messagebox.showwarning("⚠️ Selección", "💖 Por favor selecciona un gasto para eliminar")
            return
        
        respuesta = messagebox.askyesno("🗑️ Confirmar Eliminación", 
                                       "¿Estás segura de que deseas eliminar este gasto?\n\n"
                                       "⚠️ Esta acción no se puede deshacer.")
        if respuesta:
            # Obtener índice del item seleccionado
            valores = tabla.item(seleccionado)["values"]
            # Buscar y eliminar el gasto de la lista
            for i, gasto in enumerate(gastos_registrados):
                if (gasto['concepto'] == valores[1] and 
                    gasto['valor'] == float(valores[2].replace('$', '').replace(',', ''))):
                    del gastos_registrados[i]
                    break
            
            actualizar_tabla()
            messagebox.showinfo("✅ Eliminado", "💖 Gasto eliminado exitosamente")

    def modificar_gasto():
        seleccionado = tabla.focus()
        if not seleccionado:
            messagebox.showwarning("⚠️ Selección", "💖 Por favor selecciona un gasto para modificar")
            return
        
        # Obtener datos del gasto seleccionado
        valores = tabla.item(seleccionado)["values"]
        
        # Ventana de modificación
        ventana_mod = tk.Toplevel(ventana)
        ventana_mod.title("✏️ Modificar Gasto")
        ventana_mod.geometry("450x300")
        ventana_mod.configure(bg="#FFE4F1")
        ventana_mod.resizable(False, False)
        
        # Centrar ventana
        ventana_mod.transient(ventana)
        ventana_mod.grab_set()
        
        tk.Label(ventana_mod, text="✏️ MODIFICAR GASTO", font=("Segoe UI", 16, "bold"), 
                bg="#FFE4F1", fg="#C71585").pack(pady=20)
        
        # Variables para modificación
        mod_concepto = tk.StringVar(value=valores[1])
        mod_valor = tk.StringVar(value=str(float(valores[2].replace('$', '').replace(',', ''))))
        
        # Campos de modificación
        campos_frame = tk.Frame(ventana_mod, bg="#FFE4F1")
        campos_frame.pack(pady=20, padx=30)
        
        tk.Label(campos_frame, text="📝 Concepto:", font=("Segoe UI", 11, "bold"), 
                bg="#FFE4F1", fg="#8B0054").pack(anchor="w", pady=(0, 5))
        tk.Entry(campos_frame, textvariable=mod_concepto, font=("Segoe UI", 11), 
                width=40).pack(fill="x", pady=(0, 15))
        
        tk.Label(campos_frame, text="💰 Valor:", font=("Segoe UI", 11, "bold"), 
                bg="#FFE4F1", fg="#8B0054").pack(anchor="w", pady=(0, 5))
        tk.Entry(campos_frame, textvariable=mod_valor, font=("Segoe UI", 11), 
                width=40).pack(fill="x", pady=(0, 20))
        
        def guardar_cambios():
            try:
                nuevo_valor = float(mod_valor.get().replace(',', '').replace('$', ''))
                if nuevo_valor <= 0:
                    raise ValueError("El valor debe ser mayor a 0")
                
                # Buscar y modificar el gasto
                for gasto in gastos_registrados:
                    if (gasto['concepto'] == valores[1] and 
                        gasto['valor'] == float(valores[2].replace('$', '').replace(',', ''))):
                        gasto['concepto'] = mod_concepto.get().strip()
                        gasto['valor'] = nuevo_valor
                        break
                
                actualizar_tabla()
                ventana_mod.destroy()
                messagebox.showinfo("✅ Modificado", "💖 Gasto modificado exitosamente")
                
            except ValueError as e:
                messagebox.showwarning("⚠️ Error", "💖 Por favor ingresa un valor numérico válido")
        
        # Botones
        btn_frame = tk.Frame(ventana_mod, bg="#FFE4F1")
        btn_frame.pack(pady=20)
        
        tk.Button(btn_frame, text="💾 Guardar Cambios", command=guardar_cambios,
                 bg="#32CD32", fg="white", font=("Segoe UI", 11, "bold"), 
                 padx=20, pady=8, relief="flat", cursor="hand2").pack(side="left", padx=10)
        
        tk.Button(btn_frame, text="❌ Cancelar", command=ventana_mod.destroy,
                 bg="#FF6B6B", fg="white", font=("Segoe UI", 11, "bold"), 
                 padx=20, pady=8, relief="flat", cursor="hand2").pack(side="left", padx=10)

    # Botones de acción
    buttons_frame = tk.Frame(row2, bg="#FFC0CB")
    buttons_frame.pack(side="right")

    btn_ingresar = tk.Button(buttons_frame, text="💎 Ingresar", command=ingresar_gasto,
                            bg="#32CD32", fg="white", font=("Segoe UI", 11, "bold"), 
                            padx=15, pady=8, relief="flat", cursor="hand2")
    btn_ingresar.pack(side="left", padx=5)

    btn_eliminar = tk.Button(buttons_frame, text="🗑️ Eliminar", command=eliminar_gasto,
                            bg="#FF6B6B", fg="white", font=("Segoe UI", 11, "bold"), 
                            padx=15, pady=8, relief="flat", cursor="hand2")
    btn_eliminar.pack(side="left", padx=5)

    btn_modificar = tk.Button(buttons_frame, text="✏️ Modificar", command=modificar_gasto,
                             bg="#4ECDC4", fg="white", font=("Segoe UI", 11, "bold"), 
                             padx=15, pady=8, relief="flat", cursor="hand2")
    btn_modificar.pack(side="left", padx=5)

    # 🔍 Panel de búsqueda
    search_frame = tk.Frame(ventana, bg="#FFE4F1")
    search_frame.pack(fill="x", pady=10, padx=10)

    search_container = tk.Frame(search_frame, bg="#FFE4F1")
    search_container.pack()

    tk.Label(search_container, text="🔍 Buscar:", font=("Segoe UI", 11, "bold"), 
             bg="#FFE4F1", fg="#C71585").pack(side="left", padx=(0, 10))
    
    search_var = tk.StringVar()
    search_entry = tk.Entry(search_container, textvariable=search_var, font=("Segoe UI", 11), 
                           width=35, relief="solid", bd=1)
    search_entry.pack(side="left", padx=(0, 10))

    def buscar_gastos():
        busqueda = search_var.get().lower()
        if not busqueda:
            actualizar_tabla()
            return
        
        # Filtrar gastos
        tabla.delete(*tabla.get_children())
        for i, gasto in enumerate(gastos_registrados):
            if (busqueda in gasto['concepto'].lower() or 
                busqueda in str(gasto['valor']) or 
                busqueda in gasto['fecha']):
                
                tag = "even" if i % 2 == 0 else "odd"
                tabla.insert("", "end", values=(
                    i + 1,
                    gasto['concepto'],
                    f"${gasto['valor']:,.0f}",
                    gasto['fecha'],
                    gasto['hora']
                ), tags=(tag,))

    tk.Button(search_container, text="💖 Buscar", command=buscar_gastos,
             bg="#FF69B4", fg="white", font=("Segoe UI", 10, "bold"), 
             padx=15, pady=5, relief="flat", cursor="hand2").pack(side="left", padx=5)

    tk.Button(search_container, text="🔄 Mostrar Todos", command=lambda: [search_var.set(""), actualizar_tabla()],
             bg="#9370DB", fg="white", font=("Segoe UI", 10, "bold"), 
             padx=15, pady=5, relief="flat", cursor="hand2").pack(side="left", padx=5)

    # 📋 Tabla de gastos
    table_frame = tk.Frame(ventana, bg="#FFE4F1")
    table_frame.pack(fill="both", expand=True, padx=10, pady=10)

    tk.Label(table_frame, text="📋 Lista de Gastos Registrados", font=("Segoe UI", 14, "bold"), 
             bg="#FFE4F1", fg="#C71585").pack(pady=(0, 10))

    # Contenedor de tabla con scrollbars
    table_container = tk.Frame(table_frame, bg="white", relief="raised", bd=2)
    table_container.pack(fill="both", expand=True)

    # Configurar estilo de la tabla
    style = ttk.Style()
    style.configure("Gastos.Treeview", 
                   background="white",
                   foreground="#333",
                   rowheight=35,
                   fieldbackground="white")
    style.configure("Gastos.Treeview.Heading",
                   background="#FF69B4",
                   foreground="white",
                   font=('Segoe UI', 11, 'bold'))

    columnas = ("Id", "Concepto", "Valor", "Fecha", "Hora")
    tabla = ttk.Treeview(table_container, columns=columnas, show="headings", 
                        height=10, style="Gastos.Treeview")

    # Configurar columnas
    widths = [60, 300, 120, 100, 80]
    for i, col in enumerate(columnas):
        tabla.heading(col, text=col)
        tabla.column(col, width=widths[i], anchor="center")

    # Scrollbars
    v_scrollbar = ttk.Scrollbar(table_container, orient="vertical", command=tabla.yview)
    h_scrollbar = ttk.Scrollbar(table_container, orient="horizontal", command=tabla.xview)
    tabla.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

    tabla.pack(side="left", fill="both", expand=True)
    v_scrollbar.pack(side="right", fill="y")
    h_scrollbar.pack(side="bottom", fill="x")

    def actualizar_tabla():
        # Limpiar tabla
        tabla.delete(*tabla.get_children())
        
        # Agregar gastos
        for i, gasto in enumerate(gastos_registrados):
            tag = "even" if i % 2 == 0 else "odd"
            tabla.insert("", "end", values=(
                i + 1,
                gasto['concepto'],
                f"${gasto['valor']:,.0f}",
                gasto['fecha'],
                gasto['hora']
            ), tags=(tag,))
        
        # Configurar colores alternos
        tabla.tag_configure("even", background="#FFF0F5")
        tabla.tag_configure("odd", background="white")
        
        # Actualizar estadísticas
        actualizar_estadisticas()

    def actualizar_estadisticas():
        # Recalcular estadísticas
        total_gastos, gastos_hoy, total_registros = calcular_estadisticas()
        
        # Actualizar las tarjetas de estadísticas (esto requeriría recrear las tarjetas)
        # Por simplicidad, se podría implementar una función más compleja aquí

    # Agregar algunos datos de ejemplo
    gastos_ejemplo = [
        {'concepto': 'Alquiler del local', 'valor': 800000, 'fecha': fecha_var.get(), 'hora': '08:00:00'},
        {'concepto': 'Compra de papel', 'valor': 150000, 'fecha': fecha_var.get(), 'hora': '10:30:00'},
        {'concepto': 'Servicios públicos', 'valor': 200000, 'fecha': fecha_var.get(), 'hora': '14:15:00'},
        {'concepto': 'Tinta para impresoras', 'valor': 85000, 'fecha': fecha_var.get(), 'hora': '16:45:00'}
    ]
    
    gastos_registrados.extend(gastos_ejemplo)
    actualizar_tabla()

    # 🌟 Footer
    footer_frame = tk.Frame(ventana, bg="#FF1493", height=50)
    footer_frame.pack(fill="x")
    footer_frame.pack_propagate(False)

    tk.Label(footer_frame, text="💎 Control de Gastos • Mantén tus finanzas organizadas 💎", 
             font=("Segoe UI", 11, "bold"), bg="#FF1493", fg="white").pack(expand=True, pady=15)

    # Enfocar el campo concepto al inicio
    concepto_entry.focus()

    # 🎯 Eventos de teclado
    def keyboard_shortcuts(event):
        if event.state & 4:  # Ctrl presionado
            key = event.keysym.lower()
            if key == 'n':  # Ctrl+N para nuevo gasto
                concepto_entry.focus()
            elif key == 'f':  # Ctrl+F para buscar
                search_entry.focus()
            elif key == 's':  # Ctrl+S para guardar
                ingresar_gasto()

    # Vincular Enter para ingresar gasto
    def on_enter(event):
        if event.widget == valor_entry:
            ingresar_gasto()

    valor_entry.bind('<Return>', on_enter)
    concepto_entry.bind('<Return>', lambda e: valor_entry.focus())

    ventana.bind("<KeyPress>", keyboard_shortcuts)
    ventana.focus_set()

    ventana.mainloop()

# Ejecutar si es llamado directamente
if __name__ == "__main__":
    iniciar_gastos()