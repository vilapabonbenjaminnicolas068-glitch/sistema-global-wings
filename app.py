import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="GLOBAL WINGS - SISTEMA INTEGRAL", layout="wide")

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
    if 'db_inv' not in st.session_state:
        st.session_state.db_inv = pd.DataFrame(columns=["Insumo", "Tipo", "Unidad", "Stock", "Costo_Unit_Bs"])
    if 'db_recetas' not in st.session_state:
        st.session_state.db_recetas = pd.DataFrame(columns=["Combo", "Insumo", "Cantidad"])
    if 'db_combos' not in st.session_state:
        st.session_state.db_combos = pd.DataFrame(columns=["Nombre_Combo", "Precio_Venta_Bs"])
    if 'db_ventas' not in st.session_state:
        st.session_state.db_ventas = pd.DataFrame(columns=["Fecha", "Combo", "Total_Bs", "Costo_Total", "Estado"])
    if 'db_caja' not in st.session_state:
        st.session_state.db_caja = pd.DataFrame(columns=["Fecha", "Concepto", "Tipo", "Monto_Bs"])

    st.sidebar.title("🦅 GLOBAL WINGS")
    opcion = st.sidebar.radio("Navegación", ["🏠 Inicio", "🍗 Inventario & Compras", "🍔 Ingeniería de Combos", "💰 Punto de Venta", "📉 Finanzas & Reportes"])

    # --- 1. INICIO (DASHBOARD) ---
    if opcion == "🏠 Inicio":
        st.header("🏠 Panel de Control - Global Wings")
        
        # Cálculos rápidos
        ventas_totales = st.session_state.db_ventas[st.session_state.db_ventas['Estado'] == 'Confirmado']['Total_Bs'].sum()
        gastos_totales = st.session_state.db_caja[st.session_state.db_caja['Tipo'] == 'Egreso']['Monto_Bs'].sum()
        capital_inyectado = st.session_state.db_caja[st.session_state.db_caja['Tipo'] == 'Capital']['Monto_Bs'].sum()
        caja_actual = (ventas_totales + capital_inyectado) - gastos_totales
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Ventas Totales", f"{ventas_totales:,.2f} Bs", delta_color="normal")
        c2.metric("Gastos Totales", f"{gastos_totales:,.2f} Bs", delta_color="inverse")
        c3.metric("Caja Disponible", f"{caja_actual:,.2f} Bs")
        c4.metric("Insumos en Alerta", len(st.session_state.db_inv[st.session_state.db_inv['Stock'] < 5]))

        st.divider()
        st.subheader("Últimas Ventas")
        st.dataframe(st.session_state.db_ventas.tail(5), use_container_width=True)

    # --- 2. INVENTARIO & COMPRAS ---
    elif opcion == "🍗 Inventario & Compras":
        st.header("🍗 Gestión de Inventario")
        
        tab_inv, tab_compra = st.tabs(["Stock Actual", "🛒 Registrar Compra (Aumentar Stock)"])
        
        with tab_inv:
            st.write("Edita directamente las celdas para ajustes manuales:")
            st.session_state.db_inv = st.data_editor(st.session_state.db_inv, num_rows="dynamic", use_container_width=True)
            
        with tab_compra:
            st.subheader("Registrar Entrada de Mercadería")
            with st.form("form_compra"):
                insumo_compra = st.selectbox("Seleccionar Insumo", st.session_state.db_inv["Insumo"] if not st.session_state.db_inv.empty else ["Crea un insumo primero"])
                cant_compra = st.number_input("Cantidad Comprada", min_value=0.1)
                costo_compra = st.number_input("Costo Total de la Compra (Bs)", min_value=0.1)
                
                if st.form_submit_button("Confirmar Compra"):
                    # 1. Aumentar Stock
                    idx = st.session_state.db_inv.index[st.session_state.db_inv['Insumo'] == insumo_compra][0]
                    st.session_state.db_inv.at[idx, 'Stock'] += cant_compra
                    # 2. Actualizar Costo Unitario Promedio
                    nuevo_costo_unit = costo_compra / cant_compra
                    st.session_state.db_inv.at[idx, 'Costo_Unit_Bs'] = nuevo_costo_unit
                    # 3. Registrar Salida de Caja
                    nc = pd.DataFrame([{"Fecha": datetime.now(), "Concepto": f"Compra de {insumo_compra}", "Tipo": "Egreso", "Monto_Bs": costo_compra}])
                    st.session_state.db_caja = pd.concat([st.session_state.db_caja, nc], ignore_index=True)
                    st.success(f"Stock de {insumo_compra} aumentado. Dinero descontado de caja.")

    # --- 3. INGENIERÍA DE COMBOS ---
    elif opcion == "🍔 Ingeniería de Combos":
        st.header("🍔 Diseño de Combos")
        c1, c2 = st.columns(2)
        with c1:
            with st.form("crear_combo"):
                nc = st.text_input("Nombre del Combo")
                pv = st.number_input("Precio de Venta (Bs)", min_value=0.0)
                if st.form_submit_button("Registrar Combo"):
                    st.session_state.db_combos = pd.concat([st.session_state.db_combos, pd.DataFrame([{"Nombre_Combo": nc, "Precio_Venta_Bs": pv}])], ignore_index=True)
        with c2:
            st.write("Añadir Ingredientes:")
            if not st.session_state.db_combos.empty:
                sel_c = st.selectbox("Combo", st.session_state.db_combos["Nombre_Combo"])
                sel_i = st.selectbox("Ingrediente", st.session_state.db_inv["Insumo"])
                cant_i = st.number_input("Cantidad", min_value=0.01)
                if st.button("Vincular"):
                    st.session_state.db_recetas = pd.concat([st.session_state.db_recetas, pd.DataFrame([{"Combo": sel_c, "Insumo": sel_i, "Cantidad": cant_i}])], ignore_index=True)
                    st.success("Vinculado")

    # --- 4. PUNTO DE VENTA ---
    elif opcion == "💰 Punto de Venta":
        st.header("💰 Caja Registradora")
        if not st.session_state.db_combos.empty:
            sel_v = st.selectbox("Elegir Combo", st.session_state.db_combos["Nombre_Combo"])
            cant_v = st.number_input("Cantidad", min_value=1)
            
            if st.button("CONFIRMAR VENTA"):
                receta = st.session_state.db_recetas[st.session_state.db_recetas["Combo"] == sel_v]
                can_sell = True
                costo_vta = 0
                
                for _, r in receta.iterrows():
                    idx = st.session_state.db_inv.index[st.session_state.db_inv["Insumo"] == r["Insumo"]][0]
                    if st.session_state.db_inv.at[idx, "Stock"] < (r["Cantidad"] * cant_v):
                        can_sell = False
                        st.error(f"¡No hay suficiente {r['Insumo']}!")
                    costo_vta += st.session_state.db_inv.at[idx, "Costo_Unit_Bs"] * (r["Cantidad"] * cant_v)
                
                if can_sell:
                    for _, r in receta.iterrows():
                        idx = st.session_state.db_inv.index[st.session_state.db_inv["Insumo"] == r["Insumo"]][0]
                        st.session_state.db_inv.at[idx, "Stock"] -= (r["Cantidad"] * cant_v)
                    
                    p_vta = st.session_state.db_combos[st.session_state.db_combos["Nombre_Combo"] == sel_v]["Precio_Venta_Bs"].values[0]
                    nv = pd.DataFrame([{"Fecha": datetime.now(), "Combo": sel_v, "Total_Bs": p_vta * cant_v, "Costo_Total": costo_vta, "Estado": "Confirmado"}])
                    st.session_state.db_ventas = pd.concat([st.session_state.db_ventas, nv], ignore_index=True)
                    st.success("¡Venta Exitosa!")

    # --- 5. FINANZAS & REPORTES ---
    elif opcion == "📉 Finanzas & Reportes":
        st.header("📉 Gestión Financiera")
        
        with st.expander("💸 Inyectar Capital o Registrar Gasto Externo"):
            with st.form("finanzas_manual"):
                conc = st.text_input("Concepto")
                monto = st.number_input("Monto (Bs)", min_value=0.0)
                tipo_f = st.selectbox("Tipo", ["Egreso", "Capital"])
                if st.form_submit_button("Guardar Movimiento"):
                    nf = pd.DataFrame([{"Fecha": datetime.now(), "Concepto": conc, "Tipo": tipo_f, "Monto_Bs": monto}])
                    st.session_state.db_caja = pd.concat([st.session_state.db_caja, nf], ignore_index=True)
                    st.success("Finanzas actualizadas.")

        # REPORTES
        ing = st.session_state.db_ventas['Total_Bs'].sum()
        cv = st.session_state.db_ventas['Costo_Total'].sum()
        gas = st.session_state.db_caja[st.session_state.db_caja['Tipo'] == 'Egreso']['Monto_Bs'].sum()
        cap = st.session_state.db_caja[st.session_state.db_caja['Tipo'] == 'Capital']['Monto_Bs'].sum()
        inv_val = (st.session_state.db_inv['Stock'] * st.session_state.db_inv['Costo_Unit_Bs']).sum()
        
        st.subheader("Estado de Resultados")
        st.write(f"Ventas: {ing} Bs | Costo Ventas: {cv} Bs | Gastos: {gas} Bs")
        st.metric("UTILIDAD NETA", f"{(ing - cv) - gas:,.2f} Bs")
        
        st.subheader("Balance General")
        st.write(f"Activo (Caja + Inventario): {(ing + cap - gas) + inv_val} Bs")
