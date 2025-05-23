# Importación de librerías necesarias
import base64  # Para decodificar el contenido del archivo subido
import io      # Para manejar flujos de datos en memoria
import uuid    # Para generar identificadores únicos en nombres de archivo
import pandas as pd  # Para manipulación de datos tabulares
from dash import dcc, html, dash_table, Output, Input, State  # Componentes de Dash
import dash_bootstrap_components as dbc  # Componentes con estilos Bootstrap
import dash  # Framework principal de la app
import os    # Para operaciones de sistema de archivos

# Registro de esta página como parte del multipage Dash app
dash.register_page(__name__, path="/upload", name="Cargar Archivos")

# Definición de carpetas y archivos auxiliares
TEMP_DIR = "archivos_temporales"  # Carpeta para guardar archivos temporales
RUTA_TXT = "ruta_actual.txt"      # Archivo que guarda la ruta del archivo subido más reciente

# Crear carpeta y archivo si no existen
os.makedirs(TEMP_DIR, exist_ok=True)
if not os.path.exists(RUTA_TXT):
    with open(RUTA_TXT, "w") as f:
        f.write("")

# Layout de la página de carga de archivos
layout = dbc.Container([
    html.H2("Carga de Archivos (CSV, Excel, JSON)", className="my-3"),

    # Componente de subida de archivos
    dcc.Upload(
        id='upload-data',
        children=html.Div(['Arrastra o haz clic para subir un archivo']),
        style={
            'width': '100%', 'height': '80px', 'lineHeight': '80px',
            'borderWidth': '1px', 'borderStyle': 'dashed',
            'borderRadius': '5px', 'textAlign': 'center',
            'margin-bottom': '20px'
        },
        multiple=False  # Solo permite un archivo a la vez
    ),

    # Contenedor para resumen y previsualización del archivo
    html.Div(id='output-summary'),
    html.Div(id='output-preview'),

    html.Br(),

    # Botón para pasar a la limpieza de datos
    dbc.Button("Continuar con limpieza de datos ➡️", id="go-to-etl", color="secondary", className="mt-3", disabled=True),
    
    # Elemento oculto para redirección de página
    dcc.Location(id="url", refresh=True)
])

# Función para decodificar el contenido subido, cargarlo como DataFrame y guardarlo como archivo temporal
def parse_and_save_file(contents, filename):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)

    try:
        # Detectar formato del archivo según su extensión
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

    # Generar nombre único para el archivo temporal
    temp_filename = f"archivo_{uuid.uuid4().hex[:6]}.csv"
    file_path = os.path.abspath(os.path.join(TEMP_DIR, temp_filename))

    try:
        # Guardar el DataFrame como archivo temporal CSV
        df.to_csv(file_path, index=False)
        print(f"✅ Archivo guardado en: {file_path}")

        # Guardar la ruta en archivo persistente para referencia futura
        with open(RUTA_TXT, "w") as f:
            f.write(file_path)
        print(f"📝 Ruta escrita en {RUTA_TXT}")

    except Exception as e:
        print("❌ No se pudo guardar el archivo:", e)
        return None, None

    return df, file_path

# Callback para manejar la carga de archivos y mostrar resumen + vista previa
@dash.callback(
    Output('output-summary', 'children'),     # Muestra resumen de datos cargados
    Output('output-preview', 'children'),     # Muestra los primeros registros como tabla
    Output('go-to-etl', 'disabled'),          # Habilita botón de limpieza si todo salió bien
    Input('upload-data', 'contents'),         # Disparador: archivo subido
    State('upload-data', 'filename'),         # Nombre del archivo subido
    prevent_initial_call=True                 # Evita ejecutar al cargar la página
)
def update_output(contents, filename):
    if contents is None or filename is None:
        print("⚠️ No hay contenido. No se actualizará la ruta.")
        return "", "", True

    df, file_path = parse_and_save_file(contents, filename)

    if df is None or not os.path.exists(file_path):
        print("❌ No se pudo procesar o guardar el archivo.")
        return html.Div("❌ Error al procesar el archivo."), "", True

    # Componente HTML con el resumen de archivo
    resumen = html.Div([
        html.H5("✅ Archivo cargado correctamente"),
        html.P(f"📄 Nombre original: {filename}"),
        html.P(f"📊 Filas: {df.shape[0]}"),
        html.P(f"📈 Columnas: {df.shape[1]}"),
        html.P(f"🗂️ Ruta temporal: {file_path}")
    ])

    # Tabla con los primeros 5 registros
    preview = dash_table.DataTable(
        data=df.head(5).to_dict('records'),
        columns=[{"name": col, "id": col} for col in df.columns],
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'left', 'fontSize': '14px'},
        page_size=5
    )

    return resumen, preview, False  # Habilita el botón "Continuar"

# Callback para redireccionar a la página de limpieza (/etl) cuando se hace clic en el botón
@dash.callback(
    Output("url", "href"),             # Modifica la URL de la app
    Input("go-to-etl", "n_clicks"),    # Se activa al hacer clic en el botón
    prevent_initial_call=True
)
def redirect_to_etl(n):
    return "/etl"
