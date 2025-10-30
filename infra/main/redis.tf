########################
# ElastiCache (Redis)
########################

# Security group for Redis: allow 6379 from app_sg
resource "aws_security_group" "redis_sg" {
  name        = "genonaut-redis-sg-${var.env}"
  description = "Redis access from app tasks"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "Redis from app"
    from_port       = 6379
    to_port         = 6379
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
    Name = "genonaut-redis-sg-${var.env}"
    Env  = var.env
  }
}

# Subnet group for Redis (ElastiCache wants to know which subnets to use)
resource "aws_elasticache_subnet_group" "redis" {
  name       = "genonaut-redis-${var.env}"
  subnet_ids = [
    aws_subnet.private.id
    # NOTE: unlike RDS, ElastiCache will let you run single-node in one subnet/AZ.
  ]

  tags = {
    Name = "genonaut-redis-${var.env}"
    Env  = var.env
  }
}

# Single-node Redis cluster (not replication group yet)
resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "genonaut-redis-${var.env}"
  engine               = "redis"
  engine_version       = "7.1"          # todo: bump if you want
  node_type            = "cache.t4g.micro"
  num_cache_nodes      = 1
  port                 = 6379
  parameter_group_name = "default.redis7"

  subnet_group_name          = aws_elasticache_subnet_group.redis.name
  security_group_ids         = [aws_security_group.redis_sg.id]
  apply_immediately          = true

  tags = {
    Name = "genonaut-redis-${var.env}"
    Env  = var.env
  }
}
