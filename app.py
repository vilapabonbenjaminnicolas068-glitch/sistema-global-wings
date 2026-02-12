import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="GLOBAL WINGS - ERP PRECISIÓN", layout="wide")

# --- ESTILOS ---
st.markdown("""
    <style>
    .reportview-container { background: #f0f2f6; }
    .stMetric { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border: 1px solid #eee; }
    </style>
    """, unsafe_allow_stdio=True)

# --- INICIALIZACIÓN DE DATOS ---
tablas = {
    'db_inv': ["Insumo", "Unidad", "Stock", "Costo_Unit_Bs"],
    'db_activos': ["Activo", "Valor_Bs"],
    'db_combos': ["Nombre", "Precio_Venta"],
    'db_recetas': ["Combo", "Insumo", "Cantidad"],
    'db_costos_ind': ["Combo", "Detalle", "Monto_Bs"],
    'db_ventas': ["Fecha", "Cliente", "Combo", "Total_Bs", "Costo_Prod", "Metodo"],
    'db_gastos_op': ["Fecha", "Concepto", "Monto_Bs"],
    'db_clientes': ["Codigo", "Nombre", "Celular"]
}

for t, cols in tablas.items():
    if t not in st.session_state:
        st.session_state[t] = pd.DataFrame(columns=cols)

if 'config' not in st.session_state:
    st.session_state.config = {"inversion": 0.0, "deuda": 0.0}

# --- LOGIN ---
if "auth" not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.title("🦅 Global Wings - Acceso Privado")
    with st.container():
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
        g = st.session_state.db_gastos_op
        
        c1, c2, c3, c4 = st.columns(4)
        ventas_totales = v['Total_Bs'].sum()
        c1.metric("Ventas Totales", f"{ventas_totales:,.2f} Bs")
        
        utilidad_bruta = ventas_totales - v['Costo_Prod'].sum()
        c2.metric("Utilidad Bruta", f"{utilidad_bruta:,.2f} Bs")
        
        caja_actual = (ventas_totales + st.session_state.config['inversion']) - g['Monto_Bs'].sum()
        c3.metric("Efectivo en Caja", f"{caja_actual:,.2f} Bs")
        
        c4.metric("Valor del Inventario", f"{(st.session_state.db_inv['Stock'] * st.session_state.db_inv['Costo_Unit_Bs']).sum():,.2f} Bs")

        st.divider()
        st.subheader("Últimos Pedidos")
        st.dataframe(v.tail(10), use_container_width=True)

    # --- 2. ALMACÉN ---
    elif menu == "🍗 Almacén e Insumos":
        st.header("📦 Gestión de Materia Prima")
        with st.expander("➕ Registrar Nuevo Insumo"):
            with st.form("n_i"):
                nom = st.text_input("Nombre (ej: Pollo, Papa, Aceite)")
                uni = st.selectbox("Unidad", ["Kg", "Litro", "Unidad", "Gramo"])
                if st.form_submit_button("Añadir al Almacén"):
                    st.session_state.db_inv = pd.concat([st.session_state.db_inv, pd.DataFrame([{"Insumo": nom, "Unidad": uni, "Stock": 0.0, "Costo_Unit_Bs": 0.0}])], ignore_index=True)
        
        st.subheader("🛒 Registrar Compras (Actualiza Costo Unitario)")
        if not st.session_state.db_inv.empty:
            with st.form("compra"):
                ins = st.selectbox("Insumo Comprado", st.session_state.db_inv["Insumo"])
                can = st.number_input("Cantidad", min_value=0.01)
                pre = st.number_input("Monto Total de Factura (Bs)", min_value=0.1)
                if st.form_submit_button("Confirmar Entrada"):
                    idx = st.session_state.db_inv.index[st.session_state.db_inv['Insumo'] == ins][0]
                    st.session_state.db_inv.at[idx, 'Stock'] += can
                    st.session_state.db_inv.at[idx, 'Costo_Unit_Bs'] = pre / can
                    st.success("Inventario actualizado. Los costos de recetas se han ajustado solos.")
        st.dataframe(st.session_state.db_inv, use_container_width=True)

    # --- 3. ACTIVOS (EL SARTÉN) ---
    elif menu == "🍳 Activos y Equipos":
        st.header("🍳 Activos Fijos (Patrimonio)")
        st.write("Registra equipos que son propiedad del negocio (Sartenes, Mesas, Maquinaria).")
        with st.form("f_act"):
            ac = st.text_input("Descripción del Equipo")
            va = st.number_input("Valor de Mercado / Compra (Bs)", min_value=0.0)
            if st.form_submit_button("Registrar en Balance"):
                st.session_state.db_activos = pd.concat([st.session_state.db_activos, pd.DataFrame([{"Activo": ac, "Valor_Bs": va}])], ignore_index=True)
        st.dataframe(st.session_state.db_activos, use_container_width=True)

    # --- 4. INGENIERÍA DE RECETAS (COSTOS Y RENTABILIDAD) ---
    elif menu == "👨‍🍳 Ingeniería de Recetas":
        st.header("👨‍🍳 Costeo Maestro de Combos")
        
        # Crear Combo
        with st.form("f_c"):
            st.subheader("1. Definir Nuevo Combo")
            c1, c2 = st.columns(2)
            n_c = c1.text_input("Nombre del Combo")
            p_v = c2.number_input("Precio de Venta al Público (Bs)", min_value=0.0)
            if st.form_submit_button("Crear Combo"):
                st.session_state.db_combos = pd.concat([st.session_state.db_combos, pd.DataFrame([{"Nombre": n_c, "Precio_Venta": p_v}])], ignore_index=True)

        st.divider()
        if not st.session_state.db_combos.empty:
            st.subheader("2. Estructura de Costos del Producto")
            combo_sel = st.selectbox("Elegir Combo para editar receta", st.session_state.db_combos["Nombre"])
            
            col_rec, col_ind = st.columns(2)
            with col_rec:
                st.info("**Costos Directos (Inventario)**")
                if not st.session_state.db_inv.empty:
                    ins_r = st.selectbox("Insumo", st.session_state.db_inv["Insumo"])
                    can_r = st.number_input("Cantidad Necesaria", min_value=0.001, format="%.3f")
                    if st.button("Vincular Insumo"):
                        st.session_state.db_recetas = pd.concat([st.session_state.db_recetas, pd.DataFrame([{"Combo": combo_sel, "Insumo": ins_r, "Cantidad": can_r}])], ignore_index=True)
            
            with col_ind:
                st.info("**Costos Indirectos (Manuales)**")
                det_i = st.text_input("Detalle (Salsa, Empaque, Gas)")
                mon_i = st.number_input("Costo unitario Bs", min_value=0.0)
                if st.button("Añadir Indirecto"):
                    st.session_state.db_costos_ind = pd.concat([st.session_state.db_costos_ind, pd.DataFrame([{"Combo": combo_sel, "Detalle": det_i, "Monto_Bs": mon_i}])], ignore_index=True)

            st.subheader("📊 Análisis de Rentabilidad")
            # Cálculo de Costo Directo
            receta = st.session_state.db_recetas[st.session_state.db_recetas["Combo"] == combo_sel]
            costo_directo = 0
            for _, r in receta.iterrows():
                costo_u = st.session_state.db_inv[st.session_state.db_inv["Insumo"] == r["Insumo"]]["Costo_Unit_Bs"].values[0]
                costo_directo += costo_u * r["Cantidad"]
            
            # Cálculo de Costo Indirecto
            costo_indirecto = st.session_state.db_costos_ind[st.session_state.db_costos_ind["Combo"] == combo_sel]["Monto_Bs"].sum()
            costo_produccion = costo_directo + costo_indirecto
            
            precio_v = st.session_state.db_combos[st.session_state.db_combos["Nombre"] == combo_sel]["Precio_Venta"].values[0]
            utilidad_un = precio_v - costo_produccion
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Costo de Producción", f"{costo_produccion:,.2f} Bs")
            c2.metric("Precio de Venta", f"{precio_v:,.2f} Bs")
            c3.metric("Utilidad por Combo", f"{utilidad_un:,.2f} Bs", delta=f"{((utilidad_un/precio_v)*100 if precio_v > 0 else 0):,.1f}% Margen")
            
            st.write("**Detalle de Receta:**")
            st.table(receta)

    # --- 5. PUNTO DE VENTA ---
    elif menu == "💰 Punto de Venta":
        st.header("💰 Caja Registradora")
        if not st.session_state.db_combos.empty:
            c1, c2 = st.columns(2)
            with c1:
                sel_v = st.selectbox("Elegir Combo", st.session_state.db_combos["Nombre"])
                can_v = st.number_input("Cantidad", min_value=1)
                met_v = st.radio("Método", ["Efectivo", "QR"])
            with c2:
                cli_v = st.selectbox("Cliente", ["Público General"] + st.session_state.db_clientes["Nombre"].tolist())
                st.info(f"Total a pagar: {st.session_state.db_combos[st.session_state.db_combos['Nombre']==sel_v]['Precio_Venta'].values[0] * can_v:,.2f} Bs")

            if st.button("🚀 FINALIZAR VENTA"):
                # Calcular Costos
                receta = st.session_state.db_recetas[st.session_state.db_recetas["Combo"] == sel_v]
                cd = 0
                for _, r in receta.iterrows():
                    idx = st.session_state.db_inv.index[st.session_state.db_inv["Insumo"] == r["Insumo"]][0]
                    st.session_state.db_inv.at[idx, "Stock"] -= (r["Cantidad"] * can_v)
                    cd += st.session_state.db_inv.at[idx, "Costo_Unit_Bs"] * (r["Cantidad"] * can_v)
                ci = st.session_state.db_costos_ind[st.session_state.db_costos_ind["Combo"] == sel_v]["Monto_Bs"].sum() * can_v
                pv = st.session_state.db_combos[st.session_state.db_combos["Nombre"] == sel_v]["Precio_Venta"].values[0] * can_v
                
                # Registrar
                nv = pd.DataFrame([{"Fecha": datetime.now(), "Cliente": cli_v, "Combo": sel_v, "Total_Bs": pv, "Costo_Prod": cd + ci, "Metodo": met_v}])
                st.session_state.db_ventas = pd.concat([st.session_state.db_ventas, nv], ignore_index=True)
                st.success("Venta Exitosa")

    # --- 6. CLIENTES (CRM) ---
    elif menu == "👥 Clientes":
        st.header("👥 Gestión de Clientes")
        with st.form("n_cl"):
            n_cli = st.text_input("Nombre Completo")
            c_cli = st.text_input("Celular")
            if st.form_submit_button("Registrar Cliente"):
                st.session_state.db_clientes = pd.concat([st.session_state.db_clientes, pd.DataFrame([{"Codigo": f"GW-{len(st.session_state.db_clientes)+1}", "Nombre": n_cli, "Celular": c_cli}])], ignore_index=True)
        
        st.subheader("Historial de Compras")
        if not st.session_state.db_clientes.empty:
            bus = st.selectbox("Ver cliente:", st.session_state.db_clientes["Nombre"])
            hist = st.session_state.db_ventas[st.session_state.db_ventas["Cliente"] == bus]
            st.write(f"Ventas totales: {len(hist)} | Inversión: {hist['Total_Bs'].sum():,.2f} Bs")
            st.dataframe(hist)

    # --- 7. FINANZAS Y BALANCE ---
    elif menu == "📉 Finanzas y Balance":
        st.header("📊 Contabilidad Profesional")
        with st.expander("⚙️ Inversión y Deudas"):
            st.session_state.config['inversion'] = st.number_input("Inversión Inicial Bs", value=st.session_state.config['inversion'])
            st.session_state.config['deuda'] = st.number_input("Pasivos (Deudas) Bs", value=st.session_state.config['deuda'])

        with st.form("gastos_f"):
            st.subheader("Registrar Gasto Mensual (Servicios)")
            con_g = st.text_input("Concepto (Luz, Agua, Alquiler, Sueldos)")
            mon_g = st.number_input("Monto Bs", min_value=0.0)
            if st.form_submit_button("Pagar Gasto"):
                st.session_state.db_gastos_op = pd.concat([st.session_state.db_gastos_op, pd.DataFrame([{"Fecha": datetime.now(), "Concepto": con_g, "Monto_Bs": mon_g}])], ignore_index=True)

        # CÁLCULOS
        v_netas = st.session_state.db_ventas['Total_Bs'].sum()
        cmv = st.session_state.db_ventas['Costo_Prod'].sum()
        gastos = st.session_state.db_gastos_op['Monto_Bs'].sum()
        val_inv = (st.session_state.db_inv['Stock'] * st.session_state.db_inv['Costo_Unit_Bs']).sum()
        val_act = st.session_state.db_activos['Valor_Bs'].sum()
        caja = (v_netas + st.session_state.config['inversion']) - gastos

        tab1, tab2 = st.tabs(["📉 Estado de Resultados", "🏛️ Balance General"])
        with tab1:
            st.markdown("### Rendimiento Económico")
            st.write(f"**Ventas Totales:** {v_netas:,.2f} Bs")
            st.write(f"**(-) Costo de Ventas (COGS):** {cmv:,.2f} Bs")
            st.divider()
            st.write(f"**Utilidad Bruta:** {v_netas - cmv:,.2f} Bs")
            st.write(f"**(-) Gastos Operativos:** {gastos:,.2f} Bs")
            st.metric("UTILIDAD NETA", f"{(v_netas - cmv) - gastos:,.2f} Bs")

        with tab2:
            st.markdown("### Situación Patrimonial")
            col_a, col_b = st.columns(2)
            with col_a:
                st.info("**ACTIVOS**")
                st.write(f"Caja y Bancos: {caja:,.2f} Bs")
                st.write(f"Inventarios: {val_inv:,.2f} Bs")
                st.write(f"Equipos (Sartenes/Maquinaria): {val_act:,.2f} Bs")
                st.divider()
                st.write(f"**TOTAL ACTIVOS:** {caja + val_inv + val_act:,.2f} Bs")
            with col_b:
                st.error("**PASIVOS Y PATRIMONIO**")
                st.write(f"Deudas: {st.session_state.config['deuda']:,.2f} Bs")
                st.write(f"Inversión Inicial: {st.session_state.config['inversion']:,.2f} Bs")
                st.write(f"Utilidad Retenida: {(v_netas - cmv) - gastos:,.2f} Bs")
                st.divider()
                st.write(f"**TOTAL PAS + PAT:** {st.session_state.config['deuda'] + st.session_state.config['inversion'] + (v_netas-cmv-gastos):,.2f} Bs")
