import pandas as pd
import numpy as np
import dateutil.parser
from sklearn.impute import KNNImputer

class DataCleaner:
    # Columnas que se quiere conservar al final del proceso
    COLUMNS_TO_KEEP = [
        "hotel",
        "reservation_status_date",
        "children",
        "country",
        "agent",
        "company",
        "stays_in_weekend_nights",
        "stays_in_week_nights",
        "is_canceled",
        "lead_time",
        "previous_cancellations",
        "adr",
        "previous_bookings_not_canceled",
        "required_car_parking_spaces",
        "arrival_date_year",
        "arrival_date_month"
    ]

    def __init__(self, dataframe: pd.DataFrame):
        self.df = dataframe.copy()  # Copia de seguridad del DataFrame original

    def drop_duplicates(self):
        before = self.df.shape[0]
        self.df = self.df.drop_duplicates()
        after = self.df.shape[0]
        print(f"Eliminados {before - after} registros duplicados.")

    def standardize_dates(self):
        """Convierten 'reservation_status_date' a formato YYYY-MM-DD y eliminan registros con fecha inválida."""
        if "reservation_status_date" in self.df.columns:
            # Intentar convertir a datetime
            self.df["reservation_status_date"] = pd.to_datetime(
                self.df["reservation_status_date"],
                errors='coerce',
                infer_datetime_format=True
            )
            # Eliminar filas donde la fecha es inválida (NaT)
            invalid_dates = self.df["reservation_status_date"].isna().sum()
            if invalid_dates > 0:
                print(f"Eliminando {invalid_dates} registros con fecha inválida en 'reservation_status_date'.")
                self.df = self.df.dropna(subset=["reservation_status_date"])
            # Convertir a string con formato uniforme
            self.df["reservation_status_date"] = self.df["reservation_status_date"].dt.strftime("%Y-%m-%d")

    def fill_missing_values(self):
        """Imputa valores faltantes en columnas categóricas usando muestreo basado en la distribución real."""
        def smart_impute(col_name, unique_code=-1):
            if col_name in self.df.columns:
                valid_entries = self.df[self.df[col_name].notna() & (self.df[col_name] != 0)][col_name]
                if not valid_entries.empty:
                    # Calcular distribución real
                    freq = valid_entries.value_counts(normalize=True)
                    values = freq.index.tolist()
                    probabilities = freq.values.tolist()
                    null_mask = self.df[col_name].isna()
                    n_nulls = null_mask.sum()
                    sampled_values = np.random.choice(values, size=n_nulls, p=probabilities)
                    self.df.loc[null_mask, col_name] = sampled_values
                    print(f"Imputados {n_nulls} valores en '{col_name}' con distribución real.")
                else:
                    self.df[col_name] = self.df[col_name].fillna(unique_code)
                    print(f"No se encontraron valores válidos para '{col_name}'; se usará el código: {unique_code}.")
                # Reemplazar 0 por código único
                self.df.loc[self.df[col_name] == 0, col_name] = unique_code

        smart_impute("agent", unique_code=999)
        smart_impute("company", unique_code=888)

    def advanced_imputation_knn(self):
        """Imputa valores faltantes en columnas numéricas (excepto 'is_canceled') usando KNN."""
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
        if "is_canceled" in numeric_cols:
            numeric_cols.remove("is_canceled")
        if numeric_cols:
            imputer = KNNImputer(n_neighbors=5)
            imputed = imputer.fit_transform(self.df[numeric_cols])
            self.df[numeric_cols] = pd.DataFrame(imputed, columns=numeric_cols, index=self.df.index)
            print(f"Imputados valores numéricos en las columnas: {numeric_cols}")

    def validate_numeric_columns(self):
        """Elimina registros con valores numéricos negativos en columnas claves."""
        # Por ejemplo: lead_time, adr y total_nights deben ser no negativos
        for col in ["lead_time", "adr", "total_nights"]:
            if col in self.df.columns:
                n_invalid = (self.df[col] < 0).sum()
                if n_invalid > 0:
                    self.df = self.df[self.df[col] >= 0]
                    print(f"Eliminadas {n_invalid} tuplas con valores negativos en '{col}'.")

    def drop_missing_targets(self):
        """Elimina registros que no tengan valor en 'is_canceled'."""
        if "is_canceled" in self.df.columns:
            n_missing = self.df["is_canceled"].isna().sum()
            if n_missing > 0:
                self.df = self.df.dropna(subset=["is_canceled"])
                print(f"Eliminadas {n_missing} tuplas sin valor en 'is_canceled'.")

    def create_new_columns(self):
        """Crea la columna 'total_nights' a partir de la suma de 'stays_in_weekend_nights' y 'stays_in_week_nights'."""
        if "stays_in_weekend_nights" in self.df.columns and "stays_in_week_nights" in self.df.columns:
            self.df["total_nights"] = self.df["stays_in_weekend_nights"] + self.df["stays_in_week_nights"]
            print("Columna 'total_nights' creada correctamente.")
        else:
            print("No se pudo crear 'total_nights': faltan columnas.")

    def drop_unused_columns(self):
        """Elimina las columnas que no se consideran útiles en el análisis final."""
        current_columns = set(self.df.columns)
        columns_to_keep = set(self.COLUMNS_TO_KEEP + ["total_nights"])
        columns_to_drop = list(current_columns - columns_to_keep)
        self.df = self.df.drop(columns=columns_to_drop, errors='ignore')
        print(f"Se eliminaron las columnas no usadas: {columns_to_drop}")

    def get_dataframe(self) -> pd.DataFrame:
        return self.df.copy()