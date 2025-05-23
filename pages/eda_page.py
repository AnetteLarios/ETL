import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import os
import plotly.express as px
import plotly.graph_objs as go



dash.register_page(__name__, path="/eda", name="Míneria de datos (EDA y resultados)")

layout = dbc.Container([
    dcc.Location(id="url"),
    html.Div( [
        html.Img(src="/assets/eda.png", style={"height": "35px", "align":"center", "margin-right": "20px", "justify":"center", "margin-top": "20px"}),
        html.H2("EDA", className="my-3")], style={"display":"flex"}),
    html.Div(id="eda-stats", style={"whiteSpace": "pre-wrap", "marginBottom": "20px"}),
    html.Div(id="eda-hist"),
    html.Div(id="eda-box"),
    html.Br(),

    dbc.Button("➡️ Ejecutar técnicas de minería de datos", href="/data_mining", color="info", className="mt-3"),
    html.Br()
])

@dash.callback(
    Output("eda-stats", "children"),
    Output("eda-hist", "children"),
    Output("eda-box", "children"),
    Input("url", "pathname")
)
def mostrar_eda(pathname):
    if pathname != "/eda":
        return dash.no_update, dash.no_update, dash.no_update

    temp_path = os.path.join("archivos_guardados", "limpio_temp.csv")
    if not os.path.exists(temp_path):
        return "❌ No hay datos limpios disponibles.", go.Figure(), go.Figure()

    df = pd.read_csv(temp_path)
    
    columns_to_calculate = ["arrival_date_day_of_month","stays_in_week_nights","stays_in_weekend_nights","total_nights"]

    stats_all = ""
    histograms = []
    boxplots = []

    for col in columns_to_calculate:
    # Selecciona una columna numérica para el ejemplo, puedes cambiarla
        media = df[col].mean()
        mediana = df[col].median()
        desviacion = df[col].std()
        stats_all += (
                f"Columna analizada: {col}\n"
                f"Media: {media:.2f}\n"
                f"Mediana: {mediana:.2f}\n"
                f"Desviación estándar: {desviacion:.2f}\n"
            )
        histograms.append(dcc.Graph(figure=px.histogram(df, x=col, nbins=30, title=f"Histograma de {col}")))
        boxplots.append(dcc.Graph(figure=px.box(df, y=col, title=f"Boxplot de {col}")))

    # Devuelve todos los resultados juntos
    return (
        stats_all,
        histograms,
        boxplots
    )

      
