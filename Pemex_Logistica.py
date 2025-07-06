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
    rutas = [DATA_FOLDER, os.getcwd()]
    for carpeta in rutas:
        if os.path.exists(carpeta):
            for archivo in os.listdir(carpeta):
                if nombre_parcial.replace(" ", "").upper() in archivo.replace(" ", "").upper():
                    return os.path.join(carpeta, archivo)
    return None

def cargar_completo_v5():
    path = buscar_archivo('Completo v5')
    if path:
        df = pd.read_excel(path, sheet_name='Reporte SAD', header=3)
        df.columns = [str(c).strip() for c in df.columns]
        df.rename(columns={'GASOLINA REGULAR': 'Terminal'}, inplace=True)
        df = df[df['Terminal'].notna() & ~df['Terminal'].astype(str).str.contains('Terminales', case=False, na=False)]
        df = df.reset_index(drop=True)
        return df
    return pd.DataFrame()

def cargar_base():
    path = buscar_archivo('PACIFICO')
    if not path:
        return None, None
    base_dict = {}
    xls = pd.ExcelFile(path)
    for hoja in TERMINALES:
        if hoja in xls.sheet_names:
            df_raw = pd.read_excel(xls, sheet_name=hoja, header=None)
            for i, fila in df_raw.iterrows():
                columnas = fila.astype(str).str.strip().str.upper().tolist()
                if 'DESTINO' in columnas and any(p in columnas for p in ['REGULAR', 'PREMIUM', 'DIESEL']):
                    tabla = df_raw.iloc[i+1:].copy()
                    tabla.columns = columnas
                    tabla = tabla[['DESTINO', 'REGULAR', 'PREMIUM', 'DIESEL']]
                    tabla.dropna(subset=['DESTINO'], inplace=True)
                    tabla['Terminal'] = hoja
                    base_dict[hoja] = tabla.reset_index(drop=True)
                    break
    return path, base_dict

def graficas(base_dict, df_v5):
    figs = []

    df_all = pd.concat(base_dict.values())
    resumen_total_terminal = df_all.groupby('Terminal')[['REGULAR', 'PREMIUM', 'DIESEL']].sum().reset_index()
    total_productos = resumen_total_terminal[['REGULAR', 'PREMIUM', 'DIESEL']].sum().reset_index()
    total_productos.columns = ['Producto', 'Volumen']
    figs.append(px.pie(total_productos, names='Producto', values='Volumen', title='Participación por Producto'))

    figs.append(px.bar(resumen_total_terminal, x='Terminal', y=['REGULAR', 'PREMIUM', 'DIESEL'], barmode='stack',
                       title='Volumen Programado Total por Terminal'))

    figs.append(px.bar(total_productos, x='Producto', y='Volumen', title='Volumen Total por Producto'))

    for hoja, df in base_dict.items():
        resumen_terminal = df.groupby('DESTINO', as_index=False)[['REGULAR', 'PREMIUM', 'DIESEL']].sum()
        resumen_terminal['DESTINO'] = resumen_terminal['DESTINO'].astype(str)
        fig = px.bar(resumen_terminal, x='DESTINO', y=['REGULAR', 'PREMIUM', 'DIESEL'], barmode='stack',
                     title=f'Volumen Programado hacia Destinos desde {hoja}')
        fig.update_xaxes(
            title_text='Destino',
            categoryorder='array',
            categoryarray=resumen_terminal['DESTINO'].tolist(),
            type='category'
        )
        figs.append(fig)

    if not df_v5.empty:
        df_v5_sorted = df_v5.sort_values('Terminal')
        col_cump = next((c for c in df_v5.columns if 'Cump' in c), None)
        col_util = next((c for c in df_v5.columns if 'Utilizado' in c), None)
        col_dif = next((c for c in df_v5.columns if 'Diferencia' in c), None)

        if col_cump:
            figs.append(px.line(df_v5_sorted, x='Terminal', y=col_cump, markers=True,
                                title='Cumplimiento de Demanda por Terminal'))
        if col_util:
            figs.append(px.line(df_v5_sorted, x='Terminal', y=col_util, markers=True,
                                title='Utilización de Capacidad'))
        if col_dif:
            figs.append(px.bar(df_v5_sorted, x='Terminal', y=col_dif,
                               title='Brecha Programado vs Asignado'))

    for fig in figs:
        fig.update_layout(transition_duration=500)

    return figs

app.layout = dbc.Container(fluid=True, children=[
    html.H1("PEMEX Logística - Dashboard Zona Pacífico", className="text-center my-4 text-primary fw-bold"),

    dbc.Row([
        dbc.Col(html.Div([html.H4("Total"), html.Div("0", id="kpi-total", className="display-6 text-muted")]), width=3),
        dbc.Col(html.Div([html.H4("Regular"), html.Div("0", id="kpi-regular", className="display-6 text-muted")]), width=3),
        dbc.Col(html.Div([html.H4("Premium"), html.Div("0", id="kpi-premium", className="display-6 text-muted")]), width=3),
        dbc.Col(html.Div([html.H4("Diesel"), html.Div("0", id="kpi-diesel", className="display-6 text-muted")]), width=3),
    ], className="mb-4"),

    dbc.Button("Cargar Datos", id="load-data", color="primary", className="my-3"),
    html.Div("Esperando datos…", id="load-status", className="mb-3 text-info"),

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
        return "❌ Datos no encontrados", "0", "0", "0", "0", []

    df_v5 = cargar_completo_v5()
    reg = sum(pd.to_numeric(df.get('REGULAR'), errors='coerce').fillna(0).sum() for df in base_dict.values())
    pre = sum(pd.to_numeric(df.get('PREMIUM'), errors='coerce').fillna(0).sum() for df in base_dict.values())
    die = sum(pd.to_numeric(df.get('DIESEL'), errors='coerce').fillna(0).sum() for df in base_dict.values())
    total = reg + pre + die

    figs = graficas(base_dict, df_v5)

    graficas_html = [
        dbc.Col(dcc.Graph(figure=fig), width=6, className="mb-4")
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
