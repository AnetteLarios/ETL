import dash                                  # Importa el núcleo del framework Dash
from dash import html                        # Importa componentes HTML (como Div, P, H2, etc.)
import dash_bootstrap_components as dbc      # Importa componentes con estilo Bootstrap para Dash

dash.register_page(__name__, path="/", name="Inicio")   # Registra esta página como la principal ("/") en una app multipágina

layout = dbc.Container([                     # Contenedor principal con márgenes automáticos y centrado.
    html.H2("Bienvenido al Sistema de ETL para Hotel Bookings", className="my-4"),  # Título principal con margen vertical.
    html.P("Este sistema permite cargar archivos de datos, realizar limpieza, análisis y minería para apoyar en la toma de decisiones."),  # Descripción del sistema
    html.Hr(),                               # Línea horizontal para separar secciones.
    html.P("Navega por las pestañas para explorar cada módulo del sistema y su proceso ETL."),  # Instrucción para navegar por la app
    dbc.Alert("Estamos listos para comenzar 🚀", color="success")  # Alerta visual de éxito con mensaje motivador.
])
