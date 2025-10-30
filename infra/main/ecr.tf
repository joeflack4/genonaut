########################
# ECR repositories
########################

# Helper to namespace per env
locals {
  ecr_repo_api       = "genonaut-api-${var.env}"
  ecr_repo_worker    = "genonaut-worker-${var.env}"
  ecr_repo_image_gen = "genonaut-imagegen-${var.env}"
}

resource "aws_ecr_repository" "api" {
  name = local.ecr_repo_api

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = {
    Name = local.ecr_repo_api
    Env  = var.env
  }
}

resource "aws_ecr_repository" "worker" {
  name = local.ecr_repo_worker

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = {
    Name = local.ecr_repo_worker
    Env  = var.env
  }
}

resource "aws_ecr_repository" "image_gen" {
  name = local.ecr_repo_image_gen

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = {
    Name = local.ecr_repo_image_gen
    Env  = var.env
  }
}

# Optional: output the repo URLs so you know what to `docker push`
output "ecr_repo_api_url" {
  value       = aws_ecr_repository.api.repository_url
  description = "ECR URL for API image (tag and push here)"
}

output "ecr_repo_worker_url" {
  value       = aws_ecr_repository.worker.repository_url
  description = "ECR URL for worker image"
}

output "ecr_repo_image_gen_url" {
  value       = aws_ecr_repository.image_gen.repository_url
  description = "ECR URL for image-gen image"
}
