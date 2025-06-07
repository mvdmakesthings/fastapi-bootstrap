variable "app_name" {
  description = "The name of the application"
  type        = string
}

variable "environment" {
  description = "The deployment environment (dev, test, prod)"
  type        = string
}

variable "vpc_id" {
  description = "The VPC ID"
  type        = string
}

variable "private_subnets" {
  description = "The private subnet IDs"
  type        = list(string)
}

variable "security_group_id" {
  description = "The security group ID for the VPC Link"
  type        = string
}

variable "alb_listener_arn" {
  description = "The ARN of the ALB listener"
  type        = string
}

variable "certificate_arn" {
  description = "The ARN of the SSL certificate for HTTPS"
  type        = string
  default     = ""
}

variable "web_acl_arn" {
  description = "The ARN of the WAF Web ACL"
  type        = string
  default     = null
}

variable "api_gateway_enabled" {
  description = "Whether to enable API Gateway"
  type        = bool
  default     = false
}

variable "custom_domain_name" {
  description = "The custom domain name for the API Gateway"
  type        = string
  default     = ""
}

# API Gateway HTTP API
resource "aws_apigatewayv2_api" "main" {
  count = var.api_gateway_enabled ? 1 : 0

  name          = "${var.app_name}-${var.environment}"
  protocol_type = "HTTP"
  
  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allow_headers = ["Content-Type", "Authorization", "X-Amz-Date", "X-Api-Key", "X-Amz-Security-Token"]
    max_age       = 300
  }

  tags = {
    Name        = "${var.app_name}-${var.environment}"
    Environment = var.environment
  }
}

# VPC Link for private integration
resource "aws_apigatewayv2_vpc_link" "main" {
  count = var.api_gateway_enabled ? 1 : 0

  name               = "${var.app_name}-${var.environment}"
  security_group_ids = [var.security_group_id]
  subnet_ids         = var.private_subnets

  tags = {
    Name        = "${var.app_name}-${var.environment}"
    Environment = var.environment
  }
}

# API Gateway integration with ALB
resource "aws_apigatewayv2_integration" "main" {
  count = var.api_gateway_enabled ? 1 : 0

  api_id           = aws_apigatewayv2_api.main[0].id
  integration_type = "HTTP_PROXY"
  
  integration_uri    = var.alb_listener_arn
  integration_method = "ANY"
  connection_type    = "VPC_LINK"
  connection_id      = aws_apigatewayv2_vpc_link.main[0].id

  payload_format_version = "1.0"
}

# API Gateway route for all paths
resource "aws_apigatewayv2_route" "main" {
  count = var.api_gateway_enabled ? 1 : 0

  api_id    = aws_apigatewayv2_api.main[0].id
  route_key = "ANY /{proxy+}"
  target    = "integrations/${aws_apigatewayv2_integration.main[0].id}"
}

# API Gateway stage
resource "aws_apigatewayv2_stage" "main" {
  count = var.api_gateway_enabled ? 1 : 0

  api_id      = aws_apigatewayv2_api.main[0].id
  name        = "$default"
  auto_deploy = true

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway[0].arn
    format = jsonencode({
      requestId      = "$context.requestId"
      ip             = "$context.identity.sourceIp"
      requestTime    = "$context.requestTime"
      httpMethod     = "$context.httpMethod"
      routeKey       = "$context.routeKey"
      status         = "$context.status"
      protocol       = "$context.protocol"
      responseLength = "$context.responseLength"
      path           = "$context.path"
      integrationLatency = "$context.integrationLatency"
      responseLatency = "$context.responseLatency"
    })
  }

  default_route_settings {
    throttling_burst_limit = 100
    throttling_rate_limit  = 50
  }

  tags = {
    Name        = "${var.app_name}-${var.environment}"
    Environment = var.environment
  }
}

# CloudWatch Log Group for API Gateway
resource "aws_cloudwatch_log_group" "api_gateway" {
  count = var.api_gateway_enabled ? 1 : 0

  name              = "/aws/apigateway/${var.app_name}-${var.environment}"
  retention_in_days = 30

  tags = {
    Name        = "${var.app_name}-${var.environment}"
    Environment = var.environment
  }
}

# Custom domain name (if provided)
resource "aws_apigatewayv2_domain_name" "main" {
  count = var.api_gateway_enabled && var.custom_domain_name != "" && var.certificate_arn != "" ? 1 : 0

  domain_name = var.custom_domain_name
  
  domain_name_configuration {
    certificate_arn = var.certificate_arn
    endpoint_type   = "REGIONAL"
    security_policy = "TLS_1_2"
  }

  tags = {
    Name        = "${var.app_name}-${var.environment}"
    Environment = var.environment
  }
}

# API mapping for custom domain
resource "aws_apigatewayv2_api_mapping" "main" {
  count = var.api_gateway_enabled && var.custom_domain_name != "" && var.certificate_arn != "" ? 1 : 0

  api_id      = aws_apigatewayv2_api.main[0].id
  domain_name = aws_apigatewayv2_domain_name.main[0].id
  stage       = aws_apigatewayv2_stage.main[0].id
}

# WAF Web ACL association with API Gateway
resource "aws_wafv2_web_acl_association" "api_gateway" {
  count = var.api_gateway_enabled && var.web_acl_arn != null ? 1 : 0

  resource_arn = aws_apigatewayv2_stage.main[0].arn
  web_acl_arn  = var.web_acl_arn
}

# Outputs
output "api_gateway_id" {
  description = "The ID of the API Gateway"
  value       = var.api_gateway_enabled ? aws_apigatewayv2_api.main[0].id : null
}

output "api_gateway_endpoint" {
  description = "The endpoint of the API Gateway"
  value       = var.api_gateway_enabled ? aws_apigatewayv2_api.main[0].api_endpoint : null
}

output "api_gateway_stage_arn" {
  description = "The ARN of the API Gateway stage"
  value       = var.api_gateway_enabled ? aws_apigatewayv2_stage.main[0].arn : null
}

output "custom_domain_url" {
  description = "The custom domain URL for the API Gateway"
  value       = var.api_gateway_enabled && var.custom_domain_name != "" ? "https://${var.custom_domain_name}" : null
}