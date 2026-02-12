import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="GLOBAL WINGS - ERP TOTAL", layout="wide")

# --- INICIALIZACIÓN DE BASES DE DATOS ---
tablas = ['db_inv', 'db_recetas', 'db_combos', 'db_ventas', 'db_caja', 'db_activos', 'db_costos_ind']
for t in tablas:
    if t not in st.session_state:
        if t == 'db_inv': st.session_state[t] = pd.DataFrame(columns=["Insumo", "Unidad", "Stock", "Costo_Unit_Bs"])
        elif t == 'db_recetas': st.session_state[t] = pd.DataFrame(columns=["Combo", "Insumo", "Cantidad"])
        elif t == 'db_combos': st.session_state[t] = pd.DataFrame(columns=["Nombre", "Precio_Bs"])
        elif t == 'db_ventas': st.session_state[t] = pd.DataFrame(columns=["Fecha", "Combo", "Total_Bs", "Costo_Prod", "Metodo"])
        elif t == 'db_caja': st.session_state[t] = pd.DataFrame(columns=["Fecha", "Concepto", "Monto_Bs", "Tipo"])
        elif t == 'db_activos': st.session_state[t] = pd.DataFrame(columns=["Activo", "Monto_Bs"])
        elif t == 'db_costos_ind': st.session_state[t] = pd.DataFrame(columns=["Combo", "Detalle", "Monto_Bs"])

if 'config' not in st.session_state:
    st.session_state.config = {"inversion": 0.0}

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
    # --- MENÚ LATERAL ---
    menu = st.sidebar.radio("SISTEMA INTEGRAL", ["📊 Dashboard", "🍗 Almacén e Insumos", "🍳 Activos y Equipos", "👨‍🍳 Ingeniería de Recetas", "💰 Punto de Venta", "🏛️ Balance y Finanzas"])

    # --- 1. DASHBOARD ---
    if menu == "📊 Dashboard":
        st.header("📊 Resumen de Operaciones")
        v = st.session_state.db_ventas
        c1, c2, c3 = st.columns(3)
        c1.metric("Ventas Totales", f"{v['Total_Bs'].sum():,.2f} Bs")
        val_inv = (st.session_state.db_inv['Stock'] * st.session_state.db_inv['Costo_Unit_Bs']).sum()
        c2.metric("Valor en Inventario", f"{val_inv:,.2f} Bs")
        c3.metric("Activos Fijos", f"{st.session_state.db_activos['Monto_Bs'].sum():,.2f} Bs")
        st.dataframe(v.tail(10), use_container_width=True)

    # --- 2. ALMACÉN E INSUMOS ---
    elif menu == "🍗 Almacén e Insumos":
        st.header("📦 Gestión de Insumos")
        with st.form("f_inv"):
            ni = st.text_input("Nombre del Insumo")
            un = st.selectbox("Unidad", ["Kg", "Lt", "Unidad", "Gramo"])
            if st.form_submit_button("Registrar Insumo"):
                nuevo_i = pd.DataFrame([{"Insumo": ni, "Unidad": un, "Stock": 0.0, "Costo_Unit_Bs": 0.0}])
                st.session_state.db_inv = pd.concat([st.session_state.db_inv, nuevo_i], ignore_index=True)
        
        st.subheader("🛒 Cargar Compra")
        if not st.session_state.db_inv.empty:
            with st.form("f_compra"):
                ins_compra = st.selectbox("Insumo", st.session_state.db_inv["Insumo"])
                can_compra = st.number_input("Cantidad", min_value=0.01)
                pre_compra = st.number_input("Costo Total Bs", min_value=0.01)
                if st.form_submit_button("Actualizar Almacén"):
                    idx = st.session_state.db_inv.index[st.session_state.db_inv['Insumo'] == ins_compra][0]
                    st.session_state.db_inv.at[idx, 'Stock'] += can_compra
                    st.session_state.db_inv.at[idx, 'Costo_Unit_Bs'] = pre_compra / can_compra
                    st.success("Inventario actualizado.")
        st.dataframe(st.session_state.db_inv, use_container_width=True)

    # --- 3. ACTIVOS E EQUIPOS ---
    elif menu == "🍳 Activos y Equipos":
        st.header("🍳 Gestión de Activos Fijos")
        with st.form("f_act"):
            ac_nom = st.text_input("Nombre del Activo (Sartén, Freidora, etc.)")
            ac_val = st.number_input("Valor Bs", min_value=0.0)
            if st.form_submit_button("Registrar"):
                nuevo_a = pd.DataFrame([{"Activo": ac_nom, "Monto_Bs": ac_val}])
                st.session_state.db_activos = pd.concat([st.session_state.db_activos, nuevo_a], ignore_index=True)
                st.success("Activo registrado.")
        st.dataframe(st.session_state.db_activos, use_container_width=True)

    # --- 4. INGENIERÍA DE RECETAS ---
    elif menu == "👨‍🍳 Ingeniería de Recetas":
        st.header("👨‍🍳 Costeo Maestro")
        with st.form("f_combo_crear"):
            nom_c = st.text_input("Nombre del Combo")
            pre_c = st.number_input("Precio de Venta Bs", min_value=0.0)
            if st.form_submit_button("Crear Combo"):
                st.session_state.db_combos = pd.concat([st.session_state.db_combos, pd.DataFrame([{"Nombre": nom_c, "Precio_Bs": pre_c}])], ignore_index=True)

        if not st.session_state.db_combos.empty:
            st.divider()
            target_c = st.selectbox("Configurar Receta para:", st.session_state.db_combos["Nombre"])
            
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("Insumos Directos (Inventario)")
                if not st.session_state.db_inv.empty:
                    ins_r = st.selectbox("Insumo", st.session_state.db_inv["Insumo"])
                    can_r = st.number_input("Cantidad Necesaria", min_value=0.001, format="%.3f")
                    if st.button("Vincular Insumo"):
                        n_r = pd.DataFrame([{"Combo": target_c, "Insumo": ins_r, "Cantidad": can_r}])
                        st.session_state.db_recetas = pd.concat([st.session_state.db_recetas, n_r], ignore_index=True)
            with c2:
                st.subheader("Costos Indirectos (Manuales)")
                det_ind = st.text_input("Concepto (ej: Empaque, Salsa)")
                mon_ind = st.number_input("Costo Unitario Bs", min_value=0.0)
                if st.button("Añadir Indirecto"):
                    n_i = pd.DataFrame([{"Combo": target_c, "Detalle": det_ind, "Monto_Bs": mon_ind}])
                    st.session_state.db_costos_ind = pd.concat([st.session_state.db_costos_ind, n_i], ignore_index=True)
            
            # Cálculo de Utilidad
            receta = st.session_state.db_recetas[st.session_state.db_recetas["Combo"] == target_c]
            c_dir = sum([st.session_state.db_inv[st.session_state.db_inv["Insumo"] == r["Insumo"]]["Costo_Unit_Bs"].values[0] * r["Cantidad"] for _, r in receta.iterrows()])
            c_ind = st.session_state.db_costos_ind[st.session_state.db_costos_ind["Combo"] == target_c]["Monto_Bs"].sum()
            pv = st.session_state.db_combos[st.session_state.db_combos["Nombre"] == target_c]["Precio_Bs"].values[0]
            st.info(f"Análisis de {target_c}: Costo Total {c_dir + c_ind:,.2f} Bs | Utilidad {pv - (c_dir + c_ind):,.2f} Bs")

    # --- 5. PUNTO DE VENTA ---
    elif menu == "💰 Punto de Venta":
        st.header("💰 Caja")
        if not st.session_state.db_combos.empty:
            sel_v = st.selectbox("Combo", st.session_state.db_combos["Nombre"])
            cant_v = st.number_input("Cantidad", min_value=1)
            met_v = st.radio("Método", ["Efectivo", "QR"])
            
            if st.button("🚀 FINALIZAR VENTA"):
                # Descuento de stock y cálculo de costos
                receta = st.session_state.db_recetas[st.session_state.db_recetas["Combo"] == sel_v]
                costo_d = 0.0
                for _, r in receta.iterrows():
                    idx = st.session_state.db_inv.index[st.session_state.db_inv["Insumo"] == r["Insumo"]][0]
                    st.session_state.db_inv.at[idx, "Stock"] -= (r["Cantidad"] * cant_v)
                    costo_d += st.session_state.db_inv.at[idx, "Costo_Unit_Bs"] * (r["Cantidad"] * cant_v)
                
                costo_i = st.session_state.db_costos_ind[st.session_state.db_costos_ind["Combo"] == sel_v]["Monto_Bs"].sum() * cant_v
                pv = st.session_state.db_combos[st.session_state.db_combos["Nombre"] == sel_v]["Precio_Bs"].values[0]
                
                v_final = pd.DataFrame([{"Fecha": datetime.now(), "Combo": sel_v, "Total_Bs": pv * cant_v, "Costo_Prod": costo_d + costo_i, "Metodo": met_v}])
                st.session_state.db_ventas = pd.concat([st.session_state.db_ventas, v_final], ignore_index=True)
                st.success("Venta Exitosa.")

    # --- 6. BALANCE Y FINANZAS ---
    elif menu == "🏛️ Balance y Finanzas":
        st.header("📊 Finanzas")
        st.session_state.config['inversion'] = st.sidebar.number_input("Inversión Inicial Bs", value=st.session_state.config['inversion'])
        
        with st.form("f_gastos_adm"):
            concepto = st.text_input("Servicio (Luz, Agua, Alquiler)")
            monto = st.number_input("Monto Bs", min_value=0.0)
            if st.form_submit_button("Registrar Gasto"):
                n_g = pd.DataFrame([{"Fecha": datetime.now(), "Concepto": concepto, "Monto_Bs": monto, "Tipo": "Egreso"}])
                st.session_state.db_caja = pd.concat([st.session_state.db_caja, n_g], ignore_index=True)

        v_t = st.session_state.db_ventas['Total_Bs'].sum()
        c_p = st.session_state.db_ventas['Costo_Prod'].sum()
        g_t = st.session_state.db_caja['Monto_Bs'].sum()
        st.metric("UTILIDAD NETA", f"{(v_t - c_p) - g_t:,.2f} Bs")
