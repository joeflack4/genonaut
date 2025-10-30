########################################
# Shared locals / settings
########################################

locals {
  container_port_api = 8001
}

########################################
# Web API service
########################################

resource "aws_ecs_task_definition" "api" {
  family                   = "genonaut-api-${var.env}"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 256
  memory                   = 512
  execution_role_arn       = aws_iam_role.task_execution.arn
  task_role_arn            = aws_iam_role.task.arn

  container_definitions = jsonencode([
    {
      name         = "api"
      image        = "nginx:latest" # TODO: replace with your ECR image later
      essential    = true
      portMappings = [
        {
          containerPort = local.container_port_api
          protocol      = "tcp"
        }
      ]
      # inject secrets from SSM for this env (generated in ecs_secrets.auto.tf)
      secrets = lookup(
        {
          demo = local.ecs_secrets_demo
          dev  = local.ecs_secrets_dev
          prod = local.ecs_secrets_prod
          test = local.ecs_secrets_test
        },
        var.env
      )
    }
  ])
}

resource "aws_ecs_service" "api" {
  name            = "genonaut-api-${var.env}"
  cluster         = aws_ecs_cluster.main.arn
  launch_type     = "FARGATE"
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = 1

  network_configuration {
    subnets         = [aws_subnet.private.id, aws_subnet.private_b.id]
    security_groups = [aws_security_group.app_sg.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.app_tg.arn
    container_name   = "api"
    container_port   = local.container_port_api
  }

  depends_on = [
    aws_lb_listener.http,
    aws_lb_target_group.app_tg
  ]

  tags = {
    Name = "genonaut-api-${var.env}"
    Env  = var.env
  }
}

########################################
# Second API service (api2)
########################################
# This is drafted as a parallel service. We assume you'll
# later create a second target group + listener rule in alb.tf.
# For now, we include the task def and service with a TODO.

resource "aws_ecs_task_definition" "api2" {
  family                   = "genonaut-api2-${var.env}"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 256
  memory                   = 512
  execution_role_arn       = aws_iam_role.task_execution.arn
  task_role_arn            = aws_iam_role.task.arn

  container_definitions = jsonencode([
    {
      name         = "api2"
      image        = "nginx:latest" # TODO: swap once you have separate image
      essential    = true
      portMappings = [
        {
          containerPort = local.container_port_api
          protocol      = "tcp"
        }
      ]
      secrets = lookup(
        {
          demo = local.ecs_secrets_demo
          dev  = local.ecs_secrets_dev
          prod = local.ecs_secrets_prod
          test = local.ecs_secrets_test
        },
        var.env
      )
    }
  ])
}

# NOTE: we don't yet have a second target group/listener rule wired.
# We'll stub the service but comment out the load_balancer block so plan won't fail.

resource "aws_ecs_service" "api2" {
  name            = "genonaut-api2-${var.env}"
  cluster         = aws_ecs_cluster.main.arn
  launch_type     = "FARGATE"
  task_definition = aws_ecs_task_definition.api2.arn
  desired_count   = 0 # start disabled / scaled to 0 so you're not billed

  network_configuration {
    subnets         = [aws_subnet.private.id, aws_subnet.private_b.id]
    security_groups = [aws_security_group.app_sg.id]
    assign_public_ip = false
  }

  # load_balancer {
  #   target_group_arn = aws_lb_target_group.api2_tg.arn  # TODO: define in alb.tf later
  #   container_name   = "api2"
  #   container_port   = local.container_port_api
  # }

  tags = {
    Name = "genonaut-api2-${var.env}"
    Env  = var.env
  }
}

########################################
# Celery / worker service
########################################
# No ALB, internal only, can run on FARGATE or FARGATE_SPOT later.

resource "aws_ecs_task_definition" "celery" {
  family                   = "genonaut-celery-${var.env}"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 256
  memory                   = 512
  execution_role_arn       = aws_iam_role.task_execution.arn
  task_role_arn            = aws_iam_role.task.arn

  container_definitions = jsonencode([
    {
      name      = "celery"
      image     = "nginx:latest" # TODO: swap to your worker image
      essential = true

      # usually Celery has no inbound portMappings, so we leave that out

      command = [
        "bash",
        "-c",
        "echo 'TODO run celery worker here' && sleep 3600"
      ]

      secrets = lookup(
        {
          demo = local.ecs_secrets_demo
          dev  = local.ecs_secrets_dev
          prod = local.ecs_secrets_prod
          test = local.ecs_secrets_test
        },
        var.env
      )
    }
  ])
}

resource "aws_ecs_service" "celery" {
  name            = "genonaut-celery-${var.env}"
  cluster         = aws_ecs_cluster.main.arn
  launch_type     = "FARGATE"
  task_definition = aws_ecs_task_definition.celery.arn
  desired_count   = 0 # start at 0 so you're not billed until you want workers

  network_configuration {
    subnets         = [aws_subnet.private.id, aws_subnet.private_b.id]
    security_groups = [aws_security_group.app_sg.id] # can reuse app SG for now
    assign_public_ip = false
  }

  tags = {
    Name = "genonaut-celery-${var.env}"
    Env  = var.env
  }
}

########################################
# Outputs (so you can see ARNs in `plan` / `apply`)
########################################

output "service_api_arn" {
  value       = aws_ecs_service.api.arn
  description = "Web API service ARN"
}

output "service_api2_arn" {
  value       = aws_ecs_service.api2.arn
  description = "Second API service ARN"
}

output "service_celery_arn" {
  value       = aws_ecs_service.celery.arn
  description = "Celery worker service ARN"
}
