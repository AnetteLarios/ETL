import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import os
import plotly.express as px
import plotly.figure_factory as ff
from data_analysis import (
    CancellationPredictor,
    StayLengthEstimator,
    CustomerSegmentation,
    TemporalAnalysis
)

dash.register_page(__name__, path="/data_mining", name="Míneria de datos")

layout = dbc.Container([
    dcc.Location(id="url"),
    html.H2("Minería de Datos", className="my-3"),
    html.Div(id="mining-results", style={"whiteSpace": "pre-wrap", "marginBottom": "20px"}),
    html.Div(id="scatter-plots"),
    html.Div(id="heatmap"),
    html.Div(id="dendrogram"),
    html.Div(id="temporal"),
    html.Br(),
    dbc.Button("⬅️ Volver a EDA", href="/eda", color="secondary", className="mt-3"),
    dbc.Button("➡️ Visualizar objetivo", href="/goal", color="info", className="mt-3")
])

@dash.callback(
    Output("mining-results", "children"),
    Output("scatter-plots", "children"),
    Output("heatmap", "children"),
    Output("dendrogram", "children"),
    Output("temporal", "children"),
    Input("url", "pathname")
)
def mostrar_mineria(pathname):
    if pathname != "/data_mining":
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

    temp_path = os.path.join("archivos_guardados", "limpio_temp.csv")
    if not os.path.exists(temp_path):
        return "❌ No hay datos limpios disponibles.", "", "", "", ""

    df = pd.read_csv(temp_path)
    results = ""
    scatter_plots = []
    heatmap_fig = html.Div()
    dendro_fig = html.Div()
    temporal_fig = html.Div()

    # 1. Cancelación de reservas (Clasificación)
    try:
        cancelador = CancellationPredictor()
        cancel_text = cancelador.train_and_report(df)
        results += (
            "🔎 **Predicción de Cancelación de Reservas**\n"
            "Se utiliza regresión logística para predecir si una reserva será cancelada. "
            "La métrica principal es la exactitud y el reporte de clasificación.\n\n"
            f"{cancel_text}\n"
        )
        # Scatter plot: lead_time vs adr coloreado por is_canceled
        if 'lead_time' in df.columns and 'adr' in df.columns and 'is_canceled' in df.columns:
            scatter_plots.append(
                html.Div([
                    html.P("Relación entre lead_time y adr, coloreado por cancelación:"),
                    dcc.Graph(figure=px.scatter(
                        df, x='lead_time', y='adr', color='is_canceled',
                        title="Scatter: lead_time vs adr (Cancelación)"
                    ))
                ])
            )
    except Exception as e:
        results += f"❌ Error en modelo de cancelación: {e}\n"

    # 2. Estimación de duración de estancia (Regresión)
    try:
        estimator = StayLengthEstimator()
        stay_text = estimator.train_and_report(df)
        results += (
            "🔎 **Estimación de Duración de Estancia**\n"
            "Se utiliza un Random Forest para predecir el número de noches de estancia. "
            "La métrica principal es el error absoluto medio (MAE).\n\n"
            f"{stay_text}\n"
        )
        # Scatter plot: adr vs total_nights
        if 'adr' in df.columns and 'total_nights' in df.columns:
            scatter_plots.append(
                html.Div([
                    html.P("Relación entre adr y total_nights:"),
                    dcc.Graph(figure=px.scatter(
                        df, x='adr', y='total_nights',
                        title="Scatter: adr vs total_nights"
                    ))
                ])
            )
    except Exception as e:
        results += f"❌ Error en modelo de estancia: {e}\n"

    # 3. Segmentación de clientes (Clustering)
    try:
        segmentador = CustomerSegmentation(n_clusters=4)
        df_small = df.sample(min(500, len(df)), random_state=42) if len(df) > 500 else df
        df_cluster = segmentador.segment(df_small)
        cluster_counts = df_cluster['cluster'].value_counts().to_dict()
        results += (
            "🔎 **Segmentación de Clientes (K-Means)**\n"
            "Se agrupan los clientes en 4 clústeres usando lead_time, adr y total_nights. "
            "Esto ayuda a identificar diferentes perfiles de clientes.\n\n"
            f"Distribución de clústeres: {cluster_counts}\n\n"
        )
        # Scatter plot: lead_time vs adr coloreado por cluster
        if 'lead_time' in df_cluster.columns and 'adr' in df_cluster.columns and 'cluster' in df_cluster.columns:
            scatter_plots.append(
                html.Div([
                    html.P("Clusters de clientes según lead_time y adr:"),
                    dcc.Graph(figure=px.scatter(
                        df_cluster, x='lead_time', y='adr', color='cluster',
                        title="Clusters de clientes (lead_time vs adr)"
                    ))
                ])
            )
        # Dendrograma para visualizar la similitud entre clientes
        from scipy.cluster.hierarchy import linkage
        from scipy.spatial.distance import pdist
        dendro_df = df_cluster[['lead_time', 'adr', 'total_nights']].dropna()
        if len(dendro_df) > 1:
            dendro_fig = html.Div([
                html.P("Dendrograma de similitud entre clientes:"),
                dcc.Graph(figure=ff.create_dendrogram(dendro_df, orientation='left'))
            ])
    except Exception as e:
        results += f"❌ Error en segmentación: {e}\n"

    # 4. Análisis temporal (Demanda por mes/año)
    try:
        temporal = TemporalAnalysis()
        demand_by_month = temporal.monthly_demand(df)
        results += (
            "🔎 **Análisis Temporal de la Demanda**\n"
            "Se analiza la cantidad de reservas por mes y año para identificar tendencias estacionales.\n\n"
        )
        # Gráfica de líneas para demanda mensual
        demand_by_month_sorted = demand_by_month.sort_values('year_month')
        temporal_fig = html.Div([
            html.P("Demanda mensual de reservas:"),
            dcc.Graph(figure=px.line(
                demand_by_month_sorted, x='year_month', y='total_reservas',
                title="Demanda Mensual (Total de Reservas)"
            ))
        ])
    except Exception as e:
        results += f"❌ Error en análisis temporal: {e}\n"

    # 5. Heatmap de correlación general
    try:
        numeric_cols = df.select_dtypes(include='number').columns
        if len(numeric_cols) > 1:
            corr = df[numeric_cols].corr()
            heatmap_fig = html.Div([
                html.P("Mapa de calor de correlación entre variables numéricas:"),
                dcc.Graph(figure=px.imshow(corr, text_auto=True, title="Heatmap de Correlación"))
            ])
        else:
            heatmap_fig = html.Div("No hay suficientes columnas numéricas para heatmap.")
    except Exception as e:
        heatmap_fig = html.Div(f"No se pudo generar heatmap: {e}")

    return (
        results,
        html.Div(scatter_plots),
        heatmap_fig,
        dendro_fig,
        temporal_fig
    )