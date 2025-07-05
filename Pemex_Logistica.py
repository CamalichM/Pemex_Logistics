import dash
from dash import html, dcc, Output, Input
import dash_bootstrap_components as dbc
import pandas as pd
import os
import sys
from datetime import datetime
import plotly.express as px
import threading
import webbrowser
import signal

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

TERMINALES = ['Guaymas', 'Zapopan', 'El Castillo', 'Rosarito', 'Topolobampo', 'L Cardenas', 'Manzanillo']

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

DATA_FOLDER = resource_path('data')
HISTORICO_FOLDER = resource_path('historico')
os.makedirs(HISTORICO_FOLDER, exist_ok=True)

def buscar_archivo_base():
    desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
    posibles_rutas = [desktop, DATA_FOLDER, os.path.abspath('.')]
    for folder in posibles_rutas:
        if os.path.exists(folder):
            for file in os.listdir(folder):
                if "PACIFICO" in file.upper() and file.endswith((".xlsm", ".xlsx")):
                    return os.path.join(folder, file)
    return None

def detectar_tabla(df):
    for i in range(len(df)):
        fila = df.iloc[i]
        columnas = fila.astype(str).str.strip().str.upper().tolist()
        if "DESTINO" in columnas and any(prod in columnas for prod in ["REGULAR", "PREMIUM", "DIESEL"]):
            df_tabla = df.iloc[i+1:].copy()
            df_tabla.columns = columnas
            cols = ["DESTINO"] + [col for col in ["REGULAR", "PREMIUM", "DIESEL"] if col in columnas]
            return df_tabla[cols].dropna(subset=["DESTINO"])
    return None

def cargar_base(path):
    base_dict = {}
    xls = pd.ExcelFile(path)
    for hoja in TERMINALES:
        if hoja in xls.sheet_names:
            try:
                df_raw = pd.read_excel(xls, sheet_name=hoja, header=None)
                tabla = detectar_tabla(df_raw)
                if tabla is not None and not tabla.empty:
                    tabla['Terminal'] = hoja
                    base_dict[hoja] = tabla
            except Exception as e:
                print(f"Error leyendo {hoja}: {e}")
    return base_dict

def historico_csv(base_dict):
    today = datetime.today().strftime('%d.%m.%Y')
    out_file = os.path.join(HISTORICO_FOLDER, f"historico_{today}.csv.gz")
    df = pd.concat(base_dict.values(), ignore_index=True)
    df.to_csv(out_file, index=False, compression='gzip')

def calcular_kpis(base_dict):
    total, reg, pre, die = 0, 0, 0, 0
    for df in base_dict.values():
        reg += df.get('REGULAR', pd.Series(0)).fillna(0).sum()
        pre += df.get('PREMIUM', pd.Series(0)).fillna(0).sum()
        die += df.get('DIESEL', pd.Series(0)).fillna(0).sum()
    total = reg + pre + die
    return int(total), int(reg), int(pre), int(die)

def graficas(base_dict):
    df_all = pd.concat(base_dict.values(), ignore_index=True)

    # Gráfico 1: Total por Terminal
    term_data = df_all.groupby('Terminal')[['REGULAR', 'PREMIUM', 'DIESEL']].sum().sum(axis=1).reset_index(name='Cantidad')
    fig1 = px.bar(term_data, x='Terminal', y='Cantidad', title="Requerimientos por Terminal", color_discrete_sequence=["#800020"])

    # Gráfico 2: Distribución por Producto
    prod_data = df_all[['REGULAR', 'PREMIUM', 'DIESEL']].sum().reset_index()
    prod_data.columns = ['Producto', 'Cantidad']
    fig2 = px.pie(prod_data, names='Producto', values='Cantidad', title="Distribución por Producto", color_discrete_sequence=["#800020", "#FFCC00", "#666666"])

    # Gráfico 3: Cumplimiento General por Terminal
    cumpl = term_data.copy()
    cumpl['% Cumplimiento'] = (cumpl['Cantidad'] / cumpl['Cantidad'].replace(0,1)) * 100
    fig3 = px.bar(cumpl, x='Terminal', y='% Cumplimiento', title="Cumplimiento % por Terminal", color_discrete_sequence=["#FFCC00"])

    # Gráfico 4: Brecha de Asignación por Terminal (Dummy)
    cumpl['Brecha'] = cumpl['Cantidad'] * 0.1
    fig4 = px.bar(cumpl, x='Terminal', y='Brecha', title="Brecha de Asignación por Terminal", color_discrete_sequence=["#800020"])

    # Gráfico 5: Cumplimiento por Producto (Dummy)
    comp_prod = prod_data.copy()
    comp_prod['%'] = (comp_prod['Cantidad'] / comp_prod['Cantidad'].sum()) * 100
    fig5 = px.bar(comp_prod, x='Producto', y='%', title="Cumplimiento por Producto", color_discrete_sequence=["#800020"])

    # Gráfico 6: Total Programado vs Asignado Global (Dummy)
    total_prog = df_all[['REGULAR', 'PREMIUM', 'DIESEL']].sum().sum()
    total_asig = total_prog * 0.8
    pie_data = pd.DataFrame({
        'Estado': ['Programado', 'Asignado'],
        'Cantidad': [total_prog, total_asig]
    })
    fig6 = px.pie(pie_data, names='Estado', values='Cantidad', title="Programado vs Asignado", color_discrete_sequence=["#800020", "#FFCC00"])

    return fig1, fig2, fig3, fig4, fig5, fig6

app.layout = dbc.Container(fluid=True, children=[
    html.H1("PEMEX Logística - Dashboard Zona Pacífico", className="text-center my-4 text-danger fw-bold"),

    dbc.Row([
        dbc.Col([
            html.H5("Carga de Datos Locales"),
            html.P("La aplicación buscará BASE PACIFICO primero en el Escritorio, luego en /data/ y luego en la carpeta actual."),
            dbc.Button("Cargar Datos y Generar Dashboard", id="load-data", color="warning", className="mb-3 w-100"),
            html.Div(id="load-status", className="alert mt-2"),
        ], width=3),

        dbc.Col([
            dbc.Row([
                dbc.Col(html.Div([
                    html.H4("Total Requerimientos"),
                    html.Div(id="kpi-total", className="display-6 text-primary")
                ], className="kpi-card"), width=3),

                dbc.Col(html.Div([
                    html.H4("Regular"),
                    html.Div(id="kpi-regular", className="display-6")
                ], className="kpi-card"), width=3),

                dbc.Col(html.Div([
                    html.H4("Premium"),
                    html.Div(id="kpi-premium", className="display-6")
                ], className="kpi-card"), width=3),

                dbc.Col(html.Div([
                    html.H4("Diesel"),
                    html.Div(id="kpi-diesel", className="display-6")
                ], className="kpi-card"), width=3),
            ])
        ], width=9),
    ]),

    dbc.Row([
        dbc.Col(dcc.Graph(id="grafico1"), width=6),
        dbc.Col(dcc.Graph(id="grafico2"), width=6),
    ], className="mt-4"),

    dbc.Row([
        dbc.Col(dcc.Graph(id="grafico3"), width=6),
        dbc.Col(dcc.Graph(id="grafico4"), width=6),
    ], className="mt-4"),

    dbc.Row([
        dbc.Col(dcc.Graph(id="grafico5"), width=6),
        dbc.Col(dcc.Graph(id="grafico6"), width=6),
    ], className="mt-4"),

    html.Hr(),

    dbc.Row([
        dbc.Col(
            dbc.Button("Salir de la Aplicación", id="exit-button", color="danger", className="w-25"),
            width={"size": 12},
            className="d-flex justify-content-center mb-4"
        ),
    ]),
])

@app.callback(
    [Output("load-status", "children"),
     Output("kpi-total", "children"),
     Output("kpi-regular", "children"),
     Output("kpi-premium", "children"),
     Output("kpi-diesel", "children"),
     Output("grafico1", "figure"),
     Output("grafico2", "figure"),
     Output("grafico3", "figure"),
     Output("grafico4", "figure"),
     Output("grafico5", "figure"),
     Output("grafico6", "figure")],
    Input("load-data", "n_clicks")
)
def actualizar(n_clicks):
    if not n_clicks:
        return "", "", "", "", "", {}, {}, {}, {}, {}, {}

    base = buscar_archivo_base()
    if not base:
        return "❌ BASE PACIFICO no encontrado.", "", "", "", "", {}, {}, {}, {}, {}, {}

    base_dict = cargar_base(base)
    if not base_dict:
        return "❌ No se cargaron hojas válidas.", "", "", "", "", {}, {}, {}, {}, {}, {}

    historico_csv(base_dict)
    total, reg, pre, die = calcular_kpis(base_dict)
    figs = graficas(base_dict)

    status = f"✅ Cargado: {os.path.basename(base)}"
    return status, total, reg, pre, die, *figs

@app.callback(
    Output("load-status", "children"),
    Input("exit-button", "n_clicks"),
    prevent_initial_call=True
)
def salir(n):
    os.kill(os.getpid(), signal.SIGTERM)
    return "Aplicación cerrada."

def abrir_navegador():
    webbrowser.open_new("http://127.0.0.1:8050/")

if __name__ == "__main__":
    threading.Timer(1, abrir_navegador).start()
    app.run_server(debug=False)
