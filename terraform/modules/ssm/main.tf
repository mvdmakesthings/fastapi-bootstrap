variable "app_name" {
  description = "The name of the application"
  type        = string
}

variable "environment" {
  description = "The deployment environment (dev, test, prod)"
  type        = string
}

variable "kms_key_id" {
  description = "The KMS key ID for parameter encryption"
  type        = string
}

variable "parameters" {
  description = "Map of parameters to create"
  type        = map(object({
    value       = string
    description = string
    type        = string
  }))
  default     = {}
}

# Create SSM Parameters
resource "aws_ssm_parameter" "parameters" {
  for_each = var.parameters

  name        = "/${var.app_name}/${var.environment}/${each.key}"
  description = each.value.description
  type        = each.value.type
  value       = each.value.value
  key_id      = var.kms_key_id
  
  tags = {
    Name        = "${var.app_name}-${var.environment}-${each.key}"
    Environment = var.environment
  }
}

# Outputs
output "parameter_arns" {
  description = "ARNs of the created parameters"
  value = {
    for key, param in aws_ssm_parameter.parameters : key => param.arn
  }
}

output "parameter_names" {
  description = "Names of the created parameters"
  value = {
    for key, param in aws_ssm_parameter.parameters : key => param.name
  }
}