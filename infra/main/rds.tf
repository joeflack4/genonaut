########################
# RDS (Postgres)
########################

# FYI: AWS requires DB subnet groups to include subnets in at least 2 AZs, hence, why we have private and private_b.
resource "aws_db_subnet_group" "postgres" {
  name       = "genonaut-postgres-${var.env}"
  subnet_ids = [
    aws_subnet.private.id,
    aws_subnet.private_b.id
  ]
  tags = {
    Name = "genonaut-postgres-${var.env}"
    Env  = var.env
  }
}

# Inputs for admin creds
variable "db_master_username" {
  description = "Master username for Postgres"
  type        = string
  default     = "postgres"
}

variable "db_master_password" {
  description = "Master password for Postgres"
  type        = string
  sensitive   = true
  # no default on purpose; you'll pass this via -var or tfvars you DO NOT commit
}

resource "aws_db_instance" "postgres" {
  identifier              = "genonaut-${var.env}-postgres"
  engine                  = "postgres"
  engine_version          = "16.4" # todo: update if you want a different minor
  instance_class          = "db.t4g.micro"   # small / cheap
  allocated_storage       = 20               # GB
  max_allocated_storage   = 100              # autoscale headroom
  username                = var.db_master_username
  password                = var.db_master_password
  db_name                 = "genonaut_${var.env}"
  port                    = 5432

  storage_encrypted       = true
  skip_final_snapshot     = !(var.env == "prod" || var.env == "demo")  # final snapshot means it'll back up before destroy

  publicly_accessible     = false
  multi_az                = false           # single-AZ to save $ now

  vpc_security_group_ids  = [aws_security_group.db_sg.id]
  db_subnet_group_name    = aws_db_subnet_group.postgres.name


  backup_retention_period = (var.env == "prod" || var.env == "demo") ? 3 : 0  # How many days of automated daily backups AWS keeps for you.
  deletion_protection     = (var.env == "prod" || var.env == "demo")

  tags = {
    Name = "genonaut-postgres-${var.env}"
    Env  = var.env
  }
}
