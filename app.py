
from flask import Flask, request, jsonify, render_template_string
import sqlite3
from datetime import datetime

app = Flask(__name__)
DATABASE = "database.db"

# -----------------------------
# BASE DE DATOS
# -----------------------------

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS inventario (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT,
        cantidad REAL,
        costo_unitario REAL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS recetas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS receta_ingredientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        receta_id INTEGER,
        inventario_id INTEGER,
        cantidad REAL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS movimientos_financieros (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tipo TEXT,
        monto REAL,
        fecha TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# -----------------------------
# RUTA PRINCIPAL (FRONTEND)
# -----------------------------

@app.route("/")
def index():
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Global Wings ERP</title>
        <style>
            body { font-family: Arial; margin: 40px; background:#f4f4f4;}
            h1 { color:#c0392b; }
            section { background:white; padding:20px; margin-bottom:20px; border-radius:10px;}
            button { padding:5px 10px; margin-top:5px;}
            input { margin:5px; padding:5px;}
        </style>
    </head>
    <body>
        <h1>GLOBAL WINGS - SISTEMA FINANCIERO (Bs)</h1>

        <section>
            <h2>Inventario</h2>
            <input id="nombre" placeholder="Nombre">
            <input id="cantidad" type="number" placeholder="Cantidad">
            <input id="costo" type="number" placeholder="Costo Unitario Bs">
            <button onclick="agregarInventario()">Agregar</button>
            <ul id="listaInventario"></ul>
        </section>

        <section>
            <h2>Crear Receta</h2>
            <input id="nombreReceta" placeholder="Nombre Receta">
            <button onclick="crearReceta()">Crear</button>
        </section>

        <
