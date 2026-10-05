resource "aws_iam_user" "databricks_user" {
  name = "databricks-lakehouse-reader"
  path = "/service-accounts/"
}

resource "aws_iam_access_key" "databricks_keys" {
  user = aws_iam_user.databricks_user.name
}

resource "aws_iam_policy" "databricks_s3_policy" {
  name        = "DatabricksS3ReadOnlyPolicy"
  description = "Permite apenas leitura na camada Bronze do Lakehouse"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::insurance-lakehouse-landing-zone-vitor-dev",
          "arn:aws:s3:::insurance-lakehouse-landing-zone-vitor-dev/*"
        ]
      }
    ]
  })
}

resource "aws_iam_user_policy_attachment" "databricks_attach" {
  user       = aws_iam_user.databricks_user.name
  policy_arn = aws_iam_policy.databricks_s3_policy.arn
}

output "databricks_access_key_id" {
  description = "Access Key para configurar no Databricks"
  value       = aws_iam_access_key.databricks_keys.id
}

output "databricks_secret_access_key" {
  description = "Secret Key para configurar no Databricks"
  value       = aws_iam_access_key.databricks_keys.secret
  sensitive   = true 
}