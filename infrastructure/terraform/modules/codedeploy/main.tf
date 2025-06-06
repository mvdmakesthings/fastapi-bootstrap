variable "app_name" {
  description = "The name of the application"
  type        = string
}

variable "environment" {
  description = "The deployment environment (dev, test, prod)"
  type        = string
}

variable "ecs_cluster_name" {
  description = "The name of the ECS cluster"
  type        = string
}

variable "ecs_service_names" {
  description = "The names of the ECS services"
  type        = list(string)
}

# CodeDeploy Role
resource "aws_iam_role" "codedeploy" {
  name = "${var.app_name}-${var.environment}-codedeploy-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "codedeploy.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "${var.app_name}-${var.environment}-codedeploy-role"
    Environment = var.environment
  }
}

resource "aws_iam_role_policy_attachment" "codedeploy" {
  role       = aws_iam_role.codedeploy.name
  policy_arn = "arn:aws:iam::aws:policy/AWSCodeDeployRoleForECS"
}

# CodeDeploy Application - API v1
resource "aws_codedeploy_app" "api_v1" {
  name             = "${var.app_name}-v1-${var.environment}"
  compute_platform = "ECS"

  tags = {
    Name        = "${var.app_name}-v1-${var.environment}"
    Environment = var.environment
  }
}

# CodeDeploy Deployment Group - API v1
resource "aws_codedeploy_deployment_group" "api_v1" {
  app_name               = aws_codedeploy_app.api_v1.name
  deployment_group_name  = "${var.app_name}-v1-${var.environment}"
  deployment_config_name = "CodeDeployDefault.ECSAllAtOnce"
  service_role_arn       = aws_iam_role.codedeploy.arn

  auto_rollback_configuration {
    enabled = true
    events  = ["DEPLOYMENT_FAILURE"]
  }

  blue_green_deployment_config {
    deployment_ready_option {
      action_on_timeout = "CONTINUE_DEPLOYMENT"
    }

    terminate_blue_instances_on_deployment_success {
      action                           = "TERMINATE"
      termination_wait_time_in_minutes = 5
    }
  }

  deployment_style {
    deployment_option = "WITH_TRAFFIC_CONTROL"
    deployment_type   = "BLUE_GREEN"
  }

  ecs_service {
    cluster_name = var.ecs_cluster_name
    service_name = var.ecs_service_names[0]
  }

  tags = {
    Name        = "${var.app_name}-v1-${var.environment}"
    Environment = var.environment
  }
}

# Outputs
output "codedeploy_app_names" {
  value = [
    aws_codedeploy_app.api_v1.name
  ]
}

output "codedeploy_group_names" {
  value = [
    aws_codedeploy_deployment_group.api_v1.deployment_group_name
  ]
}
