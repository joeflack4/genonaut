########################
# ECS Cluster
########################

resource "aws_ecs_cluster" "main" {
  name = "genonaut-${var.env}"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Name = "genonaut-${var.env}"
    Env  = var.env
  }
}

# Fargate capacity providers (these let ECS run Fargate tasks on this cluster)
resource "aws_ecs_cluster_capacity_providers" "main" {
  cluster_name = aws_ecs_cluster.main.name

  capacity_providers = [
    "FARGATE",
    "FARGATE_SPOT"
  ]

  default_capacity_provider_strategy {
    capacity_provider = "FARGATE"
    weight            = 1
  }
}

# Output the cluster ARN (useful later when attaching services)
output "ecs_cluster_arn" {
  value       = aws_ecs_cluster.main.arn
  description = "ECS cluster ARN"
}
