# Terraform Infra Setup: Stage A (Bootstrap) & Stage B (Main Infra)

This guide covers the exact file structure and contents needed to bootstrap and configure Terraform for your AWS infrastructure.  
It is split into two phases:

---

## 🪜 Stage A — Bootstrap (S3 + DynamoDB)

### 🎯 Goal
Set up Terraform’s **remote state backend** — the infrastructure Terraform itself needs to work safely.  
This is done once and used by all future infra deployments.

**What it creates:**
- An S3 bucket (for Terraform state)
- A DynamoDB table (for state locking)

---

### 📁 Directory Structure
```
infra/
  bootstrap/
    main.tf
    variables.tf
    outputs.tf
    versions.tf
```

---

### 🧾 `versions.tf`
```hcl
terraform {
  required_version = ">= 1.6.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }
}
```

### 🧾 `variables.tf`
```hcl
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
  default     = { Project = "genonaut", Owner = "joe" }
}
```

### 🧾 `main.tf`
```hcl
provider "aws" {
  region = var.region
}

# S3 bucket for remote state
resource "aws_s3_bucket" "tf_state" {
  bucket = var.state_bucket_name
  tags   = var.tags
}

resource "aws_s3_bucket_public_access_block" "tf_state" {
  bucket                  = aws_s3_bucket.tf_state.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "tf_state" {
  bucket = aws_s3_bucket.tf_state.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "tf_state" {
  bucket = aws_s3_bucket.tf_state.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "tf_state" {
  bucket = aws_s3_bucket.tf_state.id
  rule {
    id     = "expire-old-versions"
    status = "Enabled"
    noncurrent_version_expiration {
      noncurrent_days = 30
    }
  }
}

# DynamoDB table for state locking
resource "aws_dynamodb_table" "tf_lock" {
  name         = var.dynamodb_table_name
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  tags = var.tags
}
```

### 🧾 `outputs.tf`
```hcl
output "state_bucket_name" {
  value = aws_s3_bucket.tf_state.bucket
}

output "dynamodb_table_name" {
  value = aws_dynamodb_table.tf_lock.name
}
```

---

### ▶️ Run Commands
```bash
cd infra/bootstrap
export AWS_PROFILE=genonaut-admin
export AWS_REGION=us-east-1

terraform init
terraform apply   -var="state_bucket_name=genonaut-tf-state-<unique>"   -var="region=us-east-1"
```

---

## 🪜 Stage B — Main Infrastructure

### 🎯 Goal
Configure Terraform to **use the remote state backend** created in Stage A, and define your actual infra (VPC, ECS, RDS, etc.).

**What it does:**
- Uses S3 + DynamoDB as the Terraform backend.
- Provisions real AWS resources.

---

### 📁 Directory Structure
```
infra/
  main/
    versions.tf
    backend.hcl
    provider.tf
    vpc.tf   # and other infra .tf files
```

---

### 🧾 `versions.tf`
```hcl
terraform {
  required_version = ">= 1.6.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }
  backend "s3" {}
}
```

### 🧾 `backend.hcl`
```hcl
bucket         = "genonaut-tf-state-<unique>"
key            = "envs/dev/terraform.tfstate"
region         = "us-east-1"
dynamodb_table = "terraform-state-locks"
encrypt        = true
```

### 🧾 `provider.tf`
```hcl
provider "aws" {
  region = "us-east-1"
}
```

---

## 💡 Summary

| Stage | Purpose                              | What it creates                       | Run when                    |
|-------|---------------------------------------|-----------------------------------------|------------------------------|
| A     | Bootstrap Terraform backend           | S3 bucket + DynamoDB for state locking | Once per account             |
| B     | Deploy real infra using that backend | ECS, RDS, VPC, etc.                    | Every time you deploy infra  |

✅ Stage A is safe to do **early**, before deciding what to deploy.  
✅ Stage B can evolve iteratively as your app architecture grows.
