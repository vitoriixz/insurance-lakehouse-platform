# 1. VPC (A sua rede isolada na AWS)
resource "aws_vpc" "lakehouse_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags = { Name = "insurance-lakehouse-vpc" }
}

# 2. Internet Gateway (O "modem" que dá acesso à internet)
resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.lakehouse_vpc.id
}

# 3. Subnet Pública (Onde o seu contêiner vai rodar)
resource "aws_subnet" "public_subnet" {
  vpc_id                  = aws_vpc.lakehouse_vpc.id
  cidr_block              = "10.0.1.0/24"
  map_public_ip_on_launch = true # Essencial para manter o custo zero (sem NAT Gateway)
  availability_zone       = "us-east-1a"
}

# 4. Tabela de Roteamento (Avisa a Subnet para usar o Internet Gateway)
resource "aws_route_table" "public_rt" {
  vpc_id = aws_vpc.lakehouse_vpc.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }
}

resource "aws_route_table_association" "public_rta" {
  subnet_id      = aws_subnet.public_subnet.id
  route_table_id = aws_route_table.public_rt.id
}

# 5. Security Group (O Firewall do seu contêiner)
resource "aws_security_group" "ecs_sg" {
  name        = "ecs_task_sg"
  description = "Permite saida de dados para a internet"
  vpc_id      = aws_vpc.lakehouse_vpc.id

  # Bloqueamos qualquer tráfego de entrada (Inbound) por segurança.
  # Mas liberamos a saída (Outbound) para ele conseguir mandar os dados pro S3.
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}