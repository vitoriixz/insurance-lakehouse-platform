import boto3
import datetime
import random
from faker import Faker

print("Starting Insurance Data Ingestion (BOM API & Faker)...")
print("Generating multidimensional claims batch (Temporal, Geographic, Status)...")

# Inicializa o Faker com a localização da Austrália (detalhe que ganha pontos na entrevista)
fake = Faker('en_AU')

# 1. Cabeçalho enriquecido
csv_header = "claim_id,amount,weather_condition,claim_date,city,claim_type,status\n"
csv_rows = []

# Dicionários de dimensões de negócio
condicoes = ['rain', 'clear', 'snow', 'storm', 'fog']
cidades = ['Sydney', 'Melbourne', 'Brisbane', 'Adelaide', 'Perth', 'Gold Coast']
tipos_sinistro = ['Collision', 'Property Damage', 'Theft', 'Water Damage']
status_lista = ['Approved', 'Pending', 'Rejected']

# 2. Geramos 150 linhas de sinistros com riqueza de dados
for _ in range(150):
    claim_id = fake.unique.random_int(min=10000, max=99999)
    amount = round(random.uniform(500.0, 25000.0), 2)
    weather = random.choice(condicoes)
    claim_date = fake.date_between(start_date='-2y', end_date='today').strftime('%Y-%m-%d')
    city = random.choice(cidades)
    claim_type = random.choice(tipos_sinistro)
    
    # Lógica de negócio falsa (peso maior para aprovados)
    status = random.choices(status_lista, weights=[60, 30, 10], k=1)[0]
    
    csv_rows.append(f"{claim_id},{amount},{weather},{claim_date},{city},{claim_type},{status}")

csv_data = csv_header + "\n".join(csv_rows)

# 3. Conecta no S3 e faz o upload
s3 = boto3.client('s3', region_name='us-east-1')
bucket_name = "insurance-lakehouse-landing-zone-vitor-dev" 
file_name = f"claims_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.csv"

# CORREÇÃO: Adiciona o prefixo 'landing/' ao caminho do arquivo
s3_key = f"landing/{file_name}"

try:
    print(f"Uploading {file_name} to S3 bucket {bucket_name}...")
    s3.put_object(Bucket=bucket_name, Key=s3_key, Body=csv_data)
    print("Upload successful. Task completed.")
except Exception as e:
    print(f"FATAL ERROR: Failed to upload to S3. Details: {e}")
    raise

#Teste Esteira