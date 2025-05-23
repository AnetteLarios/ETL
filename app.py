import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

# Inicializar la aplicación
app = dash.Dash(
    __name__,
    use_pages=True,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap"
    ],
    suppress_callback_exceptions=True  # permite callbacks entre páginas aunque el layout aún no se haya cargado
)
app.title = "Sistema ETL Hotelería"

# ✅ Declaración de Sto
# res globales, afuera del Container
app.layout = html.Div([
    # Almacenes de datos accesibles desde todas las páginas
    dcc.Store(id="stored-raw-data", storage_type="memory"),
    dcc.Store(id="clean-data-store", storage_type="memory"),

    
    # Contenedor visual principal
    dbc.Container([
       
        # Navegación entre páginas
        dbc.Nav([
            html.Img(src="/assets/hotel.png", style={"height": "50px", "margin-right": "10px", "margin-left": "5px"}),
            html.H1("Sistema Hotelería", className="my-3",style={"margin-right":"30px", "thickness":"bold", "font-color":"#034081"}),
            dbc.NavLink("Inicio", href="/", active="exact"),
            dbc.NavLink("Cargar Archivos", href="/upload", active="exact"),
            dbc.NavLink("ETL", href="/etl", active="exact"),
            dbc.NavLink("Minería de datos", href="/eda", active="exact"),
            dbc.NavLink("Toma de decisión", href="/goal", active="exact")
        ], pills=True, style={"alignItems": "center", "background-color": "#0f81f3", "width": "100%", "color": "white"}),
    

        # Sección donde se renderiza cada página (multipágina)
        dash.page_container
    ], fluid=True, style={"background-color": "#fdf4e2"}),
])

# Ejecutar la aplicación
if __name__ == "__main__":
    app.run(debug=True)
