#######################
# Security Groups
#######################

# ALB / public ingress
resource "aws_security_group" "alb_sg" {
  name        = "genonaut-alb-sg"
  description = "Allow public HTTP/HTTPS to ALB"
  vpc_id      = aws_vpc.main.id

  # Allow inbound HTTP (80) from anywhere
  ingress {
    description      = "HTTP from anywhere"
    from_port        = 80
    to_port          = 80
    protocol         = "tcp"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  # (Optional now, future HTTPS)
  ingress {
    description      = "HTTPS from anywhere"
    from_port        = 443
    to_port          = 443
    protocol         = "tcp"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  # Outbound: ALB can talk to ECS services
  egress {
    description = "All outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "genonaut-alb-sg"
    Env  = var.env
  }
}

# ECS tasks / app containers
resource "aws_security_group" "app_sg" {
  name        = "genonaut-app-sg"
  description = "App tasks (ECS services)"
  vpc_id      = aws_vpc.main.id

  # Inbound: only from ALB SG on port 8000 (example FastAPI port)
  # todo: later: if add an ALB: If your container listens on a different port, change 8000.
  #  That rule only matters once you later add: (i) an ALB (which forwards traffic to your ECS service), and
  #  (ii) an ECS task definition (which runs your app container).
  ingress {
    description            = "App traffic from ALB"
    from_port              = 8000
    to_port                = 8000
    protocol               = "tcp"
    security_groups        = [aws_security_group.alb_sg.id]
  }

  # Outbound: app can reach DB, Redis, internet (via NAT)
  egress {
    description = "All outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "genonaut-app-sg"
    Env  = var.env
  }
}

# Security group for Postgres: allow 5432 from app_sg only
resource "aws_security_group" "db_sg" {
  name        = "genonaut-db-sg-${var.env}"
  description = "Postgres access from app"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "Postgres from app"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.app_sg.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "genonaut-db-sg-${var.env}"
    Env  = var.env
  }
}
