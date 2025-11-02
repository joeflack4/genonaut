########################################
# Shared locals / settings
########################################

locals {
  container_port_api = 8001
  container_port_image_gen    = 8189
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
      command = [
        "make",
        "cloud-${var.env}"
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
# Image gen API service
########################################
resource "aws_ecs_task_definition" "image_gen_mock_api" {
  family                   = "genonaut-image-gen-${var.env}"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 256
  memory                   = 512
  execution_role_arn       = aws_iam_role.task_execution.arn
  task_role_arn            = aws_iam_role.task.arn

  container_definitions = jsonencode([
    {
      name         = "image_gen_mock_api"
      image        = "nginx:latest"  # TODO replace with your mock image-gen container
      essential    = true
      portMappings = [
        {
          containerPort = local.container_port_image_gen
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

resource "aws_ecs_service" "image_gen_mock_api" {
  name            = "genonaut-image-gen-${var.env}"
  cluster         = aws_ecs_cluster.main.arn
  launch_type     = "FARGATE"
  task_definition = aws_ecs_task_definition.image_gen_mock_api.arn
  desired_count   = 1

  network_configuration {
    subnets          = [aws_subnet.private.id, aws_subnet.private_b.id]
    security_groups  = [aws_security_group.app_sg.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.image_gen_tg.arn
    container_name   = "image_gen_mock_api"
    container_port   = local.container_port_image_gen
  }

  depends_on = [
    aws_lb_listener.http,
    aws_lb_target_group.image_gen_tg,
    aws_lb_listener_rule.image_gen_rule
  ]

  tags = {
    Name = "genonaut-image-gen-${var.env}"
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
  desired_count   = 1

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
