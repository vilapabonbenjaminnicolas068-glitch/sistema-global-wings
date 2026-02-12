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
                    st.session_state.db_caja = pd.concat([st.session_state.db_caja, g], ignore_index=True)
                    st.success("Inventario y Caja actualizados.")
        st.dataframe(st.session_state.db_inv)

    # --- 3. ACTIVOS ---
    elif menu == "🍳 Activos y Equipos":
        st.header("🍳 Activos Fijos")
        with st.form("f_act"):
            ac = st.text_input("Nombre del Activo (Sartén, Freidora)")
            mo = st.number_input("Valor Bs", min_value=0.0)
            if st.form_submit_button("Registrar Activo"):
                n = pd.DataFrame([{"Activo": ac, "Monto_Bs": mo}])
                st.session_state.db_activos = pd.concat([st.session_state.db_activos, n], ignore_index=True)
        st.dataframe(st.session_state.db_activos)

    # --- 4. RECETAS ---
    elif menu == "👨‍🍳 Recetas y Costos":
        st.header("👨‍🍳 Ingeniería de Menú")
        with st.form("f_comb"):
            nom = st.text_input("Nombre del Combo")
            pre = st.number_input("Precio Venta Bs", min_value=0.0)
            if st.form_submit_button("Crear Combo"):
                st.session_state.db_combos = pd.concat([st.session_state.db_combos, pd.DataFrame([{"Nombre": nom, "Precio_Bs": pre}])], ignore_index=True)
        
        if not st.session_state.db_combos.empty:
            st.divider()
            c1, c2 = st.columns(2)
            sel_c = c1.selectbox("Combo", st.session_state.db_combos["Nombre"])
            # Validación de insumos existentes para evitar error
            if not st.session_state.db_inv.empty:
                sel_i = c1.selectbox("Añadir Insumo", st.session_state.db_inv["Insumo"])
                can_r = c2.number_input("Cantidad Necesaria", min_value=0.001)
                if st.button("Vincular Insumo a la Receta"):
                    n = pd.DataFrame([{"Combo": sel_c, "Insumo": sel_i, "Cantidad": can_r}])
                    st.session_state.db_recetas = pd.concat([st.session_state.db_recetas, n], ignore_index=True)
            
            # --- CORRECCIÓN LÍNEA 142 (CÁLCULO SEGURO) ---
            st.subheader("📊 Análisis de Rentabilidad")
            rec = st.session_state.db_recetas[st.session_state.db_recetas["Combo"] == sel_c]
            costo_total = 0.0
            if not rec.empty:
                for _, r in rec.iterrows():
                    insumo_data = st.session_state.db_inv[st.session_state.db_inv["Insumo"] == r["Insumo"]]
                    if not insumo_data.empty:
                        c_u = insumo_data["Costo_Unit_Bs"].values[0]
                        costo_total += float(c_u) * float(r["Cantidad"])
            
            precio_row = st.session_state.db_combos[st.session_state.db_combos["Nombre"] == sel_c]
            precio = float(precio_row["Precio_Bs"].values[0]) if not precio_row.empty else 0.0
            st.info(f"Combo: {sel_c} | Costo Producción: {costo_total:,.2f} Bs | Utilidad: {precio - costo_total:,.2f} Bs")

    # --- 5. PUNTO DE VENTA ---
    elif menu == "💰 Punto de Venta":
        st.header("💰 Caja Registradora")
        if not st.session_state.db_combos.empty:
            c_sel = st.selectbox("Elegir Combo", st.session_state.db_combos["Nombre"])
            c_cant = st.number_input("Cantidad", min_value=1)
            c_met = st.radio("Método", ["Efectivo", "QR"])
            
            if st.button("🚀 FINALIZAR VENTA"):
                receta = st.session_state.db_recetas[st.session_state.db_recetas["Combo"] == c_sel]
                c_vta = 0.0
                if not receta.empty:
                    for _, r in receta.iterrows():
                        idx = st.session_state.db_inv.index[st.session_state.db_inv["Insumo"] == r["Insumo"]][0]
                        st.session_state.db_inv.at[idx, "Stock"] -= (r["Cantidad"] * c_cant)
                        c_vta += st.session_state.db_inv.at[idx, "Costo_Unit_Bs"] * (r["Cantidad"] * c_cant)
                
                pv = st.session_state.db_combos[st.session_state.db_combos["Nombre"] == c_sel]["Precio_Bs"].values[0]
                n_v = pd.DataFrame([{"Fecha": datetime.now(), "Combo": c_sel, "Total_Bs": pv * c_cant, "Costo_Total": c_vta, "Metodo": c_met}])
                st.session_state.db_ventas = pd.concat([st.session_state.db_ventas, n_v], ignore_index=True)
                n_c = pd.DataFrame([{"Fecha": datetime.now(), "Concepto": f"Venta {c_sel}", "Monto_Bs": pv * c_cant, "Tipo": "Ingreso"}])
                st.session_state.db_caja = pd.concat([st.session_state.db_caja, n_c], ignore_index=True)
                st.success("Venta procesada con éxito.")

    # --- 6. BALANCE Y FINANZAS ---
    elif menu == "🏛️ Balance y Finanzas":
        st.header("📊 Estados Financieros")
        with st.expander("⚙️ Configuración de Capital"):
            st.session_state.config['inversion'] = st.number_input("Inversión Inicial Bs", value=st.session_state.config['inversion'])
            st.session_state.config['caja_inicial'] = st.number_input("Efectivo de Apertura Bs", value=st.session_state.config['caja_inicial'])
        
        with st.form("f_gastos"):
            con = st.text_input("Concepto Gasto (Luz, Agua, Alquiler)")
            mon = st.number_input("Monto Bs", min_value=0.0)
            if st.form_submit_button("Registrar Gasto"):
                g = pd.DataFrame([{"Fecha": datetime.now(), "Concepto": con, "Monto_Bs": mon, "Tipo": "Egreso"}])
                st.session_state.db_caja = pd.concat([st.session_state.db_caja, g], ignore_index=True)

        v_t = st.session_state.db_ventas['Total_Bs'].sum()
        c_v = st.session_state.db_ventas['Costo_Total'].sum()
        g_t = st.session_state.db_caja[~st.session_state.db_caja['Concepto'].str.contains("Compra|Venta", na=False)]['Monto_Bs'].sum()
        utilidad = (v_t - c_v) - g_t
        val_inv = (st.session_state.db_inv['Stock'] * st.session_state.db_inv['Costo_Unit_Bs']).sum()
        val_act = st.session_state.db_activos['Monto_Bs'].sum()
        ing = st.session_state.db_caja[st.session_state.db_caja['Tipo'] == 'Ingreso']['Monto_Bs'].sum()
        egr = st.session_state.db_caja[st.session_state.db_caja['Tipo'] == 'Egreso']['Monto_Bs'].sum()
        efectivo = ing - egr + st.session_state.config['caja_inicial']

        tab1, tab2 = st.tabs(["📉 Estado de Resultados", "🏛️ Balance General"])
        with tab1:
            st.write(f"**Ventas:** {v_t:,.2f} Bs | **Costo CMV:** {c_v:,.2f} Bs | **Gastos:** {g_t:,.2f} Bs")
            st.metric("UTILIDAD NETA", f"{utilidad:,.2f} Bs")
        with tab2:
            st.subheader("Balance General")
            col1, col2 = st.columns(2)
            with col1:
                st.info("**ACTIVOS**")
                st.write(f"Efectivo: {efectivo:,.2f} Bs")
                st.write(f"Inventario: {val_inv:,.2f} Bs")
                st.write(f"Equipos: {val_act:,.2f} Bs")
                st.divider()
                st.write(f"**TOTAL ACTIVOS:** {efectivo + val_inv + val_act:,.2f} Bs")
            with col2:
                st.success("**PATRIMONIO**")
                st.write(f"Inversión Inicial: {st.session_state.config['inversion']:,.2f} Bs")
                st.write(f"Utilidad del Periodo: {utilidad:,.2f} Bs")
                st.divider()
                st.write(f"**TOTAL PATRIMONIO:** {st.session_state.config['inversion'] + utilidad:,.2f} Bs")
