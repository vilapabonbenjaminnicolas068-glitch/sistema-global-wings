from flask import Flask, render_template_string, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_DATA'] = 'sqlite:///global_wings.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- MODELOS DE BASE DE DATOS ---

class Insumo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    unidad = db.Column(db.String(20), nullable=False)
    stock = db.Column(db.Float, default=0.0)
    costo_unitario = db.Column(db.Float, default=0.0)

class Receta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    precio_venta = db.Column(db.Float, default=0.0)

class IngredienteReceta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    receta_id = db.Column(db.Integer, db.ForeignKey('receta.id'))
    insumo_id = db.Column(db.Integer, db.ForeignKey('insumo.id'))
    cantidad = db.Column(db.Float, nullable=False)

class Venta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    receta_id = db.Column(db.Integer, db.ForeignKey('receta.id'))
    cantidad = db.Column(db.Integer, nullable=False)
    monto_total = db.Column(db.Float, nullable=False)
    costo_total = db.Column(db.Float, nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.now)

class Gasto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    concepto = db.Column(db.String(200))
    monto = db.Column(db.Float, nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.now)

class Configuracion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    capital_inicial = db.Column(db.Float, default=0.0)

# --- INICIALIZACIÓN ---
with app.app_context():
    db.create_all()
    if not Configuracion.query.first():
        db.session.add(Configuracion(capital_inicial=0.0))
        db.session.commit()

# --- LÓGICA FINANCIERA ---
def obtener_datos_financieros():
    insumos = Insumo.query.all()
    ventas = Venta.query.all()
    gastos = Gasto.query.all()
    config = Configuracion.query.first()

    valor_inventario = sum(i.stock * i.costo_unitario for i in insumos)
    total_ventas = sum(v.monto_total for v in ventas)
    total_costo_ventas = sum(v.costo_total for v in ventas)
    total_gastos = sum(g.monto for g in gastos)
    
    utilidad_bruta = total_ventas - total_costo_ventas
    utilidad_neta = utilidad_bruta - total_gastos
    
    caja = config.capital_inicial + total_ventas - total_gastos - sum(i.stock * i.costo_unitario for i in insumos if i.stock > 0) # Simplificado para fines educativos
    
    return {
        "valor_inventario": valor_inventario,
        "total_ventas": total_ventas,
        "total_gastos": total_gastos,
        "utilidad_neta": utilidad_neta,
        "utilidad_bruta": utilidad_bruta,
        "caja": caja,
        "capital": config.capital_inicial,
        "activos": caja + valor_inventario,
        "pasivos": total_gastos, # Simplificación de pasivos corrientes
        "patrimonio": config.capital_inicial + utilidad_neta
    }

# --- RUTAS ---

@app.route('/')
def index():
    data = obtener_datos_financieros()
    insumos = Insumo.query.all()
    recetas = Receta.query.all()
    return render_template_string(HTML_TEMPLATE, data=data, insumos=insumos, recetas=recetas)

@app.route('/insumo/add', methods=['POST'])
def add_insumo():
    n = request.form['nombre']
    u = request.form['unidad']
    c = float(request.form['costo'])
    db.session.add(Insumo(nombre=n, unidad=u, costo_unitario=c, stock=0))
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/insumo/update_stock', methods=['POST'])
def update_stock():
    iid = request.form['id']
    cant = float(request.form['cantidad'])
    insumo = Insumo.query.get(iid)
    insumo.stock += cant
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/receta/add', methods=['POST'])
def add_receta():
    n = request.form['nombre']
    p = float(request.form['precio'])
    nueva = Receta(nombre=n, precio_venta=p)
    db.session.add(nueva)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/receta/add_ingrediente', methods=['POST'])
def add_ingrediente():
    rid = request.form['receta_id']
    iid = request.form['insumo_id']
    cant = float(request.form['cantidad'])
    db.session.add(IngredienteReceta(receta_id=rid, insumo_id=iid, cantidad=cant))
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/venta/add', methods=['POST'])
def add_venta():
    rid = request.form['receta_id']
    cant_v = int(request.form['cantidad'])
    receta = Receta.query.get(rid)
    
    # Calcular costo y descontar stock
    costo_u = 0
    ingredientes = IngredienteReceta.query.filter_by(receta_id=rid).all()
    
    for ing in ingredientes:
        ins = Insumo.query.get(ing.insumo_id)
        if ins.stock < (ing.cantidad * cant_v):
            return "ERROR: Stock insuficiente", 400
        ins.stock -= (ing.cantidad * cant_v)
        costo_u += (ing.cantidad * ins.costo_unitario)
    
    total = receta.precio_venta * cant_v
    db.session.add(Venta(receta_id=rid, cantidad=cant_v, monto_total=total, costo_total=costo_u * cant_v))
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/config/capital', methods=['POST'])
def update_capital():
    c = float(request.form['capital'])
    config = Configuracion.query.first()
    config.capital_inicial = c
    db.session.commit()
    return redirect(url_for('index'))

# --- FRONTEND (HTML INTEGRADO) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Global Wings - ERP</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: #f4f7f6; font-size: 0.9rem; }
        .card { border: none; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .header-wings { background: #e63946; color: white; padding: 20px; border-radius: 0 0 20px 20px; }
        .metric-card { text-align: center; padding: 15px; }
        .metric-value { font-size: 1.5rem; font-weight: bold; color: #1d3557; }
    </style>
</head>
<body>
<div class="container">
    <div class="header-wings mb-4 text-center">
        <h1>🦅 GLOBAL WINGS</h1>
        <p>Sistema Financiero Universitario - Moneda: Bs</p>
    </div>

    <div class="row">
        <div class="col-md-3"><div class="card metric-card">Ventas Totales<div class="metric-value">{{ "%.2f"|format(data.total_ventas) }} Bs</div></div></div>
        <div class="col-md-3"><div class="card metric-card">Utilidad Neta<div class="metric-value text-success">{{ "%.2f"|format(data.utilidad_neta) }} Bs</div></div></div>
        <div class="col-md-3"><div class="card metric-card">Caja Efectivo<div class="metric-value">{{ "%.2f"|format(data.caja) }} Bs</div></div></div>
        <div class="col-md-3"><div class="card metric-card">Valor Almacén<div class="metric-value">{{ "%.2f"|format(data.valor_inventario) }} Bs</div></div></div>
    </div>

    <div class="row">
        <div class="col-md-6">
            <div class="card p-3">
                <h4>📦 Inventario Operativo</h4>
                <form action="/insumo/add" method="POST" class="row g-2 mb-3">
                    <div class="col-4"><input type="text" name="nombre" class="form-control" placeholder="Insumo" required></div>
                    <div class="col-3"><input type="text" name="unidad" class="form-control" placeholder="Unidad" required></div>
                    <div class="col-3"><input type="number" step="0.01" name="costo" class="form-control" placeholder="Costo Bs" required></div>
                    <div class="col-2"><button class="btn btn-danger w-100">+</button></div>
                </form>
                <table class="table table-sm">
                    <thead><tr><th>Nombre</th><th>Stock</th><th>Costo U.</th><th>Acción</th></tr></thead>
                    <tbody>
                        {% for i in insumos %}
                        <tr>
                            <td>{{ i.nombre }}</td>
                            <td>{{ i.stock }} {{ i.unidad }}</td>
                            <td>{{ i.costo_unitario }} Bs</td>
                            <td>
                                <form action="/insumo/update_stock" method="POST" class="d-flex">
                                    <input type="hidden" name="id" value="{{ i.id }}">
                                    <input type="number" name="cantidad" style="width: 60px" class="form-control form-control-sm me-1" placeholder="+/-">
                                    <button class="btn btn-sm btn-dark">Ok</button>
                                </form>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>

        <div class="col-md-6">
            <div class="card p-3">
                <h4>💰 Punto de Venta</h4>
                <form action="/venta/add" method="POST" class="row g-2 mb-3">
                    <div class="col-7">
                        <select name="receta_id" class="form-select">
                            {% for r in recetas %} <option value="{{ r.id }}">{{ r.nombre }} ({{ r.precio_venta }} Bs)</option> {% endfor %}
                        </select>
                    </div>
                    <div class="col-3"><input type="number" name="cantidad" class="form-control" value="1"></div>
                    <div class="col-2"><button class="btn btn-success w-100">Vender</button></div>
                </form>
                <hr>
                <h4>👨‍🍳 Crear Receta</h4>
                <form action="/receta/add" method="POST" class="row g-2 mb-3">
                    <div class="col-6"><input type="text" name="nombre" class="form-control" placeholder="Nombre Combo"></div>
                    <div class="col-4"><input type="number" step="0.1" name="precio" class="form-control" placeholder="Precio Venta"></div>
                    <div class="col-2"><button class="btn btn-primary w-100">Crear</button></div>
                </form>
            </div>
        </div>
    </div>

    <div class="row">
        <div class="col-md-6">
            <div class="card p-3">
                <h4>🏛️ Balance General</h4>
                <form action="/config/capital" method="POST" class="d-flex mb-3">
                    <input type="number" name="capital" class="form-control me-2" placeholder="Capital Inicial">
                    <button class="btn btn-dark">Definir Capital</button>
                </form>
                <ul class="list-group">
                    <li class="list-group-item d-flex justify-content-between"><b>ACTIVO (Caja + Inv)</b> <span>{{ "%.2f"|format(data.activos) }} Bs</span></li>
                    <li class="list-group-item d-flex justify-content-between"><b>PASIVO (Gastos/Deudas)</b> <span>{{ "%.2f"|format(data.pasivos) }} Bs</span></li>
                    <li class="list-group-item d-flex justify-content-between"><b>PATRIMONIO (Cap + Utilidad)</b> <span>{{ "%.2f"|format(data.patrimonio) }} Bs</span></li>
                </ul>
                <div class="alert mt-3 {{ 'alert-success' if (data.activos|round(2) == (data.pasivos + data.patrimonio)|round(2)) else 'alert-danger' }}">
                    Ecuación Contable: {{ "%.2f"|format(data.activos) }} = {{ "%.2f"|format(data.pasivos + data.patrimonio) }}
                </div>
            </div>
        </div>
        <div class="col-md-6">
            <div class="card p-3">
                <h4>📉 Estado de Resultados</h4>
                <table class="table">
                    <tr><td>Ingresos por Ventas</td><td class="text-end">{{ "%.2f"|format(data.total_ventas) }} Bs</td></tr>
                    <tr><td>(-) Costo de Ventas</td><td class="text-end">-{{ "%.2f"|format(data.total_ventas - data.utilidad_bruta) }} Bs</td></tr>
                    <tr class="table-secondary"><td><b>Utilidad Bruta</b></td><td class="text-end"><b>{{ "%.2f"|format(data.utilidad_bruta) }} Bs</b></td></tr>
                    <tr><td>(-) Gastos Operativos</td><td class="text-end">-{{ "%.2f"|format(data.total_gastos) }} Bs</td></tr>
                    <tr class="table-dark"><td><b>UTILIDAD NETA</b></td><td class="text-end"><b>{{ "%.2f"|format(data.utilidad_neta) }} Bs</b></td></tr>
                </table>
            </div>
        </div>
    </div>
</div>
</body>
</html>
"""

if __name__ == '__main__':
    app.run(debug=True)
