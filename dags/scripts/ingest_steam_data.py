import os
import json
import requests
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv
from datetime import datetime, timezone

# Cargar credenciales
load_dotenv()
connect_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
container_name = os.getenv("AZURE_CONTAINER_NAME")
api_key = os.getenv("STEAM_API_KEY")

# Inicializar el cliente de conexión
blob_service_client = BlobServiceClient.from_connection_string(connect_str)
container_client = blob_service_client.get_container_client(container_name)

def fetch_steam_data():

    url = f"https://api.steampowered.com/ISteamChartsService/GetGamesByConcurrentPlayers/v1/?key={api_key}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        print("Extracción de STEAM API exitosa")
    else:
        data = None
        print(f"Error: {response.status_code}")

    return data

def generate_utc_path(): # Saco la fecha y hora para crear carpetas en el blob storage

    now = datetime.now(timezone.utc)
    utc_path = now.strftime("%Y/%m/%d/%H/")

    return utc_path


def upload_to_blob(data, utc_path):

    if data is None:
        print("No hay datos para subir.")
        return
    
    json_data = json.dumps(data)
    file_path = f"top_games/{utc_path}raw_steam_data.json"
    blob_client = container_client.get_blob_client(file_path)

    try:
        blob_client.upload_blob(json_data, overwrite=True)
        print(f"Archivo subido exitosamente a: {blob_client.url}")
    except Exception as e:
        print(f"Error al subir el archivo: {e}")

if __name__ == "__main__":
    print("Iniciando proceso de ingesta de Steam...")
    
    # 1. Ejecutar la extracción (Función 1)
    datos_extraidos = fetch_steam_data()
    
    # Validamos que datos_extraidos no esté vacío o sea None antes de seguir
    if datos_extraidos:
        # 2. Generar la ruta particionada (Función 2)
        ruta_particionada = generate_utc_path()
        
        # 3. Subir al Data Lake (Función 3)
        upload_to_blob(datos_extraidos, ruta_particionada)
        
        print("Proceso completado.")
    else:
        print("Proceso detenido: No se obtuvieron datos de la API.")

# Revisar la carga
"""
az storage blob list \
  --container-name steam-raw-data \
  --connection-string $CONN_STRING \
  --query "[].[name]" \
  --output tsv
"""