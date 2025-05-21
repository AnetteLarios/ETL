import dash
from dash import dcc, html, dash_table, Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import os
import uuid
from data_cleaner import DataCleaner
from file_manager import FileManager

dash.register_page(__name__, path="/etl", name="Limpieza ETL")

RUTA_TXT = "ruta_actual.txt"
ARCHIVOS_GUARDADOS = "archivos_guardados"
os.makedirs(ARCHIVOS_GUARDADOS, exist_ok=True)

layout = dbc.Container([
    dcc.Location(id="url"),
    dcc.Interval(id="etl-interval", interval=500, n_intervals=0, max_intervals=5),
    dcc.Store(id="etl-progress-store", data=0),

    html.H2("Proceso ETL - Limpieza de Datos", className="my-3"),

    html.Div(id="debug-info", style={"color": "red", "marginBottom": "15px"}),
    html.Pre(id="debug-console", style={
        "backgroundColor": "#f8f9fa",
        "padding": "10px",
        "border": "1px solid #ccc",
        "whiteSpace": "pre-wrap"
    }),

    dbc.Progress(id="etl-progress-bar", value=0, striped=True, animated=True, className="mb-4"),

    dbc.Row([
        dbc.Col([
            html.H4("1️⃣ Datos Originales (preview)"),
            html.Div(id='original-preview')
        ], width=6),
        dbc.Col([
            html.H4("2️⃣ Datos Limpios (preview)"),
            html.Div(id='clean-preview')
        ], width=6),
    ]),

    html.Br(),
    html.Div(id="proceso-etl-detallado"),

    html.H5("3️⃣ Guardar o descargar archivo limpio"),
    dcc.Dropdown(
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
    dbc.Button("Guardar", id="btn-save", color="success", className="mt-2"),
    html.Div(id="save-output", className="mt-2", style={"whiteSpace": "pre-wrap"}),
    dcc.Download(id="download-cleaned-file"),

    html.Br(),
    dbc.Button("⬅️ Volver a carga de archivos", href="/upload", color="secondary", className="mt-3"),

    html.Br(),
    dbc.Button("➡️ Ir a análisis exploratorio", href="/eda", color="info", className="mt-3")
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

@dash.callback(
    Output("original-preview", "children"),
    Output("clean-preview", "children"),
    Output("debug-info", "children"),
    Output("debug-console", "children"),
    Output("proceso-etl-detallado", "children"),
    Input("etl-progress-store", "data")
)
def limpiar_auto(progress):
    if progress < 100:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

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

@dash.callback(
    Output("save-output", "children"),
    Output("download-cleaned-file", "data"),
    Input("btn-save", "n_clicks"),
    State("save-format", "value"),
    prevent_initial_call=True
)
def guardar_o_descargar(n, formato):
    try:
        temp_path = os.path.join(ARCHIVOS_GUARDADOS, "limpio_temp.csv")
        if not os.path.exists(temp_path):
            return "❌ No hay archivo limpio disponible.", None

        df_clean = pd.read_csv(temp_path)
        fm = FileManager()

        if formato == "postgresql":
            fm.save_data(df_clean, "postgresql")
            return "✅ Guardado en PostgreSQL exitosamente.", None

        ext = formato if formato != "xlsx" else "xlsx"
        filename = f"data_cleaned_{uuid.uuid4().hex[:6]}.{ext}"
        filepath = os.path.join(ARCHIVOS_GUARDADOS, filename)

        fm.save_data(df_clean, filepath)
        return f"✅ Archivo listo para descarga: {filename}", dcc.send_file(filepath)

    except Exception as e:
        return f"❌ Error al guardar: {str(e)}", None
