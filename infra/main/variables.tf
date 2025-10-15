// infra/main/variables.tf
variable "env" {
  description = "Deployment environment (dev|test|prod|demo)"
  type        = string
}

variable "region" {
  description = "AWS region for this stack"
  type        = string
}

variable "name_prefix" {
  description = "Base name prefix for resources (keeps names DRY)"
  type        = string
  default     = "genonaut"
}

variable "tags" {
  description = "Common tags applied to all resources"
  type        = map(string)
  default     = {}
}

# Networking knobs (safe defaults; override per env if needed)
variable "vpc_cidr" {
  type        = string
  default     = "10.20.0.0/16"
}

variable "public_subnet_cidrs" {
  type        = list(string)
  default     = ["10.20.0.0/24", "10.20.1.0/24"]
}

variable "private_subnet_cidrs" {
  type        = list(string)
  default     = ["10.20.10.0/24", "10.20.11.0/24"]
}
