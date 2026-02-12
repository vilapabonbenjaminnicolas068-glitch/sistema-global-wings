import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="GLOBAL WINGS - SISTEMA INTEGRAL", layout="wide")

# --- LOGIN ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🦅 Global Wings - Acceso Privado")
    user = st.text_input("Usuario")
    pw = st.text_input("Contraseña", type="password")
    if st.button("Entrar"):
        if user == "admin" and pw == "wings2026":
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Credenciales incorrectas")
else:
    # --- INICIALIZACIÓN DE DATOS ---
    if 'db_inv' not in st.session_state:
        st.session_state.db_inv = pd.DataFrame(columns=["Insumo", "Tipo", "Unidad", "Stock", "Costo_Unit_Bs"])
    if 'db_activos' not in st.session_state:
        st.session_state.db_activos = pd.DataFrame(columns=["Nombre_Activo", "Valor_Bs", "Fecha_Compra"])
    if 'db_recetas' not in st.session_state:
        st.session_state.db_recetas = pd.DataFrame(columns=["Combo", "Insumo", "Cantidad"])
    if 'db_combos' not in st.session_state:
        st.session_state.db_combos = pd.DataFrame(columns=["Nombre_Combo", "Precio_Venta_Bs"])
    if 'db_ventas' not in st.session_state:
        st.session_state.db_ventas = pd.DataFrame(columns=["Fecha", "Combo", "Total_Bs", "Costo_Total"])
    if 'db_gastos' not in st.session_state:
        st.session_state.db_gastos = pd.DataFrame(columns=["Fecha", "Concepto", "Monto_Bs"])
    if 'capital' not in st.session_state:
        st.session_state.capital = 0.0

    # --- NAVEGACIÓN ---
    st.sidebar.title("🦅 GLOBAL WINGS")
    opcion = st.sidebar.radio("Navegación", 
        ["🏠 Inicio", "📦 Stock e Inventario", "🍳 Activos (Equipos)", "🍔 Ingeniería de Combos", "💰 Punto de Venta", "💸 Gastos Operativos", "📊 Reportes Financieros"])

    # --- INICIO ---
    if opcion == "🏠 Inicio":
        st.header("🏠 Panel de Control")
        v_total = st.session_state.db_ventas['Total_Bs'].sum()
        g_total = st.session_state.db_gastos['Monto_Bs'].sum()
        act_total = st.session_state.db_activos['Valor_Bs'].sum()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Ventas Totales", f"{v_total:,.2f} Bs")
        c2.metric("Inversión en Equipos", f"{act_total:,.2f} Bs")
        c3.metric("Gastos Registrados", f"{g_total:,.2f} Bs")
        
        st.subheader("Ventas Recientes")
        st.dataframe(st.session_state.db_ventas.tail(5), use_container_width=True)

    # --- INVENTARIO ---
    elif opcion == "📦 Stock e Inventario":
        st.header("🍗 Gestión de Insumos")
        with st.expander("➕ Nuevo Insumo (Pollo, Papas, etc)"):
            with st.form("n_insumo"):
                nom = st.text_input("Nombre")
                uni = st.selectbox("Unidad", ["Kg", "Litro", "Unidad", "Porción"])
                if st.form_submit_button("Crear"):
                    n = pd.DataFrame([{"Insumo": nom, "Tipo": "Consumible", "Unidad": uni, "Stock": 0.0, "Costo_Unit_Bs": 0.0}])
                    st.session_state.db_inv = pd.concat([st.session_state.db_inv, n], ignore_index=True)
        
        st.subheader("🛒 Cargar Compra")
        if not st.session_state.db_inv.empty:
            with st.form("c_inv"):
                ins = st.selectbox("Insumo", st.session_state.db_inv["Insumo"])
                can = st.number_input("Cantidad", min_value=0.1)
                pre = st.number_input("Costo Total (Bs)", min_value=0.1)
                if st.form_submit_button("Confirmar Entrada"):
                    idx = st.session_state.db_inv.index[st.session_state.db_inv['Insumo'] == ins][0]
                    st.session_state.db_inv.at[idx, 'Stock'] += can
                    st.session_state.db_inv.at[idx, 'Costo_Unit_Bs'] = pre / can
                    st.success("Inventario actualizado")
        st.dataframe(st.session_state.db_inv)

    # --- ACTIVOS (EL SARTÉN) ---
    elif opcion == "🍳 Activos (Equipos)":
        st.header("🍳 Registro de Activos Fijos")
        st.write("Registra aquí equipos que no se venden (Sartenes, Freidoras, Mesas).")
        with st.form("f_activos"):
            n_act = st.text_input("Nombre del Equipo (ej: Sartén Industrial)")
            v_act = st.number_input("Valor de Compra (Bs)", min_value=0.0)
            if st.form_submit_button("Registrar Activo"):
                n = pd.DataFrame([{"Nombre_Activo": n_act, "Valor_Bs": v_act, "Fecha_Compra": datetime.now()}])
                st.session_state.db_activos = pd.concat([st.session_state.db_activos, n], ignore_index=True)
                st.success(f"{n_act} añadido al Balance General.")
        st.dataframe(st.session_state.db_activos)

    # --- COMBOS ---
    elif opcion == "🍔 Ingeniería de Combos":
        st.header("🍔 Diseño de Combos y Rentabilidad")
        with st.form("n_combo"):
            nc = st.text_input("Nombre del Combo")
            pv = st.number_input("Precio Venta (Bs)", min_value=0.0)
            if st.form_submit_button("Crear"):
                st.session_state.db_combos = pd.concat([st.session_state.db_combos, pd.DataFrame([{"Nombre_Combo": nc, "Precio_Venta_Bs": pv}])], ignore_index=True)
        
        st.subheader("Añadir Ingredientes")
        if not st.session_state.db_combos.empty:
            c_sel = st.selectbox("Combo", st.session_state.db_combos["Nombre_Combo"])
            i_sel = st.selectbox("Ingrediente", st.session_state.db_inv["Insumo"])
            can_r = st.number_input("Cantidad", min_value=0.01)
            if st.button("Vincular"):
                st.session_state.db_recetas = pd.concat([st.session_state.db_recetas, pd.DataFrame([{"Combo": c_sel, "Insumo": i_sel, "Cantidad": can_r}])], ignore_index=True)

    # --- PUNTO DE VENTA ---
    elif opcion == "💰 Punto de Venta":
        st.header("💰 Caja")
        if not st.session_state.db_combos.empty:
            cmb = st.selectbox("Combo", st.session_state.db_combos["Nombre_Combo"])
            can = st.number_input("Cantidad", min_value=1)
            if st.button("Procesar Venta"):
                receta = st.session_state.db_recetas[st.session_state.db_recetas["Combo"] == cmb]
                costo_vta = 0
                for _, r in receta.iterrows():
                    idx = st.session_state.db_inv.index[st.session_state.db_inv["Insumo"] == r["Insumo"]][0]
                    st.session_state.db_inv.at[idx, "Stock"] -= (r["Cantidad"] * can)
                    costo_vta += st.session_state.db_inv.at[idx, "Costo_Unit_Bs"] * (r["Cantidad"] * can)
                p_vta = st.session_state.db_combos[st.session_state.db_combos["Nombre_Combo"] == cmb]["Precio_Venta_Bs"].values[0]
                nv = pd.DataFrame([{"Fecha": datetime.now(), "Combo": cmb, "Total_Bs": p_vta * can, "Costo_Total": costo_vta}])
                st.session_state.db_ventas = pd.concat([st.session_state.db_ventas, nv], ignore_index=True)
                st.success("Venta procesada")

    # --- GASTOS ---
    elif opcion == "💸 Gastos Operativos":
        st.header("💸 Gastos con Nombre (Luz, Agua, Alquiler)")
        with st.form("f_gastos"):
            con = st.text_input("Concepto del Gasto")
            mon = st.number_input("Monto (Bs)", min_value=0.0)
            if st.form_submit_button("Registrar Gasto"):
                n = pd.DataFrame([{"Fecha": datetime.now(), "Concepto": con, "Monto_Bs": mon}])
                st.session_state.db_gastos = pd.concat([st.session_state.db_gastos, n], ignore_index=True)
        st.dataframe(st.session_state.db_gastos)

    # --- REPORTES FINANCIEROS (CON EL SARTÉN) ---
    elif opcion == "📊 Reportes Financieros":
        st.header("📊 Estados Financieros")
        # Cálculos
        v_t = st.session_state.db_ventas['Total_Bs'].sum()
        c_v = st.session_state.db_ventas['Costo_Total'].sum()
        g_t = st.session_state.db_gastos['Monto_Bs'].sum()
        utilidad = (v_t - c_v) - g_t
        val_inv = (st.session_state.db_inv['Stock'] * st.session_state.db_inv['Costo_Unit_Bs']).sum()
        val_act = st.session_state.db_activos['Valor_Bs'].sum()
        
        tab1, tab2 = st.tabs(["📉 Estado de Resultados", "🏛️ Balance General"])
        
        with tab1:
            st.write(f"Ventas: {v_t} Bs")
            st.write(f"Costo Mercadería: {c_v} Bs")
            st.write(f"Gastos Operativos: {g_t} Bs")
            st.divider()
            st.metric("UTILIDAD NETA", f"{utilidad:,.2f} Bs")

        with tab2:
            st.markdown("### Balance General")
            col1, col2 = st.columns(2)
            with col1:
                st.info("**ACTIVOS**")
                st.write(f"Efectivo en Caja: {v_t - g_t} Bs")
                st.write(f"Inventario (Insumos): {val_inv:,.2f} Bs")
                st.write(f"Equipos (Activos Fijos): {val_act:,.2f} Bs")
                st.divider()
                st.write(f"**TOTAL ACTIVOS:** {(v_t - g_t + val_inv + val_act):,.2f} Bs")
            with col2:
                st.success("**PATRIMONIO**")
                st.write(f"Utilidad del Periodo: {utilidad:,.2f} Bs")
