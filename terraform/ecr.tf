# Create the ECR repository to store the Python ingestion Docker image
resource "aws_ecr_repository" "ingestion_repo" {
  name                 = "insurance-ingestion"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}