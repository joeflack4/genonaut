# Infrastructure

This document provides an overview of the Terraform infrastructure setup in the `infra/` directory.

## Directory Structure

The `infra/` directory is organized into two main parts: `bootstrap` and `main`.

```
infra/
├── bootstrap/
│   ├── main.tf
│   ├── outputs.tf
│   ├── variables.tf
│   └── versions.tf
└── main/
    ├── backend.hcl
    ├── provider.tf
    ├── versions.tf
    └── vpc.tf
```

### `infra/bootstrap`

This directory contains the Terraform code to set up the backend for Terraform itself. This is a one-time setup.

- `main.tf`: Defines the AWS resources for the Terraform backend, including an S3 bucket for state storage and a DynamoDB table for state locking.
- `variables.tf`: Declares variables used in the bootstrap configuration, such as the AWS region, S3 bucket name, and DynamoDB table name.
- `outputs.tf`: Defines the outputs of the bootstrap process, such as the names of the created S3 bucket and DynamoDB table.
- `versions.tf`: Specifies the required versions of Terraform and the AWS provider.

### `infra/main`

This directory contains the main infrastructure code for the application.

- `versions.tf`: Specifies the required versions of Terraform and the AWS provider, and configures the S3 backend.
- `backend.hcl`: Contains the configuration for the Terraform S3 backend, specifying the bucket, key, region, and DynamoDB table for state locking.
- `provider.tf`: Configures the AWS provider, specifying the region.
- `vpc.tf`: An example file for defining the VPC and other network-related resources.

## Makefile Commands

The following `make` commands are available for managing the infrastructure:

- `aws-login`: Use if you have invalid credentials error when running terraform commands.
- `tf-bootstrap-init`: Initializes the Terraform bootstrap directory.
- `tf-bootstrap-apply`: Applies the Terraform bootstrap configuration.
- `tf-bootstrap-destroy`: Destroys the Terraform bootstrap resources.
- `tf-init`: Initializes the main Terraform directory.
- `tf-plan`: Creates a plan for the main Terraform infrastructure.
- `tf-apply`: Applies the main Terraform infrastructure changes.
- `tf-destroy`: Destroys the main Terraform infrastructure.
- `tf-fmt`: Formats the Terraform code in the main directory.
- `tf-validate`: Validates the Terraform code in the main directory.
- `tf-console`: Opens the Terraform console for the main directory.

## Environment Variables

The following environment variables must be set for the Makefile commands to work correctly.

They're best put by default in `env/.env.shared`. But further customizability can be done. You can read more about that in: [./configuration.md](./configuration.md)

### AWS

- `DEPLOY_AWS_REGION`: The AWS region to deploy the infrastructure in.
- `DEPLOY_AWS_PROFILE`: The AWS profile to use for authentication.

### Terraform

- `DEPLOY_TF_STATE_BUCKET_NAME`: The name of the S3 bucket for Terraform state.
- `DEPLOY_TF_DYNAMO_DB_TABLE`: The name of the DynamoDB table for Terraform state locking.
