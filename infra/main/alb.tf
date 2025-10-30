########################
# Application Load Balancer
########################

# ALB itself (public)
resource "aws_lb" "app" {
  name               = "genonaut-alb-${var.env}"
  load_balancer_type = "application"
  internal           = false                            # public-facing
  security_groups    = [aws_security_group.alb_sg.id]   # from security_groups.tf
  subnets = [
    aws_subnet.public.id,
    aws_subnet.public_b.id
  ]

  enable_deletion_protection = var.env == "prod" || var.env == "demo"

  tags = {
    Name = "genonaut-alb-${var.env}"
    Env  = var.env
  }
}

# Target group for the app service
resource "aws_lb_target_group" "app_tg" {
  name        = "genonaut-tg-${var.env}"
  port        = 8001                      # container port exposed by your service
  protocol    = "HTTP"
  target_type = "ip"                      # Fargate tasks register their ENI IPs
  vpc_id      = aws_vpc.main.id

  health_check {
    path                = "/health"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 5
    matcher             = "200-399"
  }

  tags = {
    Name = "genonaut-tg-${var.env}"
    Env  = var.env
  }
}

# Listener on port 80 → forwards to the target group
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.app.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app_tg.arn
  }

  tags = {
    Env = var.env
  }
}

# Outputs that are useful to see after apply
output "alb_arn" {
  value       = aws_lb.app.arn
  description = "Application Load Balancer ARN"
}

output "alb_dns_name" {
  value       = aws_lb.app.dns_name
  description = "Public DNS for the ALB"
}
