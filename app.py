import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="GLOBAL WINGS - ERP", layout="wide")

# --- INICIALIZACIÓN DE DATOS (SEGURA) ---
tablas = ['db_inv', 'db_recetas', 'db_combos', 'db_ventas', 'db_caja', 'db_activos']
for t in tablas:
    if t not in st.session_state:
        if t == 'db_inv': st.session_state[t] = pd.DataFrame(columns=["Insumo", "Unidad", "Stock", "Costo_Unit_Bs", "Alerta"])
        elif t == 'db_recetas': st.session_state[t] = pd.DataFrame(columns=["Combo", "Insumo", "Cantidad"])
        elif t == 'db_combos': st.session_state[t] = pd.DataFrame(columns=["Nombre", "Precio_Bs"])
        elif t == 'db_ventas': st.session_state[t] = pd.DataFrame(columns=["Fecha", "Combo", "Total_Bs", "Costo_Total", "Metodo"])
        elif t == 'db_caja': st.session_state[t] = pd.DataFrame(columns=["Fecha", "Concepto", "Monto_Bs", "Tipo"])
        elif t == 'db_activos': st.session_state[t] = pd.DataFrame(columns=["Activo", "Monto_Bs"])

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
    menu = st.sidebar.radio("MENÚ PRINCIPAL", ["🏠 Inicio", "🍗 Almacén e Insumos", "🍳 Activos y Equipos", "👨‍🍳 Recetas y Costos", "💰 Punto de Venta", "🏛️ Balance y Finanzas"])

    # --- 1. INICIO ---
    if menu == "🏠 Inicio":
        st.header("🏠 Dashboard Global Wings")
        v = st.session_state.db_ventas
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Ventas Totales", f"{v['Total_Bs'].sum():,.2f} Bs")
        
        ingresos = st.session_state.db_caja[st.session_state.db_caja['Tipo'] == 'Ingreso']['Monto_Bs'].sum()
        egresos = st.session_state.db_caja[st.session_state.db_caja['Tipo'] == 'Egreso']['Monto_Bs'].sum()
        c2.metric("Efectivo en Caja", f"{(ingresos - egresos + st.session_state.config['caja_inicial']):,.2f} Bs")
        c3.metric("Valor Inventario", f"{(st.session_state.db_inv['Stock'] * st.session_state.db_inv['Costo_Unit_Bs']).sum():,.2f} Bs")
        c4.metric("Activos Fijos", f"{st.session_state.db_activos['Monto_Bs'].sum():,.2f} Bs")

    # --- 2. ALMACÉN ---
    elif menu == "🍗 Almacén e Insumos":
        st.header("🍗 Gestión de Insumos")
        with st.form("f_inv"):
            c1, c2, c3 = st.columns(3)
            ni = c1.text_input("Nombre (Pollo, Papa, Aceite, Salsa)")
            un = c2.selectbox("Unidad", ["Kg", "Lt", "Unidad", "Gramo"])
            al = c3.number_input("Alerta Stock Mínimo", value=5.0)
            if st.form_submit_button("Crear Insumo"):
                n = pd.DataFrame([{"Insumo": ni, "Unidad": un, "Stock": 0.0, "Costo_Unit_Bs": 0.0, "Alerta": al}])
                st.session_state.db_inv = pd.concat([st.session_state.db_inv, n], ignore_index=True)

        st.subheader("🛒 Cargar Compra")
        if not st.session_state.db_inv.empty:
            with st.form("f_compra"):
                ins = st.selectbox("Insumo", st.session_state.db_inv["Insumo"])
                can = st.number_input("Cantidad", min_value=0.01)
                tot = st.number_input("Costo Total Bs", min_value=0.01)
                if st.form_submit_button("Confirmar Compra"):
                    idx = st.session_state.db_inv.index[st.session_state.db_inv['Insumo'] == ins][0]
                    st.session_state.db_inv.at[idx, 'Stock'] += can
                    st.session_state.db_inv.at[idx, 'Costo_Unit_Bs'] = tot / can
                    g = pd.DataFrame([{"Fecha": datetime.now(), "Concepto": f"Compra {ins}", "Monto_Bs": tot, "Tipo": "Egreso"}])
                    st.session_state.db_caja = pd.concat([st.session_state.db_caja, g
