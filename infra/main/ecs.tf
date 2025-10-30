resource "aws_ecs_task_definition" "api" {
  family                   = "genonaut-api"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 256
  memory                   = 512
  execution_role_arn       = aws_iam_role.task_execution.arn
  task_role_arn            = aws_iam_role.task.arn

  container_definitions = jsonencode([
    {
      name      = "api"
      image     = "nginx:latest"
      essential = true
      portMappings = [{ containerPort = 8000 }]
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
