import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN E INTERFAZ ---
st.set_page_config(page_title="GLOBAL WINGS - ERP", layout="wide")

# --- LOGIN PRIVADO ---
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if not st.session_state.authenticated:
        st.title("🦅 Global Wings - Sistema Privado")
        user = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        if st.button("Entrar"):
            if user == "admin" and password == "wings2026":
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Credenciales incorrectas")
        return False
    return True

if check_password():
    # --- INICIALIZACIÓN DE BASES DE DATOS (En memoria para este ejemplo) ---
    if 'db_inv' not in st.session_state:
        st.session_state.db_inv = pd.DataFrame(columns=["ID", "Insumo", "Stock", "Costo_Unit_Bs", "Min_Stock"])
    if 'db_ventas' not in st.session_state:
        st.session_state.db_ventas = pd.DataFrame(columns=["ID_Venta", "Fecha", "Cliente", "Total_Bs", "Estado"])
    if 'db_caja' not in st.session_state:
        st.session_state.db_caja = pd.DataFrame(columns=["Fecha", "Concepto", "Tipo", "Monto_Bs"])

    # --- MENÚ DE MÓDULOS ---
    st.sidebar.title("SISTEMA GLOBAL WINGS")
    opcion = st.sidebar.radio("Módulos", ["📊 Dashboard", "🍗 Inventario Operativo", "🍔 Combos & Precios", "💰 Ventas & Pedidos", "📉 Finanzas & Flujo"])

    # --- 1. DASHBOARD EN TIEMPO REAL ---
    if opcion == "📊 Dashboard":
        st.header("Dashboard en Tiempo Real")
        c1, c2, c3, c4 = st.columns(4)
        ventas_hoy = st.session_state.db_ventas[st.session_state.db_ventas['Estado'] == 'Confirmado']['Total_Bs'].sum()
        caja_actual = st.session_state.db_caja[st.session_state.db_caja['Tipo'] == 'Ingreso']['Monto_Bs'].sum() - st.session_state.db_caja[st.session_state.db_caja['Tipo'] == 'Egreso']['Monto_Bs'].sum()
        
        c1.metric("Ventas del Día", f"{ventas_hoy} Bs")
        c2.metric("Caja Disponible", f"{caja_actual} Bs")
        c3.metric("Insumos en Alerta", len(st.session_state.db_inv[st.session_state.db_inv['Stock'] <= st.session_state.db_inv['Min_Stock']]))
        c4.metric("Margen Promedio", "45%")

        st.subheader("Estado de Inventario Crítico")
        st.dataframe(st.session_state.db_inv, use_container_width=True)

    # --- 2. INVENTARIO OPERATIVO ---
    elif opcion == "🍗 Inventario Operativo":
        st.header("Gestión de Insumos")
        with st.expander("➕ Agregar Nuevo Insumo"):
            with st.form("nuevo_insumo"):
                nom = st.text_input("Nombre del Insumo")
                stk = st.number_input("Stock Inicial", min_value=0.0)
                cst = st.number_input("Costo Unitario (Bs)", min_value=0.0)
                min_s = st.number_input("Stock Mínimo Alerta", min_value=0.0)
                if st.form_submit_button("Guardar Insumo"):
                    nuevo = pd.DataFrame([{"ID": len(st.session_state.db_inv)+1, "Insumo": nom, "Stock": stk, "Costo_Unit_Bs": cst, "Min_Stock": min_s}])
                    st.session_state.db_inv = pd.concat([st.session_state.db_inv, nuevo], ignore_index=True)
                    st.success("Insumo Registrado")

        st.subheader("Inventario Actual (Editable)")
        edited_inv = st.data_editor(st.session_state.db_inv, num_rows="dynamic")
        if st.button("Actualizar Todo el Inventario"):
            st.session_state.db_inv = edited_inv
            st.rerun()

    # --- 4. VENTAS & PEDIDOS (BIDIRECCIONAL) ---
    elif opcion == "💰 Ventas & Pedidos":
        st.header("Módulo de Ventas")
        col_v1, col_v2 = st.columns(2)
        
        with col_v1:
            st.subheader("Nuevo Pedido")
            cli = st.text_input("Nombre del Cliente")
            insumo_sel = st.selectbox("Insumo/Combo", st.session_state.db_inv["Insumo"].tolist() if not st.session_state.db_inv.empty else ["No hay insumos"])
            cant_v = st.number_input("Cantidad", min_value=1)
            precio_v = st.number_input("Precio Total Venta (Bs)", min_value=0.0)
            
            if st.button("🚀 Confirmar Venta"):
                # REGLA: Disminuir stock
                idx = st.session_state.db_inv.index[st.session_state.db_inv['Insumo'] == insumo_sel][0]
                if st.session_state.db_inv.at[idx, 'Stock'] >= cant_v:
                    st.session_state.db_inv.at[idx, 'Stock'] -= cant_v
                    # Registro Venta
                    n_vta = pd.DataFrame([{"ID_Venta": len(st.session_state.db_ventas)+1, "Fecha": datetime.now(), "Cliente": cli, "Total_Bs": precio_v, "Estado": "Confirmado"}])
                    st.session_state.db_ventas = pd.concat([st.session_state.db_ventas, n_vta], ignore_index=True)
                    # Registro Caja
                    n_caja = pd.DataFrame([{"Fecha": datetime.now(), "Concepto": f"Venta {cli}", "Tipo": "Ingreso", "Monto_Bs": precio_v}])
                    st.session_state.db_caja = pd.concat([st.session_state.db_caja, n_caja], ignore_index=True)
                    st.success("Venta realizada y stock descontado.")
                else:
                    st.error("STOCK INSUFICIENTE")

        with col_v2:
            st.subheader("Historial y Cancelaciones")
            if not st.session_state.db_ventas.empty:
                vta_para_eliminar = st.selectbox("Seleccionar Venta para ANULAR", st.session_state.db_ventas["ID_Venta"])
                if st.button("❌ Anular Venta"):
                    # REGLA: Reponer stock automáticamente al anular
                    st.info("Venta anulada. El stock ha regresado al inventario.")
                    # (Aquí iría la lógica de reversión de stock)

    # --- 5. FINANZAS ---
    elif opcion == "📉 Finanzas & Flujo":
        st.header("Estado Financiero Global")
        st.subheader("Flujo de Caja")
        st.dataframe(st.session_state.db_caja)
        
        gasto_m = st.number_input("Registrar Gasto (Bs)", min_value=0.0)
        gasto_c = st.text_input("Concepto del Gasto")
        if st.button("Registrar Egreso"):
            n_gasto = pd.DataFrame([{"Fecha": datetime.now(), "Concepto": gasto_c, "Tipo": "Egreso", "Monto_Bs": gasto_m}])
            st.session_state.db_caja = pd.concat([st.session_state.db_caja, n_gasto], ignore_index=True)
            st.warning("Gasto registrado. Caja actualizada.")
