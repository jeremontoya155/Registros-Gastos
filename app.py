import tkinter as tk
from tkinter import messagebox, ttk
import sqlite3
import os
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import random

DB_NAME = "finanzas.db"


class DatabaseManager:
    """Clase para manejar la base de datos."""

    def __init__(self):
        self.conn = sqlite3.connect(DB_NAME)
        self.init_db()

    def init_db(self):
        """Inicializa la base de datos si no existe."""
        cursor = self.conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS transacciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            tipo TEXT NOT NULL,
            categoria TEXT NOT NULL,
            monto REAL NOT NULL,
            descripcion TEXT
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE
        )
        """)
        # Insertar categorías iniciales si no existen
        cursor.executemany("""
        INSERT OR IGNORE INTO categorias (nombre) VALUES (?)
        """, [("Alimentación",), ("Transporte",), ("Ocio",), ("Otros",)])
        self.conn.commit()

    def insert_transaction(self, tipo, categoria, monto, descripcion):
        """Inserta una transacción en la base de datos."""
        cursor = self.conn.cursor()
        cursor.execute("""
        INSERT INTO transacciones (fecha, tipo, categoria, monto, descripcion)
        VALUES (datetime('now', 'localtime'), ?, ?, ?, ?)
        """, (tipo, categoria, monto, descripcion))
        self.conn.commit()

    def get_transactions(self):
        """Obtiene todas las transacciones."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT fecha, tipo, categoria, monto, descripcion FROM transacciones ORDER BY fecha DESC")
        return cursor.fetchall()

    def close(self):
        """Cierra la conexión con la base de datos."""
        self.conn.close()


class FinanceApp:
    """Clase principal de la aplicación."""

    def __init__(self, root):
        self.root = root
        self.root.title("Gestor de Finanzas Diarias")
        self.root.geometry("800x400")
        self.db = DatabaseManager()

        # Crear estilos para widgets
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("TButton", font=("Helvetica", 12), padding=5)
        self.style.configure("TLabel", font=("Helvetica", 12))

        # Crear la interfaz
        self.create_interface()

    def create_interface(self):
        """Crea la interfaz gráfica."""
        # Frame para ingreso de transacciones
        self.frame_entry = ttk.LabelFrame(self.root, text="Nueva Transacción", padding=10)
        self.frame_entry.pack(pady=10, fill=tk.X, padx=20)

        ttk.Label(self.frame_entry, text="Tipo:").grid(row=0, column=0, padx=5, pady=5)
        self.tipo_var = tk.StringVar(value="Ingreso")
        ttk.Combobox(self.frame_entry, textvariable=self.tipo_var, values=["Ingreso", "Gasto"]).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(self.frame_entry, text="Categoría:").grid(row=1, column=0, padx=5, pady=5)
        self.categoria_var = tk.StringVar()
        categorias = [row[0] for row in self.db.conn.execute("SELECT nombre FROM categorias")]
        ttk.Combobox(self.frame_entry, textvariable=self.categoria_var, values=categorias).grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(self.frame_entry, text="Monto:").grid(row=2, column=0, padx=5, pady=5)
        self.monto_var = tk.DoubleVar()
        ttk.Entry(self.frame_entry, textvariable=self.monto_var).grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(self.frame_entry, text="Descripción:").grid(row=3, column=0, padx=5, pady=5)
        self.descripcion_var = tk.StringVar()
        ttk.Entry(self.frame_entry, textvariable=self.descripcion_var).grid(row=3, column=1, padx=5, pady=5)

        ttk.Button(self.frame_entry, text="Registrar", command=self.registrar_transaccion).grid(row=4, column=0, columnspan=2, pady=10)

        # Frame para opciones
        self.frame_display = ttk.LabelFrame(self.root, text="Opciones", padding=10)
        self.frame_display.pack(pady=10, fill=tk.X, padx=20)
        ttk.Button(self.frame_display, text="Balance", command=self.mostrar_marca_pro).grid(row=0, column=3, padx=10)

        ttk.Button(self.frame_display, text="Ver Historial", command=self.mostrar_historial).grid(row=0, column=0, padx=10)
        ttk.Button(self.frame_display, text="Ver Gráficos", command=self.mostrar_grafico).grid(row=0, column=1, padx=10)
        ttk.Button(self.frame_display, text="Proyección de Gastos", command=self.mostrar_proyeccion).grid(row=0, column=2, padx=10)

    def registrar_transaccion(self):
        """Registra una nueva transacción."""
        tipo = self.tipo_var.get()
        categoria = self.categoria_var.get()
        monto = self.monto_var.get()
        descripcion = self.descripcion_var.get()

        if not categoria or not monto:
            messagebox.showerror("Error", "Debe completar todos los campos.")
            return

        self.db.insert_transaction(tipo, categoria, monto, descripcion)
        messagebox.showinfo("Éxito", "Transacción registrada correctamente.")

    def mostrar_historial(self):
        """Muestra el historial de transacciones."""
        historial = self.db.get_transactions()

        # Crear una nueva ventana para el historial
        historial_window = tk.Toplevel(self.root)
        historial_window.title("Historial de Transacciones")
        tree = ttk.Treeview(historial_window, columns=("Fecha", "Tipo", "Categoría", "Monto", "Descripción"), show="headings")
        tree.pack(fill=tk.BOTH, expand=True)

        for col in ("Fecha", "Tipo", "Categoría", "Monto", "Descripción"):
            tree.heading(col, text=col)

        for row in historial:
            tree.insert("", tk.END, values=row)

    def mostrar_grafico(self):
        """Muestra un gráfico de ingresos vs. gastos."""
        datos = pd.read_sql_query("SELECT tipo, SUM(monto) as total FROM transacciones GROUP BY tipo", self.db.conn)
        if datos.empty:
            messagebox.showinfo("Sin datos", "No hay datos para generar el gráfico.")
            return

        fig, ax = plt.subplots()
        ax.bar(datos["tipo"], datos["total"], color=["green", "red"])
        ax.set_title("Ingresos vs. Gastos")
        ax.set_ylabel("Monto")
        ax.set_xlabel("Tipo")

        # Mostrar el gráfico en la interfaz
        grafico_window = tk.Toplevel(self.root)
        grafico_window.title("Gráfico")
        canvas = FigureCanvasTkAgg(fig, master=grafico_window)
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        canvas.draw()

    def mostrar_marca_pro(self):
        """Muestra el módulo 'Tu Marca Pro'."""
        # Cálculo del balance financiero
        datos = pd.read_sql_query("SELECT tipo, SUM(monto) as total FROM transacciones GROUP BY tipo", self.db.conn)
        ingresos = datos.loc[datos["tipo"] == "Ingreso", "total"].sum() if not datos.empty else 0
        gastos = datos.loc[datos["tipo"] == "Gasto", "total"].sum() if not datos.empty else 0
        balance = ingresos - gastos

        # Calificación financiera
        if balance > 0:
            calificacion = "¡Excelente trabajo! Mantén este ritmo."
            color = "green"
        elif balance == 0:
            calificacion = "Estás equilibrado. ¿Puedes ahorrar un poco más?"
            color = "blue"
        else:
            calificacion = "¡Cuidado! Estás gastando más de lo que ganas."
            color = "red"

        # Frases motivadoras
        frases = [
            "La clave para ahorrar es comenzar.",
            "Gastar menos no es una limitación, es una estrategia.",
            "Cada centavo cuenta para tu éxito financiero.",
            "Invierte en tus sueños, no en tus impulsos.",
            "La disciplina financiera hoy es libertad mañana.",
        ]
        frase_inspiradora = random.choice(frases)

        # Crear ventana especial para 'Tu Marca Pro'
        marca_pro_window = tk.Toplevel(self.root)
        marca_pro_window.title("Balance")
        marca_pro_window.geometry("400x300")
        marca_pro_window.configure(bg="#f0f0f0")

        # Diseño único
        ttk.Label(marca_pro_window, text="¡Bienvenido a Tu Marca Pro!", font=("Helvetica", 16, "bold"), foreground="#333").pack(pady=10)
        ttk.Label(marca_pro_window, text=f"Balance Financiero: ${balance:.2f}", font=("Helvetica", 14), foreground=color).pack(pady=5)
        ttk.Label(marca_pro_window, text=calificacion, font=("Helvetica", 12), wraplength=350).pack(pady=10)

        ttk.Label(marca_pro_window, text="Frase Inspiradora:", font=("Helvetica", 14, "italic"), foreground="#555").pack(pady=10)
        ttk.Label(marca_pro_window, text=f"“{frase_inspiradora}”", font=("Helvetica", 12), wraplength=350, foreground="#444").pack(pady=5)

        ttk.Button(marca_pro_window, text="Cerrar", command=marca_pro_window.destroy).pack(pady=15)

    def mostrar_proyeccion(self):
        """Muestra una proyección de gastos futuros."""
        datos = pd.read_sql_query("""
            SELECT fecha, tipo, monto FROM transacciones WHERE tipo = 'Gasto'
        """, self.db.conn)
        if datos.empty:
            messagebox.showinfo("Sin datos", "No hay datos para generar la proyección.")
            return

        datos["fecha"] = pd.to_datetime(datos["fecha"])
        promedio_diario = datos.groupby(datos["fecha"].dt.date)["monto"].sum().mean()
        proyeccion = promedio_diario * 30

        # Mostrar resultados en una ventana emergente
        proyeccion_window = tk.Toplevel(self.root)
        proyeccion_window.title("Proyección de Gastos")
        ttk.Label(proyeccion_window, text=f"Gasto promedio diario: ${promedio_diario:.2f}").pack(pady=5)
        ttk.Label(proyeccion_window, text=f"Proyección para los próximos 30 días: ${proyeccion:.2f}").pack(pady=5)

        # Gráfico
        fig, ax = plt.subplots()
        ax.plot(datos["fecha"], datos["monto"], label="Histórico", color="red")
        ax.axhline(y=promedio_diario, color="blue", linestyle="--", label="Promedio Diario")
        ax.set_title("Proyección de Gastos")
        ax.set_ylabel("Monto")
        ax.set_xlabel("Fecha")
        ax.legend()

        canvas = FigureCanvasTkAgg(fig, master=proyeccion_window)
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        canvas.draw()


if __name__ == "__main__":
    app = tk.Tk()
    FinanceApp(app)
    app.mainloop()
