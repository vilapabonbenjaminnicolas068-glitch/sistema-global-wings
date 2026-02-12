import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="GLOBAL WINGS - SISTEMA EMPRESARIAL", layout="wide")

# --- LOGIN ---
def check_password():
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
        return False
    return True

if check_password():
    # --- INICIALIZACIÓN DE DATOS ---
    for db in ['db_inv', 'db_recetas', 'db_combos', 'db_ventas', 'db_caja', 'db_clientes']:
        if db not in st.session_state:
            if db == 'db_inv': st.session_state[db] = pd.DataFrame(columns=["Insumo", "Tipo", "Unidad", "Stock", "Costo_Unit_Bs"])
            elif db == 'db_clientes': st.session_state[db] = pd.DataFrame(columns=["Codigo", "Nombre", "Celular"])
            elif db == 'db_ventas': st.session_state[db] = pd.DataFrame(columns=["Fecha", "Cliente", "Combo", "Extras", "Total_Bs", "Costo_Total", "Metodo", "Estado"])
            else: st.session_state[db] = pd.DataFrame()

    st.sidebar.title("🦅 GLOBAL WINGS")
    opcion = st.sidebar.radio("Navegación", ["🏠 Inicio", "🍗 Inventario & Compras", "🍔 Combos & Extras", "💰 Punto de Venta", "👥 Clientes", "📊 Reportes Financieros"])

    # --- 1. INICIO ---
    if opcion == "🏠 Inicio":
        st.header("🏠 Panel Principal")
        v_ok = st.session_state.db_ventas[st.session_state.db_ventas['Estado'] == 'Confirmado']
        c1, c2, c3 = st.columns(3)
        c1.metric("Ventas Hoy (Bs)", f"{v_ok['Total_Bs'].sum():,.2f}")
        c2.metric("Pedidos Realizados", len(v_ok))
        c3.metric("Clientes Registrados", len(st.session_state.db_clientes))
        
        st.subheader("Ventas Recientes")
        st.dataframe(v_ok.tail(10), use_container_width=True)

    # --- 2. INVENTARIO & COMPRAS ---
    elif opcion == "🍗 Inventario & Compras":
        st.header("🍗 Gestión de Suministros")
        with st.expander("➕ Añadir Nuevo Insumo"):
            with st.form("n_insumo"):
                n = st.text_input("Nombre del Insumo")
                t = st.selectbox("Tipo", ["Directo Combo", "Insumo General", "Extra/Adicional"])
                u = st.selectbox("Unidad", ["Unidad", "Kilos", "Litros", "Porción"])
                if st.form_submit_button("Guardar"):
                    nuevo = pd.DataFrame([{"Insumo": n, "Tipo": t, "Unidad": u, "Stock": 0.0, "Costo_Unit_Bs": 0.0}])
                    st.session_state.db_inv = pd.concat([st.session_state.db_inv, nuevo], ignore_index=True)
        
        st.subheader("Cargar Compras / Aumentar Stock")
        if not st.session_state.db_inv.empty:
            with st.form("compra"):
                ins = st.selectbox("Insumo", st.session_state.db_inv["Insumo"])
                can = st.number_input("Cantidad Comprada", min_value=0.1)
                pre = st.number_input("Costo Total (Bs)", min_value=0.1)
                if st.form_submit_button("Registrar Compra"):
                    idx = st.session_state.db_inv.index[st.session_state.db_inv['Insumo'] == ins][0]
                    st.session_state.db_inv.at[idx, 'Stock'] += can
                    st.session_state.db_inv.at[idx, 'Costo_Unit_Bs'] = pre / can
                    st.success("Inventario actualizado y costo recalculado.")

    # --- 3. COMBOS & EXTRAS ---
    elif opcion == "🍔 Combos & Extras":
        st.header("🍔 Ingeniería de Menú")
        with st.form("c_combo"):
            nom = st.text_input("Nombre del Combo")
            pre = st.number_input("Precio de Venta (Bs)", min_value=0.0)
            if st.form_submit_button("Crear Combo"):
                st.session_state.db_combos = pd.concat([st.session_state.db_combos, pd.DataFrame([{"Nombre_Combo": nom, "Precio_Venta_Bs": pre}])], ignore_index=True)
        
        st.divider()
        st.subheader("Receta del Combo")
        if not st.session_state.db_combos.empty:
            sel_c = st.selectbox("Elegir Combo", st.session_state.db_combos["Nombre_Combo"])
            sel_i = st.selectbox("Añadir Insumo a la Receta", st.session_state.db_inv["Insumo"])
            cant_r = st.number_input("Cantidad de este insumo", min_value=0.01)
            if st.button("Vincular Insumo"):
                st.session_state.db_recetas = pd.concat([st.session_state.db_recetas, pd.DataFrame([{"Combo": sel_c, "Insumo": sel_i, "Cantidad": cant_r}])], ignore_index=True)
                st.success("Actualizado")

    # --- 4. PUNTO DE VENTA (PERSONALIZADO) ---
    elif opcion == "💰 Punto de Venta":
        st.header("💰 Toma de Pedidos")
        col1, col2 = st.columns(2)
        with col1:
            cliente = st.selectbox("Cliente Registrado", ["Público General"] + st.session_state.db_clientes["Nombre"].tolist())
            combo = st.selectbox("Combo Principal", st.session_state.db_combos["Nombre_Combo"] if not st.session_state.db_combos.empty else [])
            metodo = st.radio("Método de Pago", ["Efectivo", "QR / Transferencia"])
        
        with col2:
            st.write("🛒 **Adicionales / Extras**")
            extras_list = st.session_state.db_inv[st.session_state.db_inv["Tipo"] == "Extra/Adicional"]["Insumo"].tolist()
            extras_sel = st.multiselect("Añadir Extras al pedido", extras_list)
            cant_v = st.number_input("Cantidad de Combos", min_value=1)

        if st.button("⚡ CONFIRMAR Y FINALIZAR VENTA"):
            # Lógica de descuento y costo
            costo_total = 0
            receta = st.session_state.db_recetas[st.session_state.db_recetas["Combo"] == combo]
            
            # 1. Descontar Combo
            for _, r in receta.iterrows():
                idx = st.session_state.db_inv.index[st.session_state.db_inv["Insumo"] == r["Insumo"]][0]
                st.session_state.db_inv.at[idx, "Stock"] -= (r["Cantidad"] * cant_v)
                costo_total += st.session_state.db_inv.at[idx, "Costo_Unit_Bs"] * (r["Cantidad"] * cant_v)
            
            # 2. Descontar Extras
            for ex in extras_sel:
                idx_ex = st.session_state.db_inv.index[st.session_state.db_inv["Insumo"] == ex][0]
                st.session_state.db_inv.at[idx_ex, "Stock"] -= 1
                costo_total += st.session_state.db_inv.at[idx_ex, "Costo_Unit_Bs"]

            precio_v = st.session_state.db_combos[st.session_state.db_combos["Nombre_Combo"] == combo]["Precio_Venta_Bs"].values[0]
            nv = pd.DataFrame([{"Fecha": datetime.now(), "Cliente": cliente, "Combo": combo, "Extras": ", ".join(extras_sel), "Total_Bs": precio_v * cant_v, "Costo_Total": costo_total, "Metodo": metodo, "Estado": "Confirmado"}])
            st.session_state.db_ventas = pd.concat([st.session_state.db_ventas, nv], ignore_index=True)
            st.balloons()
            st.success("Venta procesada con éxito")

    # --- 5. CLIENTES ---
    elif opcion == "👥 Clientes":
        st.header("👥 CRM Clientes")
        with st.form("n_c"):
            nom = st.text_input("Nombre Completo")
            cel = st.text_input("Celular")
            if st.form_submit_button("Registrar Cliente"):
                cod = f"GW-{len(st.session_state.db_clientes)+1}"
                st.session_state.db_clientes = pd.concat([st.session_state.db_clientes, pd.DataFrame([{"Codigo": cod, "Nombre": nom, "Celular": cel}])], ignore_index=True)

    # --- 6. REPORTES FINANCIEROS (PRO) ---
    elif opcion == "📊 Reportes Financieros":
        st.header("📈 Estados Financieros")
        
        v_ok = st.session_state.db_ventas[st.session_state.db_ventas['Estado'] == 'Confirmado']
        ingresos = v_ok['Total_Bs'].sum()
        costo_v = v_ok['Costo_Total'].sum()
        inv_val = (st.session_state.db_inv['Stock'] * st.session_state.db_inv['Costo_Unit_Bs']).sum()
        caja = ingresos # Simplificado

        t1, t2 = st.tabs(["📉 Estado de Resultados", "🏛️ Balance General"])
        
        with t1:
            st.markdown("### ESTADO DE RESULTADOS")
            st.write(f"**(+) INGRESOS OPERATIVOS:** {ingresos:,.2f} Bs")
            st.write(f"**(-) COSTO DE VENTAS:** {costo_v:,.2f} Bs")
            st.divider()
            st.write(f"**(=) UTILIDAD BRUTA:** {ingresos - costo_v:,.2f} Bs")
            st.write("**(-) GASTOS ADMINISTRATIVOS:** 0.00 Bs")
            st.metric("UTILIDAD NETA", f"{ingresos - costo_v:,.2f} Bs")

        with t2:
            st.markdown("### BALANCE GENERAL")
            col_a, col_b = st.columns(2)
            with col_a:
                st.write("**ACTIVOS**")
                st.write(f"Caja y Bancos: {caja:,.2f} Bs")
                st.write(f"Inventario Mercaderías: {inv_val:,.2f} Bs")
                st.divider()
                st.write(f"**TOTAL ACTIVOS:** {caja + inv_val:,.2f} Bs")
            with col_b:
                st.write("**PATRIMONIO**")
                st.write(f"Utilidad del Periodo: {ingresos - costo_v:,.2f} Bs")
                st.divider()
                st.write(f"**TOTAL PATRIMONIO:** {ingresos - costo_v:,.2f} Bs")
