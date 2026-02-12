import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="GLOBAL WINGS - ERP", layout="wide")

# --- INICIALIZACIÓN DE DATOS ---
tablas = ['db_inv', 'db_recetas', 'db_combos', 'db_ventas', 'db_caja', 'db_activos', 'db_clientes', 'db_costos_ind']
for t in tablas:
    if t not in st.session_state:
        if t == 'db_inv': st.session_state[t] = pd.DataFrame(columns=["Insumo", "Unidad", "Stock", "Costo_Unit_Bs"])
        elif t == 'db_recetas': st.session_state[t] = pd.DataFrame(columns=["Combo", "Insumo", "Cantidad"])
        elif t == 'db_combos': st.session_state[t] = pd.DataFrame(columns=["Nombre", "Precio_Bs"])
        elif t == 'db_ventas': st.session_state[t] = pd.DataFrame(columns=["Fecha", "Cliente", "Combo", "Total_Bs", "Costo_Prod", "Metodo"])
        elif t == 'db_caja': st.session_state[t] = pd.DataFrame(columns=["Fecha", "Concepto", "Monto_Bs", "Tipo"])
        elif t == 'db_activos': st.session_state[t] = pd.DataFrame(columns=["Activo", "Monto_Bs"])
        elif t == 'db_clientes': st.session_state[t] = pd.DataFrame(columns=["Nombre", "Celular"])
        elif t == 'db_costos_ind': st.session_state[t] = pd.DataFrame(columns=["Combo", "Detalle", "Monto_Bs"])

if 'config' not in st.session_state:
    st.session_state.config = {"inversion": 0.0, "caja_inicial": 0.0}

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
    menu = st.sidebar.radio("MENÚ PRINCIPAL", ["🏠 Inicio", "🍗 Almacén", "🍳 Activos", "👨‍🍳 Recetas", "💰 Punto de Venta", "📊 Finanzas"])

    # --- 1. INICIO ---
    if menu == "🏠 Inicio":
        st.header("🏠 Dashboard")
        v = st.session_state.db_ventas
        c1, c2, c3 = st.columns(3)
        c1.metric("Ventas Totales", f"{v['Total_Bs'].sum():,.2f} Bs")
        val_inv = (st.session_state.db_inv['Stock'] * st.session_state.db_inv['Costo_Unit_Bs']).sum()
        c2.metric("Valor Inventario", f"{val_inv:,.2f} Bs")
        c3.metric("Activos Fijos", f"{st.session_state.db_activos['Monto_Bs'].sum():,.2f} Bs")
        st.dataframe(v.tail(10))

    # --- 2. ALMACÉN ---
    elif menu == "🍗 Almacén":
        st.header("📦 Gestión de Insumos")
        with st.form("f_inv"):
            ni = st.text_input("Nombre Insumo")
            un = st.selectbox("Unidad", ["Kg", "Lt", "Unidad"])
            if st.form_submit_button("Crear"):
                n = pd.DataFrame([{"Insumo": ni, "Unidad": un, "Stock": 0.0, "Costo_Unit_Bs": 0.0}])
                st.session_state.db_inv = pd.concat([st.session_state.db_inv, n], ignore_index=True)
        
        if not st.session_state.db_inv.empty:
            with st.form("f_compra"):
                ins = st.selectbox("Insumo", st.session_state.db_inv["Insumo"])
                can = st.number_input("Cantidad", min_value=0.01)
                tot = st.number_input("Costo Total Bs", min_value=0.01)
                if st.form_submit_button("Cargar Compra"):
                    idx = st.session_state.db_inv.index[st.session_state.db_inv['Insumo'] == ins][0]
                    st.session_state.db_inv.at[idx, 'Stock'] += can
                    st.session_state.db_inv.at[idx, 'Costo_Unit_Bs'] = tot / can
                    st.success("Stock actualizado")
        st.dataframe(st.session_state.db_inv)

    # --- 3. ACTIVOS ---
    elif menu == "🍳 Activos":
        st.header("🍳 Equipos y Activos")
        with st.form("f_act"):
            ac = st.text_input("Nombre del Activo (Sartén, Freidora)")
            mo = st.number_input("Valor Bs",
