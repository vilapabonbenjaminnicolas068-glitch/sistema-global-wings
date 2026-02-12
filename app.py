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
        st.session_state.db_inv = pd.DataFrame(columns=["Insumo", "Tipo", "Unidad", "Stock", "Costo_Unit_Bs"])
    if 'db_recetas' not in st.session_state:
        st.session_state.db_recetas = pd.DataFrame(columns=["Combo", "Insumo", "Cantidad"])
    if 'db_combos' not in st.session_state:
        st.session_state.db_combos = pd.DataFrame(columns=["Nombre_Combo", "Precio_Venta_Bs"])
    if 'db_ventas' not in st.session_state:
        st.session_state.db_ventas = pd.DataFrame(columns=["Fecha", "Cliente", "Combo", "Total_Bs", "Costo_Total", "Metodo"])
    if 'db_clientes' not in st.session_state:
        st.session_state.db_clientes = pd.DataFrame(columns=["Codigo", "Nombre", "Celular"])
    if 'finanzas_adj' not in st.session_state:
        st.session_state.finanzas_adj = {"ajuste_activo": 0.0, "ajuste_pasivo": 0.0, "ajuste_gastos": 0.0}

    st.sidebar.title("🦅 GLOBAL WINGS")
    opcion = st.sidebar.radio("Navegación", 
        ["🏠 Inicio", "📦 Monitor de Stock", "🍗 Gestión Inventario", "🍔 Combos & Recetas", "💰 Punto de Venta", "👥 Clientes & Historial", "📊 Estados Financieros"])

    # --- 1. INICIO ---
    if opcion == "🏠 Inicio":
        st.header("🏠 Resumen de Operaciones")
        v = st.session_state.db_ventas
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Ventas Totales", f"{v['Total_Bs'].sum():,.2f} Bs")
        c2.metric("Utilidad Bruta", f"{(v['Total_Bs'].sum() - v['Costo_Total'].sum()):,.2f} Bs")
        c3.metric("Clientes", len(st.session_state.db_clientes))
        c4.metric("Insumos Críticos", len(st.session_state.db_inv[st.session_state.db_inv['Stock'] < 5]))
        
        st.subheader("Últimos Movimientos")
        st.dataframe(v.tail(10), use_container_width=True)

    # --- 2. MONITOR DE STOCK (NUEVA PESTAÑA) ---
    elif opcion == "📦 Monitor de Stock":
        st.header("📦 Monitor de Inventario en Tiempo Real")
        st.write("Estado actual de existencias:")
        
        def color_stock(val):
            color = 'red' if val < 5 else 'orange' if val < 15 else 'green'
            return f'color: {color}; font-weight: bold'

        if not st.session_state.db_inv.empty:
            df_mon = st.session_state.db_inv.copy()
            df_mon['Valor_en_Dinero'] = df_mon['Stock'] * df_mon['Costo_Unit_Bs']
            st.dataframe(df_mon.style.applymap(color_stock, subset=['Stock']), use_container_width=True)
            
            st.info("🟢 Verde: Stock Seguro | 🟠 Naranja: Reabastecer Pronto | 🔴 Rojo: Alerta Crítica")
        else:
            st.warning("No hay insumos registrados.")

    # --- 3. GESTIÓN INVENTARIO ---
    elif opcion == "🍗 Gestión Inventario":
        st.header("🍗 Entrada y Configuración de Insumos")
        with st.expander("➕ Registrar Nuevo Item"):
            with st.form("n_insumo"):
                nom = st.text_input("Nombre (ej: Alitas, Aceite, Bolsas)")
                tip = st.selectbox("Categoría", ["Insumo Combo", "Gasto General", "Adicional/Extra"])
                uni = st.selectbox("Medida", ["Kg", "Litro", "Unidad", "Porción"])
                if st.form_submit_button("Crear Insumo"):
                    n = pd.DataFrame([{"Insumo": nom, "Tipo": tip, "Unidad": uni, "Stock": 0.0, "Costo_Unit_Bs": 0.0}])
                    st.session_state.db_inv = pd.concat([st.session_state.db_inv, n], ignore_index=True)
        
        st.subheader("🛒 Cargar Compras (Aumentar Cantidades)")
        if not st.session_state.db_inv.empty:
            with st.form("compra"):
                ins_sel = st.selectbox("Insumo", st.session_state.db_inv["Insumo"])
                cant_c = st.number_input("Cantidad que entra", min_value=0.1)
                costo_t = st.number_input("Costo Total de esta compra (Bs)", min_value=0.1)
                if st.form_submit_button("Confirmar Entrada"):
                    idx = st.session_state.db_inv.index[st.session_state.db_inv['Insumo'] == ins_sel][0]
                    st.session_state.db_inv.at[idx, 'Stock'] += cant_c
                    st.session_state.db_inv.at[idx, 'Costo_Unit_Bs'] = costo_t / cant_c
                    st.success("Inventario aumentado.")

    # --- 4. COMBOS & RECETAS ---
    elif opcion == "🍔 Combos & Recetas":
        st.header("🍔 Ingeniería de Menú")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Crear Combo")
            with st.form("c_combo"):
                n_c = st.text_input("Nombre del Combo")
                p_v = st.number_input("Precio Venta (Bs)", min_value=0.0)
                if st.form_submit_button("Guardar Combo"):
                    st.session_state.db_combos = pd.concat([st.session_state.db_combos, pd.DataFrame([{"Nombre_Combo": n_c, "Precio_Venta_Bs": p_v}])], ignore_index=True)
        with col2:
            st.subheader("Añadir Ingredientes")
            if not st.session_state.db_combos.empty:
                c_sel = st.selectbox("Combo", st.session_state.db_combos["Nombre_Combo"])
                i_sel = st.selectbox("Insumo", st.session_state.db_inv["Insumo"])
                can_r = st.number_input("Cantidad requerida", min_value=0.01)
                if st.button("Vincular a Receta"):
                    st.session_state.db_recetas = pd.concat([st.session_state.db_recetas, pd.DataFrame([{"Combo": c_sel, "Insumo": i_sel, "Cantidad": can_r}])], ignore_index=True)

    # --- 5. PUNTO DE VENTA ---
    elif opcion == "💰 Punto de Venta":
        st.header("💰 Caja Registradora")
        c1, c2 = st.columns(2)
        with c1:
            cli_v = st.selectbox("Cliente", ["Público General"] + st.session_state.db_clientes["Nombre"].tolist())
            com_v = st.selectbox("Combo", st.session_state.db_combos["Nombre_Combo"] if not st.session_state.db_combos.empty else [])
            met_v = st.radio("Pago", ["Efectivo", "QR / Transferencia"])
        with c2:
            can_v = st.number_input("Cantidad", min_value=1)
            if st.button("🚀 PROCESAR VENTA"):
                # Lógica Descuento y Costeo
                receta = st.session_state.db_recetas[st.session_state.db_recetas["Combo"] == com_v]
                costo_total = 0
                for _, r in receta.iterrows():
                    idx = st.session_state.db_inv.index[st.session_state.db_inv["Insumo"] == r["Insumo"]][0]
                    st.session_state.db_inv.at[idx, "Stock"] -= (r["Cantidad"] * can_v)
                    costo_total += st.session_state.db_inv.at[idx, "Costo_Unit_Bs"] * (r["Cantidad"] * can_v)
                
                precio = st.session_state.db_combos[st.session_state.db_combos["Nombre_Combo"] == com_v]["Precio_Venta_Bs"].values[0]
                nv = pd.DataFrame([{"Fecha": datetime.now(), "Cliente": cli_v, "Combo": com_v, "Total_Bs": precio * can_v, "Costo_Total": costo_total, "Metodo": met_v}])
                st.session_state.db_ventas = pd.concat([st.session_state.db_ventas, nv], ignore_index=True)
                st.success("¡Venta Realizada!")

    # --- 6. CLIENTES & HISTORIAL ---
    elif opcion == "👥 Clientes & Historial":
        st.header("👥 Base de Datos de Clientes")
        with st.expander("Registrar Nuevo Cliente"):
            with st.form("n_cli"):
                n_c = st.text_input("Nombre Completo")
                c_c = st.text_input("Celular")
                if st.form_submit_button("Registrar"):
                    cod = f"GW-{len(st.session_state.db_clientes)+1}"
                    st.session_state.db_clientes = pd.concat([st.session_state.db_clientes, pd.DataFrame([{"Codigo": cod, "Nombre": n_c, "Celular": c_c}])], ignore_index=True)
        
        st.subheader("Buscador de Historial por Cliente")
        if not st.session_state.db_clientes.empty:
            cli_h = st.selectbox("Ver historial de:", st.session_state.db_clientes["Nombre"])
            hist = st.session_state.db_ventas[st.session_state.db_ventas["Cliente"] == cli_h]
            st.write(f"Ventas totales: {len(hist)} | Inversión del cliente: {hist['Total_Bs'].sum():,.2f} Bs")
            st.dataframe(hist, use_container_width=True)

    # --- 7. ESTADOS FINANCIEROS (EDITABLES) ---
    elif opcion == "📊 Estados Financieros":
        st.header("📊 Reportes Contables")
        
        # Ajustes manuales
        with st.expander("⚙️ Realizar Ajustes Manuales (Editable)"):
            st.session_state.finanzas_adj["ajuste_activo"] = st.number_input("Ajuste a Activos (Bs)", value=st.session_state.finanzas_adj["ajuste_activo"])
            st.session_state.finanzas_adj["ajuste_gastos"] = st.number_input("Otros Gastos Extra (Bs)", value=st.session_state.finanzas_adj["ajuste_gastos"])

        v_sum = st.session_state.db_ventas['Total_Bs'].sum()
        c_sum = st.session_state.db_ventas['Costo_Total'].sum()
        inv_v = (st.session_state.db_inv['Stock'] * st.session_state.db_inv['Costo_Unit_Bs']).sum()
        
        t1, t2 = st.tabs(["📉 Estado de Resultados", "🏛️ Balance General"])
        
        with t1:
            st.markdown("### ESTADO DE RESULTADOS")
            res_data = {
                "Cuentas": ["(+) Ventas Netas", "(-) Costo de Ventas", "(=) Utilidad Bruta", "(-) Gastos Operativos/Ajustes", "(=) UTILIDAD NETA"],
                "Monto (Bs)": [v_sum, c_sum, v_sum-c_sum, st.session_state.finanzas_adj["ajuste_gastos"], (v_sum-c_sum)-st.session_state.finanzas_adj["ajuste_gastos"]]
            }
            st.table(pd.DataFrame(res_data))

        with t2:
            st.markdown("### BALANCE GENERAL")
            activos = (v_sum + st.session_state.finanzas_adj["ajuste_activo"]) + inv_v
            bal_data = {
                "ACTIVOS": ["Caja y Bancos", "Inventarios", f"Ajustes: {st.session_state.finanzas_adj['ajuste_activo']}", "TOTAL ACTIVOS"],
                "Bs": [v_sum, inv_v, st.session_state.finanzas_adj['ajuste_activo'], activos],
                "PATRIMONIO": ["Capital", "Utilidad del Periodo", "-", "TOTAL PATRIMONIO"],
                "Bs ": [0.0, (v_sum-c_sum)-st.session_state.finanzas_adj["ajuste_gastos"], "-", activos]
            }
            st.table(pd.DataFrame(bal_data))
