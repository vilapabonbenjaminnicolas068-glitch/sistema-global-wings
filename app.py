import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="GLOBAL WINGS - ERP TOTAL", layout="wide")

# --- LOGIN ---
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if not st.session_state.authenticated:
        st.title("🦅 Global Wings - Sistema Administrativo")
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
    # --- INICIALIZACIÓN DE BASES DE DATOS ---
    if 'db_inv' not in st.session_state:
        st.session_state.db_inv = pd.DataFrame(columns=["Insumo", "Tipo", "Unidad", "Stock", "Costo_Unit_Bs"])
    if 'db_recetas' not in st.session_state:
        st.session_state.db_recetas = pd.DataFrame(columns=["Combo", "Insumo", "Cantidad"])
    if 'db_combos' not in st.session_state:
        st.session_state.db_combos = pd.DataFrame(columns=["Nombre_Combo", "Precio_Venta_Bs"])
    if 'db_ventas' not in st.session_state:
        st.session_state.db_ventas = pd.DataFrame(columns=["Fecha", "Cliente", "Combo", "Total_Bs", "Costo_Total", "Metodo"])
    if 'db_clientes' not in st.session_state:
        st.session_state.db_clientes = pd.DataFrame(columns=["Codigo", "Nombre", "Celular"])
    if 'finanzas' not in st.session_state:
        st.session_state.finanzas = {"inversion_inicial": 0.0, "pasivos": 0.0, "otros_gastos": 0.0}

    st.sidebar.title("🦅 GLOBAL WINGS")
    opcion = st.sidebar.radio("Navegación", 
        ["🏠 Inicio", "📦 Monitor de Stock", "🍗 Inventario & Compras", "🍔 Ingeniería de Combos", "💰 Punto de Venta", "👥 Clientes & Historial", "📊 Estados Financieros"])

    # --- 1. INICIO ---
    if opcion == "🏠 Inicio":
        st.header("🏠 Panel General")
        v = st.session_state.db_ventas
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Ventas Acumuladas", f"{v['Total_Bs'].sum():,.2f} Bs")
        c2.metric("Inversión Inicial", f"{st.session_state.finanzas['inversion_inicial']:,.2f} Bs")
        c3.metric("Deudas (Pasivos)", f"{st.session_state.finanzas['pasivos']:,.2f} Bs")
        c4.metric("Clientes", len(st.session_state.db_clientes))
        
        st.subheader("Últimas 5 Ventas")
        st.dataframe(v.tail(5), use_container_width=True)

    # --- 2. MONITOR DE STOCK ---
    elif opcion == "📦 Monitor de Stock":
        st.header("📦 Estado del Inventario")
        if not st.session_state.db_inv.empty:
            df_view = st.session_state.db_inv.copy()
            df_view['Valor_Total_Bs'] = df_view['Stock'] * df_view['Costo_Unit_Bs']
            st.dataframe(df_view, use_container_width=True)
        else:
            st.warning("Inventario vacío.")

    # --- 3. GESTIÓN INVENTARIO ---
    elif opcion == "🍗 Inventario & Compras":
        st.header("🍗 Suministros y Compras")
        with st.expander("➕ Crear Insumo o Extra"):
            with st.form("n_i"):
                nom = st.text_input("Nombre")
                tip = st.selectbox("Categoría", ["Insumo Combo", "Extra (Para Venta)", "Gasto Operativo"])
                uni = st.selectbox("Unidad", ["Unidad", "Kg", "Litro", "Porción"])
                if st.form_submit_button("Registrar"):
                    n = pd.DataFrame([{"Insumo": nom, "Tipo": tip, "Unidad": uni, "Stock": 0.0, "Costo_Unit_Bs": 0.0}])
                    st.session_state.db_inv = pd.concat([st.session_state.db_inv, n], ignore_index=True)

        st.subheader("🛒 Registrar Compra")
        if not st.session_state.db_inv.empty:
            with st.form("compra"):
                ins = st.selectbox("¿Qué compraste?", st.session_state.db_inv["Insumo"])
                can = st.number_input("Cantidad", min_value=0.1)
                pre = st.number_input("Costo Total de la Compra (Bs)", min_value=0.1)
                if st.form_submit_button("Confirmar Entrada"):
                    idx = st.session_state.db_inv.index[st.session_state.db_inv['Insumo'] == ins][0]
                    st.session_state.db_inv.at[idx, 'Stock'] += can
                    st.session_state.db_inv.at[idx, 'Costo_Unit_Bs'] = pre / can
                    st.success("Stock actualizado.")

    # --- 4. COMBOS ---
    elif opcion == "🍔 Ingeniería de Combos":
        st.header("🍔 Diseño de Menú")
        with st.form("c_combo"):
            nc = st.text_input("Nombre del Combo")
            pv = st.number_input("Precio Venta (Bs)", min_value=0.0)
            if st.form_submit_button("Crear"):
                st.session_state.db_combos = pd.concat([st.session_state.db_combos, pd.DataFrame([{"Nombre_Combo": nc, "Precio_Venta_Bs": pv}])], ignore_index=True)
        
        st.subheader("Añadir Ingredientes")
        if not st.session_state.db_combos.empty:
            sel_c = st.selectbox("Combo", st.session_state.db_combos["Nombre_Combo"])
            sel_i = st.selectbox("Ingrediente", st.session_state.db_inv["Insumo"])
            can_r = st.number_input("Cantidad", min_value=0.01)
            if st.button("Vincular"):
                st.session_state.db_recetas = pd.concat([st.session_state.db_recetas, pd.DataFrame([{"Combo": sel_c, "Insumo": sel_i, "Cantidad": can_r}])], ignore_index=True)

    # --- 5. PUNTO DE VENTA (CON VISTA DE RECETA) ---
    elif opcion == "💰 Punto de Venta":
        st.header("💰 Caja Registradora")
        if not st.session_state.db_combos.empty:
            c1, c2 = st.columns(2)
            with c1:
                cli = st.selectbox("Cliente", ["Público General"] + st.session_state.db_clientes["Nombre"].tolist())
                cmb = st.selectbox("Elegir Combo", st.session_state.db_combos["Nombre_Combo"])
                met = st.radio("Método", ["Efectivo", "QR"])
                
                # MOSTRAR CONTENIDO DEL COMBO
                st.info("**Contenido del Combo:**")
                receta_view = st.session_state.db_recetas[st.session_state.db_recetas["Combo"] == cmb]
                if not receta_view.empty:
                    for _, r in receta_view.iterrows():
                        st.write(f"- {r['Cantidad']} {r['Insumo']}")
                else:
                    st.warning("Este combo no tiene receta.")

            with c2:
                # EXTRAS
                st.write("✨ **Adicionales**")
                extras_db = st.session_state.db_inv[st.session_state.db_inv["Tipo"] == "Extra (Para Venta)"]["Insumo"].tolist()
                ex_sel = st.multiselect("Extras", extras_db)
                can_v = st.number_input("Cantidad de Combos", min_value=1)
                
                if st.button("🚀 CONFIRMAR VENTA"):
                    # Lógica de descuento
                    costo_vta = 0
                    # Descontar receta
                    for _, r in receta_view.iterrows():
                        idx = st.session_state.db_inv.index[st.session_state.db_inv["Insumo"] == r["Insumo"]][0]
                        st.session_state.db_inv.at[idx, "Stock"] -= (r["Cantidad"] * can_v)
                        costo_vta += st.session_state.db_inv.at[idx, "Costo_Unit_Bs"] * (r["Cantidad"] * can_v)
                    
                    p_vta = st.session_state.db_combos[st.session_state.db_combos["Nombre_Combo"] == cmb]["Precio_Venta_Bs"].values[0]
                    nv = pd.DataFrame([{"Fecha": datetime.now(), "Cliente": cli, "Combo": cmb, "Total_Bs": p_vta * can_v, "Costo_Total": costo_vta, "Metodo": met}])
                    st.session_state.db_ventas = pd.concat([st.session_state.db_ventas, nv], ignore_index=True)
                    st.success("Venta Exitosa")

    # --- 6. CLIENTES ---
    elif opcion == "👥 Clientes & Historial":
        st.header("👥 Gestión de Clientes")
        with st.form("n_c"):
            nom = st.text_input("Nombre")
            cel = st.text_input("Celular")
            if st.form_submit_button("Crear"):
                st.session_state.db_clientes = pd.concat([st.session_state.db_clientes, pd.DataFrame([{"Codigo": f"GW-{len(st.session_state.db_clientes)+1}", "Nombre": nom, "Celular": cel}])], ignore_index=True)
        st.dataframe(st.session_state.db_clientes)

    # --- 7. FINANZAS (EL BALANCE CREATIVO) ---
    elif opcion == "📊 Estados Financieros":
        st.header("📊 Finanzas de Global Wings")
        
        with st.expander("⚙️ Configuración Inicial y Deudas"):
            st.session_state.finanzas["inversion_inicial"] = st.number_input("Inversión Inicial (Bs)", value=st.session_state.finanzas["inversion_inicial"])
            st.session_state.finanzas["pasivos"] = st.number_input("Deudas Pendientes (Bs)", value=st.session_state.finanzas["pasivos"])
            st.session_state.finanzas["otros_gastos"] = st.number_input("Gastos Mensuales (Alquiler, etc)", value=st.session_state.finanzas["otros_gastos"])

        v_t = st.session_state.db_ventas['Total_Bs'].sum()
        c_t = st.session_state.db_ventas['Costo_Total'].sum()
        inv_v = (st.session_state.db_inv['Stock'] * st.session_state.db_inv['Costo_Unit_Bs']).sum()
        utilidad = (v_t - c_t) - st.session_state.finanzas["otros_gastos"]

        t1, t2 = st.tabs(["📉 Estado de Resultados", "🏛️ Balance General"])
        
        with t1:
            st.subheader("Estado de Pérdidas y Ganancias")
            st.write(f"**Ventas Totales:** {v_t:,.2f} Bs")
            st.write(f"**(-) Costo de Mercadería:** {c_t:,.2f} Bs")
            st.divider()
            st.write(f"**Utilidad Bruta:** {v_t - c_t:,.2f} Bs")
            st.write(f"**(-) Gastos Operativos:** {st.session_state.finanzas['otros_gastos']:,.2f} Bs")
            st.metric("UTILIDAD NETA", f"{utilidad:,.2f} Bs")

        with t2:
            st.subheader("Situación Patrimonial")
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.info("📦 **ACTIVOS**")
                st.write(f"Efectivo en Caja: {v_t + st.session_state.finanzas['inversion_inicial']:,.2f} Bs")
                st.write(f"Inventario: {inv_v:,.2f} Bs")
                st.divider()
                st.write(f"**TOTAL ACTIVOS:** {(v_t + st.session_state.finanzas['inversion_inicial'] + inv_v):,.2f} Bs")
            
            with col_b:
                st.error("💳 **PASIVOS**")
                st.write(f"Deudas a Terceros: {st.session_state.finanzas['pasivos']:,.2f} Bs")
                st.divider()
                st.write(f"**TOTAL PASIVOS:** {st.session_state.finanzas['pasivos']:,.2f} Bs")

            with col_c:
                st.success("🏦 **PATRIMONIO**")
                st.write(f"Capital Inicial: {st.session_state.finanzas['inversion_inicial']:,.2f} Bs")
                st.write(f"Utilidades: {utilidad:,.2f} Bs")
                st.divider()
                st.write(f"**TOTAL PATRIMONIO:** {st.session_state.finanzas['inversion_inicial'] + utilidad:,.2f} Bs")
