import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="GLOBAL WINGS - SISTEMA INTEGRAL", layout="wide")

# --- INICIALIZACIÓN DE BASES DE DATOS ---
if 'db_inv' not in st.session_state:
    # Inventario: Materia Prima
    st.session_state.db_inv = pd.DataFrame(columns=["Insumo", "Unidad", "Stock", "Costo_Unit_Bs"])

if 'db_recetas' not in st.session_state:
    # Tabla de Costos Directos: Vincula Combo con Insumos
    st.session_state.db_recetas = pd.DataFrame(columns=["Combo", "Insumo", "Cantidad_Necesaria"])

if 'db_combos' not in st.session_state:
    # Catálogo de productos a la venta
    st.session_state.db_combos = pd.DataFrame(columns=["Nombre_Combo", "Precio_Venta_Bs"])

if 'db_ventas' not in st.session_state:
    # Registro de ventas realizadas
    st.session_state.db_ventas = pd.DataFrame(columns=["Fecha", "Combo", "Cantidad", "Total_Venta_Bs", "Costo_Total_Bs", "Utilidad_Bs"])

# --- LOGIN ---
if "auth" not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.title("🦅 Acceso Global Wings")
    u = st.text_input("Usuario")
    p = st.text_input("Contraseña", type="password")
    if st.button("Ingresar"):
        if u == "admin" and p == "wings2026":
            st.session_state.auth = True
            st.rerun()
        else: st.error("Credenciales incorrectas")
else:
    menu = st.sidebar.radio("MENÚ", ["📦 Inventario", "👨‍🍳 Recetas y Costos", "💰 Ventas", "📊 Reportes"])

    # --- 1. INVENTARIO (ALMACÉN) ---
    if menu == "📦 Inventario":
        st.header("📦 Almacén de Materia Prima")
        
        with st.expander("➕ Registrar Nuevo Insumo"):
            with st.form("nuevo_insumo"):
                n_i = st.text_input("Nombre del Insumo (ej: Pollo)")
                u_i = st.selectbox("Unidad", ["Kg", "Lt", "Unidad", "Gr"])
                if st.form_submit_button("Añadir al Almacén"):
                    nueva_fila = pd.DataFrame([{"Insumo": n_i, "Unidad": u_i, "Stock": 0.0, "Costo_Unit_Bs": 0.0}])
                    st.session_state.db_inv = pd.concat([st.session_state.db_inv, nueva_fila], ignore_index=True)
                    st.success(f"{n_i} añadido.")

        st.subheader("🛒 Cargar Compras (Actualiza Stock y Costos)")
        if not st.session_state.db_inv.empty:
            with st.form("compra_stock"):
                ins_sel = st.selectbox("Seleccionar Insumo", st.session_state.db_inv["Insumo"])
                cant_compra = st.number_input("Cantidad Comprada", min_value=0.01)
                costo_total_compra = st.number_input("Monto Total Pagado (Bs)", min_value=0.1)
                if st.form_submit_button("Registrar Compra"):
                    idx = st.session_state.db_inv.index[st.session_state.db_inv['Insumo'] == ins_sel][0]
                    # Actualizar Stock y calcular nuevo costo unitario promedio
                    st.session_state.db_inv.at[idx, 'Stock'] += cant_compra
                    st.session_state.db_inv.at[idx, 'Costo_Unit_Bs'] = costo_total_compra / cant_compra
                    st.success("Inventario y costos actualizados.")
        
        st.dataframe(st.session_state.db_inv, use_container_width=True)

    # --- 2. RECETAS (COSTOS DIRECTOS) ---
    elif menu == "👨‍🍳 Recetas y Costos":
        st.header("👨‍🍳 Ingeniería de Recetas")
        
        with st.form("crear_combo"):
            st.subheader("1. Crear Nuevo Combo")
            c1, c2 = st.columns(2)
            n_combo = c1.text_input("Nombre del Combo (ej: Combo 12 Alas)")
