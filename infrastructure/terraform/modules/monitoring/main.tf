variable "app_name" {
  description = "The name of the application"
  type        = string
}

variable "environment" {
  description = "The deployment environment (dev, test, prod)"
  type        = string
}

variable "cluster_name" {
  description = "The name of the ECS cluster"
  type        = string
}

variable "service_names" {
  description = "The names of the ECS services"
  type        = list(string)
}

variable "alb_arn_suffix" {
  description = "The ARN suffix of the ALB"
  type        = string
}

variable "alarm_email" {
  description = "Email address to send alarm notifications"
  type        = string
  default     = ""
}

# SNS Topic for Alarms
resource "aws_sns_topic" "alarms" {
  name = "${var.app_name}-${var.environment}-alarms"
  
  tags = {
    Name        = "${var.app_name}-${var.environment}-alarms"
    Environment = var.environment
  }
}

# Email subscription if provided
resource "aws_sns_topic_subscription" "email" {
  count     = var.alarm_email != "" ? 1 : 0
  topic_arn = aws_sns_topic.alarms.arn
  protocol  = "email"
  endpoint  = var.alarm_email
}

# CloudWatch Dashboard
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${var.app_name}-${var.environment}"
  
  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["AWS/ECS", "CPUUtilization", "ServiceName", var.service_names[0], "ClusterName", var.cluster_name]
          ]
          period = 300
          stat   = "Average"
          region = "us-east-1"
          title  = "ECS CPU Utilization"
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["AWS/ECS", "MemoryUtilization", "ServiceName", var.service_names[0], "ClusterName", var.cluster_name]
          ]
          period = 300
          stat   = "Average"
          region = "us-east-1"
          title  = "ECS Memory Utilization"
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["AWS/ApplicationELB", "RequestCount", "LoadBalancer", var.alb_arn_suffix]
          ]
          period = 300
          stat   = "Sum"
          region = "us-east-1"
          title  = "ALB Request Count"
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 6
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["AWS/ApplicationELB", "TargetResponseTime", "LoadBalancer", var.alb_arn_suffix]
          ]
          period = 300
          stat   = "Average"
          region = "us-east-1"
          title  = "ALB Response Time"
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 12
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["AWS/ApplicationELB", "HTTPCode_Target_4XX_Count", "LoadBalancer", var.alb_arn_suffix],
            ["AWS/ApplicationELB", "HTTPCode_Target_5XX_Count", "LoadBalancer", var.alb_arn_suffix]
          ]
          period = 300
          stat   = "Sum"
          region = "us-east-1"
          title  = "HTTP Error Codes"
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 12
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["AWS/WAFV2", "BlockedRequests", "WebACL", "${var.app_name}-${var.environment}-web-acl", "Region", "us-east-1"]
          ]
          period = 300
          stat   = "Sum"
          region = "us-east-1"
          title  = "WAF Blocked Requests"
        }
      }
    ]
  })
}

# High CPU Utilization Alarm
resource "aws_cloudwatch_metric_alarm" "high_cpu" {
  alarm_name          = "${var.app_name}-${var.environment}-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "This alarm monitors ECS service CPU utilization"
  alarm_actions       = [aws_sns_topic.alarms.arn]
  ok_actions          = [aws_sns_topic.alarms.arn]
  
  dimensions = {
    ClusterName = var.cluster_name
    ServiceName = var.service_names[0]
  }
  
  tags = {
    Name        = "${var.app_name}-${var.environment}-high-cpu"
    Environment = var.environment
  }
}

# High Memory Utilization Alarm
resource "aws_cloudwatch_metric_alarm" "high_memory" {
  alarm_name          = "${var.app_name}-${var.environment}-high-memory"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "MemoryUtilization"
  namespace           = "AWS/ECS"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "This alarm monitors ECS service memory utilization"
  alarm_actions       = [aws_sns_topic.alarms.arn]
  ok_actions          = [aws_sns_topic.alarms.arn]
  
  dimensions = {
    ClusterName = var.cluster_name
    ServiceName = var.service_names[0]
  }
  
  tags = {
    Name        = "${var.app_name}-${var.environment}-high-memory"
    Environment = var.environment
  }
}

# High 5XX Error Rate Alarm
resource "aws_cloudwatch_metric_alarm" "high_5xx" {
  alarm_name          = "${var.app_name}-${var.environment}-high-5xx"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "HTTPCode_Target_5XX_Count"
  namespace           = "AWS/ApplicationELB"
  period              = 300
  statistic           = "Sum"
  threshold           = 10
  alarm_description   = "This alarm monitors for high 5XX error rates"
  alarm_actions       = [aws_sns_topic.alarms.arn]
  ok_actions          = [aws_sns_topic.alarms.arn]
  
  dimensions = {
    LoadBalancer = var.alb_arn_suffix
  }
  
  tags = {
    Name        = "${var.app_name}-${var.environment}-high-5xx"
    Environment = var.environment
  }
}

# Outputs
output "dashboard_name" {
  value = aws_cloudwatch_dashboard.main.dashboard_name
}

output "alarm_topic_arn" {
  value = aws_sns_topic.alarms.arn
}