# 1. CLUSTER ECS
resource "aws_ecs_cluster" "main" {
  name = "insurance-lakehouse-cluster"
}

# 2. EXECUTION ROLE 
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

resource "aws_iam_role_policy_attachment" "ecs_execution_role_policy" {
  role       = aws_iam_role.ecs_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# 3. TASK ROLE 
resource "aws_iam_role" "ecs_task_role" {
  name = "insurance_ecs_task_role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_task_role_s3_policy" {
  role       = aws_iam_role.ecs_task_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

# 4. CLOUDWATCH LOG GROUP 
resource "aws_cloudwatch_log_group" "ecs_logs" {
  name              = "/ecs/insurance-ingestion"
  retention_in_days = 7
}

# 5. TASK DEFINITION 
resource "aws_ecs_task_definition" "ingestion_task" {
  family                   = "insurance-ingestion-task"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "256"
  memory                   = "512"
  
  execution_role_arn       = aws_iam_role.ecs_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([{
    name      = "ingestion-container"
    image     = "${aws_ecr_repository.ingestion_repo.repository_url}:latest"
    essential = true
    
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.ecs_logs.name
        "awslogs-region"        = "us-east-1"
        "awslogs-stream-prefix" = "ecs"
      }
    }
  }])
}