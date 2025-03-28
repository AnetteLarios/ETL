import pandas as pd
import os
import psycopg2
import io
from sqlalchemy import create_engine

class FileManager:
    def __init__(self):
        pass

    def get_db_connection_params(self):
        print("\n=== Parámetros de conexión PostgreSQL ===")
        return {
            'host': input("Host (ej: localhost): "),
            'port': input("Puerto (ej: 5432): "),
            'database': input("Nombre de la base de datos: "),
            'user': input("Usuario: "),
            'password': input("Contraseña: ")
        }
    
    def create_table_from_df(self, cursor, table_name, df):
        """
        Crea la tabla en PostgreSQL de forma dinámica a partir de los tipos de datos del DataFrame.
        Se utiliza un mapeo simple entre los tipos de pandas y los tipos en PostgreSQL.
        """
        # Mapeo entre dtypes de pandas y tipos de PostgreSQL
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
            # Se cita el nombre de la columna para evitar conflictos con palabras reservadas.
            columns_def.append(f'"{col}" {pg_type}')
        columns_sql = ", ".join(columns_def)
        ddl = f'CREATE TABLE IF NOT EXISTS "{table_name}" ({columns_sql});'
        cursor.execute(ddl)
        print(f"Tabla '{table_name}' creada (si no existía).")
        
    def save_to_postgresql_copy(self, df, params):
        """
        Inserta los datos del DataFrame en PostgreSQL usando psycopg2 y el método COPY.
        Además, crea la tabla en la base de datos a partir de la estructura del DataFrame.
        """
        try:
            table_name = input("\nNombre de la tabla donde guardar los datos: ")
            drop_table = input("¿Deseas reemplazar la tabla si ya existe? (s/n): ")

            # Crear cadena de conexión para psycopg2 (sin usar SQLAlchemy)
            conn_str = (
                f"dbname='{params['database']}' user='{params['user']}' "
                f"password='{params['password']}' host='{params['host']}' port='{params['port']}'"
            )
            conn = psycopg2.connect(conn_str)
            cursor = conn.cursor()

            if drop_table.lower() == 's':
                cursor.execute(f'DROP TABLE IF EXISTS "{table_name}";')
                conn.commit()
                print(f"Tabla '{table_name}' eliminada.")
            
            # Crear la tabla según la estructura del DataFrame
            self.create_table_from_df(cursor, table_name, df)
            conn.commit()

            # Convertir el DataFrame a CSV en memoria utilizando BytesIO.
            # Luego, decodificarlo explicitamente para asegurar que usamos UTF-8 y reemplacemos errores.
            import io
            csv_buffer = io.BytesIO()
            # Escribir en el buffer como bytes, usando UTF-8
            df.to_csv(csv_buffer, sep='\t', index=False, header=False, encoding='utf-8')
            csv_buffer.seek(0)
            # Leer el contenido de bytes y decodificarlo, reemplazando errores en el proceso
            csv_data = csv_buffer.read().decode('utf-8', errors='replace')
            # Crear un StringIO a partir del CSV ya decodificado
            csv_str_io = io.StringIO(csv_data)

            # Insertar datos usando COPY (se asume que la tabla y el orden de columnas coinciden)
            cursor.copy_from(csv_str_io, table_name, sep='\t')
            conn.commit()

            cursor.close()
            conn.close()

            print(f"\n✅ Datos guardados exitosamente en la tabla {table_name}")

        except Exception as e:
            print(f"\n❌ Error al guardar en PostgreSQL usando COPY: {str(e)}")
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
            db_params = self.get_db_connection_params()
            # Llama al método optimizado que crea tabla e inserta los datos
            self.save_to_postgresql_copy(df, db_params)
        else:
            raise ValueError("Formato no soportado para guardar.")