import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="GLOBAL WINGS - ERP", layout="wide")

# --- INICIALIZACIÓN DE DATOS (REFORZADA) ---
if 'db_inv' not in st.session_state:
    st.session_state.db_inv = pd.DataFrame(columns=["Insumo", "Unidad", "Stock", "Costo_Unit_Bs"])
if 'db_activos' not in st.session_state:
    st.session_state.db_activos = pd.DataFrame(columns=["Activo", "Valor_Bs"])
if 'db_combos' not in st.session_state:
    st.session_state.db_combos = pd.DataFrame(columns=["Nombre", "Precio_Venta"])
if 'db_recetas' not in st.session_state:
    st.session_state.db_recetas = pd.DataFrame(columns=["Combo", "Insumo", "Cantidad"])
if 'db_costos_ind' not in st.session_state:
    st.session_state.db_costos_ind = pd.DataFrame(columns=["Combo", "Detalle", "Monto_Bs"])
if 'db_ventas' not in st.session_state:
    st.session_state.db_ventas = pd.DataFrame(columns=["Fecha", "Cliente", "Combo", "Total_Bs", "Costo_Prod", "Metodo"])
if 'db_gastos_op' not in st.session_state:
    st.session_state.db_gastos_op = pd.DataFrame(columns=["Fecha", "Concepto", "Monto_Bs"])
if 'db_clientes' not in st.session_state:
    st.session_state.db_clientes = pd.DataFrame(columns=["Codigo", "Nombre", "Celular"])
if 'config' not in st.session_state:
    st.session_state.config = {"inversion": 0.0, "deuda": 0.0}

# --- LOGIN ---
if "auth" not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.title("🦅 Global Wings - Acceso Privado")
    u = st.text_input("Usuario")
    p = st.text_input("Contraseña", type="password")
    if st.button("Ingresar"):
        if u == "admin" and p == "wings2026":
            st.session_state.auth = True
            st.rerun()
        else: st.error("Acceso Denegado")
else:
    # --- NAVEGACIÓN ---
    st.sidebar.title("🦅 GLOBAL WINGS ERP")
    menu = st.sidebar.radio("Navegación", 
        ["📊 Dashboard", "🍗 Almacén e Insumos", "🍳 Activos y Equipos", "👨‍🍳 Ingeniería de Recetas", "💰 Punto de Venta", "👥 Clientes", "📉 Finanzas y Balance"])

    # --- 1. DASHBOARD ---
    if menu == "📊 Dashboard":
        st.header("📊 Inteligencia de Negocio")
        v = st.session_state.db_ventas
        c1, c2, c3 = st.columns(3)
        c1.metric("Ventas Totales", f"{v['Total_Bs'].sum():,.2f} Bs")
        c2.metric("Clientes", len(st.session_state.db_clientes))
        c3.metric("Valor Inventario", f"{(st.session_state.db_inv['Stock'] * st.session_state.db_inv['Costo_Unit_Bs']).sum():,.2f} Bs")

    # --- 2. ALMACÉN ---
    elif menu == "🍗 Almacén e Insumos":
        st.header("📦 Gestión de Materia Prima")
        with st.form("n_i"):
            nom = st.text_input("Nombre (ej: Pollo, Papa, Aceite)")
            uni = st.selectbox("Unidad", ["Kg", "Litro", "Unidad", "Gramo"])
            if st.form_submit_button("Añadir al Almacén"):
                st.session_state.db_inv = pd.concat([st.session_state.db_inv, pd.DataFrame([{"Insumo": nom, "Unidad": uni, "Stock": 0.0, "Costo_Unit_Bs": 0.0}])], ignore_index=True)
        
        st.subheader("🛒 Registrar Compras")
        if not st.session_state.db_inv.empty:
            with st.form("compra"):
                ins = st.selectbox("Insumo Comprado", st.session_state.db_inv["Insumo"])
                can = st.number_input("Cantidad", min_value=0.01)
                pre = st.number_input("Costo Total (Bs)", min_value=0.1)
                if st.form_submit_button("Confirmar Entrada"):
                    idx = st.session_state.db_inv.index[st.session_state.db_inv['Insumo'] == ins][0]
                    st.session_state.db_inv.at[idx, 'Stock'] += can
                    st.session_state.db_inv.at[idx, 'Costo_Unit_Bs'] = pre / can
                    st.success("Inventario actualizado.")
        st.dataframe(st.session_state.db_inv)

    # --- 3. ACTIVOS (EQUIPOS) ---
    elif menu == "🍳 Activos y Equipos":
        st.header("🍳 Activos Fijos")
        with st.form("f_act"):
            ac = st.text_input("Descripción del Equipo (ej: Sartén)")
            va = st.number_input("Valor (Bs)", min_value=0.0)
            if st.form_submit_button("Registrar"):
                st.session_state.db_activos = pd.concat([st.session_state.db_activos, pd.DataFrame([{"Activo": ac, "Valor_Bs": va}])], ignore_index=True)
        st.dataframe(st.session_state.db_activos)

    # --- 4. INGENIERÍA DE RECETAS ---
    elif menu == "👨‍🍳 Ingeniería de Recetas":
        st.header("👨‍🍳 Costeo Maestro")
        with st.form("f_c"):
            n_c = st.text_input("Nombre del Combo")
            p_v = st.number_input("Precio Venta (Bs)", min_value=0.0)
            if st.form_submit_button("Crear"):
                st.session_state.db_combos = pd.concat([st.session_state.db_combos, pd.DataFrame([{"Nombre": n_c, "Precio_Venta": p_v}])], ignore_index=True)

        if not st.session_state.db_combos.empty:
            st.divider()
            combo_sel = st.selectbox("Seleccionar Combo", st.session_state.db_combos["Nombre"])
            
            c_rec, c_ind = st.columns(2)
            with c_rec:
                ins_r = st.selectbox("Insumo", st.session_state.db_inv["Insumo"] if not st.session_state.db_inv.empty else [])
                can_r = st.number_input("Cantidad", min_value=0.001)
                if st.button("Añadir Insumo Directo"):
                    st.session_state.db_recetas = pd.concat([st.session_state.db_recetas, pd.DataFrame([{"Combo": combo_sel, "Insumo": ins_r, "Cantidad": can_r}])], ignore_index=True)
            with c_ind:
                det_i = st.text_input("Detalle (Salsa, Empaque)")
                mon_i = st.number_input("Costo unitario (Bs)", min_value=0.0)
                if st.button("Añadir Costo Indirecto"):
                    st.session_state.db_costos_ind = pd.concat([st.session_state.db_costos_ind, pd.DataFrame([{"Combo": combo_sel, "Detalle": det_i, "Monto_Bs": mon_i}])], ignore_index=True)

            # Cálculo de rentabilidad
            receta = st.session_state.db_recetas[st.session_state.db_recetas["Combo"] == combo_sel]
            costo_d = 0
            for _, r in receta.iterrows():
                costo_u = st.session_state.db_inv[st.session_state.db_inv["Insumo"] == r["Insumo"]]["Costo_Unit_Bs"].values[0]
                costo_d += costo_u * r["Cantidad"]
            costo_i = st.session_state.db_costos_ind[st.session_state.db_costos_ind["Combo"] == combo_sel]["Monto_Bs"].sum()
            
            st.subheader(f"Rentabilidad: {combo_sel}")
            st.write(f"Costo Producción: {costo_d + costo_i:,.2f} Bs")
            st.table(receta)

    # --- 5. PUNTO DE VENTA ---
    elif menu == "💰 Punto de Venta":
        st.header("💰 Caja")
        if not st.session_state.db_combos.empty:
            sel_v = st.selectbox("Combo", st.session_state.db_combos["Nombre"])
            can_v = st.number_input("Cantidad", min_value=1)
            met_v = st.radio("Pago", ["Efectivo", "QR"])
            if st.button("Finalizar Venta"):
                # (Lógica de descuento de stock simplificada para evitar errores)
                pv = st.session_state.db_combos[st.session_state.db_combos['Nombre']==sel_v]['Precio_Venta'].values[0]
                nv = pd.DataFrame([{"Fecha": datetime.now(), "Cliente": "Gral", "Combo": sel_v, "Total_Bs": pv * can_v, "Costo_Prod": 0, "Metodo": met_v}])
                st.session_state.db_ventas = pd.concat([st.session
