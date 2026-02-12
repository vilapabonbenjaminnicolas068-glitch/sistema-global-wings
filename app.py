import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN E INTERFAZ ---
st.set_page_config(page_title="GLOBAL WINGS ERP - SISTEMA INTEGRAL", layout="wide")

# --- LOGIN PRIVADO ---
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
    # --- INICIALIZACIÓN DE BASES DE DATOS ---
    if 'db_inv' not in st.session_state:
        st.session_state.db_inv = pd.DataFrame(columns=["ID", "Insumo", "Stock", "Costo_Unit_Bs", "Min_Stock"])
    if 'db_combos' not in st.session_state:
        st.session_state.db_combos = pd.DataFrame(columns=["Nombre_Combo", "Insumo_ID", "Cantidad_Insumo", "Precio_Venta_Bs"])
    if 'db_clientes' not in st.session_state:
        st.session_state.db_clientes = pd.DataFrame(columns=["Codigo_Cliente", "Nombre", "Total_Pedidos", "Total_Gastado_Bs"])
    if 'db_ventas' not in st.session_state:
        st.session_state.db_ventas = pd.DataFrame(columns=["ID_Venta", "Fecha", "Cod_Cliente", "Combo", "Total_Bs", "Estado"])
    if 'db_finanzas' not in st.session_state:
        st.session_state.db_finanzas = pd.DataFrame(columns=["Fecha", "Concepto", "Tipo", "Monto_Bs"]) # Tipo: Ingreso, Egreso, Capital, Activo

    st.sidebar.title("🦅 GLOBAL WINGS ERP")
    opcion = st.sidebar.radio("Módulos", ["📊 Dashboard & Balance", "🍗 Inventario Operativo", "🍔 Gestión de Combos", "💰 Punto de Venta", "👥 Clientes (CRM)", "📉 Flujo de Caja"])

    # --- 1. DASHBOARD & BALANCE GENERAL ---
    if opcion == "📊 Dashboard & Balance":
        st.header("📊 Balance General y Dashboard")
        
        # Cálculos de Balance
        activos_caja = st.session_state.db_finanzas[st.session_state.db_finanzas['Tipo'].isin(['Ingreso', 'Capital'])]['Monto_Bs'].sum() - \
                       st.session_state.db_finanzas[st.session_state.db_finanzas['Tipo'] == 'Egreso']['Monto_Bs'].sum()
        valor_inventario = (st.session_state.db_inv['Stock'] * st.session_state.db_inv['Costo_Unit_Bs']).sum()
        total_activos = activos_caja + valor_inventario
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Caja Disponible (Bs)", f"{activos_caja:,.2f} Bs")
        col2.metric("Valor Inventario (Bs)", f"{valor_inventario:,.2f} Bs")
        col3.metric("TOTAL ACTIVOS", f"{total_activos:,.2f} Bs")

        st.subheader("Estado de Situación")
        balance_data = {
            "Categoría": ["Activo Circulante (Caja)", "Inventario de Mercaderías", "TOTAL ACTIVOS", "Capital Social", "Utilidades Acumuladas"],
            "Monto (Bs)": [activos_caja, valor_inventario, total_activos, 0, activos_caja]
        }
        st.table(pd.DataFrame(balance_data))

    # --- 2. INVENTARIO OPERATIVO ---
    elif opcion == "🍗 Inventario Operativo":
        st.header("🍗 Inventario de Insumos")
        with st.form("nuevo_insumo"):
            c1, c2, c3 = st.columns(3)
            nom = c1.text_input("Insumo (ej: Alitas, Papas)")
            stk = c2.number_input("Stock Inicial", min_value=0.0)
            cst = c3.number_input("Costo Unitario (Bs)", min_value=0.0)
            if st.form_submit_button("Añadir al Sistema"):
                nuevo = pd.DataFrame([{"ID": len(st.session_state.db_inv)+1, "Insumo": nom, "Stock": stk, "Costo_Unit_Bs": cst, "Min_Stock": 10}])
                st.session_state.db_inv = pd.concat([st.session_state.db_inv, nuevo], ignore_index=True)
                st.success("Insumo añadido.")
        
        st.subheader("Control de Stock")
        st.session_state.db_inv = st.data_editor(st.session_state.db_inv, num_rows="dynamic")

    # --- 3. GESTIÓN DE COMBOS (VINCULADO A COSTOS) ---
    elif opcion == "🍔 Gestión de Combos":
        st.header("🍔 Ingeniería de Combos")
        st.write("Crea combos vinculados a insumos para calcular el costo real.")
        
        if not st.session_state.db_inv.empty:
            with st.form("crear_combo"):
                nom_c = st.text_input("Nombre del Combo (ej: Combo Familiar)")
                ins_id = st.selectbox("Insumo que utiliza", st.session_state.db_inv["Insumo"].tolist())
                cant_i = st.number_input("Cantidad de este insumo", min_value=1.0)
                pv = st.number_input("Precio de Venta (Bs)", min_value=0.0)
                if st.form_submit_button("Crear Combo"):
                    n_combo = pd.DataFrame([{"Nombre_Combo": nom_c, "Insumo_ID": ins_id, "Cantidad_Insumo": cant_i, "Precio_Venta_Bs": pv}])
                    st.session_state.db_combos = pd.concat([st.session_state.db_combos, n_combo], ignore_index=True)
                    st.success("Combo creado.")
            
            st.subheader("Combos Activos y Rentabilidad")
            # Unir para ver costos
            if not st.session_state.db_combos.empty:
                df_c = st.session_state.db_combos.merge(st.session_state.db_inv[['Insumo', 'Costo_Unit_Bs']], left_on='Insumo_ID', right_on='Insumo')
                df_c['Costo_Produccion'] = df_c['Cantidad_Insumo'] * df_c['Costo_Unit_Bs']
                df_c['Margen_Bs'] = df_c['Precio_Venta_Bs'] - df_c['Costo_Produccion']
                st.dataframe(df_c[['Nombre_Combo', 'Insumo_ID', 'Costo_Produccion', 'Precio_Venta_Bs', 'Margen_Bs']])
        else:
            st.warning("Primero agrega insumos al inventario.")

    # --- 4. PUNTO DE VENTA (BIDIRECCIONAL) ---
    elif opcion == "💰 Punto de Venta":
        st.header("💰 Punto de Venta")
        if not st.session_state.db_combos.empty:
            c1, c2 = st.columns(2)
            sel_cli = c1.selectbox("Cliente", st.session_state.db_clientes["Nombre"].tolist() if not st.session_state.db_clientes.empty else ["Genérico"])
            sel_combo = c2.selectbox("Seleccionar Combo", st.session_state.db_combos["Nombre_Combo"].unique())
            cant_v = st.number_input("Cantidad", min_value=1)
            
            if st.button("CONFIRMAR VENTA"):
                # Lógica: Descontar stock e Impactar Clientes
                combo_info = st.session_state.db_combos[st.session_state.db_combos["Nombre_Combo"] == sel_combo].iloc[0]
                insumo_a_descontar = combo_info["Insumo_ID"]
                cant_a_descontar = combo_info["Cantidad_Insumo"] * cant_v
                precio_t = combo_info["Precio_Venta_Bs"] * cant_v
                
                idx_inv = st.session_state.db_inv.index[st.session_state.db_inv["Insumo"] == insumo_a_descontar][0]
                
                if st.session_state.db_inv.at[idx_inv, "Stock"] >= cant_a_descontar:
                    st.session_state.db_inv.at[idx_inv, "Stock"] -= cant_a_descontar
                    # Registrar Venta
                    nv = pd.DataFrame([{"ID_Venta": len(st.session_state.db_ventas)+1, "Fecha": datetime.now(), "Cod_Cliente": sel_cli, "Combo": sel_combo, "Total_Bs": precio_t, "Estado": "Confirmado"}])
                    st.session_state.db_ventas = pd.concat([st.session_state.db_ventas, nv], ignore_index=True)
                    # Registrar Finanzas
                    nf = pd.DataFrame([{"Fecha": datetime.now(), "Concepto": f"Venta {sel_combo}", "Tipo": "Ingreso", "Monto_Bs": precio_t}])
                    st.session_state.db_finanzas = pd.concat([st.session_state.db_finanzas, nf], ignore_index=True)
                    st.success(f"Venta Exitosa por {precio_t} Bs. Inventario actualizado.")
                else:
                    st.error("No hay stock suficiente para este combo.")
        else:
            st.error("Debes crear al menos un combo antes de vender.")

    # --- 5. CLIENTES (CRM) ---
    elif opcion == "👥 Clientes (CRM)":
        st.header("👥 Gestión Dinámica de Clientes")
        with st.form("nuevo_cliente"):
            nom_cli = st.text_input("Nombre Completo")
            if st.form_submit_button("Registrar Cliente"):
                cod = f"GW-{len(st.session_state.db_clientes)+1001}"
                n_c = pd.DataFrame([{"Codigo_Cliente": cod, "Nombre": nom_cli, "Total_Pedidos": 0, "Total_Gastado_Bs": 0}])
                st.session_state.db_clientes = pd.concat([st.session_state.db_clientes, n_c], ignore_index=True)
                st.success(f"Cliente registrado con código: {cod}")
        
        # Actualizar estadísticas de clientes desde ventas
        if not st.session_state.db_ventas.empty:
            for idx, row in st.session_state.db_clientes.iterrows():
                v_cli = st.session_state.db_ventas[st.session_state.db_ventas["Cod_Cliente"] == row["Nombre"]]
                st.session_state.db_clientes.at[idx, "Total_Pedidos"] = len(v_cli)
                st.session_state.db_clientes.at[idx, "Total_Gastado_Bs"] = v_cli["Total_Bs"].sum()
        
        st.dataframe(st.session_state.db_clientes, use_container_width=True)

    # --- 6. FLUJO DE CAJA ---
    elif opcion == "📉 Flujo de Caja":
        st.header("📉 Movimientos de Caja")
        with st.expander("💸 Registrar Gasto / Capital"):
            with st.form("mov_caja"):
                con = st.text_input("Concepto (ej: Pago Sueldos, Inyección Capital)")
                tip = st.selectbox("Tipo", ["Egreso", "Capital"])
                mon = st.number_input("Monto (Bs)", min_value=0.0)
                if st.form_submit_button("Registrar Movimiento"):
                    nf = pd.DataFrame([{"Fecha": datetime.now(), "Concepto": con, "Tipo": tip, "Monto_Bs": mon}])
                    st.session_state.db_finanzas = pd.concat([st.session_state.db_finanzas, nf], ignore_index=True)
                    st.success("Movimiento guardado.")
        
        st.subheader("Historial de Caja")
        st.dataframe(st.session_state.db_finanzas)
