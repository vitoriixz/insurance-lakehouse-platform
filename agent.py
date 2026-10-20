import os
import re
import sys
from dotenv import load_dotenv
from groq import Groq
from databricks import sql

load_dotenv(override=True)
api_key = os.getenv("GROQ_API_KEY")
db_host = os.getenv("DATABRICKS_SERVER_HOSTNAME")
db_path = os.getenv("DATABRICKS_HTTP_PATH")
db_token = os.getenv("DATABRICKS_TOKEN")

print(f"[SecOps Debug]: Usando o token -> {db_token[:8]}...")

if not api_key:
    raise ValueError("Chave GROQ_API_KEY não encontrada no ambiente.")
if not all([db_host, db_path, db_token]):
    raise ValueError("Credenciais do Databricks ausentes no ambiente.")

client = Groq(api_key=api_key)

def selecionar_modelo_ativo(groq_client):
    """
    Seleciona o modelo ativo com base no catálogo real retornado pela API da Groq.
    """
    preferencia = [
        "openai/gpt-oss-120b",
        "qwen/qwen3.8-27b",
        "openai/gpt-oss-20b"
    ]
    try:
        modelos_online = [m.id for m in groq_client.models.list().data]
        for mod in preferencia:
            if mod in modelos_online:
                print(f"[SecOps Debug]: Modelo validado e ativo na Groq -> {mod}")
                return mod
        
        bloqueados = ["guard", "safeguard", "whisper", "orpheus", "tts", "vision"]
        for mod in modelos_online:
            if not any(b in mod.lower() for b in bloqueados):
                print(f"[SecOps Debug]: Usando modelo alternativo detectado -> {mod}")
                return mod
    except Exception as e:
        print(f"[Aviso]: Não foi possível listar catálogo ({e}). Usando fallback padrão.")
    
    return "openai/gpt-oss-120b"

schema_silver = """
Tabela: workspace.default.silver_claims
Colunas:
- claim_id (INT): Identificador único do sinistro
- amount (DOUBLE): Valor financeiro do sinistro
- weather_condition (STRING): Condição climática no momento do incidente (Ex: 'Rain', 'Clear', 'Snow')
- claim_date (DATE): Data do registro do sinistro
- city (STRING): Cidade de ocorrência do sinistro
- claim_type (STRING): Tipo do seguro acionado
- status (STRING): Status atual do processo (Ex: 'Approved', 'Pending', 'Rejected')
"""

instrucao_sistema = f"""
Você é um Arquiteto de Dados especialista em Databricks e Spark SQL.
Sua única função é receber uma pergunta de negócio e retornar EXATAMENTE o código SQL necessário para respondê-la.
REGRA CRÍTICA 1: Retorne APENAS a query SQL pura. Não adicione explicações, saudações, raciocínio ou blocos de formatação markdown (como ```sql).
REGRA CRÍTICA 2: Ao filtrar colunas de texto (STRING), use sempre ILIKE (case-insensitive) em vez de '=' para evitar falhas de maiúsculas/minúsculas. Não use COALESCE para forçar zero em agregações vazias, deixe o banco retornar NULL caso o filtro não encontre linhas.

Use estritamente o seguinte schema para basear suas queries:
{schema_silver}
"""

print("Iniciando o Agente Data Lakehouse (Conexão Live AWS Databricks)...\n")

try:
    modelo_ativo = selecionar_modelo_ativo(client)

    if len(sys.argv) > 1:
        pergunta_usuario = sys.argv[1]
    else:
        pergunta_usuario = "Qual é o valor total financeiro (amount) de todos os sinistros registrados na base?"
    
    print(f"[Diretoria]: '{pergunta_usuario}'")

    response_sql = client.chat.completions.create(
        model=modelo_ativo,
        messages=[
            {"role": "system", "content": instrucao_sistema},
            {"role": "user", "content": pergunta_usuario}
        ],
        temperature=0.1
    )

    query_gerada = response_sql.choices[0].message.content.strip()
    query_gerada = re.sub(r"<think>.*?</think>", "", query_gerada, flags=re.DOTALL).strip()
    query_gerada = query_gerada.replace("```sql", "").replace("```", "").strip()
    
    print(f"\n[Agente - Motor SQL]:\n{query_gerada}")

    print("\n[Sistema]: Estabelecendo túnel JDBC com o Databricks SQL Warehouse...")

    with sql.connect(
        server_hostname=db_host,
        http_path=db_path,
        access_token=db_token
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(query_gerada)
            rows = cursor.fetchall()


    sem_dados = (
        not rows 
        or len(rows) == 0 
        or all(val is None for val in rows[0])
    )

    if sem_dados:
        print("[Databricks - Camada Silver]: ALERTA -> A query executou com sucesso, mas retornou NULL / 0 registros compatíveis.")
        print("\n[Agente - Resposta Executiva]:")
        print(
            "Prezado Diretor,\n\n"
            "A consulta foi executada na camada Silver do Databricks, porém **nenhum registro foi encontrado** "
            "para os critérios informados na sua pergunta (o banco de dados retornou vazio/nulo).\n\n"
            "Recomendo verificar se o termo buscado consta na base de dados ou solicitar uma listagem das categorias disponíveis."
        )
    else:
        # Extrai o resultado real (suporta valor único ou múltiplas linhas/colunas)
        resultado_banco = rows[0][0] if len(rows) == 1 and len(rows[0]) == 1 else rows
        print(f"[Databricks - Camada Silver]: Resultado real extraído -> {resultado_banco}")

        # =====================================================================
        # FASE 3: A SÍNTESE (Resposta Executiva apenas com dados validados)
        # =====================================================================
        print("\n[Agente - Resposta Executiva]:")
        
        prompt_sintese = f"""
        A pergunta de negócio do diretor foi: {pergunta_usuario}
        A nossa query SQL no Databricks retornou exatamente este resultado validado: {resultado_banco}

        Aja como um Arquiteto de Soluções respondendo de forma educada, direta e profissional ao diretor.
        Formate valores monetários em dólares quando aplicável. Não explique a query SQL, foque no insight de negócio.
        """

        try:
            response_final = client.chat.completions.create(
                model=modelo_ativo,
                messages=[
                    {"role": "system", "content": "Você é um Arquiteto de Soluções C-Level. Responda de forma direta, sem tags de raciocínio."},
                    {"role": "user", "content": prompt_sintese}
                ],
                temperature=0.4
            )
            texto_final = response_final.choices[0].message.content.strip()
            texto_final = re.sub(r"<think>.*?</think>", "", texto_final, flags=re.DOTALL).strip()
            print(texto_final)
            
        except Exception as e_sintese:
            print("Prezado Diretor,")
            print(f"A nossa análise direta na base de dados retornou o resultado: **{resultado_banco}**.")
            print("\nAtenciosamente,")
            print("**Equipe de Arquitetura de Soluções**")

except Exception as e:
    print(f"\n[ERRO DE INFRAESTRUTURA] Falha crítica na extração dos dados.")
    print(f"Detalhe técnico: {e}")