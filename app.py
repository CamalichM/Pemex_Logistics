import dash
from dash import html, dcc, Output, Input
import dash_bootstrap_components as dbc
import pandas as pd
import os
from datetime import datetime
import plotly.express as px

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

DATA_FOLDER = os.path.join(os.getcwd(), 'data')
HISTORICO_FOLDER = os.path.join(os.getcwd(), 'historico')
os.makedirs(HISTORICO_FOLDER, exist_ok=True)

TERMINALES = ['Guaymas', 'Zapopan', 'El Castillo', 'Rosarito', 'Topolobampo', 'L Cardenas', 'Manzanillo']

def buscar_archivo_base():
    posibles_carpetas = [DATA_FOLDER, os.getcwd()]
    for folder in posibles_carpetas:
        if os.path.exists(folder):
            for f in os.listdir(folder):
                if "PACIFICO" in f.upper() and f.endswith((".xlsm", ".xlsx")):
                    return os.path.join(folder, f)
    return None

def detectar_tabla(df):
    for i in range(len(df)):
        fila = df.iloc[i]
        columnas = fila.astype(str).str.strip().str.upper().tolist()
        if "DESTINO" in columnas and any(prod in columnas for prod in ["REGULAR", "PREMIUM", "DIESEL"]):
            df_tabla = df.iloc[i+1:].copy()
            df_tabla.columns = columnas
            cols_validas = ["DESTINO"] + [col for col in ["REGULAR", "PREMIUM", "DIESEL"] if col in columnas]
            df_tabla = df_tabla[cols_validas].dropna(subset=["DESTINO"])
            return df_tabla
    return None

def cargar_tabla_requerimientos(path):
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
                print(f"⚠️ Error leyendo hoja {hoja}: {e}")
    return base_dict

def guardar_historico(base_dict):
    today = datetime.today().strftime('%d.%m.%Y')
    output_file = os.path.join(HISTORICO_FOLDER, f"historico_{today}.csv.gz")
    df_total = pd.concat(base_dict.values(), ignore_index=True)
    df_total.to_csv(output_file, index=False, compression='gzip')

def calcular_kpis(base_dict):
    total_req = 0
    por_producto = {'REGULAR': 0, 'PREMIUM': 0, 'DIESEL': 0}

    for df in base_dict.values():
        for prod in por_producto.keys():
            if prod in df.columns:
                por_producto[prod] += df[prod].fillna(0).sum()
                total_req += df[prod].fillna(0).sum()

    return int(total_req), por_producto

app.layout = dbc.Container(fluid=True, children=[
    html.H1("PEMEX Logística - Dashboard Zona Pacífico", className="text-center my-4"),

    dbc.Row([
        dbc.Col([
            html.H5("Carga de Datos Locales"),
            html.P("La aplicación buscará BASE PACIFICO en /data/ o raíz."),
            dbc.Button("Cargar Datos y Generar Dashboard", id="load-data", color="warning"),
            html.Div(id="load-status", className="alert mt-2")
        ], width=3),

        dbc.Col([
            dbc.Row([
                dbc.Col(html.Div([
                    html.H4("Total Requerimientos"),
                    html.Div(id="kpi-total", className="display-6 text-primary")
                ], className="kpi-card"), width=4),

                dbc.Col(html.Div([
                    html.H4("Regular"),
                    html.Div(id="kpi-regular", className="display-6")
                ], className="kpi-card"), width=4),

                dbc.Col(html.Div([
                    html.H4("Diesel"),
                    html.Div(id="kpi-diesel", className="display-6")
                ], className="kpi-card"), width=4),
            ])
        ], width=9),
    ]),

    dbc.Row([
        dbc.Col(dcc.Graph(id="grafico-terminal"), width=6),
        dbc.Col(dcc.Graph(id="grafico-producto"), width=6),
    ], className="mt-4"),

    dbc.Row([
        dbc.Col(dcc.Graph(id="grafico-destino"), width=12),
    ], className="mt-4")
])

@app.callback(
    [Output("load-status", "children"),
     Output("kpi-total", "children"),
     Output("kpi-regular", "children"),
     Output("kpi-diesel", "children"),
     Output("grafico-terminal", "figure"),
     Output("grafico-producto", "figure"),
     Output("grafico-destino", "figure")],
    Input("load-data", "n_clicks")
)
def procesar_datos(n_clicks):
    if not n_clicks:
        return "", "", "", "", {}, {}, {}

    base_file = buscar_archivo_base()
    if not base_file:
        return "❌ No se encontró BASE PACIFICO.", "", "", "", {}, {}, {}

    base_dict = cargar_tabla_requerimientos(base_file)
    if not base_dict:
        return "❌ No se pudo cargar ninguna hoja válida.", "", "", "", {}, {}, {}

    guardar_historico(base_dict)
    total_req, por_producto = calcular_kpis(base_dict)
    status = f"✅ Cargado: {os.path.basename(base_file)}"

    # Gráfico por Terminal
    terminal_data = []
    for hoja, df in base_dict.items():
        total_terminal = df[['REGULAR', 'PREMIUM', 'DIESEL']].fillna(0).sum().sum()
        terminal_data.append({"Terminal": hoja, "Cantidad": total_terminal})
    df_terminal = pd.DataFrame(terminal_data)
    fig_terminal = px.bar(df_terminal, x="Terminal", y="Cantidad", title="Requerimientos por Terminal")

    # Gráfico por Producto
    prod_data = [{"Producto": prod, "Cantidad": qty} for prod, qty in por_producto.items()]
    df_prod = pd.DataFrame(prod_data)
    fig_producto = px.pie(df_prod, names='Producto', values='Cantidad', title="Distribución por Producto")

    # Gráfico por Destino
    df_destinos = pd.concat(base_dict.values(), ignore_index=True)
    df_destinos = df_destinos.melt(id_vars=['DESTINO'], value_vars=['REGULAR', 'PREMIUM', 'DIESEL'], var_name='Producto', value_name='Cantidad')
    df_dest_group = df_destinos.groupby('DESTINO')['Cantidad'].sum().reset_index()
    fig_destino = px.bar(df_dest_group, x='DESTINO', y='Cantidad', title="Requerimientos por Destino", color='DESTINO')

    return status, total_req, int(por_producto['REGULAR']), int(por_producto['DIESEL']), fig_terminal, fig_producto, fig_destino

if __name__ == "__main__":
    app.run_server(debug=True)
