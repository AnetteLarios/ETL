import pandas as pd
import numpy as np

class DataCleaner:
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()

    def drop_duplicates(self):
        self.df.drop_duplicates(inplace=True)

    def standardize_dates(self):
        if 'reservation_status_date' in self.df.columns:
            self.df['reservation_status_date'] = pd.to_datetime(
                self.df['reservation_status_date'], errors='coerce', dayfirst=False)
            
            # ❌ Eliminar filas con fechas inválidas
            self.df = self.df[self.df['reservation_status_date'].notna()]

    def fill_missing_values(self):
        if 'children' in self.df.columns:
            self.df['children'].fillna(0, inplace=True)

        if 'country' in self.df.columns:
            top_country = self.df['country'].mode()[0]
            self.df['country'].fillna(top_country, inplace=True)

        for col in ['agent', 'company']:
            if col in self.df.columns:
                self.df[col].fillna(-1, inplace=True)

        for col in ['lead_time', 'adr', 'is_canceled']:
            if col in self.df.columns:
                self.df[col].fillna(self.df[col].median(), inplace=True)

    def advanced_imputation_knn(self):
        # (Opcional) Imputación avanzada si se requiere
        pass

    def create_new_columns(self):
        if 'stays_in_weekend_nights' in self.df.columns and 'stays_in_week_nights' in self.df.columns:
            self.df['total_nights'] = self.df['stays_in_weekend_nights'] + self.df['stays_in_week_nights']

    def validate_numeric_columns(self):
        numeric_cols = self.df.select_dtypes(include=['float64', 'int64']).columns
        for col in numeric_cols:
            self.df[col] = pd.to_numeric(self.df[col], errors='coerce')

    def drop_missing_targets(self):
        if 'is_canceled' in self.df.columns:
            self.df = self.df[self.df['is_canceled'].notna()]

    def drop_unused_columns(self):
        to_drop = ['company', 'reservation_status']
        for col in to_drop:
            if col in self.df.columns:
                self.df.drop(columns=[col], inplace=True)

    def get_dataframe(self):
        return self.df
