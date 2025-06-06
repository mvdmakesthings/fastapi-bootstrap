variable "app_name" {
  description = "The name of the application"
  type        = string
}

variable "environment" {
  description = "The deployment environment (dev, test, prod)"
  type        = string
}

# IAM role for Lambda functions
resource "aws_iam_role" "lambda_role" {
  name = "${var.app_name}-${var.environment}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "${var.app_name}-${var.environment}-lambda-role"
    Environment = var.environment
  }
}

# Attach basic Lambda execution policy
resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Lambda function for pre-deployment validation
resource "aws_lambda_function" "validate_before_install" {
  function_name = "${var.app_name}-validate-before-install-${var.environment}"
  role          = aws_iam_role.lambda_role.arn
  handler       = "lambda_handler.handler"
  runtime       = "python3.9"
  timeout       = 30

  filename         = "${path.module}/lambda_functions/validate_before_install.zip"
  source_code_hash = filebase64sha256("${path.module}/lambda_functions/validate_before_install.zip")

  environment {
    variables = {
      ENVIRONMENT = var.environment
    }
  }

  tags = {
    Name        = "${var.app_name}-validate-before-install-${var.environment}"
    Environment = var.environment
  }
}

# Lambda function for post-deployment validation
resource "aws_lambda_function" "validate_deployment" {
  function_name = "${var.app_name}-validate-deployment-${var.environment}"
  role          = aws_iam_role.lambda_role.arn
  handler       = "lambda_handler.handler"
  runtime       = "python3.9"
  timeout       = 30

  filename         = "${path.module}/lambda_functions/validate_deployment.zip"
  source_code_hash = filebase64sha256("${path.module}/lambda_functions/validate_deployment.zip")

  environment {
    variables = {
      ENVIRONMENT = var.environment
    }
  }

  tags = {
    Name        = "${var.app_name}-validate-deployment-${var.environment}"
    Environment = var.environment
  }
}

# Lambda function for test traffic validation
resource "aws_lambda_function" "validate_test_traffic" {
  function_name = "${var.app_name}-validate-test-traffic-${var.environment}"
  role          = aws_iam_role.lambda_role.arn
  handler       = "lambda_handler.handler"
  runtime       = "python3.9"
  timeout       = 30

  filename         = "${path.module}/lambda_functions/validate_test_traffic.zip"
  source_code_hash = filebase64sha256("${path.module}/lambda_functions/validate_test_traffic.zip")

  environment {
    variables = {
      ENVIRONMENT = var.environment
    }
  }

  tags = {
    Name        = "${var.app_name}-validate-test-traffic-${var.environment}"
    Environment = var.environment
  }
}

# Lambda function for running migrations
resource "aws_lambda_function" "run_migrations" {
  function_name = "${var.app_name}-run-migrations-${var.environment}"
  role          = aws_iam_role.lambda_role.arn
  handler       = "migrations_handler.handler"
  runtime       = "python3.9"
  timeout       = 60

  filename         = "${path.module}/lambda_functions/run_migrations.zip"
  source_code_hash = filebase64sha256("${path.module}/lambda_functions/run_migrations.zip")

  environment {
    variables = {
      ENVIRONMENT = var.environment
    }
  }

  tags = {
    Name        = "${var.app_name}-run-migrations-${var.environment}"
    Environment = var.environment
  }
}

# Lambda function for production validation
resource "aws_lambda_function" "validate_production" {
  function_name = "${var.app_name}-validate-production-${var.environment}"
  role          = aws_iam_role.lambda_role.arn
  handler       = "lambda_handler.handler"
  runtime       = "python3.9"
  timeout       = 30

  filename         = "${path.module}/lambda_functions/validate_production.zip"
  source_code_hash = filebase64sha256("${path.module}/lambda_functions/validate_production.zip")

  environment {
    variables = {
      ENVIRONMENT = var.environment
    }
  }

  tags = {
    Name        = "${var.app_name}-validate-production-${var.environment}"
    Environment = var.environment
  }
}

# Outputs
output "validate_before_install_arn" {
  value = aws_lambda_function.validate_before_install.arn
}

output "validate_deployment_arn" {
  value = aws_lambda_function.validate_deployment.arn
}

output "validate_test_traffic_arn" {
  value = aws_lambda_function.validate_test_traffic.arn
}

output "run_migrations_arn" {
  value = aws_lambda_function.run_migrations.arn
}

output "validate_production_arn" {
  value = aws_lambda_function.validate_production.arn
}