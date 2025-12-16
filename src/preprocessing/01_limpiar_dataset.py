"""
01_limpiar_dataset.py
=====================
Script de preprocesamiento que limpia el dataset original.
Filtra pedidos con status 'Shipped' y productos Classic/Vintage Cars.

Entrada: data/sales_data_sample_raw.csv (original sin filtrar)
Salida:  data/sales_data_sample_clean.csv (limpio y filtrado)
"""
import os
import pandas as pd


# Rutas relativas desde la raíz del proyecto
SCRIPT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..'))
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
RAW_PATH = os.path.join(DATA_DIR, 'sales_data_sample_raw.csv')
CLEAN_PATH = os.path.join(DATA_DIR, 'sales_data_sample_clean.csv')


def main():
    """Lee el CSV original, filtra por STATUS 'Shipped' y PRODUCTLINE 'Classic Cars' o 'Vintage Cars', y guarda el resultado."""
    print("="*60)
    print("LIMPIEZA DEL DATASET")
    print("="*60)
    
    try:
        df = pd.read_csv(RAW_PATH, encoding='latin-1')
        print(f"\nArchivo cargado: {RAW_PATH}")
        print(f"Registros originales: {len(df)}")
    except FileNotFoundError:
        raise SystemExit(f"Archivo no encontrado: {RAW_PATH}\n\nAsegurate de tener sales_data_sample_raw.csv en data/")

    # Filtrar filas con STATUS == 'Shipped'
    df_filtered = df[df['STATUS'] == 'Shipped']
    print(f"Despues de filtrar STATUS='Shipped': {len(df_filtered)}")

    # Conservar solo Classic Cars o Vintage Cars
    allowed = ['Classic Cars', 'Vintage Cars']
    df_filtered = df_filtered[df_filtered['PRODUCTLINE'].isin(allowed)]
    print(f"Despues de filtrar PRODUCTLINE (Classic/Vintage): {len(df_filtered)}")

    # Guardar el dataset limpio
    df_filtered.to_csv(CLEAN_PATH, index=False)
    
    print(f"\nDataset limpio guardado en: {CLEAN_PATH}")
    print(f"Total de registros finales: {len(df_filtered)}")
    print("="*60)


if __name__ == '__main__':
    main()