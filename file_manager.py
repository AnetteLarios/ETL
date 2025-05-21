import pandas as pd
import os
import psycopg2
import io
from sqlalchemy import create_engine

class FileManager:
    def __init__(self):
        self.params = {
            'host': 'localhost',
            'port': '5432',
            'database': 'hotel_pob',
            'user': 'postgres',
            'password': 'root'
        }
        self.table_name = 'datos_limpios'

    def create_table_from_df(self, cursor, table_name, df):
        mapping = {
            'object': 'TEXT',
            'int64': 'BIGINT',
            'float64': 'DOUBLE PRECISION',
            'bool': 'BOOLEAN',
            'datetime64[ns]': 'TIMESTAMP'
        }
        columns_def = []
        for col in df.columns:
            dtype_str = str(df[col].dtype)
            pg_type = mapping.get(dtype_str, 'TEXT')
            columns_def.append(f'"{col}" {pg_type}')
        columns_sql = ", ".join(columns_def)
        ddl = f'CREATE TABLE IF NOT EXISTS "{table_name}" ({columns_sql});'
        cursor.execute(ddl)

    def save_to_postgresql_copy(self, df):
        try:
            conn_str = (
                f"dbname='{self.params['database']}' user='{self.params['user']}' "
                f"password='{self.params['password']}' host='{self.params['host']}' port='{self.params['port']}'"
            )
            conn = psycopg2.connect(conn_str)
            cursor = conn.cursor()

            cursor.execute(f'DROP TABLE IF EXISTS "{self.table_name}";')
            conn.commit()

            self.create_table_from_df(cursor, self.table_name, df)
            conn.commit()

            csv_buffer = io.BytesIO()
            df.to_csv(csv_buffer, sep='\t', index=False, header=False, encoding='utf-8')
            csv_buffer.seek(0)
            csv_data = csv_buffer.read().decode('utf-8', errors='replace')
            csv_str_io = io.StringIO(csv_data)

            cursor.copy_from(csv_str_io, self.table_name, sep='\t')
            conn.commit()

            cursor.close()
            conn.close()

            print(f"✅ Datos guardados en PostgreSQL: tabla '{self.table_name}'")

        except Exception as e:
            print(f"❌ Error al guardar en PostgreSQL: {str(e)}")
            raise

    def load_data(self, file_path: str) -> pd.DataFrame:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"El archivo {file_path} no existe.")
        extension = os.path.splitext(file_path)[1].lower()

        if extension == '.csv':
            return pd.read_csv(file_path, encoding='utf-8', na_values=['', ' ', 'NA', None])
        elif extension in ['.xlsx', '.xls']:
            return pd.read_excel(file_path)
        elif extension == '.json':
            return pd.read_json(file_path)
        else:
            raise ValueError("Formato no soportado. Use CSV, Excel o JSON.")

    def save_data(self, df: pd.DataFrame, output_path: str):
        extension = os.path.splitext(output_path)[1].lower()

        if extension == '.csv':
            df.to_csv(output_path, index=False)
        elif extension in ['.xlsx', '.xls']:
            df.to_excel(output_path, index=False)
        elif extension == '.json':
            df.to_json(output_path, orient='records')
        elif extension == '.db' or output_path.lower() == 'postgresql':
            self.save_to_postgresql_copy(df)
        else:
            raise ValueError("Formato no soportado para guardar.")
