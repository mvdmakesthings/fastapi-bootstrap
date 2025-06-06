# Cost Optimization Guide

This document outlines the cost optimization strategies implemented in the FastAPI Bootstrap project and provides guidance for Solutions Architects and DevOps Engineers on maximizing cost efficiency while maintaining performance and reliability.

## Executive Summary

The FastAPI Bootstrap project implements several cost optimization techniques that can reduce AWS infrastructure costs by up to 70% in non-production environments and 20-30% in production environments, while maintaining required performance and reliability characteristics.

## Implemented Cost Optimizations

### 1. Single NAT Gateway

**Savings: Significant (up to $32/month per NAT Gateway eliminated)**

- We've configured the VPC to use a single NAT Gateway across all environments instead of one per AZ.
- This reduces costs while maintaining outbound internet connectivity for private subnets.
- Trade-off: Reduced availability in case of AZ failure, but acceptable for most workloads.
- Implementation: Configured in the VPC module with `single_nat_gateway = true`.

### 2. AWS Fargate Spot for Non-Production

**Savings: Up to 70% compared to regular Fargate pricing**

- Dev and test environments use Fargate Spot for cost savings.
- Spot instances can be interrupted with 2-minute notification.
- Production continues to use regular Fargate for reliability.
- Implementation: Controlled via the `use_fargate_spot` variable in Terraform.
- Resilience: Application designed to handle instance termination gracefully.

### 3. Scheduled Scaling for Non-Business Hours

**Savings: 50-70% of compute costs during off-hours**

- Services automatically scale down to zero during non-business hours.
- Configured to scale back up before business hours begin.
- Customizable business hours in terraform.tfvars files.
- Implementation: Uses Application Auto Scaling with scheduled actions.
- Warm-up period: Services are configured to start 30 minutes before business hours.

### 4. CloudWatch Logs Retention

**Savings: Variable depending on log volume**

- Log retention periods are configurable based on environment.
- Dev/test environments: 7 days retention by default.
- Production: 30 days retention by default (adjustable per compliance requirements).
- Implementation: Controlled via the `log_retention_days` variable.

### 5. Right-sized Container Resources

**Savings: 20-40% of compute costs**

- Container CPU and memory allocations are optimized based on application requirements.
- Separate configurations for different environments.
- Implementation: Controlled via `task_cpu` and `task_memory` variables.

## Configuration Options

The following variables can be set in your environment's `terraform.tfvars` file:

```hcl
# Cost optimization features
use_fargate_spot = true                # Enable Fargate Spot (non-prod only)
enable_scheduled_scaling = true        # Enable scaling to zero during off-hours
business_hours_start = "13:00"         # 9:00 AM EST/EDT in UTC
business_hours_end = "01:00"           # 9:00 PM EST/EDT in UTC
log_retention_days = 7                 # Log retention period in days
task_cpu = 256                         # Task CPU units (1024 = 1 vCPU)
task_memory = 512                      # Task memory in MB
enable_alb_access_logs = false         # Disable ALB access logs for cost savings
```

## Implementation Details

### Scheduled Scaling Configuration

Scheduled scaling is implemented using AWS Application Auto Scaling with scheduled actions:

```hcl
resource "aws_appautoscaling_scheduled_action" "scale_down" {
  count              = var.enable_scheduled_scaling ? 1 : 0
  name               = "${var.app_name}-${var.environment}-scale-down"
  service_namespace  = "ecs"
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.main.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  schedule           = "cron(0 ${var.business_hours_end} ? * MON-FRI *)"

  scalable_target_action {
    min_capacity = 0
    max_capacity = 0
  }
}

resource "aws_appautoscaling_scheduled_action" "scale_up" {
  count              = var.enable_scheduled_scaling ? 1 : 0
  name               = "${var.app_name}-${var.environment}-scale-up"
  service_namespace  = "ecs"
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.main.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  schedule           = "cron(30 ${var.business_hours_start} ? * MON-FRI *)"

  scalable_target_action {
    min_capacity = var.min_capacity
    max_capacity = var.max_capacity
  }
}
```

## Additional Cost Optimization Recommendations

1. **Right-size your tasks**: Review CloudWatch metrics to determine if your tasks are over-provisioned. Look for:
   - CPU utilization consistently below 40%
   - Memory utilization consistently below 60%
   - Adjust `task_cpu` and `task_memory` values accordingly

2. **Application Performance Monitoring**: Use AWS X-Ray to identify performance bottlenecks that might require more resources:
   - Analyze trace data to find slow API endpoints
   - Look for inefficient database queries
   - Identify external service dependencies that might be optimized

3. **Reserved Instances for Production**: For predictable workloads, consider:
   - Savings Plans for Fargate (up to 50% savings)
   - 1-year or 3-year commitments based on confidence in workload stability
   - Partial coverage (e.g., 70% of baseline capacity) to maintain flexibility

4. **CloudWatch Logs Optimization**:
   - Adjust log retention periods based on compliance requirements
   - Use log filter patterns to reduce noise
   - Consider CloudWatch Logs Insights for efficient log analysis

5. **Cost Explorer Strategies**:
   - Set up cost allocation tags to track expenses by feature/team
   - Create custom reports for tracking specific service costs
   - Enable AWS Cost Anomaly Detection for unexpected cost spikes

## Monitoring Cost Optimizations

To monitor the effectiveness of these cost optimizations:

1. **AWS Budgets**:
   - Set up monthly budget alerts at 50%, 80%, and 100% thresholds
   - Create separate budgets for each environment
   - Track costs by service and by tag

2. **CloudWatch Dashboards**:
   - Monitor resource utilization metrics (CPU, memory, network)
   - Track scaling activities and instance counts
   - Visualize cost metrics alongside performance metrics

3. **AWS Cost Explorer**:
   - Review monthly to identify trends and opportunities
   - Use "Daily" view to identify patterns and anomalies
   - Compare months to track optimization progress

4. **Cost Impact Analysis**:
   - Before deploying new features, estimate cost impact
   - Conduct post-implementation cost reviews
   - Document cost savings from optimization efforts

## Disaster Recovery Considerations

Cost optimizations should not compromise disaster recovery capabilities:

- Single NAT Gateway: Consider adding a second NAT Gateway in critical environments
- Fargate Spot: Ensure critical services have appropriate retry logic
- Scheduled scaling: Implement override mechanisms for emergency access during off-hours

## References

- [AWS Fargate Pricing](https://aws.amazon.com/fargate/pricing/)
- [AWS Fargate Spot](https://aws.amazon.com/blogs/aws/aws-fargate-spot-now-generally-available/)
- [AWS NAT Gateway Pricing](https://aws.amazon.com/vpc/pricing/)
- [AWS Application Auto Scaling](https://docs.aws.amazon.com/autoscaling/application/userguide/what-is-application-auto-scaling.html)
- [AWS Savings Plans](https://aws.amazon.com/savingsplans/)
- [AWS Cost Explorer](https://aws.amazon.com/aws-cost-management/aws-cost-explorer/)
- [AWS Budgets](https://aws.amazon.com/aws-cost-management/aws-budgets/)