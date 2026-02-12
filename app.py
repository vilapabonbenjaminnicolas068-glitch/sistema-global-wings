import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="GLOBAL WINGS - ERP PROFESIONAL", layout="wide")

# --- LOGIN ---
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if not st.session_state.authenticated:
        st.title("🔐 Acceso Privado - Global Wings")
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
    if 'db_inv' not in st.session_state:
        st.session_state.db_inv = pd.DataFrame(columns=["ID", "Insumo", "Tipo", "Unidad", "Stock", "Costo_Unit_Bs"])
    if 'db_recetas' not in st.session_state:
        st.session_state.db_recetas = pd.DataFrame(columns=["Combo", "Insumo", "Cantidad"])
    if 'db_combos' not in st.session_state:
        st.session_state.db_combos = pd.DataFrame(columns=["Nombre_Combo", "Precio_Venta_Bs"])
    if 'db_clientes' not in st.session_state:
        st.session_state.db_clientes = pd.DataFrame(columns=["Codigo", "Nombre", "Pedidos"])
    if 'db_ventas' not in st.session_state:
        st.session_state.db_ventas = pd.DataFrame(columns=["ID", "Fecha", "Cliente", "Combo", "Total_Bs", "Costo_Total", "Estado"])
    if 'db_caja' not in st.session_state:
        st.session_state.db_caja = pd.DataFrame(columns=["Fecha", "Concepto", "Tipo", "Monto_Bs"])

    st.sidebar.title("🦅 GLOBAL WINGS")
    opcion = st.sidebar.radio("Módulos", ["📈 Reportes Financieros", "🍗 Inventario", "🍔 Ingeniería de Combos", "💰 Punto de Venta", "👥 Clientes"])

    # --- 1. REPORTES FINANCIEROS (BALANCE Y ESTADO DE RESULTADOS) ---
    if opcion == "📈 Reportes Financieros":
        st.header("📊 Estados Financieros")
        
        # Cálculos Base
        ingresos = st.session_state.db_ventas[st.session_state.db_ventas['Estado'] == 'Confirmado']['Total_Bs'].sum()
        costo_ventas = st.session_state.db_ventas[st.session_state.db_ventas['Estado'] == 'Confirmado']['Costo_Total'].sum()
        gastos = st.session_state.db_caja[st.session_state.db_caja['Tipo'] == 'Egreso']['Monto_Bs'].sum()
        capital = st.session_state.db_caja[st.session_state.db_caja['Tipo'] == 'Capital']['Monto_Bs'].sum()
        valor_inv = (st.session_state.db_inv['Stock'] * st.session_state.db_inv['Costo_Unit_Bs']).sum()
        caja_neta = (ingresos + capital) - gastos

        tab1, tab2 = st.tabs(["📉 Estado de Resultados", "🏛️ Balance General"])

        with tab1:
            st.subheader("Estado de Resultados (P&L)")
            st.write(f"**Ventas Netas:** {ingresos:,.2f} Bs")
            st.write(f"**(-) Costo de Ventas:** {costo_ventas:,.2f} Bs")
            st.divider()
            st.write(f"**Utilidad Bruta:** {(ingresos - costo_ventas):,.2f} Bs")
            st.write(f"**(-) Gastos Operativos:** {gastos:,.2f} Bs")
            st.divider()
            utilidad_neta = (ingresos - costo_ventas) - gastos
            st.metric("UTILIDAD NETA", f"{utilidad_neta:,.2f} Bs")

        with tab2:
            st.subheader("Balance General")
            col_a, col_b = st.columns(2)
            with col_a:
                st.info("**ACTIVOS**")
                st.write(f"Caja y Bancos: {caja_neta:,.2f} Bs")
                st.write(f"Inventarios: {valor_inv:,.2f} Bs")
                st.write(f"**TOTAL ACTIVOS:** {(caja_neta + valor_inv):,.2f} Bs")
            with col_b:
                st.info("**PASIVO + PATRIMONIO**")
                st.write(f"Capital Social: {capital:,.2f} Bs")
                st.write(f"Resultados del Ejercicio: {utilidad_neta:,.2f} Bs")
                st.write(f"**TOTAL PAS + PAT:** {(capital + utilidad_neta):,.2f} Bs")

    # --- 2. INVENTARIO CON TIPOS Y UNIDADES ---
    elif opcion == "🍗 Inventario":
        st.header("🍗 Gestión de Inventario")
        with st.form("nuevo_insumo"):
            c1, c2, c3, c4 = st.columns(4)
            nom = c1.text_input("Nombre")
            tipo = c2.selectbox("Tipo", ["Directo Combo", "Insumo General"])
            unid = c3.selectbox("Unidad", ["Unidad", "Kilos", "Litros", "Paquete"])
            cost = c4.number_input("Costo Unit. (Bs)", min_value=0.0)
            if st.form_submit_button("Registrar Insumo"):
                n = pd.DataFrame([{"ID": len(st.session_state.db_inv)+1, "Insumo": nom, "Tipo": tipo, "Unidad": unid, "Stock": 0.0, "Costo_Unit_Bs": cost}])
                st.session_state.db_inv = pd.concat([st.session_state.db_inv, n], ignore_index=True)
        
        st.subheader("Stock Actual")
        st.session_state.db_inv = st.data_editor(st.session_state.db_inv, use_container_width=True)

    # --- 3. INGENIERÍA DE COMBOS (MULTI-INSUMOS) ---
    elif opcion == "🍔 Ingeniería de Combos":
        st.header("🍔 Creación de Combos")
        # Primero crear el combo
        with st.form("crear_nombre_combo"):
            nc = st.text_input("Nombre del Combo")
            pv = st.number_input("Precio Venta (Bs)", min_value=0.0)
            if st.form_submit_button("Registrar Nombre de Combo"):
                st.session_state.db_combos = pd.concat([st.session_state.db_combos, pd.DataFrame([{"Nombre_Combo": nc, "Precio_Venta_Bs": pv}])], ignore_index=True)

        st.divider()
        st.subheader("Añadir Ingredientes a Combo")
        if not st.session_state.db_combos.empty:
            c_sel = st.selectbox("Elegir Combo", st.session_state.db_combos["Nombre_Combo"])
            i_sel = st.selectbox("Elegir Insumo", st.session_state.db_inv[st.session_state.db_inv["Tipo"]=="Directo Combo"]["Insumo"])
            cant_i = st.number_input("Cantidad necesaria", min_value=0.01)
            if st.button("Vincular Insumo a Combo"):
                st.session_state.db_recetas = pd.concat([st.session_state.db_recetas, pd.DataFrame([{"Combo": c_sel, "Insumo": i_sel, "Cantidad": cant_i}])], ignore_index=True)
                st.success("Ingrediente añadido!")
            
            st.write("Receta actual:")
            st.table(st.session_state.db_recetas[st.session_state.db_recetas["Combo"] == c_sel])

    # --- 4. PUNTO DE VENTA (EL MOTOR) ---
    elif opcion == "💰 Punto de Venta":
        st.header("💰 Punto de Venta")
        if not st.session_state.db_combos.empty:
            sel_c = st.selectbox("Combo", st.session_state.db_combos["Nombre_Combo"])
            cant_v = st.number_input("Cantidad", min_value=1)
            
            if st.button("CONFIRMAR VENTA"):
                # Cálculo de costo y validación de stock
                receta = st.session_state.db_recetas[st.session_state.db_recetas["Combo"] == sel_c]
                error_stock = False
                costo_acumulado = 0
                
                for _, item in receta.iterrows():
                    idx = st.session_state.db_inv.index[st.session_state.db_inv["Insumo"] == item["Insumo"]][0]
                    necesario = item["Cantidad"] * cant_v
                    if st.session_state.db_inv.at[idx, "Stock"] < necesario:
                        error_stock = True
                        st.error(f"Falta stock de {item['Insumo']}")
                    costo_acumulado += st.session_state.db_inv.at[idx, "Costo_Unit_Bs"] * necesario
                
                if not error_stock:
                    # Descontar
                    for _, item in receta.iterrows():
                        idx = st.session_state.db_inv.index[st.session_state.db_inv["Insumo"] == item["Insumo"]][0]
                        st.session_state.db_inv.at[idx, "Stock"] -= (item["Cantidad"] * cant_v)
                    
                    # Registrar
                    precio_v = st.session_state.db_combos[st.session_state.db_combos["Nombre_Combo"] == sel_c]["Precio_Venta_Bs"].values[0]
                    nv = pd.DataFrame([{"ID": len(st.session_state.db_ventas)+1, "Fecha": datetime.now(), "Cliente": "Genérico", "Combo": sel_c, "Total_Bs": precio_v * cant_v, "Costo_Total": costo_acumulado, "Estado": "Confirmado"}])
                    st.session_state.db_ventas = pd.concat([st.session_state.db_ventas, nv], ignore_index=True)
                    st.success("Venta procesada exitosamente!")

    # --- 5. CLIENTES ---
    elif opcion == "👥 Clientes":
        st.header("👥 CRM Clientes")
        with st.form("n_cliente"):
            n_cli = st.text_input("Nombre Cliente")
            if st.form_submit_button("Crear"):
                cod = f"CLI-{len(st.session_state.db_clientes)+100}"
                st.session_state.db_clientes = pd.concat([st.session_state.db_clientes, pd.DataFrame([{"Codigo": cod, "Nombre": n_cli, "Pedidos": 0}])], ignore_index=True)
        st.dataframe(st.session_state.db_clientes)
