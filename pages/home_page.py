import dash                                  # Importa el núcleo del framework Dash
from dash import html                        # Importa componentes HTML (como Div, P, H2, etc.)
import dash_bootstrap_components as dbc      # Importa componentes con estilo Bootstrap para Dash

dash.register_page(__name__, path="/", name="Inicio")   # Registra esta página como la principal ("/") en una app multipágina

layout = dbc.Container([
    html.Img(src="/assets/landing.jpg", style={"width": "100%"}),
    html.H2("Bienvenido al Sistema para Hotel Bookings", className="my-4"),
    html.P("Este sistema permite cargar archivos de datos, realizar limpieza, análisis y minería para apoyar en la toma de decisiones."),
    html.Hr(),
    html.P("Navega por las pestañas para explorar cada módulo del sistema y su proceso ETL."),
    dbc.Alert("Integrantes de equipo: " , color="success"),
    dbc.Alert("Larios Gonzalez Anette Paola | Código: 218544644", color="success"),
    dbc.Alert("Luna Curiel Diego Israel | Código: 218066009", color="success"),
    dbc.Alert("Magos Durán Eloisa Isabela | Código: 218113112" , color="success")
     
], style={"background-color": "#fdf4e2"})
