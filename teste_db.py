import os
from dotenv import load_dotenv
from databricks import sql

# Força a leitura do .env apagando o cache
load_dotenv(override=True)

host = os.getenv("DATABRICKS_SERVER_HOSTNAME")
path = os.getenv("DATABRICKS_HTTP_PATH")
token = os.getenv("DATABRICKS_TOKEN")

print("--- AUDITORIA DE CREDENCIAIS ---")
print(f"Host  : {host}")
print(f"Path  : {path}")
# Aqui revelamos se há espaços ou aspas embutidas e o tamanho real lido
print(f"Token : {token[:8]}...{token[-4:]} (Tamanho lido: {len(token)})")
print("--------------------------------\n")

print("Iniciando tentativa de conexão pura (Sem IA)...")
try:
    with sql.connect(
        server_hostname=host,
        http_path=path,
        access_token=token
    ) as connection:
        print("✅ SUCESSO ABSOLUTO: O Databricks aceitou a conexão!")
except Exception as e:
    print(f"❌ FALHA NA CONEXÃO: {e}")