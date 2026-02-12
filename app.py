import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="GLOBAL WINGS - ERP FINANCIERO", layout="wide")

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
        st.session_state.db_ventas = pd.DataFrame(columns=["Fecha", "Combo", "Total_Bs", "Costo_Dir", "Costo_Ind", "Metodo"])
    if 'db_flujo_caja' not in st.session_state:
        st.session_state.db_flujo_caja = pd.DataFrame(columns=["Fecha", "Concepto", "Tipo", "Monto_Bs"])
    if 'finanzas_base' not in st.session_state:
        st.session_state.finanzas_base = {"inversion": 0.0, "pasivos": 0.0}

    # --- NAVEGACIÓN ---
    st.sidebar.title("🦅 GLOBAL WINGS")
    opcion = st.sidebar.radio("Navegación", 
        ["🏠 Inicio", "📦 Almacén (Insumos Directos)", "👨‍🍳 Ingeniería de Recetas", "🍳 Activos y Equipos", "💰 Punto de Venta", "🏧 Caja y Flujo de Efectivo", "📊 Balance y Finanzas"])

    # --- 1. INICIO (DASHBOARD) ---
    if opcion == "🏠 Inicio":
        st.header("🏠 Panel de Control Global Wings")
        
        # Cálculos de Caja
        ingresos_caja = st.session_state.db_flujo_caja[st.session_state.db_flujo_caja['Tipo'] == 'Ingreso']['Monto_Bs'].sum()
        egresos_caja = st.session_state.db_flujo_caja[st.session_state.db_flujo_caja['Tipo'] == 'Egreso']['Monto_Bs'].sum()
        saldo_caja = ingresos_caja - egresos_caja + st.session_state.finanzas_base['inversion']
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Efectivo en Caja", f"{saldo_caja:,.2f} Bs")
        c2.metric("Ventas Totales", f"{st.session_state.db_ventas['Total_Bs'].sum():,.2f} Bs")
        c3.metric("Valor Inventario", f"{(st.session_state.db_inv['Stock'] * st.session_state.db_inv['Costo_Unit_Bs']).sum():,.2f} Bs")
        c4.metric("Inversión Inicial", f"{st.session_state.finanzas_base['inversion']:,.2f} Bs")

        st.divider()
        st.subheader("Últimas Ventas")
        st.dataframe(st.session_state.db_ventas.tail(5), use_container_width=True)

    # --- 2. ALMACÉN ---
    elif opcion == "📦 Almacén (Insumos Directos)":
        st.header("📦 Inventario de Materia Prima")
        with st.form("n_i"):
            c1, c2, c3 = st.columns(3)
            nom = c1.text_input("Insumo (Pollo, Papa, etc)")
            uni = c2.selectbox("Unidad", ["Kg", "Unidad", "Litro", "Gramo"])
            if st.form_submit_button("Crear Insumo"):
                st.session_state.db_inv = pd.concat([st.session_state.db_inv, pd.DataFrame([{"Insumo": nom, "Unidad": uni, "Stock": 0.0, "Costo_Unit_Bs": 0.0}])], ignore_index=True)
        
        st.subheader("🛒 Registro de Compras (Entrada)")
        if not st.session_state.db_inv.empty:
            with st.form("compra"):
                ins_sel = st.selectbox("Insumo", st.session_state.db_inv["Insumo"])
                cant_c = st.number_input("Cantidad", min_value=0.01)
                costo_t = st.number_input("Costo Total (Bs)", min_value=0.01)
                if st.form_submit_button("Actualizar Stock y Caja"):
                    idx = st.session_state.db_inv.index[st.session_state.db_inv['Insumo'] == ins_sel][0]
                    st.session_state.db_inv.at[idx, 'Stock'] += cant_c
                    st.session_state.db_inv.at[idx, 'Costo_Unit_Bs'] = costo_t / cant_c
                    # Registrar Egreso en Caja
                    st.session_state.db_flujo_caja = pd.concat([st.session_state.db_flujo_caja, pd.DataFrame([{"Fecha": datetime.now(), "Concepto": f"Compra {ins_sel}", "Tipo": "Egreso", "Monto_Bs": costo_t}])], ignore_index=True)
                    st.success("Inventario aumentado y egreso de caja registrado.")
        st.dataframe(st.session_state.db_inv)

    # --- 3. INGENIERÍA DE RECETAS ---
    elif opcion == "👨‍🍳 Ingeniería de Recetas":
        st.header("👨‍🍳 Costeo de Producción")
        if not st.session_state.db_combos.empty:
            combo = st.selectbox("Elegir Combo", st.session_state.db_combos["Nombre_Combo"])
            
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("Costo Directo (Insumos)")
                ins_r = st.selectbox("Insumo del Almacén", st.session_state.db_inv["Insumo"] if not st.session_state.db_inv.empty else [])
                can_r = st.number_input("Cantidad Necesaria", min_value=0.001)
                if st.button("Añadir Ingrediente"):
                    st.session_state.db_recetas = pd.concat([st.session_state.db_recetas, pd.DataFrame([{"Combo": combo, "Insumo": ins_r, "Cantidad": can_r}])], ignore_index=True)
            
            with c2:
                st.subheader("Costo Indirecto (Salsas, Empaque, Gas)")
                con_i = st.text_input("Concepto Indirecto")
                mon_i = st.number_input("Costo por unidad (Bs)", min_value=0.0)
                if st.button("Añadir Costo Indirecto"):
                    st.session_state.db_costos_ind = pd.concat([st.session_state.db_costos_ind, pd.DataFrame([{"Combo": combo, "Concepto": con_i, "Monto_Bs": mon_i}])], ignore_index=True)
            
            st.divider()
            # Análisis automático
            cd = 0
            rec = st.session_state.db_recetas[st.session_state.db_recetas["Combo"] == combo]
            for _, r in rec.iterrows():
                cu = st.session_state.db_inv[st.session_state.db_inv["Insumo"] == r["Insumo"]]["Costo_Unit_Bs"].values[0]
                cd += cu * r["Cantidad"]
            ci = st.session_state.db_costos_ind[st.session_state.db_costos_ind["Combo"] == combo]["Monto_Bs"].sum()
            pv = st.session_state.db_combos[st.session_state.db_combos["Nombre_Combo"] == combo]["Precio_Venta_Bs"].values[0]
            
            st.info(f"**Análisis de {combo}:** Costo Dir: {cd:,.2f} Bs | Costo Ind: {ci:,.2f} Bs | Total: {cd+ci:,.2f} Bs | **Utilidad: {pv - (cd+ci):,.2f} Bs**")
        else:
            st.warning("Debe crear un combo en la pestaña de Punto de Venta o Inicio primero.")

    # --- 4. PUNTO DE VENTA ---
    elif opcion == "💰 Punto de Venta":
        st.header("💰 Punto de Venta")
        with st.expander("➕ Crear/Editar Combo"):
            with st.form("n_c"):
                nom_c = st.text_input("Nombre del Combo")
                pre_c = st.number_input("Precio de Venta (Bs)", min_value=0.1)
                if st.form_submit_button("Registrar Combo"):
                    st.session_state.db_combos = pd.concat([st.session_state.db_combos, pd.DataFrame([{"Nombre_Combo": nom_c, "Precio_Venta_Bs": pre_c}])], ignore_index=True)

        if not st.session_state.db_combos.empty:
            sel_v = st.selectbox("Combo a Vender", st.session_state.db_combos["Nombre_Combo"])
            can_v = st.number_input("Cantidad", min_value=1)
            met_v = st.radio("Método", ["Efectivo", "QR"])
            if st.button("Finalizar Venta"):
                # Descontar Inventario y calcular costo
                receta = st.session_state.db_recetas[st.session_state.db_recetas["Combo"] == sel_v]
                cd_v = 0
                for _, r in receta.iterrows():
                    idx = st.session_state.db_inv.index[st.session_state.db_inv["Insumo"] == r["Insumo"]][0]
                    st.session_state.db_inv.at[idx, "Stock"] -= (r["Cantidad"] * can_v)
                    cd_v += st.session_state.db_inv.at[idx, "Costo_Unit_Bs"] * (r["Cantidad"] * can_v)
                
                ci_v = st.session_state.db_costos_ind[st.session_state.db_costos_ind["Combo"] == sel_v]["Monto_Bs"].sum() * can_v
                pv_v = st.session_state.db_combos[st.session_state.db_combos["Nombre_Combo"] == sel_v]["Precio_Venta_Bs"].values[0] * can_v
                
                # Registrar Venta y Caja
                st.session_state.db_ventas = pd.concat([st.session_state.db_ventas, pd.DataFrame([{"Fecha": datetime.now(), "Combo": sel_v, "Total_Bs": pv_v, "Costo_Dir": cd_v, "Costo_Ind": ci_v, "Metodo": met_v}])], ignore_index=True)
                st.session_state.db_flujo_caja = pd.concat([st.session_state.db_flujo_caja, pd.DataFrame([{"Fecha": datetime.now(), "Concepto": f"Venta {sel_v}", "Tipo": "Ingreso", "Monto_Bs": pv_v}])], ignore_index=True)
                st.success("Venta Exitosa")

    # --- 5. CAJA Y FLUJO ---
    elif opcion == "🏧 Caja y Flujo de Efectivo":
        st.header("🏧 Control de Caja y Gastos")
        with st.form("g"):
            con = st.text_input("Concepto (Luz, Agua, Alquiler, etc)")
            mon = st.number_input("Monto Bs", min_value=0.0)
            if st.form_submit_button("Registrar Salida de Caja"):
                st.session_state.db_flujo_caja = pd.concat([st.session_state.db_flujo_caja, pd.DataFrame([{"Fecha": datetime.now(), "Concepto": con, "Tipo": "Egreso", "Monto_Bs": mon}])], ignore_index=True)
        st.subheader("Historial de Movimientos")
        st.dataframe(st.session_state.db_flujo_caja, use_container_width=True)

    # --- 6. BALANCE Y FINANZAS ---
    elif opcion == "📊 Balance y Finanzas":
        st.header("📊 Estados Financieros")
        with st.expander("⚙️ Configuración de Capital y Pasivos"):
            st.session_state.finanzas_base['inversion'] = st.number_input("Inversión Inicial", value=st.session_state.finanzas_base['inversion'])
            st.session_state.finanzas_base['pasivos'] = st.number_input("Deudas (Pasivos)", value=st.session_state.finanzas_base['pasivos'])

        # Cálculos Finales
        v_netas = st.session_state.db_ventas['Total_Bs'].sum()
        cd_t = st.session_state.db_ventas['Costo_Dir'].sum()
        ci_t = st.session_state.db_ventas['Costo_Ind'].sum()
        gastos_op = st.session_state.db_flujo_caja[st.session_state.db_flujo_caja['Concepto'].str.contains("Venta|Compra") == False]['Monto_Bs'].sum()
        utilidad_n = (v_netas - cd_t - ci_t) - gastos_op
        
        val_inv = (st.session_state.db_inv['Stock'] * st.session_state.db_inv['Costo_Unit_Bs']).sum()
        act_f = st.session_state.db_activos['Valor_Bs'].sum()
        caja_final = st.session_state.db_flujo_caja[st.session_state.db_flujo_caja['Tipo'] == 'Ingreso']['Monto_Bs'].sum() - st.session_state.db_flujo_caja[st.session_state.db_flujo_caja['Tipo'] == 'Egreso']['Monto_Bs'].sum() + st.session_state.finanzas_base['inversion']

        t1, t2 = st.tabs(["📉 Estado de Resultados", "🏛️ Balance General"])
        with t1:
            st.write(f"**Ventas:** {v_netas:,.2f} Bs")
            st.write(f"**Costo de Producción (Dir+Ind):** {cd_t + ci_t:,.2f} Bs")
            st.write(f"**Gastos Operativos (Agua, Luz, etc):** {gastos_op:,.2f} Bs")
            st.divider()
            st.metric("UTILIDAD NETA", f"{utilidad_n:,.2f} Bs")

        with t2:
            st.markdown("### Balance de Global Wings")
            c_a, c_b = st.columns(2)
            with c_a:
                st.info("**ACTIVOS**")
                st.write(f"Efectivo en Caja: {caja_final:,.2f} Bs")
                st.write(f"Inventarios: {val_inv:,.2f} Bs")
                st.write(f"Activos Fijos: {act_f:,.2f} Bs")
                st.divider()
                st.write(f"**TOTAL ACTIVOS:** {caja_final + val_inv + act_f:,.2f} Bs")
            with c_b:
                st.error("**PASIVOS Y PATRIMONIO**")
                st.write(f"Deudas (Pasivos): {st.session_state.finanzas_base['pasivos']:,.2f} Bs")
                st.write(f"Capital Social (Inversión): {st.session_state.finanzas_base['inversion']:,.2f} Bs")
                st.write(f"Utilidad Retenida: {utilidad_n:,.2f} Bs")
                st.divider()
                st.write(f"**TOTAL PAS+PAT:** {st.session_state.finanzas_base['pasivos'] + st.session_state.finanzas_base['inversion'] + utilidad_n:,.2f} Bs")
