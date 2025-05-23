import dash                                   # Framework principal para apps web interactivas
from dash import dcc, html, dash_table, Input, Output, State   # Componentes de Dash y propiedades de callbacks
import dash_bootstrap_components as dbc       # Componentes con estilo Bootstrap para Dash
import pandas as pd                           # Librería para manejo de datos
import os                                     # Módulo para operaciones con el sistema de archivos
import uuid                                   # Genera identificadores únicos para nombres de archivo
import pathlib                                # Manejo avanzado de rutas
from data_cleaner import DataCleaner          # Clase personalizada para limpiar datos
from file_manager import FileManager          # Clase personalizada para guardar datos

dash.register_page(__name__, path="/etl", name="Limpieza ETL")   # Registra esta página bajo la ruta "/etl"

RUTA_TXT = "ruta_actual.txt"                  # Archivo que guarda la ruta del último archivo cargado
ARCHIVOS_GUARDADOS = "archivos_guardados"     # Carpeta donde se guardarán archivos limpios
os.makedirs(ARCHIVOS_GUARDADOS, exist_ok=True) # Crea la carpeta si no existe


layout = dbc.Container([                      # Contenedor principal de la página
    dcc.Location(id="url"),                   # Componente que permite leer la URL actual
    dcc.Interval(id="etl-interval", interval=500, n_intervals=0, max_intervals=5),
    dcc.Store(id="etl-progress-store", data=0),
    html.H2("Proceso ETL - Limpieza de Datos", className="my-3"),   # Título principal

    html.Div(id="debug-info", style={"color": "red", "marginBottom": "15px"}),   # Área para mensajes de error
    html.Pre(id="debug-console", style={       # Consola de depuración con estilo visual
        "backgroundColor": "#f8f9fa",
        "padding": "10px",
        "border": "1px solid #ccc",
        "whiteSpace": "pre-wrap"
    }),

    dbc.Row([                                  # Fila con dos columnas: datos originales y limpios
    dbc.Progress(id="etl-progress-bar", value=0, striped=True, animated=True, className="mb-4"),


        dbc.Col([
            html.H4("1️⃣ Datos Originales (preview)"),
            html.Div(id='original-preview')    # Aquí se mostrará la tabla original
        ], width=6),
        dbc.Col([
            html.H4("2️⃣ Datos Limpios (preview)"),
            html.Div(id='clean-preview')       # Aquí se mostrará la tabla limpia
        ], width=6),
    ]),

    html.Br(),

    html.H5("3️⃣ Guardar o descargar archivo limpio"),  # Sección para guardar o descargar archivo

    dcc.Dropdown(                              # Menú desplegable para elegir formato de guardado

    html.Div(id="proceso-etl-detallado"),

        id="save-format",
        options=[
            {"label": "CSV", "value": "csv"},
            {"label": "Excel (.xlsx)", "value": "xlsx"},
            {"label": "JSON", "value": "json"},
            {"label": "PostgreSQL", "value": "postgresql"},
        ],
        placeholder="Selecciona el formato de guardado",
        style={"width": "50%"}
    ),

    dbc.Button("Guardar", id="btn-save", color="success", className="mt-2"),  # Botón para guardar

    html.Div(id="save-output", className="mt-2", style={"whiteSpace": "pre-wrap"}),  # Resultado del guardado

    dcc.Download(id="download-cleaned-file"),  # Permite descargar archivos limpios

    html.Br(),
    dbc.Button("⬅️ Volver a carga de archivos", href="/upload", color="secondary", className="mt-3"),  # Navegación a carga

    html.Br(),
    dbc.Button("➡️ Ir a análisis exploratorio", href="/eda", color="info", className="mt-3")  # Navegación a EDA
])


def render_table(df: pd.DataFrame, limit=100):   # Función que crea una tabla a partir de un DataFrame
    return html.Div([
        dash_table.DataTable(
            data=df.head(limit).to_dict("records"),               # Muestra solo los primeros "limit" registros
            columns=[{"name": i, "id": i} for i in df.columns],   # Define las columnas por nombre e ID
            page_size=10,                                         # Paginación de 10 registros por página
            style_table={
                "maxHeight": "300px", "overflowY": "auto", "overflowX": "auto", "border": "1px solid #ccc"
            },
            style_cell={
                "textAlign": "left", "fontSize": "13px", "minWidth": "100px", "maxWidth": "300px", "whiteSpace": "normal"
            },
        )
    ])

@dash.callback(
    Output("etl-progress-store", "data"),
    Output("etl-progress-bar", "value"),
    Output("etl-progress-bar", "label"),
    Input("etl-interval", "n_intervals"),
    prevent_initial_call=False
)
def update_progress_bar(n):
    progress = min(n * 25, 100)
    label = f"{progress}% Completado" if progress < 100 else "ETL Completado"
    return progress, progress, label


@dash.callback(  # Callback que limpia automáticamente al cargar la página ETL
    Output("original-preview", "children"),
    Output("clean-preview", "children"),
    Output("debug-info", "children"),
    Output("debug-console", "children"),
    Output("proceso-etl-detallado", "children"),
    Input("etl-progress-store", "data")
)

def limpiar_auto(pathname):  # Función que limpia los datos al entrar a /etl
    if pathname != "/etl":
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update

    log = ""
    pasos = []

    if not os.path.exists(RUTA_TXT):
        log += "❌ No se encontró ruta_actual.txt\n"
        return html.Div("⚠️ No hay ruta guardada."), "", "Archivo .txt no existe", log, ""

    with open(RUTA_TXT, "r") as f:
        file_path = f.read().strip()

    log += f"📦 Ruta leída:\n{file_path}\n"

    if not os.path.exists(file_path):
        log += "❌ Archivo no existe\n"
        return html.Div("❌ Archivo perdido"), "", "Archivo faltante", log, ""

    try:

        df = pd.read_csv(file_path)            # Lee el archivo original
        preview_original = render_table(df)    # Prepara vista previa

        cleaner = DataCleaner(df)              # Instancia el limpiador con el DataFrame
        cleaner.drop_duplicates()              # Elimina duplicados
        cleaner.standardize_dates()            # Estandariza fechas
        cleaner.fill_missing_values()          # Llena valores nulos básicos
        cleaner.advanced_imputation_knn()      # Imputación avanzada con KNN
        cleaner.create_new_columns()           # Crea nuevas columnas si aplica
        cleaner.validate_numeric_columns()     # Verifica y limpia columnas numéricas
        cleaner.drop_missing_targets()         # Elimina filas sin variable objetivo
        cleaner.drop_unused_columns()          # Elimina columnas innecesarias
        df_clean = cleaner.get_dataframe()     # Obtiene el DataFrame limpio

        temp_path = os.path.join(ARCHIVOS_GUARDADOS, "limpio_temp.csv")  # Ruta temporal
        df_clean.to_csv(temp_path, index=False)                          # Guarda temporal

        preview_clean = render_table(df_clean)     # Prepara tabla limpia.
        log += "✅ Limpieza completada automáticamente\n"
        return preview_original, preview_clean, "✅ Datos limpios listos", log

        df = pd.read_csv(file_path)
        preview_original = render_table(df)

        pasos.append(html.Li(f"🔍 Registros originales: {df.shape[0]} filas, {df.shape[1]} columnas"))

        cleaner = DataCleaner(df)

        cleaner.drop_duplicates()
        pasos.append(html.Li(f"🧹 Duplicados eliminados. Filas después: {cleaner.df.shape[0]}"))

        cleaner.standardize_dates()
        pasos.append(html.Li(f"📆 Fechas convertidas y filas con fechas inválidas eliminadas"))

        cleaner.fill_missing_values()
        pasos.append(html.Li(f"🧩 Valores nulos rellenados en columnas como 'country', 'children', etc."))

        cleaner.advanced_imputation_knn()
        cleaner.create_new_columns()
        pasos.append(html.Li(f"➕ Columna 'total_nights' creada"))

        cleaner.validate_numeric_columns()
        pasos.append(html.Li(f"🔢 Columnas numéricas validadas y convertidas"))

        cleaner.drop_missing_targets()
        pasos.append(html.Li(f"🚫 Filas sin valor en 'is_canceled' eliminadas"))

        cleaner.drop_unused_columns()
        pasos.append(html.Li(f"🗑️ Columnas eliminadas: 'company', 'reservation_status'"))

        df_clean = cleaner.get_dataframe()
        temp_path = os.path.join(ARCHIVOS_GUARDADOS, "limpio_temp.csv")
        df_clean.to_csv(temp_path, index=False)

        preview_clean = render_table(df_clean)
        log += "✅ Limpieza completada y archivo guardado automáticamente\n"

        resumen_etl = html.Div([
            html.H5("🧾 Detalle del Proceso de Limpieza (ETL)"),
            html.Ul(pasos)
        ])

        return preview_original, preview_clean, "✅ Datos limpios listos", log, resumen_etl

    except Exception as e:
        log += f"❌ Error:\n{str(e)}"
        return html.Div("❌ Fallo al procesar archivo"), "", str(e), log, ""

def render_table(df: pd.DataFrame, limit=100):
    return html.Div([
        dash_table.DataTable(
            data=df.head(limit).to_dict("records"),
            columns=[{"name": i, "id": i} for i in df.columns],
            page_size=10,
            style_table={
                "maxHeight": "300px",
                "overflowY": "auto",
                "overflowX": "auto",
                "border": "1px solid #ccc"
            },
            style_cell={
                "textAlign": "left",
                "fontSize": "13px",
                "minWidth": "100px",
                "maxWidth": "300px",
                "whiteSpace": "normal"
            },
        )
    ])

@dash.callback(  # Callback para guardar o descargar los datos limpios.
    Output("save-output", "children"),
    Output("download-cleaned-file", "data"),
    Input("btn-save", "n_clicks"),
    State("save-format", "value"),
    prevent_initial_call=True
)
def guardar_o_descargar(n, formato):  # Función para guardar o descargar datos limpios. 
    try:
        temp_path = os.path.join(ARCHIVOS_GUARDADOS, "limpio_temp.csv")
        if not os.path.exists(temp_path):
            return "❌ No hay archivo limpio disponible.", None

        df_clean = pd.read_csv(temp_path)
        fm = FileManager()

        if formato == "postgresql":
            fm.save_data(df_clean, "postgresql")   # Guarda en base de datos PostgreSQL.
            return "✅ Guardado en PostgreSQL exitosamente.", None

        ext = formato if formato != "xlsx" else "xlsx"
        filename = f"data_cleaned_{uuid.uuid4().hex[:6]}.{ext}"  # Genera nombre único.
        filepath = os.path.join(ARCHIVOS_GUARDADOS, filename)

        fm.save_data(df_clean, filepath)            # Guarda el archivo en disco.
        return f"✅ Archivo listo para descarga: {filename}", dcc.send_file(filepath)

    except Exception as e:
        return f"❌ Error al guardar: {str(e)}", None 