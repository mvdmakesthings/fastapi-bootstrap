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

variable "public_subnets" {
  description = "The public subnet IDs"
  type        = list(string)
}

variable "ecs_task_execution_role" {
  description = "The ARN of the ECS task execution role"
  type        = string
}

variable "ecs_task_role" {
  description = "The ARN of the ECS task role"
  type        = string
}

variable "security_group_id" {
  description = "The security group ID for the ECS service"
  type        = string
}

variable "ecr_repository_url" {
  description = "The URL of the ECR repository"
  type        = string
}

variable "task_cpu" {
  description = "The CPU units for the task"
  type        = number
  default     = 256
}

variable "task_memory" {
  description = "The memory for the task in MiB"
  type        = number
  default     = 512
}

variable "min_capacity" {
  description = "The minimum number of tasks"
  type        = number
  default     = 1
}

variable "max_capacity" {
  description = "The maximum number of tasks"
  type        = number
  default     = 10
}

variable "container_port" {
  description = "The port the container listens on"
  type        = number
  default     = 8000
}

# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "${var.app_name}-${var.environment}"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Name        = "${var.app_name}-${var.environment}"
    Environment = var.environment
  }
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "main" {
  name              = "/ecs/${var.app_name}-${var.environment}"
  retention_in_days = 30

  tags = {
    Name        = "${var.app_name}-${var.environment}"
    Environment = var.environment
  }
}

# ALB
resource "aws_lb" "main" {
  name               = "${var.app_name}-${var.environment}"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [var.security_group_id]
  subnets            = var.public_subnets

  enable_deletion_protection = var.environment == "prod" ? true : false

  tags = {
    Name        = "${var.app_name}-${var.environment}"
    Environment = var.environment
  }
}

# ALB Target Groups for Blue/Green deployment - API v1
resource "aws_lb_target_group" "blue_v1" {
  name     = "${var.app_name}-blue-v1-${var.environment}"
  port     = var.container_port
  protocol = "HTTP"
  vpc_id   = var.vpc_id
  target_type = "ip"

  health_check {
    enabled             = true
    interval            = 30
    path                = "/health"
    port                = "traffic-port"
    healthy_threshold   = 3
    unhealthy_threshold = 3
    timeout             = 5
    protocol            = "HTTP"
    matcher             = "200"
  }

  tags = {
    Name        = "${var.app_name}-blue-v1-${var.environment}"
    Environment = var.environment
  }
}

resource "aws_lb_target_group" "green_v1" {
  name     = "${var.app_name}-green-v1-${var.environment}"
  port     = var.container_port
  protocol = "HTTP"
  vpc_id   = var.vpc_id
  target_type = "ip"

  health_check {
    enabled             = true
    interval            = 30
    path                = "/health"
    port                = "traffic-port"
    healthy_threshold   = 3
    unhealthy_threshold = 3
    timeout             = 5
    protocol            = "HTTP"
    matcher             = "200"
  }

  tags = {
    Name        = "${var.app_name}-green-v1-${var.environment}"
    Environment = var.environment
  }
}

# ALB Listener
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type = "redirect"

    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}

resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.main.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-2016-08"
  # certificate_arn   = var.certificate_arn # You would need to provide a certificate ARN

  default_action {
    type = "fixed-response"

    fixed_response {
      content_type = "text/plain"
      message_body = "Welcome to FastAPI Bootstrap"
      status_code  = "200"
    }
  }
}

# API v1 Listener Rule
resource "aws_lb_listener_rule" "api_v1" {
  listener_arn = aws_lb_listener.https.arn
  priority     = 10

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.blue_v1.arn
  }

  condition {
    path_pattern {
      values = ["/api/v1*"]
    }
  }
}


# ECS Task Definition - API v1
resource "aws_ecs_task_definition" "api_v1" {
  family                   = "${var.app_name}-v1-${var.environment}"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.task_cpu
  memory                   = var.task_memory
  execution_role_arn       = var.ecs_task_execution_role
  task_role_arn            = var.ecs_task_role

  container_definitions = jsonencode([{
    name      = "${var.app_name}-v1"
    image     = "${var.ecr_repository_url}:latest"
    essential = true

    portMappings = [{
      containerPort = var.container_port
      hostPort      = var.container_port
      protocol      = "tcp"
    }]

    environment = [
      { name = "ENVIRONMENT", value = var.environment }
    ]

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.main.name
        "awslogs-region"        = "us-east-1"
        "awslogs-stream-prefix" = "ecs-v1"
      }
    }

    healthCheck = {
      command     = ["CMD-SHELL", "curl -f http://localhost:${var.container_port}/health || exit 1"]
      interval    = 30
      timeout     = 5
      retries     = 3
      startPeriod = 60
    }
  }])

  tags = {
    Name        = "${var.app_name}-v1-${var.environment}"
    Environment = var.environment
  }
}

# ECS Service - API v1
resource "aws_ecs_service" "api_v1" {
  name            = "${var.app_name}-v1-${var.environment}"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.api_v1.arn
  desired_count   = var.min_capacity
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.private_subnets
    security_groups  = [var.security_group_id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.blue_v1.arn
    container_name   = "${var.app_name}-v1"
    container_port   = var.container_port
  }

  deployment_controller {
    type = "CODE_DEPLOY"
  }

  tags = {
    Name        = "${var.app_name}-v1-${var.environment}"
    Environment = var.environment
  }

  lifecycle {
    ignore_changes = [
      task_definition,
      load_balancer
    ]
  }
}


# Auto Scaling - API v1
resource "aws_appautoscaling_target" "api_v1" {
  service_namespace  = "ecs"
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.api_v1.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  min_capacity       = var.min_capacity
  max_capacity       = var.max_capacity
}

resource "aws_appautoscaling_policy" "api_v1_cpu" {
  name               = "${var.app_name}-v1-${var.environment}-cpu"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.api_v1.resource_id
  scalable_dimension = aws_appautoscaling_target.api_v1.scalable_dimension
  service_namespace  = aws_appautoscaling_target.api_v1.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value = 70.0
  }
}


# Outputs
output "cluster_name" {
  value = aws_ecs_cluster.main.name
}

output "service_names" {
  value = [
    aws_ecs_service.api_v1.name
  ]
}

output "task_definition_arns" {
  value = [
    aws_ecs_task_definition.api_v1.arn
  ]
}

output "alb_dns_name" {
  value = aws_lb.main.dns_name
}

output "blue_target_group_v1_name" {
  value = aws_lb_target_group.blue_v1.name
}

output "green_target_group_v1_name" {
  value = aws_lb_target_group.green_v1.name
}
