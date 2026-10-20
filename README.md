# Insurance Lakehouse Platform
# Serverless AI Data Lakehouse Agent

An end-to-end, serverless AI architecture that translates executive natural language queries into executable SQL, processes them against a Databricks Lakehouse, and delivers real-time business insights.

Built entirely on AWS, this project demonstrates a modern approach to AI-driven data analytics, eliminating the need for permanent compute infrastructure while maintaining high security and CI/CD best practices.

## 🏗️ Architecture & Workflow

This application operates asynchronously using a completely serverless footprint:

1. **Frontend (Presentation):** A static HTML/JS web portal captures the user's question and sends an authenticated POST request.
2. **AWS Lambda (Orchestrator):** A Lambda Function URL receives the payload, validates a custom security token, and triggers a containerized task via Boto3.
3. **AWS ECS Fargate (Ephemeral Compute):** A Docker container spins up on-demand. The user's prompt is injected directly into the container's execution environment using ECS `overrides`.
4. **Groq LLM (Intelligence):** The Python agent calls the Groq API (`gpt-oss-120b`) to translate the natural language prompt into a highly optimized Databricks SQL query.
5. **Databricks SQL Warehouse (Data Engine):** The agent establishes a JDBC tunnel to the AWS Databricks workspace, querying the `silver_claims` table and retrieving the exact numerical result.
6. **CloudWatch (Log Aggregation):** As the Fargate task runs, logs are streamed instantly (`PYTHONUNBUFFERED=1`). The Lambda orchestrator polls these logs, separates technical traces from the final executive summary, and delivers the payload back to the browser.

## 🚀 Tech Stack

* **Cloud Provider:** AWS (Lambda, ECS Fargate, ECR, CloudWatch, Secrets Manager, IAM)
* **Data Platform:** Databricks (Unity Catalog, SQL Warehouses, Silver Layer)
* **AI / LLM:** Groq API (`gpt-oss-120b` / Llama 3)
* **Backend:** Python 3.10 (Boto3, Databricks SQL Connector)
* **Frontend:** HTML5, JavaScript (Vanilla), TailwindCSS
* **DevSecOps:** GitHub Actions, Docker

## 🔒 Security & DevSecOps

Security was built into the foundation of this architecture to ensure production readiness:

* **No Hardcoded Secrets:** All sensitive credentials (Databricks tokens, Groq API keys) are securely fetched at runtime from **AWS Secrets Manager**.
* **API Protection:** The AWS Lambda Function URL is protected against unauthorized access via custom header validation (`x-token-diretoria`), managed via AWS Environment Variables.
* **Strict CORS Policies:** Configured at the AWS Lambda level to prevent cross-origin exploits.
* **Least Privilege IAM:** Execution roles are strictly scoped, allowing the Lambda only to run specific ECS tasks and read specific CloudWatch log streams.
* **Automated CI/CD:** GitHub Actions pipelines (`deploy-agent.yml`) automatically perform cross-architecture Docker builds and push new image tags directly to AWS ECR upon repository updates.

## 💻 Frontend Interface

The user interface was designed for C-Level executives, prioritizing clarity:
* **Executive Summary:** The AI's final business analysis is presented cleanly in the main chat bubble.
* **Technical Logs:** Database connections, query execution times, and LLM reasoning are hidden by default inside a collapsible "Developer / SecOps" accordion for debugging without cluttering the business view.

---

### Author
**Vitor Miranda**  
*Multicloud Solutions Engineer*  
