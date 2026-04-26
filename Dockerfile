# Usamos la imagen que ya descargamos como base
FROM apache/airflow:2.9.1

# Instalamos las librerías necesarias
# Usamos pip aquí porque es lo que viene dentro de la imagen de Airflow
RUN pip install --no-cache-dir \
    pandas \
    azure-storage-blob \
    requests \
    python-dotenv