import dash
from dash import html, dcc, Output, Input
import dash_bootstrap_components as dbc
import pandas as pd
import os
from datetime import datetime
import plotly.express as px
import threading
import webbrowser
import signal

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.LUX])
server = app.server

TERMINALES = ['Guaymas', 'Zapopan', 'El Castillo', 'Rosarito', 'Topolobampo', 'L Cardenas', 'Manzanillo']

DATA_FOLDER = 'data'
HISTORICO_FOLDER = 'historico'
os.makedirs(HISTORICO_FOLDER, exist_ok=True)

def buscar_archivo(nombre_parcial):
    rutas = [os.path.join(os.path.expanduser('~'), 'Desktop'), DATA_FOLDER, os.getcwd()]
    for carpeta in rutas:
        if os.path.exists(carpeta):
            for archivo in os.listdir(carpeta):
                if nombre_parcial.upper() in archivo.upper() and archivo.endswith(('.xlsm', '.xlsx')):
                    return os.path.join(carpeta, archivo)
    return None

def detectar_tabla(df):
    for i in range(len(df)):
        fila = df.iloc[i]
        columnas = fila.astype(str).str.strip().str.upper().tolist()
        if 'DESTINO' in columnas and any(p in columnas for p in ['REGULAR', 'PREMIUM', 'DIESEL']):
            df_tabla = df.iloc[i+1:].copy()
            df_tabla.columns = columnas
            cols = ['DESTINO'] + [c for c in ['REGULAR', 'PREMIUM', 'DIESEL'] if c in columnas]
            return df_tabla[cols].dropna(subset=['DESTINO'])
    return None

def cargar_base():
    path = buscar_archivo('PACIFICO')
    if not path:
        return None, None
    base_dict = {}
    xls = pd.ExcelFile(path)
    for hoja in TERMINALES:
        if hoja in xls.sheet_names:
            df_raw = pd.read_excel(xls, sheet_name=hoja, header=None)
            tabla = detectar_tabla(df_raw)
            if tabla is not None and not tabla.empty:
                tabla['Terminal'] = hoja
                base_dict[hoja] = tabla
    return path, base_dict

def cargar_completo_v5():
    path = buscar_archivo('Completo v5')
    if path:
        df = pd.read_excel(path, sheet_name=0)
        df.columns = [c.strip() for c in df.columns]
        return df
    return pd.DataFrame()

def historico_csv(base_dict):
    today = datetime.today().strftime('%d.%m.%Y')
    out_file = os.path.join(HISTORICO_FOLDER, f"historico_{today}.csv.gz")
    df = pd.concat(base_dict.values(), ignore_index=True)
    df.to_csv(out_file, index=False, compression='gzip')

def calcular_kpis(base_dict):
    reg = sum(df.get('REGULAR', pd.Series(0)).fillna(0).sum() for df in base_dict.values())
    pre = sum(df.get('PREMIUM', pd.Series(0)).fillna(0).sum() for df in base_dict.values())
    die = sum(df.get('DIESEL', pd.Series(0)).fillna(0).sum() for df in base_dict.values())
    total = reg + pre + die
    return int(total), int(reg), int(pre), int(die)

def graficas(base_dict, df_v5):
    df_all = pd.concat(base_dict.values(), ignore_index=True)

    figs = []

    # Volumen programado por terminal con barras apiladas
    resumen_terminal = df_all.groupby('Terminal')[['REGULAR', 'PREMIUM', 'DIESEL']].sum().reset_index()
    figs.append(px.bar(resumen_terminal, x='Terminal', y=['REGULAR', 'PREMIUM', 'DIESEL'], barmode='stack', title='Programado por Terminal'))

    # Volumen total por producto
    totales = resumen_terminal[['REGULAR', 'PREMIUM', 'DIESEL']].sum().reset_index()
    totales.columns = ['Producto', 'Volumen']
    figs.append(px.bar(totales, x='Producto', y='Volumen', title='Volumen Total por Producto'))

    # Participación por producto
    figs.append(px.pie(totales, names='Producto', values='Volumen', title='Participación por Producto'))

    if not df_v5.empty:
        df_v5_sorted = df_v5.sort_values('TERMINAL')
        figs.append(px.line(df_v5_sorted, x='TERMINAL', y='Cump Demanda %', markers=True, title='Cumplimiento de Demanda por Terminal'))
        figs.append(px.line(df_v5_sorted, x='TERMINAL', y='% Utilizado', markers=True, title='Utilización de Capacidad'))
        figs.append(px.bar(df_v5_sorted, x='TERMINAL', y='Diferencia', title='Brecha Programado vs Asignado'))

    for fig in figs:
        fig.update_layout(transition_duration=500)

    return figs

app.layout = dbc.Container(fluid=True, children=[
    html.H1("PEMEX Logística - Dashboard Zona Pacífico", className="text-center my-4 text-primary fw-bold"),

    dbc.Row([
        dbc.Col(
            html.Div([
                html.H4("Total"),
                html.Div(id="kpi-total", className="display-6 text-success"),
            ], className="kpi-card"),
            width=3,
        ),
        dbc.Col(
            html.Div([
                html.H4("Regular"),
                html.Div(id="kpi-regular", className="display-6 text-success"),
            ], className="kpi-card"),
            width=3,
        ),
        dbc.Col(
            html.Div([
                html.H4("Premium"),
                html.Div(id="kpi-premium", className="display-6 text-success"),
            ], className="kpi-card"),
            width=3,
        ),
        dbc.Col(
            html.Div([
                html.H4("Diesel"),
                html.Div(id="kpi-diesel", className="display-6 text-success"),
            ], className="kpi-card"),
            width=3,
        ),
    ], className="mb-4"),

    dbc.Button("Cargar Datos", id="load-data", color="primary", className="my-3"),
    html.Div(id="load-status", className="mb-3"),

    html.Div(id="graficas-div", className="row g-4"),

    dbc.Button("Salir", id="exit-button", color="danger", className="mt-4"),
    html.Div(id="exit-dummy", style={"display": "none"})
])

@app.callback(
    [Output("load-status", "children"),
     Output("kpi-total", "children"),
     Output("kpi-regular", "children"),
     Output("kpi-premium", "children"),
     Output("kpi-diesel", "children"),
     Output("graficas-div", "children")],
    Input("load-data", "n_clicks"),
    prevent_initial_call=True
)
def cargar(n):
    path_base, base_dict = cargar_base()
    if not path_base or not base_dict:
        return "❌ Datos no encontrados", "", "", "", "", []

    historico_csv(base_dict)
    df_v5 = cargar_completo_v5()
    total, reg, pre, die = calcular_kpis(base_dict)
    figs = graficas(base_dict, df_v5)

    graficas_html = [
        dbc.Col(
            html.Div(dcc.Graph(figure=fig), className="graph-container"),
            width=6,
            className="mb-4",
        )
        for fig in figs
    ]

    return "✅ Datos cargados", total, reg, pre, die, graficas_html

@app.callback(
    Output("exit-dummy", "children"),
    Input("exit-button", "n_clicks"),
    prevent_initial_call=True
)
def salir(n):
    os.kill(os.getpid(), signal.SIGTERM)
    return ""

def abrir_navegador():
    webbrowser.open_new("http://127.0.0.1:8050/")

if __name__ == "__main__":
    threading.Timer(1, abrir_navegador).start()
    app.run_server(debug=False)
