import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Global Wings - Sistema Privado", layout="wide")

# --- SISTEMA DE SEGURIDAD (CONTRASEÑA) ---
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.title("🦅 Global Wings - Acceso Privado")
        user = st.text_input("Usuario Administrador")
        password = st.text_input("Contraseña", type="password")
        if st.button("Ingresar al Sistema"):
            if user == "admin" and password == "wings2026": # CAMBIA TU CLAVE AQUÍ
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Acceso denegado")
        return False
    return True

if check_password():
    # --- BASE DE DATOS TEMPORAL (Esto se conecta luego a Google Sheets) ---
    if 'inv' not in st.session_state:
        st.session_state.inv = pd.DataFrame([
            {"Insumo": "Alitas", "Stock": 1000, "Costo_Bs": 1.5},
            {"Insumo": "Papas", "Stock": 500, "Costo_Bs": 2.0}
        ])
    if 'ventas' not in st.session_state:
        st.session_state.ventas = pd.DataFrame(columns=["Fecha", "Producto", "Cantidad", "Total_Bs"])

    # --- MENÚ LATERAL ---
    menu = st.sidebar.selectbox("Módulo", ["Dashboard", "Ventas", "Inventario", "Flujo de Caja"])

    # --- MÓDULO VENTAS (BIDIRECCIONAL) ---
    if menu == "Ventas":
        st.header("🛒 Registro de Ventas")
        producto = st.selectbox("Seleccionar Insumo para vender", st.session_state.inv["Insumo"])
        cantidad = st.number_input("Cantidad a vender", min_value=1)
        precio = st.number_input("Precio de Venta (Bs)", min_value=1.0)

        if st.button("Confirmar Venta"):
            # Lógica: Descontar stock
            idx = st.session_state.inv.index[st.session_state.inv['Insumo'] == producto][0]
            if st.session_state.inv.at[idx, 'Stock'] >= cantidad:
                st.session_state.inv.at[idx, 'Stock'] -= cantidad
                nueva_venta = {"Fecha": datetime.now(), "Producto": producto, "Cantidad": cantidad, "Total_Bs": cantidad * precio}
                st.session_state.ventas = pd.concat([st.session_state.ventas, pd.DataFrame([nueva_venta])], ignore_index=True)
                st.success(f"Venta Exitosa. Stock de {producto} actualizado.")
            else:
                st.error("¡ERROR: No hay stock suficiente!")

    # --- MÓDULO DASHBOARD ---
    elif menu == "Dashboard":
        st.header("📊 Resumen General (Tiempo Real)")
        col1, col2, col3 = st.columns(3)
        total_ventas = st.session_state.ventas["Total_Bs"].sum()
        valor_inv = (st.session_state.inv["Stock"] * st.session_state.inv["Costo_Bs"]).sum()
        
        col1.metric("Ingresos Totales", f"{total_ventas} Bs")
        col2.metric("Valor Inventario", f"{valor_inv} Bs")
        col3.metric("Saldo en Caja", f"{total_ventas} Bs")

        st.subheader("Estado de Inventario Actual")
        st.table(st.session_state.inv)

    # --- MÓDULO INVENTARIO ---
    elif menu == "Inventario":
        st.header("📦 Administración de Insumos")
        st.write("Aquí puedes editar costos y aumentar stock manualmente.")
        edited_df = st.data_editor(st.session_state.inv)
        if st.button("Guardar Cambios"):
            st.session_state.inv = edited_df
            st.success("Inventario actualizado.")
