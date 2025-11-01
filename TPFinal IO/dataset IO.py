import os
import pandas as pd


# Ruta al CSV (misma carpeta del script)
BASE_DIR = os.path.dirname(__file__)
CSV_PATH = os.path.join(BASE_DIR, 'sales_data_sample_clean.csv')


def main():
	"""Lee el CSV, filtra por STATUS 'Shipped' y PRODUCTLINE 'Classic Cars' o 'Vintage Cars', y guarda el resultado."""
	try:
		df = pd.read_csv(CSV_PATH)
	except FileNotFoundError:
		raise SystemExit(f"Archivo no encontrado: {CSV_PATH}")

	# Filtrar filas con STATUS == 'Shipped'
	df = df[df['STATUS'] == 'Shipped']

	# Conservar solo Classic Cars o Vintage Cars
	allowed = ['Classic Cars', 'Vintage Cars']
	df = df[df['PRODUCTLINE'].isin(allowed)]

	# Guardar el dataset limpio en el mismo archivo
	df.to_csv(CSV_PATH, index=False)


if __name__ == '__main__':
	main()