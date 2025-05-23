import base64
import io
import uuid
import pandas as pd
from dash import dcc, html, dash_table, Output, Input, State
import dash_bootstrap_components as dbc
import dash
import os

dash.register_page(__name__, path="/upload", name="Cargar Archivos")

TEMP_DIR = "archivos_temporales"
RUTA_TXT = "ruta_actual.txt"

# Asegurar que las carpetas y el archivo .txt existan
os.makedirs(TEMP_DIR, exist_ok=True)
if not os.path.exists(RUTA_TXT):
    with open(RUTA_TXT, "w") as f:
        f.write("")

layout = dbc.Container([

    html.Div( [
        html.Img(src="/assets/upload.png", style={"height": "35px", "align":"center", "margin-right": "20px", "justify":"center", "margin-top": "20px"}),
        html.H2("Carga de Archivos (CSV, Excel, JSON)", className="my-3")], style={"display":"flex"}),
   
    dcc.Upload(
        id='upload-data',
        children=html.Div(['Arrastra o haz clic para subir un archivo']),
        style={
            'width': '100%', 'height': '80px', 'lineHeight': '80px',
            'borderWidth': '1px', 'borderStyle': 'dashed',
            'borderRadius': '5px', 'textAlign': 'center',
            'margin-bottom': '20px', 'backgroundColor':  "#c9e1f8"
        },
        multiple=False
    ),

    html.Div(id='output-summary'),
    html.Div(id='output-preview'),

    html.Br(),
    html.Div([
        dbc.Button("Continuar con limpieza de datos ➡️", id="go-to-etl", color="secondary", className="mt-3", disabled=True)
    ], style={"align": "right", "align-items": "right", "justifyContent": "flex-end", "display":"flex"}),
    dcc.Location(id="url", refresh=True),
    html.Br(),
], style={"background-color": "#fdf4e2"},fluid=True)

# Guardar archivo subido y escribir ruta en ruta_actual.txt
def parse_and_save_file(contents, filename):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)

    try:
        if filename.endswith('.csv'):
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        elif filename.endswith('.xlsx') or filename.endswith('.xls'):
            df = pd.read_excel(io.BytesIO(decoded))
        elif filename.endswith('.json'):
            df = pd.read_json(io.StringIO(decoded.decode('utf-8')))
        else:
            return None, None
    except Exception as e:
        print("❌ Error al leer archivo:", e)
        return None, None

    # Guardar como archivo temporal
    temp_filename = f"archivo_{uuid.uuid4().hex[:6]}.csv"
    file_path = os.path.abspath(os.path.join(TEMP_DIR, temp_filename))

    try:
        df.to_csv(file_path, index=False)
        print(f"✅ Archivo guardado en: {file_path}")

        # Guardar ruta en archivo persistente
        with open(RUTA_TXT, "w") as f:
            f.write(file_path)
        print(f"📝 Ruta escrita en {RUTA_TXT}")

    except Exception as e:
        print("❌ No se pudo guardar el archivo:", e)
        return None, None

    return df, file_path

@dash.callback(
    Output('output-summary', 'children'),
    Output('output-preview', 'children'),
    Output('go-to-etl', 'disabled'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'),
    prevent_initial_call=True
)
def update_output(contents, filename):
    if contents is None or filename is None:
        print("⚠️ No hay contenido. No se actualizará la ruta.")
        return "", "", True

    df, file_path = parse_and_save_file(contents, filename)

    if df is None or not os.path.exists(file_path):
        print("❌ No se pudo procesar o guardar el archivo.")
        return html.Div("❌ Error al procesar el archivo."), "", True

    resumen = html.Div([
        html.H5("✅ Archivo cargado correctamente"),
        html.P(f"📄 Nombre original: {filename}"),
        html.P(f"📊 Filas: {df.shape[0]}"),
        html.P(f"📈 Columnas: {df.shape[1]}"),
        html.P(f"🗂️ Ruta temporal: {file_path}")
    ])

    preview = dash_table.DataTable(
        data=df.head(5).to_dict('records'),
        columns=[{"name": col, "id": col} for col in df.columns],
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'left', 'fontSize': '14px'},
        page_size=5
    )

    return resumen, preview, False

# Redirigir a /etl
@dash.callback(
    Output("url", "href"),
    Input("go-to-etl", "n_clicks"),
    prevent_initial_call=True
)
def redirect_to_etl(n):
    return "/etl"
