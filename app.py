import boto3
import datetime
import os

print("Starting Insurance Data Ingestion (BOM API & Faker)...")
print("Generating claims batch and fetching weather data from government API...")

# Simulando o dado gerado (Onde entraria o seu Faker/Requests real)
csv_data = "claim_id,amount,weather_condition\n1,500.00,rain\n2,1200.00,clear"

# Conecta no S3 usando as credenciais injetadas pela Task Role que configuramos no Terraform
s3 = boto3.client('s3', region_name='us-east-1')

# ATENÇÃO: Substitua pelo nome EXATO do bucket que você criou no primeiro dia!
bucket_name = "insurance-lakehouse-landing-zone-vitor-dev" 
file_name = f"claims_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.csv"

try:
    print(f"Uploading {file_name} to S3 bucket {bucket_name}...")
    s3.put_object(Bucket=bucket_name, Key=file_name, Body=csv_data)
    print("Upload successful. Task completed.")
except Exception as e:
    print(f"FATAL ERROR: Failed to upload to S3. Details: {e}")
    raise