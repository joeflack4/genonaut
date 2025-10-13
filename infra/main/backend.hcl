# These are defaults. They can be overridden by adding .env vars, e.g. in .env.shared, which the terraform
# makefile commands are set up to utilize.
bucket         = "genonaut-terraform-state"
key            = "envs/dev/terraform.tfstate"
region         = "us-east-1"
dynamodb_table = "genonaut-terraform-state-locks"
encrypt        = true
