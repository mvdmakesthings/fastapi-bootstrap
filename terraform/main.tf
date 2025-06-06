provider "aws" {
  region = var.aws_region
}

terraform {
  required_version = ">= 1.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket         = "fastapi-bootstrap-terraform-state"
    key            = "fastapi-bootstrap/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-locks"
    encrypt        = true
  }
}

# Variables
variable "aws_region" {
  description = "The AWS region to deploy to"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "The deployment environment (dev, test, prod)"
  type        = string
}

variable "app_name" {
  description = "The name of the application"
  type        = string
  default     = "fastapi-bootstrap"
}

variable "kms_key_id" {
  description = "The KMS key ID for CloudWatch Log Group encryption"
  type        = string
}

variable "certificate_arn" {
  description = "The ARN of the SSL certificate for HTTPS"
  type        = string
  default     = ""
}

# Modules
module "vpc" {
  source = "../modules/vpc"

  environment = var.environment
  app_name    = var.app_name
}

module "security" {
  source = "../modules/security"

  vpc_id      = module.vpc.vpc_id
  environment = var.environment
  app_name    = var.app_name
}

module "iam" {
  source = "../modules/iam"

  environment = var.environment
  app_name    = var.app_name
}

module "ecr" {
  source = "../modules/ecr"

  environment = var.environment
  app_name    = var.app_name
}

module "ecs" {
  source = "../modules/ecs"

  app_name                = var.app_name
  environment             = var.environment
  vpc_id                  = module.vpc.vpc_id
  private_subnets         = module.vpc.private_subnets
  public_subnets          = module.vpc.public_subnets
  ecs_task_execution_role = module.iam.ecs_task_execution_role_arn
  ecs_task_role           = module.iam.ecs_task_role_arn
  security_group_id       = module.security.ecs_security_group_id
  ecr_repository_url      = module.ecr.repository_url
  kms_key_id              = var.kms_key_id
  certificate_arn         = var.certificate_arn
}

module "lambda" {
  source = "../modules/lambda"

  app_name    = var.app_name
  environment = var.environment
}

module "codedeploy" {
  source = "../modules/codedeploy"

  app_name          = var.app_name
  environment       = var.environment
  ecs_cluster_name  = module.ecs.cluster_name
  ecs_service_names = module.ecs.service_names
}

# Outputs
output "vpc_id" {
  value = module.vpc.vpc_id
}

output "private_subnets" {
  value = module.vpc.private_subnets
}

output "ecs_security_group_id" {
  value = module.security.ecs_security_group_id
}

output "ecr_repository_url" {
  value = module.ecr.repository_url
}

output "ecs_cluster_name" {
  value = module.ecs.cluster_name
}

output "alb_dns_name" {
  value = module.ecs.alb_dns_name
}

output "api_v1_url" {
  value = "https://${module.ecs.alb_dns_name}/api/v1"
}

output "lambda_validate_before_install_arn" {
  value = module.lambda.validate_before_install_arn
}

output "lambda_validate_deployment_arn" {
  value = module.lambda.validate_deployment_arn
}

output "lambda_validate_test_traffic_arn" {
  value = module.lambda.validate_test_traffic_arn
}

output "lambda_run_migrations_arn" {
  value = module.lambda.run_migrations_arn
}

output "lambda_validate_production_arn" {
  value = module.lambda.validate_production_arn
}

