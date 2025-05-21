import dash
from dash import html
import dash_bootstrap_components as dbc

dash.register_page(__name__, path="/", name="Inicio")

layout = dbc.Container([
    html.H2("Bienvenido al Sistema de ETL para Hotel Bookings", className="my-4"),
    html.P("Este sistema permite cargar archivos de datos, realizar limpieza, análisis y minería para apoyar en la toma de decisiones."),
    html.Hr(),
    html.P("Navega por las pestañas para explorar cada módulo del sistema y su proceso ETL."),
    dbc.Alert("Estamos listos para comenzar 🚀", color="success")
])
