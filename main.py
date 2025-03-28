import sys
import os
from file_manager import FileManager
from data_cleaner import DataCleaner
from data_analysis import (
    CancellationPredictor,
    StayLengthEstimator,
    CustomerSegmentation,
    TemporalAnalysis
)

def main():
    print("=== Bienvenido al sistema de limpieza y análisis de datos de Hotel Bookings ===")
    fm = FileManager()
    while True:
        try:
            file_path = input("\nIngrese la ruta del archivo que desea limpiar (CSV, Excel o JSON) o 'salir' para terminar: ")
            if file_path.lower() == 'salir':
                sys.exit(0)
            
            # 1. Cargar datos sin limpiar
            df = fm.load_data(file_path)
            print(f"Datos cargados exitosamente desde: {file_path}")
            print("Tamaño del DataFrame:", df.shape)
            
            # 2. Limpieza de datos
            print("\n=== LIMPIEZA DE DATOS ===")
            cleaner = DataCleaner(df)
            cleaner.drop_duplicates()
            cleaner.standardize_dates()
            cleaner.fill_missing_values()
            cleaner.advanced_imputation_knn()
            # Es importante crear la nueva columna antes de validar sus valores.
            cleaner.create_new_columns()
            cleaner.validate_numeric_columns()
            cleaner.drop_missing_targets()
            cleaner.drop_unused_columns()
            df_clean = cleaner.get_dataframe()
            
            print("\nPrimeras 5 filas del DataFrame LIMPIO:")
            print(df_clean.head())
            
            # 3. Guardar el archivo limpio
            original_dir = os.path.dirname(file_path)
            base_name = os.path.basename(file_path)
            base_no_ext, _ = os.path.splitext(base_name)
            print("\nSeleccione el formato para guardar los datos LIMPIOS:")
            print("1. CSV")
            print("2. Excel")
            print("3. JSON")
            print("4. PostgreSQL")
            format_choice = input("Seleccione una opción (1-4): ")

            if format_choice == '1':
                extension = '.csv'
            elif format_choice == '2':
                extension = '.xlsx'
            elif format_choice == '3':
                extension = '.json'
            elif format_choice == '4':
                extension = '.db'  # Identificador para PostgreSQL
                output_filename = "postgresql"
            else:
                print("Opción inválida. No se guardarán los datos limpios.")
                continue

            if format_choice != '4':
                output_filename = base_no_ext + "_limpio" + extension
                new_file_path = os.path.join(original_dir, output_filename)
                fm.save_data(df_clean, new_file_path)
                print(f"Datos limpios guardados en: {new_file_path}")
            else:
                fm.save_data(df_clean, "postgresql")
                new_file_path = file_path  # Se mantiene la referencia para continuar

            # 4. (Opcional) Recargar el archivo limpio para análisis
            if format_choice != '4':
                df_clean = fm.load_data(new_file_path)
                print(f"\nLos datos LIMPIOS se han recargado desde: {new_file_path}")
                print("Tamaño del DataFrame limpio:", df_clean.shape)

            # 5. Menú de análisis sobre el archivo limpio
            while True:
                print("\n=== Menú de acciones con los datos LIMPIOS ===")
                print("1. Análisis de Cancelaciones ('is_canceled')")
                print("2. Estimación de la Duración de Estancia ('total_nights')")
                print("3. Segmentación de Clientes (K-Means)")
                print("4. Análisis de Temporalidad de la Demanda (por mes/año)")
                print("5. Finalizar / cargar otro archivo")
                action_choice = input("Seleccione una opción (1-5): ")
                if action_choice == '1':
                    print("\n=== Análisis de Cancelaciones ===")
                    canc_predictor = CancellationPredictor()
                    canc_predictor.train_model(df_clean)
                elif action_choice == '2':
                    print("\n=== Estimación de la Duración de Estancia ===")
                    stay_estimator = StayLengthEstimator()
                    stay_estimator.train_model(df_clean)
                elif action_choice == '3':
                    print("\n=== Segmentación de Clientes (K-Means) ===")
                    seg = CustomerSegmentation(n_clusters=3)
                    clustered_df = seg.segment(df_clean)
                    print("Vista rápida de clientes segmentados (primeras 5 filas):")
                    print(clustered_df[['lead_time', 'adr', 'total_nights', 'cluster']].head())
                elif action_choice == '4':
                    print("\n=== Análisis de la Temporalidad de la Demanda ===")
                    temporal_analyzer = TemporalAnalysis()
                    demand_by_month = temporal_analyzer.monthly_demand(df_clean)
                    plot_choice = input("¿Desea ver el gráfico de demanda mensual? (s/n): ")
                    if plot_choice.lower() == 's':
                        temporal_analyzer.plot_monthly_demand(demand_by_month)
                elif action_choice == '5':
                    print("Regresando al menú principal...")
                    break
                else:
                    print("Opción no válida. Intente de nuevo.")

        except Exception as e:
            print(f"\nOcurrió un error: {e}")
            print("Reintentando...\n")

if __name__ == "__main__":
    main()