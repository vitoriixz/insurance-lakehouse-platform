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

print(f"[SecOps Debug]: Using token -> {db_token[:8]}...")

if not api_key:
    raise ValueError("GROQ_API_KEY not found in environment.")
if not all([db_host, db_path, db_token]):
    raise ValueError("Databricks credentials missing in environment.")

client = Groq(api_key=api_key)

def select_active_model(groq_client):
    """
    Selects the active model based on the actual catalog returned by the Groq API.
    """
    preference = [
        "openai/gpt-oss-120b",
        "qwen/qwen3.8-27b",
        "openai/gpt-oss-20b"
    ]
    try:
        online_models = [m.id for m in groq_client.models.list().data]
        for mod in preference:
            if mod in online_models:
                print(f"[SecOps Debug]: Model validated and active in Groq -> {mod}")
                return mod
        
        blocked = ["guard", "safeguard", "whisper", "orpheus", "tts", "vision"]
        for mod in online_models:
            if not any(b in mod.lower() for b in blocked):
                print(f"[SecOps Debug]: Using detected alternative model -> {mod}")
                return mod
    except Exception as e:
        print(f"[Warning]: Could not list catalog ({e}). Using default fallback.")
    
    return "openai/gpt-oss-120b"

schema_silver = """
Table: workspace.default.silver_claims
Columns:
- claim_id (INT): Unique claim identifier
- amount (DOUBLE): Financial value of the claim
- weather_condition (STRING): Weather condition at the time of the incident (e.g., 'Rain', 'Clear', 'Snow')
- claim_date (DATE): Date the claim was registered
- city (STRING): City where the incident occurred
- claim_type (STRING): Type of insurance claimed
- status (STRING): Current process status (e.g., 'Approved', 'Pending', 'Rejected')
"""

system_instruction = f"""
You are a Data Architect specialized in Databricks and Spark SQL.
Your sole function is to receive a business question and return EXACTLY the SQL code needed to answer it.
CRITICAL RULE 1: Return ONLY the raw SQL query. Do not add explanations, greetings, reasoning, or markdown formatting blocks (like ```sql).
CRITICAL RULE 2: When filtering text columns (STRING), always use ILIKE (case-insensitive) instead of '=' to avoid case sensitivity failures. Do not use COALESCE to force zero in empty aggregations; let the database return NULL if the filter finds no rows.

Strictly use the following schema to base your queries on:
{schema_silver}
"""

print("Starting Data Lakehouse Agent (Live AWS Databricks Connection)...\n")

try:
    active_model = select_active_model(client)

    if len(sys.argv) > 1:
        user_prompt = sys.argv[1]
    else:
        user_prompt = "What is the total financial value (amount) of all claims registered in the database?"
    
    print(f"[Executive]: '{user_prompt}'")

    response_sql = client.chat.completions.create(
        model=active_model,
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.1
    )

    generated_query = response_sql.choices[0].message.content.strip()
    generated_query = re.sub(r"<think>.*?</think>", "", generated_query, flags=re.DOTALL).strip()
    generated_query = generated_query.replace("```sql", "").replace("```", "").strip()
    
    print(f"\n[Agent - SQL Engine]:\n{generated_query}")

    print("\n[System]: Establishing JDBC tunnel with Databricks SQL Warehouse...")

    with sql.connect(
        server_hostname=db_host,
        http_path=db_path,
        access_token=db_token
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(generated_query)
            rows = cursor.fetchall()

    no_data = (
        not rows 
        or len(rows) == 0 
        or all(val is None for val in rows[0])
    )

    if no_data:
        print("[Databricks - Silver Layer]: ALERT -> The query executed successfully, but returned NULL / 0 matching records.")
        print("\n[Agent - Executive Response]:")
        print(
            "Dear Executive,\n\n"
            "The query was executed in the Databricks Silver layer, but **no records were found** "
            "matching the criteria in your question (the database returned empty/null).\n\n"
            "I recommend checking if the searched term exists in the database or requesting a list of available categories."
        )
    else:
        # Extracts the actual result (supports single value or multiple rows/columns)
        db_result = rows[0][0] if len(rows) == 1 and len(rows[0]) == 1 else rows
        print(f"[Databricks - Silver Layer]: Actual result extracted -> {db_result}")

        # =====================================================================
        # PHASE 3: THE SYNTHESIS (Executive Response with validated data only)
        # =====================================================================
        print("\n[Agent - Executive Response]:")
        
        synthesis_prompt = f"""
        The executive's business question was: {user_prompt}
        Our SQL query in Databricks returned exactly this validated result: {db_result}

        Act as a Solutions Architect responding politely, directly, and professionally to the executive.
        Format monetary values in dollars when applicable. Do not explain the SQL query; focus on the business insight.
        Always sign the response as: Vitor Miranda - Solutions Engineer.
        """

        try:
            response_final = client.chat.completions.create(
                model=active_model,
                messages=[
                    {"role": "system", "content": "You are a C-Level Solutions Architect. Respond directly, without reasoning tags."},
                    {"role": "user", "content": synthesis_prompt}
                ],
                temperature=0.4
            )
            final_text = response_final.choices[0].message.content.strip()
            final_text = re.sub(r"<think>.*?</think>", "", final_text, flags=re.DOTALL).strip()
            print(final_text)
            
        except Exception as e_synthesis:
            print("Dear Executive,")
            print(f"Our direct analysis of the database returned the result: **{db_result}**.")
            print("\nSincerely,")
            print("**Solutions Architecture Team**")

except Exception as e:
    print(f"\n[INFRASTRUCTURE ERROR] Critical failure extracting data.")
    print(f"Technical detail: {e}")