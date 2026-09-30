# 1. Cria o Cluster ECS (Apenas uma fronteira lógica, custo $0)
resource "aws_ecs_cluster" "main" {
  name = "insurance-lakehouse-cluster"
}

# 2. Cria a Permissão (Role) para o ECS conseguir baixar sua imagem do ECR
resource "aws_iam_role" "ecs_execution_role" {
  name = "insurance_ecs_execution_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
    }]
  })
}

# Anexa a política oficial da AWS que libera o download da imagem e geração de logs
resource "aws_iam_role_policy_attachment" "ecs_execution_role_policy" {
  role       = aws_iam_role.ecs_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# 3. Define a "Receita" do seu Contêiner (Task Definition)
resource "aws_ecs_task_definition" "ingestion_task" {
  family                   = "insurance-ingestion-task"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "256" # 0.25 vCPU (Altamente otimizado para custo)
  memory                   = "512" # 512 MB RAM
  execution_role_arn       = aws_iam_role.ecs_execution_role.arn

  # O Terraform vai buscar a URL do seu ECR automaticamente aqui
  container_definitions = jsonencode([{
    name      = "ingestion-container"
    image     = "${aws_ecr_repository.ingestion_repo.repository_url}:latest"
    essential = true
  }])
}