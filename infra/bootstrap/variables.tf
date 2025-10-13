variable "region" {
  description = "AWS region to create state storage in"
  type        = string
  default     = "us-east-1"
}

# Bucket name must be globally unique — change this!
variable "state_bucket_name" {
  description = "Globally unique S3 bucket name for Terraform state"
  type        = string
}

variable "dynamodb_table_name" {
  description = "DynamoDB table name for Terraform state locking"
  type        = string
  default     = "terraform-state-locks"
}

variable "tags" {
  type        = map(string)
  default     = { Project = "genonaut", Env = "shared", Owner = "genonaut-admin" }
}
