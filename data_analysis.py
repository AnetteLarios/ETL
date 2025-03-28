import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.cluster import KMeans
from sklearn.metrics import classification_report, accuracy_score, mean_absolute_error

class CancellationPredictor:
    """
    Clase para predecir la cancelación de reservas (columna 'is_canceled')
    usando un modelo de Regresión Logística.
    """
    def __init__(self):
        self.model = None

    def train_model(self, df: pd.DataFrame):
        feature_cols = ['lead_time', 'previous_cancellations', 'adr', 'total_nights']
        df_model = df.dropna(subset=feature_cols + ['is_canceled'])
        X = df_model[feature_cols]
        y = df_model['is_canceled']
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        self.model = LogisticRegression(max_iter=1000)
        self.model.fit(X_train, y_train)
        y_pred = self.model.predict(X_test)
        print("=== Resultados de la predicción de cancelaciones ===")
        print(classification_report(y_test, y_pred))
        print(f"Exactitud/accuracy: {accuracy_score(y_test, y_pred):.4f}")

    def predict(self, new_data: pd.DataFrame) -> np.ndarray:
        if self.model is None:
            raise Exception("El modelo no ha sido entrenado. Llama a train_model() primero.")
        return self.model.predict(new_data)


class StayLengthEstimator:
    """
    Clase para estimar la duración de la estancia ('total_nights')
    utilizando RandomForestRegressor.
    """
    def __init__(self):
        self.model = None

    def train_model(self, df: pd.DataFrame):
        feature_cols = ['lead_time', 'adr', 'previous_bookings_not_canceled', 'required_car_parking_spaces']
        df_model = df.dropna(subset=feature_cols + ['total_nights'])
        X = df_model[feature_cols]
        y = df_model['total_nights']
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.model.fit(X_train, y_train)
        y_pred = self.model.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred)
        print("=== Resultados de la estimación de duración de estancia ===")
        print(f"MAE (Mean Absolute Error): {mae:.2f} noches")

    def predict(self, new_data: pd.DataFrame) -> np.ndarray:
        if self.model is None:
            raise Exception("El modelo no ha sido entrenado. Llama a train_model() primero.")
        return self.model.predict(new_data)


class CustomerSegmentation:
    """
    Clase para segmentar clientes utilizando K-Means.
    """
    def __init__(self, n_clusters=4):
        self.n_clusters = n_clusters
        self.kmeans = None

    def segment(self, df: pd.DataFrame) -> pd.DataFrame:
        cols_for_clustering = ['lead_time', 'adr', 'total_nights']
        df_cluster = df.dropna(subset=cols_for_clustering).copy()
        X = df_cluster[cols_for_clustering]
        self.kmeans = KMeans(n_clusters=self.n_clusters, random_state=42)
        df_cluster['cluster'] = self.kmeans.fit_predict(X)
        print("=== Resultados de la Segmentación de Clientes (K-Means) ===")
        print(f"Se formaron {self.n_clusters} clústeres.")
        print(df_cluster['cluster'].value_counts())
        return df_cluster

    def predict_cluster(self, new_data: pd.DataFrame) -> np.ndarray:
        if self.kmeans is None:
            raise Exception("Primero ejecuta segment() para entrenar el modelo K-Means.")
        return self.kmeans.predict(new_data)


class TemporalAnalysis:
    """
    Clase para el análisis de temporalidad (demanda por mes/año).
    """
    def monthly_demand(self, df: pd.DataFrame) -> pd.DataFrame:
        if 'arrival_date_year' not in df.columns or 'arrival_date_month' not in df.columns:
            raise Exception("No existen columnas de año/mes para el análisis temporal.")
        df['year_month'] = df['arrival_date_year'].astype(str) + "-" + df['arrival_date_month'].astype(str)
        demand_by_month = df.groupby('year_month')['is_canceled'].count().reset_index(name='total_reservas')
        print("=== Demanda mensual (total de reservas) ===")
        print(demand_by_month.sort_values('year_month'))
        return demand_by_month

    def plot_monthly_demand(self, demand_by_month: pd.DataFrame):
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            print("matplotlib no está instalado. Usa 'pip install matplotlib' para habilitar gráficos.")
            return
        demand_by_month_sorted = demand_by_month.sort_values('year_month')
        plt.figure()
        plt.plot(demand_by_month_sorted['year_month'], demand_by_month_sorted['total_reservas'], marker='o')
        plt.title('Demanda Mensual (Total de Reservas)')
        plt.xlabel('Año-Mes')
        plt.ylabel('Cantidad de Reservas')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()