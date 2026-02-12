import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="GLOBAL WINGS - ERP TOTAL", layout="wide")

# --- INICIALIZACIÓN DE BASES DE DATOS ---
tablas = ['db_inv', 'db_recetas', 'db_combos', 'db_ventas', 'db_caja', 'db_activos', 'db_costos_ind']
for t in tablas:
    if t not in st.session_state:
        if t == 'db_inv': st.session_state[t] = pd.DataFrame(columns=["Insumo", "Unidad", "Stock", "Costo_Unit_Bs"])
        elif t == 'db_recetas': st.session_state[t] = pd.DataFrame(columns=["Combo", "Insumo", "Cantidad"])
        elif t == 'db_combos': st.session_state[t] = pd.DataFrame(columns=["Nombre", "Precio_Bs"])
        elif t == 'db_ventas': st.session_state[t] = pd.DataFrame(columns=["Fecha", "Combo", "Total_Bs", "Costo_Prod", "Metodo"])
        elif t == 'db_caja': st.session_state[t] = pd.DataFrame(columns=["Fecha", "Concepto", "Monto_Bs", "Tipo"])
        elif t == 'db_activos': st.session_state[t] = pd.DataFrame(columns=["Activo", "Monto_Bs"])
        elif t == 'db_costos_ind': st.session_state[t] = pd.DataFrame(columns=["Combo", "Detalle", "Monto_Bs"])

if 'config' not in st.session_state:
    st.session_state.config = {"inversion": 0.0}

# --- LOGIN ---
if "auth" not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.title("🦅 Global Wings - Acceso Privado")
    u = st.text_input("Usuario")
    p = st.text_input("Contraseña", type="password")
    if st.button("Entrar"):
        if u == "admin" and p == "wings2026":
            st.session_state.auth = True
            st.rerun()
        else: st.error("Clave incorrecta")
else:
    # --- MENÚ LATERAL ---
    menu = st.sidebar.radio("SISTEMA INTEGRAL", ["📊 Dashboard", "🍗 Almacén e Insumos", "🍳 Activos y Equipos", "👨‍🍳 Ingeniería de Recetas", "💰 Punto de Venta", "🏛️ Balance y Finanzas"])

    # --- 1. DASHBOARD ---
    if menu == "📊 Dashboard":
        st.header("📊 Resumen de Operaciones")
        v = st.session_state.db_ventas
        c1, c2, c3 = st.columns(3)
        c1.metric("Ventas Totales", f"{v['Total_Bs'].sum():,.2f} Bs")
        val_inv = (st.session_state.db_inv['Stock'] * st.session_state.db_inv['Costo_Unit_Bs']).sum()
        c2.metric("Valor en Inventario", f"{val_inv:,.2f} Bs")
        c3.metric("Activos Fijos", f"{st.session_state.db_activos['Monto_Bs'].sum():,.2f} Bs")
        st.dataframe(v.tail(10), use_container_width=True)

    # --- 2. ALMACÉN E INSUMOS ---
    elif menu == "🍗 Almacén e Insumos":
        st.header("📦 Gestión de Insumos")
        with st.form("f_inv"):
            ni = st.text_input("Nombre del Insumo")
            un = st.selectbox("Unidad", ["Kg", "Lt", "Unidad", "Gramo"])
            if st.form_submit_button("Registrar Insumo"):
                nuevo_i = pd.DataFrame([{"Insumo": ni, "Unidad": un
