# ---- Networking ----
output "vpc_id" {
  value       = try(aws_vpc.main.id, null)
  description = "VPC ID"
}

output "public_subnet_ids" {
  value       = try([for s in aws_subnet.public : s.id], [])
  description = "Public subnet IDs"
}

output "private_subnet_ids" {
  value       = try([for s in aws_subnet.private : s.id], [])
  description = "Private subnet IDs"
}

output "nat_gateway_ids" {
  value       = try([for n in aws_nat_gateway.this : n.id], [])
  description = "NAT gateway IDs"
}

# ---- Load Balancer / Ingress ----
output "alb_arn" {
  value       = try(aws_lb.app.arn, null)
  description = "Application Load Balancer ARN"
}
output "alb_dns_name" {
  value       = try(aws_lb.app.dns_name, null)
  description = "Public DNS for the ALB"
}

# ---- ECS / Compute ----
output "ecs_cluster_arn" {
  value       = try(aws_ecs_cluster.main.arn, null)
  description = "ECS cluster ARN"
}
output "service_api_arn" {
  value       = try(aws_ecs_service.api.arn, null)
  description = "Web API service ARN"
}
output "service_api2_arn" {
  value       = try(aws_ecs_service.api2.arn, null)
  description = "2nd API service ARN"
}
output "service_celery_arn" {
  value       = try(aws_ecs_service.celery.arn, null)
  description = "Celery worker service ARN"
}

# ---- Datastores ----
output "rds_endpoint" {
  value       = try(aws_db_instance.postgres.address, null)
  description = "Postgres endpoint hostname"
}
output "redis_endpoint" {
  value       = try(aws_elasticache_replication_group.redis.primary_endpoint_address, try(aws_elasticache_cluster.redis.cache_nodes[0].address, null))
  description = "Redis endpoint"
}

# ---- Static site ----
output "static_site_bucket" {
  value       = try(aws_s3_bucket.static_site.bucket, null)
  description = "S3 bucket for React build"
}
output "cloudfront_domain" {
  value       = try(aws_cloudfront_distribution.site.domain_name, null)
  description = "CloudFront distribution domain"
}

# ---- Useful ARNs / misc ----
output "task_exec_role_arn" {
  value       = try(aws_iam_role.task_execution.arn, null)
  description = "ECS task execution role ARN"
}
output "task_role_arn" {
  value       = try(aws_iam_role.task.arn, null)
  description = "ECS task role ARN"
}
