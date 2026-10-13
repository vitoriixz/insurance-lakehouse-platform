import os
from dotenv import load_dotenv
from groq import Groq
from databricks import sql

# 1. Carrega as credenciais
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

# Cliente inicializado com a Groq
client = Groq(api_key=api_key)

# 2. Schema da Tabela Silver
schema_silver = """
Tabela: silver_claims
Colunas:
- claim_id (INT): Identificador único do sinistro
- amount (DOUBLE): Valor financeiro do sinistro
- weather_condition (STRING): Condição climática no momento do incidente
"""

# 3. System Instruction
instrucao_sistema = f"""
Você é um Arquiteto de Dados especialista em Databricks e Spark SQL.
Sua única função é receber uma pergunta de negócio e retornar EXATAMENTE o código SQL necessário para respondê-la.
REGRA CRÍTICA: Retorne APENAS a query SQL pura. Não adicione explicações, saudações, ou blocos de formatação markdown (como ```sql).

Use estritamente o seguinte schema para basear suas queries:
{schema_silver}
"""

print("Iniciando o Agente Data Lakehouse (Conexão Live AWS Databricks)...\n")

try:
    # =====================================================================
    # FASE 1: O CÉREBRO (Text-to-SQL via Groq/Llama 3)
    # =====================================================================
    
    pergunta_usuario = os.getenv("USER_PROMPT", "Qual é o valor total financeiro (amount) de todos os sinistros registrados na base?")
    
    print(f"[Diretoria]: '{pergunta_usuario}'")

    response_sql = client.chat.completions.create(
        model="llama-3.1-70b-versatile",
        messages=[
            {"role": "system", "content": instrucao_sistema},
            {"role": "user", "content": pergunta_usuario}
        ],
        temperature=0.1
    )

    query_gerada = response_sql.choices[0].message.content.strip()
    
    # Prevenção extra de segurança caso o modelo retorne crases teimosas
    query_gerada = query_gerada.replace("```sql", "").replace("```", "").strip()
    
    print(f"\n[Agente - Motor SQL]:\n{query_gerada}")

    # =====================================================================
    # FASE 2: O MÚSCULO (Execução Live no Databricks)
    # =====================================================================
    print("\n[Sistema]: Estabelecendo túnel JDBC com o Databricks SQL Warehouse...")

    with sql.connect(
        server_hostname=db_host,
        http_path=db_path,
        access_token=db_token
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(query_gerada)
            result = cursor.fetchone()
            resultado_banco = result[0] if result and result[0] is not None else 0.0

    print(f"[Databricks - Camada Silver]: Resultado real extraído -> {resultado_banco}")

    # =====================================================================
    # FASE 3: A SÍNTESE (Resposta Executiva)
    # =====================================================================
    print("\n[Agente - Resposta Executiva]:")
    
    prompt_sintese = f"""
    A pergunta de negócio do diretor foi: {pergunta_usuario}
    A nossa query SQL no Databricks retornou exatamente este valor bruto: {resultado_banco}

    Aja como um Arquiteto de Soluções respondendo de forma educada, direta e profissional ao diretor.
    Formate o valor monetário em dólares. Não explique a query SQL, foque no insight de negócio.
    """

    try:
        response_final = client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[
                {"role": "system", "content": "Você é um Arquiteto de Soluções C-Level."},
                {"role": "user", "content": prompt_sintese}
            ],
            temperature=0.4
        )
        print(response_final.choices[0].message.content)
        
    except Exception as e_sintese:
        # Fallback (Degradação Graciosa)
        print("Prezado Diretor,")
        print(f"A nossa análise direta na base de dados retornou o valor de **US$ {resultado_banco}**.")
        print(f"\n*(Nota do Sistema: A formatação executiva via IA está temporariamente indisponível devido a instabilidade, mas o dado bruto acima é preciso e foi extraído do Databricks com sucesso em tempo real).*")
        print("\nAtenciosamente,")
        print("**Equipe de Arquitetura de Soluções**")

except Exception as e:
    print(f"\n[ERRO DE INFRAESTRUTURA] Falha crítica na extração dos dados.")
    print(f"Detalhe técnico: {e}")

# TESTE DEPLOY ACTIONS