import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="GLOBAL WINGS - COSTEO INTEGRAL", layout="wide")

# --- LOGIN ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🦅 Global Wings - Administración")
    user = st.text_input("Usuario")
    pw = st.text_input("Contraseña", type="password")
    if st.button("Entrar"):
        if user == "admin" and pw == "wings2026":
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Credenciales incorrectas")
else:
    # --- INICIALIZACIÓN DE BASES DE DATOS ---
    if 'db_inv' not in st.session_state:
        st.session_state.db_inv = pd.DataFrame(columns=["Insumo", "Unidad", "Stock", "Costo_Unit_Bs"])
    if 'db_activos' not in st.session_state:
        st.session_state.db_activos = pd.DataFrame(columns=["Activo", "Valor_Bs"])
    if 'db_recetas' not in st.session_state:
        st.session_state.db_recetas = pd.DataFrame(columns=["Combo", "Insumo", "Cantidad"])
    if 'db_costos_ind' not in st.session_state:
        st.session_state.db_costos_ind = pd.DataFrame(columns=["Combo", "Concepto", "Monto_Bs"])
    if 'db_combos' not in st.session_state:
        st.session_state.db_combos = pd.DataFrame(columns=["Nombre_Combo", "Precio_Venta_Bs"])
    if 'db_ventas' not in st.session_state:
        st.session_state.db_ventas = pd.DataFrame(columns=["Fecha", "Combo", "Total_Bs", "Costo_Directo", "Costo_Indirecto"])
    if 'db_gastos' not in st.session_state:
        st.session_state.db_gastos = pd.DataFrame(columns=["Fecha", "Concepto", "Monto_Bs"])

    # --- NAVEGACIÓN ---
    st.sidebar.title("🦅 GLOBAL WINGS")
    opcion = st.sidebar.radio("Navegación", 
        ["🏠 Inicio", "📦 Almacén (Insumos Directos)", "👨‍🍳 Ingeniería de Recetas", "🍳 Activos y Equipos", "💰 Punto de Venta", "💸 Gastos (Luz/Agua)", "📊 Balance y Utilidades"])

    # --- 1. INICIO ---
    if opcion == "🏠 Inicio":
        st.header("🏠 Resumen de Operaciones")
        v = st.session_state.db_ventas
        c1, c2, c3 = st.columns(3)
        c1.metric("Ingresos Totales", f"{v['Total_Bs'].sum():,.2f} Bs")
        utilidad_b = v['Total_Bs'].sum() - v['Costo_Directo'].sum() - v['Costo_Indirecto'].sum()
        c2.metric("Utilidad Bruta", f"{utilidad_b:,.2f} Bs")
        c3.metric("Valor en Equipos", f"{st.session_state.db_activos['Valor_Bs'].sum():,.2f} Bs")

    # --- 2. ALMACÉN (CONECTADO A RECETAS) ---
    elif opcion == "📦 Almacén (Insumos Directos)":
        st.header("📦 Almacén de Insumos Directos")
        with st.expander("➕ Registrar Insumo"):
            with st.form("n_i"):
                nom = st.text_input("Nombre (Pollo, Papa, Aceite)")
                uni = st.selectbox("Unidad", ["Kg", "Unidad", "Litro"])
                if st.form_submit_button("Guardar"):
                    st.session_state.db_inv = pd.concat([st.session_state.db_inv, pd.DataFrame([{"Insumo": nom, "Unidad": uni, "Stock": 0.0, "Costo_Unit_Bs": 0.0}])], ignore_index=True)
        
        st.subheader("🛒 Cargar Compras")
        if not st.session_state.db_inv.empty:
            with st.form("compra"):
                ins = st.selectbox("Seleccionar Insumo", st.session_state.db_inv["Insumo"])
                can = st.number_input("Cantidad", min_value=0.1)
                pre = st.number_input("Costo Total (Bs)", min_value=0.1)
                if st.form_submit_button("Actualizar Stock"):
                    idx = st.session_state.db_inv.index[st.session_state.db_inv['Insumo'] == ins][0]
                    st.session_state.db_inv.at[idx, 'Stock'] += can
                    st.session_state.db_inv.at[idx, 'Costo_Unit_Bs'] = pre / can
                    st.success("Costo unitario recalculado automáticamente.")
        st.dataframe(st.session_state.db_inv)

    # --- 3. INGENIERÍA DE RECETAS (UNION DE COSTOS) ---
    elif opcion == "👨‍🍳 Ingeniería de Recetas":
        st.header("👨‍🍳 Diseño de Costos por Combo")
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("1. Insumos Directos (Inventario)")
            combo_sel = st.selectbox("Elegir Combo", st.session_state.db_combos["Nombre_Combo"] if not st.session_state.db_combos.empty else ["Cree un combo primero"])
            insumo_sel = st.selectbox("Añadir del Almacén", st.session_state.db_inv["Insumo"] if not st.session_state.db_inv.empty else [])
            cantidad = st.number_input("Cantidad necesaria", min_value=0.001)
            if st.button("Vincular Insumo"):
                st.session_state.db_recetas = pd.concat([st.session_state.db_recetas, pd.DataFrame([{"Combo": combo_sel, "Insumo": insumo_sel, "Cantidad": cantidad}])], ignore_index=True)

        with col2:
            st.subheader("2. Costos Indirectos (Salsas/Empaque)")
            concepto_ind = st.text_input("Concepto (ej: Salsa Especial, Caja)")
            monto_ind = st.number_input("Costo por Combo (Bs)", min_value=0.0)
            if st.button("Añadir Costo Indirecto"):
                st.session_state.db_costos_ind = pd.concat([st.session_state.db_costos_ind, pd.DataFrame([{"Combo": combo_sel, "Concepto": concepto_ind, "Monto_Bs": monto_ind}])], ignore_index=True)

        st.divider()
        st.subheader("🔍 Análisis de Costo de Producción")
        if not st.session_state.db_combos.empty:
            for c in st.session_state.db_combos["Nombre_Combo"]:
                # Calcular Costo Directo
                receta = st.session_state.db_recetas[st.session_state.db_recetas["Combo"] == c]
                c_directo = 0
                for _, r in receta.iterrows():
                    c_unit = st.session_state.db_inv[st.session_state.db_inv["Insumo"] == r["Insumo"]]["Costo_Unit_Bs"].values[0]
                    c_directo += c_unit * r["Cantidad"]
                
                # Calcular Costo Indirecto
                c_indirecto = st.session_state.db_costos_ind[st.session_state.db_costos_ind["Combo"] == c]["Monto_Bs"].sum()
                
                total_produccion = c_directo + c_indirecto
                precio_v = st.session_state.db_combos[st.session_state.db_combos["Nombre_Combo"] == c]["Precio_Venta_Bs"].values[0]
                
                with st.expander(f"📊 {c} | Costo Total: {total_produccion:,.2f} Bs | Utilidad: {precio_v - total_produccion:,.2f} Bs"):
                    st.write(f"**Costo Almacén (Directo):** {c_directo:,.2f} Bs")
                    st.write(f"**Costo Indirecto:** {c_indirecto:,.2f} Bs")
                    st.table(receta)

    # --- 4. ACTIVOS FIJOS ---
    elif opcion == "🍳 Activos y Equipos":
        st.header("🍳 Equipamiento")
        with st.form("act"):
            nom_a = st.text_input("Nombre del Activo (Sartén, Freidora)")
            val_a = st.number_input("Valor Bs", min_value=0.0)
            if st.form_submit_button("Registrar"):
                st.session_state.db_activos = pd.concat([st.session_state.db_activos, pd.DataFrame([{"Activo": nom_a, "Valor_Bs": val_a}])], ignore_index=True)
        st.dataframe(st.session_state.db_activos)

    # --- 5. PUNTO DE VENTA ---
    elif opcion == "💰 Punto de Venta":
        st.header("💰 Caja")
        if not st.session_state.db_combos.empty:
            c_v = st.selectbox("Combo", st.session_state.db_combos["Nombre_Combo"])
            can_v = st.number_input("Cantidad", min_value=1)
            if st.button("Finalizar Venta"):
                # Cálculo de costos para el histórico
                receta = st.session_state.db_recetas[st.session_state.db_recetas["Combo"] == c_v]
                cd = 0
                for _, r in receta.iterrows():
                    idx = st.session_state.db_inv.index[st.session_state.db_inv["Insumo"] == r["Insumo"]][0]
                    st.session_state.db_inv.at[idx, "Stock"] -= (r["Cantidad"] * can_v)
                    cd += st.session_state.db_inv.at[idx, "Costo_Unit_Bs"] * (r["Cantidad"] * can_v)
                
                ci = st.session_state.db_costos_ind[st.session_state.db_costos_ind["Combo"] == c_v]["Monto_Bs"].sum() * can_v
                pv = st.session_state.db_combos[st.session_state.db_combos["Nombre_Combo"] == c_v]["Precio_Venta_Bs"].values[0]
                
                nv = pd.DataFrame([{"Fecha": datetime.now(), "Combo": c_v, "Total_Bs": pv * can_v, "Costo_Directo": cd, "Costo_Indirecto": ci}])
                st.session_state.db_ventas = pd.concat([st.session_state.db_ventas, nv], ignore_index=True)
                st.success("Venta registrada")

    # --- 6. GASTOS ---
    elif opcion == "💸 Gastos (Luz/Agua)":
        st.header("💸 Gastos Operativos Mensuales")
        with st.form("g"):
            con = st.text_input("Concepto (Agua, Luz, Alquiler)")
            mon = st.number_input("Monto Bs", min_value=0.0)
            if st.form_submit_button("Registrar Gasto"):
                st.session_state.db_gastos = pd.concat([st.session_state.db_gastos, pd.DataFrame([{"Fecha": datetime.now(), "Concepto": con, "Monto_Bs": mon}])], ignore_index=True)
        st.dataframe(st.session_state.db_gastos)

    # --- 7. BALANCE ---
    elif opcion == "📊 Balance y Utilidades":
        st.header("📊 Estados Financieros")
        vt = st.session_state.db_ventas['Total_Bs'].sum()
        cd_t = st.session_state.db_ventas['Costo_Directo'].sum()
        ci_t = st.session_state.db_ventas['Costo_Indirecto'].sum()
        gt = st.session_state.db_gastos['Monto_Bs'].sum()
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### Estado de Resultados")
            st.write(f"Ventas: {vt:,.2f} Bs")
            st.write(f"(-) Costos Directos: {cd_t:,.2f} Bs")
            st.write(f"(-) Costos Indirectos: {ci_t:,.2f} Bs")
            st.divider()
            st.write(f"Utilidad Bruta: {vt - cd_t - ci_t:,.2f} Bs")
            st.write(f"(-) Gastos Operativos: {gt:,.2f} Bs")
            st.metric("UTILIDAD NETA", f"{vt - cd_t - ci_t - gt:,.2f} Bs")
