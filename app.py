import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN ESTÉTICA ---
st.set_page_config(page_title="GLOBAL WINGS - MASTER ERP", layout="wide")
st.markdown("""<style> .main { background-color: #f5f5f5; } .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #ddd; } </style>""", unsafe_allow_stdio=True)

# --- LOGIN ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🦅 Global Wings - Acceso Privado")
    user = st.text_input("Usuario Administrador")
    pw = st.text_input("Contraseña", type="password")
    if st.button("Entrar al Sistema"):
        if user == "admin" and pw == "wings2026":
            st.session_state.authenticated = True
            st.rerun()
        else: st.error("Acceso Denegado")
else:
    # --- BASES DE DATOS DINÁMICAS ---
    if 'db_inv' not in st.session_state:
        st.session_state.db_inv = pd.DataFrame(columns=["Insumo", "Unidad", "Stock", "Costo_Unit_Bs", "Alerta_Min"])
    if 'db_recetas' not in st.session_state:
        st.session_state.db_recetas = pd.DataFrame(columns=["Combo", "Insumo", "Cantidad"])
    if 'db_indirectos' not in st.session_state:
        st.session_state.db_indirectos = pd.DataFrame(columns=["Combo", "Detalle", "Costo_Bs"])
    if 'db_combos' not in st.session_state:
        st.session_state.db_combos = pd.DataFrame(columns=["Nombre_Combo", "Precio_Bs"])
    if 'db_ventas' not in st.session_state:
        st.session_state.db_ventas = pd.DataFrame(columns=["Fecha", "Combo", "Total_Bs", "Costo_Total", "Metodo", "Usuario"])
    if 'db_caja_flujo' not in st.session_state:
        st.session_state.db_caja_flujo = pd.DataFrame(columns=["Fecha", "Concepto", "Monto_Bs", "Tipo"])
    if 'config' not in st.session_state:
        st.session_state.config = {"inversion_inicial": 0.0, "caja_apertura": 0.0}

    # --- NAVEGACIÓN ---
    st.sidebar.title("🦅 GLOBAL WINGS v2.0")
    menu = st.sidebar.radio("Módulos del Sistema", 
        ["📊 Dashboard Real-Time", "🏪 Punto de Venta & Caja", "👨‍🍳 Ingeniería de Menú", "📦 Almacén Central", "💸 Gastos y Activos", "🏛️ Balance General Pro"])

    # --- 1. DASHBOARD ---
    if menu == "📊 Dashboard Real-Time":
        st.header("📊 Inteligencia de Negocios")
        v = st.session_state.db_ventas
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Ventas Totales", f"{v['Total_Bs'].sum():,.2f} Bs")
        c2.metric("Utilidad Bruta", f"{(v['Total_Bs'].sum() - v['Costo_Total'].sum()):,.2f} Bs")
        c3.metric("Efectivo en Caja", f"{(st.session_state.db_caja_flujo[st.session_state.db_caja_flujo['Tipo']=='Entrada']['Monto_Bs'].sum() - st.session_state.db_caja_flujo[st.session_state.db_caja_flujo['Tipo']=='Salida']['Monto_Bs'].sum() + st.session_state.config['caja_apertura']):,.2f} Bs")
        c4.metric("Insumos en Riesgo", len(st.session_state.db_inv[st.session_state.db_inv['Stock'] <= st.session_state.db_inv['Alerta_Min']]))
        
        st.divider()
        col_left, col_right = st.columns(2)
        with col_left:
            st.subheader("🔥 Top Combos Vendidos")
            if not v.empty: st.bar_chart(v['Combo'].value_counts())
        with col_right:
            st.subheader("⚠️ Alertas de Inventario")
            st.dataframe(st.session_state.db_inv[st.session_state.db_inv['Stock'] <= st.session_state.db_inv['Alerta_Min']])

    # --- 2. PUNTO DE VENTA & CAJA ---
    elif menu == "🏪 Punto de Venta & Caja":
        st.header("🏪 Terminal de Ventas")
        
        with st.sidebar.expander("🔑 Apertura de Caja"):
            st.session_state.config['caja_apertura'] = st.number_input("Monto Inicial Bs", value=st.session_state.config['caja_apertura'])
        
        if not st.session_state.db_combos.empty:
            c1, c2 = st.columns([2,1])
            with c1:
                sel_c = st.selectbox("Seleccionar Combo", st.session_state.db_combos["Nombre_Combo"])
                metodo = st.selectbox("Método de Pago", ["Efectivo", "QR / Transferencia"])
                cant = st.number_input("Cantidad de Pedidos", min_value=1)
                
                # Mostrar lo que incluye el combo
                receta_info = st.session_state.db_recetas[st.session_state.db_recetas["Combo"] == sel_c]
                st.info(f"📋 **Incluye:** " + ", ".join([f"{r['Cantidad']} {r['Insumo']}" for _, r in receta_info.iterrows()]))
            
            if st.button("🚀 CONFIRMAR Y COBRAR"):
                # Lógica de costos y stock
                costo_vta = 0
                error = False
                for _, r in receta_info.iterrows():
                    idx = st.session_state.db_inv.index[st.session_state.db_inv["Insumo"] == r["Insumo"]][0]
                    if st.session_state.db_inv.at[idx, "Stock"] < (r["Cantidad"] * cant):
                        st.error(f"Stock insuficiente de {r['Insumo']}")
                        error = True
                    costo_vta += st.session_state.db_inv.at[idx, "Costo_Unit_Bs"] * (r["Cantidad"] * cant)
                
                if not error:
                    for _, r in receta_info.iterrows():
                        idx = st.session_state.db_inv.index[st.session_state.db_inv["Insumo"] == r["Insumo"]][0]
                        st.session_state.db_inv.at[idx, "Stock"] -= (r["Cantidad"] * cant)
                    
                    precio = st.session_state.db_combos[st.session_state.db_combos["Nombre_Combo"] == sel_c]["Precio_Bs"].values[0]
                    total_vta = precio * cant
                    # Registrar Venta y Flujo de Caja
                    st.session_state.db_ventas = pd.concat([st.session_state.db_ventas, pd.DataFrame([{"Fecha": datetime.now(), "Combo": sel_c, "Total_Bs": total_vta, "Costo_Total": costo_vta, "Metodo": metodo, "Usuario": "Admin"}])], ignore_index=True)
                    st.session_state.db_caja_flujo = pd.concat([st.session_state.db_caja_flujo, pd.DataFrame([{"Fecha": datetime.now(), "Concepto": f"Venta {sel_c}", "Monto_Bs": total_vta, "Tipo": "Entrada"}])], ignore_index=True)
                    st.success(f"Venta Exitosa: {total_vta} Bs cobrados.")

    # --- 3. INGENIERÍA DE MENÚ (RECETAS) ---
    elif menu == "👨‍🍳 Ingeniería de Menú":
        st.header("👨‍🍳 Costeo Científico de Combos")
        tab1, tab2 = st.tabs(["🆕 Crear Combo", "📊 Análisis de Márgenes"])
        
        with tab1:
            with st.form("f_combo"):
                nc = st.text_input("Nombre del Combo")
                pv = st.number_input("Precio de Venta Bs", min_value=0.0)
                if st.form_submit_button("Registrar Combo"):
                    st.session_state.db_combos = pd.concat([st.session_state.db_combos, pd.DataFrame([{"Nombre_Combo": nc, "Precio_Bs": pv}])], ignore_index=True)
            
            if not st.session_state.db_combos.empty:
                st.divider()
                c_sel = st.selectbox("Añadir Ingredientes a:", st.session_state.db_combos["Nombre_Combo"])
                i_sel = st.selectbox("Insumo Directo", st.session_state.db_inv["Insumo"])
                cant_i = st.number_input("Cantidad Necesaria", min_value=0.001)
                if st.button("Vincular Insumo"):
                    st.session_state.db_recetas = pd.concat([st.session_state.db_recetas, pd.DataFrame([{"Combo": c_sel, "Insumo": i_sel, "Cantidad": cant_i}])], ignore_index=True)

        with tab2:
            st.subheader("Rentabilidad Real por Producto")
            for combo in st.session_state.db_combos["Nombre_Combo"]:
                receta = st.session_state.db_recetas[st.session_state.db_recetas["Combo"] == combo]
                c_insumos = 0
                for _, r in receta.iterrows():
                    c_u = st.session_state.db_inv[st.session_state.db_inv["Insumo"]==r["Insumo"]]["Costo_Unit_Bs"].values[0]
                    c_insumos += c_u * r["Cantidad"]
                
                precio = st.session_state.db_combos[st.session_state.db_combos["Nombre_Combo"] == combo]["Precio_Bs"].values[0]
                utilidad = precio - c_insumos
                st.write(f"**{combo}** | Costo: {c_insumos:,.2f} Bs | Ganancia: {utilidad:,.2f} Bs | **Margen: {(utilidad/precio*100):,.1f}%**")

    # --- 4. ALMACÉN CENTRAL ---
    elif menu == "📦 Almacén Central":
        st.header("📦 Gestión de Materia Prima")
        with st.form("f_inv"):
            c1, c2, c3 = st.columns(3)
            ni = c1.text_input("Nombre Insumo")
            un = c2.selectbox("Unidad", ["Kg", "Lt", "Unidad", "Gramo"])
            al = c3.number_input("Alerta Stock Mínimo", value=5.0)
            if st.form_submit_button("Crear Insumo"):
                st.session_state.db_inv = pd.concat([st.session_state.db_inv, pd.DataFrame([{"Insumo": ni, "Unidad": un, "Stock": 0.0, "Costo_Unit_Bs": 0.0, "Alerta_Min": al}])], ignore_index=True)
        
        st.subheader("📥 Registro de Compras (Entradas)")
        if not st.session_state.db_inv.empty:
            with st.form("f_compra"):
                ins = st.selectbox("¿Qué compró?", st.session_state.db_inv["Insumo"])
                can = st.number_input("Cantidad", min_value=0.1)
                tot = st.number_input("Precio Total Pagado Bs", min_value=0.1)
                if st.form_submit_button("Confirmar Compra"):
                    idx = st.session_state.db_inv.index[st.session_state.db_inv['Insumo'] == ins][0]
                    st.session_state.db_inv.at[idx, 'Stock'] += can
                    st.session_state.db_inv.at[idx, 'Costo_Unit_Bs'] = tot / can
                    # Salida de Caja
                    st.session_state.db_caja_flujo = pd.concat([st.session_state.db_caja_flujo, pd.DataFrame([{"Fecha": datetime.now(), "Concepto": f"Compra {ins}", "Monto_Bs": tot, "Tipo": "Salida"}])], ignore_index=True)
                    st.success("Inventario actualizado y caja descontada.")
        st.dataframe(st.session_state.db_inv, use_container_width=True)

    # --- 5. GASTOS Y ACTIVOS ---
    elif menu == "💸 Gastos y Activos":
        st.header("💸 Egresos Operativos y Activos")
        col_g, col_a = st.columns(2)
        with col_g:
            st.subheader("Registrar Gasto (Luz, Agua, Alquiler)")
            with st.form("f_g"):
                con = st.text_input("Concepto del Gasto")
                mon = st.number_input("Monto Bs", min_value=0.0)
                if st.form_submit_button("Pagar Gasto"):
                    st.session_state.db_caja_flujo = pd.concat([st.session_state.db_caja_flujo, pd.DataFrame([{"Fecha": datetime.now(), "Concepto": con, "Monto_Bs": mon, "Tipo": "Salida"}])], ignore_index=True)
        
        with col_a:
            st.subheader("Registrar Inversión Inicial")
            st.session_state.config['inversion_inicial'] = st.number_input("Capital de Inversión Inicial (Bs)", value=st.session_state.config['inversion_inicial'])

    # --- 6. BALANCE GENERAL PRO ---
    elif menu == "🏛️ Balance General Pro":
        st.header("🏛️ Contabilidad de Global Wings")
        
        # Cálculos Financieros
        ventas_totales = st.session_state.db_ventas['Total_Bs'].sum()
        costo_mercaderia = st.session_state.db_ventas['Costo_Total'].sum()
        gastos_fijos = st.session_state.db_caja_flujo[st.session_state.db_caja_flujo['Concepto'].str.contains("Venta|Compra") == False]['Monto_Bs'].sum()
        utilidad_neta = (ventas_totales - costo_mercaderia) - gastos_fijos
        
        valor_inventario = (st.session_state.db_inv['Stock'] * st.session_state.db_inv['Costo_Unit_Bs']).sum()
        caja_efectivo = (st.session_state.db_caja_flujo[st.session_state.db_caja_flujo['Tipo']=='Entrada']['Monto_Bs'].sum() - st.session_state.db_caja_flujo[st.session_state.db_caja_flujo['Tipo']=='Salida']['Monto_Bs'].sum() + st.session_state.config['caja_apertura'])

        t1, t2 = st.tabs(["📉 Estado de Resultados", "🏛️ Balance General"])
        with t1:
            st.subheader("Rendimiento del Negocio")
            st.write(f"**(+) Ventas Netas:** {ventas_totales:,.2f} Bs")
            st.write(f"**(-) Costo de Producción (CMV):** {costo_mercaderia:,.2f} Bs")
            st.divider()
            st.write(f"**(=) Utilidad Bruta:** {ventas_totales - costo_mercaderia:,.2f} Bs")
            st.write(f"**(-) Gastos de Operación (Agua, Luz, Alquiler):** {gastos_fijos:,.2f} Bs")
            st.metric("UTILIDAD NETA", f"{utilidad_neta:,.2f} Bs")

        with t2:
            st.subheader("Situación Patrimonial")
            c1, c2 = st.columns(2)
            with c1:
                st.info("**ACTIVOS (Lo que tienes)**")
                st.write(f"Efectivo en Caja: {caja_efectivo:,.2f} Bs")
                st.write(f"Mercadería en Almacén: {valor_inventario:,.2f} Bs")
                st.write(f"**TOTAL ACTIVOS:** {caja_efectivo + valor_inventario:,.2f} Bs")
            with c2:
                st.success("**PATRIMONIO (De donde vino)**")
                st.write(f"Inversión Inicial: {st.session_state.config['inversion_inicial']:,.2f} Bs")
                st.write(f"Ganancias del Periodo: {utilidad_neta:,.2f} Bs")
                st.write(f"**TOTAL PATRIMONIO:** {st.session_state.config['inversion_inicial'] + utilidad_neta:,.2f} Bs")
