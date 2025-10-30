#################################
# IAM Roles for ECS Tasks
#################################

# Execution role: ECS agent / runtime stuff
resource "aws_iam_role" "task_execution" {
  name = "genonaut-task-execution-role-${var.env}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        },
        Action = "sts:AssumeRole"
      }
    ]
  })
  tags = {
    Name = "genonaut-task-execution-role"
    Env  = var.env
  }
}

# Attach the standard AWS managed policy so the task can pull from ECR, write logs, etc.
resource "aws_iam_role_policy_attachment" "task_execution_policy" {
  role       = aws_iam_role.task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Task role: your app code runs with this
resource "aws_iam_role" "task" {
  name = "genonaut-app-task-role-${var.env}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        },
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Name = "genonaut-app-task-role"
    Env  = var.env
  }
}

# Inline policy example giving the app role permission to read params/secrets from SSM
resource "aws_iam_role_policy" "task_ssm_read" {
  name = "genonaut-task-ssm-read"
  role = aws_iam_role.task.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Sid    = "ReadAppSecrets",
        Effect = "Allow",
        Action = [
          "ssm:GetParameter",
          "ssm:GetParameters",
          "ssm:GetParametersByPath"
        ],
        Resource = [
          "arn:aws:ssm:${var.region}:${var.account_id}:parameter/genonaut/${var.env}/*"
        ]
      }
    ]
  })
}
