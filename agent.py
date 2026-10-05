import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai import errors

# 1. Carrega as credenciais
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("Chave GEMINI_API_KEY não encontrada no arquivo .env.")

client = genai.Client(api_key=api_key)

# 2. O Contexto do Agente: Mapeamento da Tabela Silver
schema_silver = """
Tabela: silver_claims
Engine: Databricks Spark SQL (Delta Lake)
Colunas:
- claim_id (STRING): Identificador único do sinistro
- policy_id (STRING): Identificador da apólice
- incident_date (DATE): Data do acidente
- incident_type (STRING): Tipo de sinistro (Ex: 'Colisão', 'Roubo', 'Climático')
- claim_amount (DOUBLE): Valor acionado em dólares
- status (STRING): Status atual ('Aprovado', 'Pendente', 'Negado')
"""

# 3. System Instruction: A regra de negócio rígida do Agente
instrucao_sistema = f"""
Você é um Arquiteto de Dados especialista em Databricks e Spark SQL.
Sua única função é receber uma pergunta de negócio e retornar EXATAMENTE o código SQL necessário para respondê-la.
REGRA CRÍTICA: Retorne APENAS a query SQL pura. Não adicione explicações, saudações, ou blocos de formatação markdown (como ```sql).

Use estritamente o seguinte schema para basear suas queries:
{schema_silver}
"""

print("Iniciando o Agente Data Lakehouse (PoC Arquitetural)...\n")

try:
    # =====================================================================
    # FASE 1: O CÉREBRO (Text-to-SQL)
    # =====================================================================
    chat_sql = client.chats.create(
        model='gemini-3.8-flash',
        config=types.GenerateContentConfig(
            system_instruction=instrucao_sistema,
            temperature=0.1 
        )
    )

    pergunta_usuario = "Qual é o valor total financeiro de todos os sinistros que já foram aprovados e que são do tipo Colisão?"
    print(f"[Diretoria]: '{pergunta_usuario}'")
    
    response_sql = chat_sql.send_message(pergunta_usuario)
    query_gerada = response_sql.text.strip()
    print(f"\n[Agente - Motor SQL]:\n{query_gerada}")

    # =====================================================================
    # FASE 2: O MÚSCULO (Motor Databricks)
    # =====================================================================
    print("\n[Sistema]: Roteando query via JDBC para o cluster Databricks...")
    
    # NOTA ARQUITETURAL: Em produção (AWS/Databricks Enterprise), usaríamos 
    # a biblioteca databricks-sql-connector e o comando cursor.execute(query_gerada).
    # Como o Databricks Community Edition (Free Tier) oculta o HTTP Path e Server Hostname,
    # realizamos um mock do retorno do banco para validar a orquestração do Agente.
    resultado_banco = 158500.00 
    
    print(f"[Databricks - Camada Silver]: Resultado bruto retornado -> {resultado_banco}")

    # =====================================================================
    # FASE 3: A SÍNTESE (Resposta Executiva)
    # =====================================================================
    chat_resposta = client.chats.create(
        model='gemini-3.8-flash',
        config=types.GenerateContentConfig(temperature=0.4) # Temperatura levemente maior para linguagem natural
    )
    
    prompt_sintese = f"""
    A pergunta de negócio do diretor foi: {pergunta_usuario}
    A nossa query SQL no Databricks retornou exatamente este valor bruto: {resultado_banco}
    
    Aja como um Arquiteto de Soluções respondendo de forma educada, direta e profissional ao diretor.
    Formate o valor monetário em dólares. Não explique a query SQL, foque no insight de negócio.
    """
    
    response_final = chat_resposta.send_message(prompt_sintese)
    print(f"\n[Agente - Resposta Executiva]:\n{response_final.text}\n")

# =====================================================================
# TRATAMENTO DE ERROS (Enterprise Grade)
# =====================================================================
# Captura APENAS erros dos servidores da API (Ex: 503 Overloaded, 500 Internal Error)
except errors.ServerError as e:
    print(f"\n[ERRO DE INFRAESTRUTURA GOOGLE] O servidor falhou ou está sobrecarregado.")
    print(f"Código HTTP: {e.code} | Detalhe: {e.message}")

# Captura APENAS erros causados pelo nosso lado/código (Ex: 401 Sem permissão, 404 Modelo não existe)
except errors.ClientError as e:
    print(f"\n[ERRO NO CLIENTE] Nossa requisição foi negada pela API.")
    print(f"Código HTTP: {e.code} | Detalhe: {e.message}")

# O Catch-All agora só captura o que sobrar (Ex: falta de rede local no Mac, erro de memória)
except Exception as e:
    print(f"\n[ERRO DESCONHECIDO NO SISTEMA LOCAL] Falha na execução do Python.")
    print(f"Detalhe técnico: {e}")