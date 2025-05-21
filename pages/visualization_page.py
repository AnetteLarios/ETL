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

dash.register_page(__name__, path="/goal", name="Visualización de objetivo")

layout = dbc.Container([
    dcc.Location(id="url"),
    html.H2("Visualización de objetivo y toma de decisiones", className="my-3"),
    html.Div(id="decision-cancel"),
    html.Div(id="decision-stay"),
    html.Div(id="decision-segment"),
    html.Div(id="decision-temporal"),
    html.Br(),
    dbc.Button("⬅️ Volver a minería de datos", href="/data_mining", color="secondary", className="mt-3"),
])

@dash.callback(
    Output("decision-cancel", "children"),
    Output("decision-stay", "children"),
    Output("decision-segment", "children"),
    Output("decision-temporal", "children"),
    Input("url", "pathname")
)
def mostrar_decisiones(pathname):
    if pathname != "/goal":
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update

    temp_path = os.path.join("archivos_guardados", "limpio_temp.csv")
    if not os.path.exists(temp_path):
        msg = html.Div("❌ No hay datos limpios disponibles.")
        return msg, msg, msg, msg

    df = pd.read_csv(temp_path)

    # 1. Análisis de Cancelaciones: solo proporción de canceladas/no canceladas
    try:
        cancelador = CancellationPredictor()
        cancel_text = cancelador.train_and_report(df)
        if 'is_canceled' in df.columns:
            cancel_counts = df['is_canceled'].value_counts(normalize=True).rename({0: "No Cancelada", 1: "Cancelada"})
            # Solo muestra la proporción, no detalles individuales
            fig_cancel = px.pie(
                names=cancel_counts.index, values=cancel_counts.values,
                title="Proporción de Reservas Canceladas"
            )
        else:
            fig_cancel = None
        explicacion_cancel = (
            html.Div([
                html.H4("1. Análisis de Cancelaciones"),
                dcc.Graph(figure=fig_cancel) if fig_cancel else html.Div("No hay datos de cancelación."),
                html.P("**Dato clave:** {:.1f}% de las reservas fueron canceladas.".format(
                    cancel_counts.get("Cancelada", 0)*100 if 'Cancelada' in cancel_counts else 0)),
                html.P(
                    "Decisión: Si la tasa de cancelación es alta, se pueden implementar políticas de depósito, "
                    "mejorar la comunicación con los clientes o identificar patrones para reducir cancelaciones."
                ),
                html.Pre(cancel_text, style={"fontSize": "12px", "background": "#f8f9fa"})
            ])
        )
    except Exception as e:
        explicacion_cancel = html.Div(f"Error en análisis de cancelaciones: {e}")

    # 2. Estimación de la duración de estancia: solo la media y la moda
    try:
        estimator = StayLengthEstimator()
        stay_text = estimator.train_and_report(df)
        if 'total_nights' in df.columns:
            nights_mean = df['total_nights'].mean()
            nights_mode = df['total_nights'].mode()[0] if not df['total_nights'].mode().empty else None
            # Solo muestra la media y la moda en la gráfica
            df_stay = pd.DataFrame({
                'Tipo': ['Media', 'Moda'],
                'Valor': [nights_mean, nights_mode]
            })
            fig_stay = px.bar(df_stay, x='Tipo', y='Valor', title="Duración Promedio y Más Frecuente de Estancia")
        else:
            fig_stay = None
            nights_mean = 0
        explicacion_stay = (
            html.Div([
                html.H4("2. Estimación de la Duración de Estancia"),
                dcc.Graph(figure=fig_stay) if fig_stay else html.Div("No hay datos de duración de estancia."),
                html.P("**Dato clave:** La estancia promedio es de {:.2f} noches. La moda es {} noches.".format(
                    nights_mean, nights_mode if 'nights_mode' in locals() else 'N/A')),
                html.P(
                    "Decisión: Conocer la duración promedio y la más frecuente ayuda a ajustar precios, promociones y disponibilidad."
                ),
                html.Pre(stay_text, style={"fontSize": "12px", "background": "#f8f9fa"})
            ])
        )
    except Exception as e:
        explicacion_stay = html.Div(f"Error en estimación de duración de estancia: {e}")

    # 3. Segmentación de clientes: solo muestra el centroide de cada cluster
    try:
        segmentador = CustomerSegmentation(n_clusters=4)
        df_small = df.sample(min(500, len(df)), random_state=42) if len(df) > 500 else df
        df_cluster = segmentador.segment(df_small)
        # Calcula centroides
        centroids = df_cluster.groupby('cluster')[['lead_time', 'adr']].mean().reset_index()
        fig_seg = px.scatter(
            centroids, x='lead_time', y='adr', color='cluster',
            title="Centroides de Segmentos de Clientes (lead_time vs adr)",
            labels={'lead_time': 'Lead Time', 'adr': 'ADR'}
        )
        cluster_counts = df_cluster['cluster'].value_counts().to_dict()
        explicacion_segment = (
            html.Div([
                html.H4("3. Segmentación de Clientes"),
                dcc.Graph(figure=fig_seg),
                html.P("**Dato clave:** Distribución de clientes por clúster: {}".format(cluster_counts)),
                html.P(
                    "Decisión: Permite diseñar estrategias personalizadas para cada segmento, "
                    "como promociones para clientes de alta anticipación o tarifas especiales para los más rentables."
                )
            ])
        )
    except Exception as e:
        explicacion_segment = html.Div(f"Error en segmentación de clientes: {e}")

    # 4. Análisis de Temporalidad de la Demanda: solo el mes de mayor demanda
    try:
        temporal = TemporalAnalysis()
        demand_by_month = temporal.monthly_demand(df)
        demand_by_month_sorted = demand_by_month.sort_values('year_month')
        max_month_row = demand_by_month_sorted.loc[demand_by_month_sorted['total_reservas'].idxmax()]
        # Solo muestra el mes de mayor demanda
        fig_temp = px.bar(
            x=[max_month_row['year_month']], y=[max_month_row['total_reservas']],
            labels={'x': 'Mes', 'y': 'Total Reservas'},
            title="Mes de Mayor Demanda"
        )
        explicacion_temporal = (
            html.Div([
                html.H4("4. Análisis de Temporalidad de la Demanda"),
                dcc.Graph(figure=fig_temp),
                html.P(f"**Dato clave:** El mes con mayor demanda fue: {max_month_row['year_month']} ({int(max_month_row['total_reservas'])} reservas)."),
                html.P(
                    "Decisión: Identificar el mes pico permite ajustar precios, planificar personal y lanzar campañas de marketing en ese periodo."
                )
            ])
        )
    except Exception as e:
        explicacion_temporal = html.Div(f"Error en análisis temporal: {e}")

    return explicacion_cancel, explicacion_stay, explicacion_segment, explicacion_temporal