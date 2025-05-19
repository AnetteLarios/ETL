import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

# Inicializar la aplicación
app = dash.Dash(
    __name__,
    use_pages=True,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True  # permite callbacks entre páginas aunque el layout aún no se haya cargado
)
app.title = "Sistema ETL Hotelería"

# ✅ Declaración de Stores globales, afuera del Container
app.layout = html.Div([
    # Almacenes de datos accesibles desde todas las páginas
    dcc.Store(id="stored-raw-data", storage_type="memory"),
    dcc.Store(id="clean-data-store", storage_type="memory"),

    # Contenedor visual principal
    dbc.Container([
        html.H1("Sistema ETL Hotelería", className="my-3"),

        # Navegación entre páginas
        dbc.Nav([
            dbc.NavLink("Inicio", href="/", active="exact"),
            dbc.NavLink("Cargar Archivos", href="/upload", active="exact"),
            dbc.NavLink("Limpieza ETL", href="/etl", active="exact")
        ], pills=True),

        html.Hr(),

        # Sección donde se renderiza cada página (multipágina)
        dash.page_container
    ], fluid=True)
])

# Ejecutar la aplicación
if __name__ == "__main__":
    app.run(debug=True)
