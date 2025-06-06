# Cost Optimization Guide

This document outlines the cost optimization strategies implemented in the FastAPI Bootstrap project.

## Implemented Cost Optimizations

### 1. Single NAT Gateway

**Savings: Significant (up to $32/month per NAT Gateway eliminated)**

- We've configured the VPC to use a single NAT Gateway across all environments.
- This reduces costs while maintaining outbound internet connectivity for private subnets.
- Trade-off: Reduced availability in case of AZ failure, but acceptable for most workloads.

### 2. AWS Fargate Spot for Non-Production

**Savings: Up to 70% compared to regular Fargate pricing**

- Dev and test environments use Fargate Spot for cost savings.
- Spot instances can be interrupted with 2-minute notification.
- Production continues to use regular Fargate for reliability.

### 3. Scheduled Scaling for Non-Business Hours

**Savings: 50-70% of compute costs during off-hours**

- Services automatically scale down to zero during non-business hours.
- Configured to scale back up before business hours begin.
- Customizable business hours in terraform.tfvars files.

## Configuration Options

The following variables can be set in your environment's `terraform.tfvars` file:

```hcl
# Cost optimization features
use_fargate_spot = true                # Enable Fargate Spot (non-prod only)
enable_scheduled_scaling = true        # Enable scaling to zero during off-hours
business_hours_start = "13:00"         # 9:00 AM EST/EDT in UTC
business_hours_end = "01:00"           # 9:00 PM EST/EDT in UTC
```

## Additional Cost Optimization Recommendations

1. **Right-size your tasks**: Review CloudWatch metrics to determine if your tasks are over-provisioned.

2. **Application Performance Monitoring**: Use AWS X-Ray to identify performance bottlenecks that might require more resources.

3. **Reserved Instances for Production**: For predictable workloads, consider Savings Plans for Fargate.

4. **CloudWatch Logs Retention**: Adjust log retention periods based on compliance requirements.

5. **Cost Explorer**: Regularly review AWS Cost Explorer to identify unexpected costs.

## Monitoring Cost Optimizations

To monitor the effectiveness of these cost optimizations:

1. Set up AWS Budgets to track spending.
2. Create CloudWatch dashboards to monitor resource utilization.
3. Review AWS Cost Explorer monthly to identify trends and opportunities.

## References

- [AWS Fargate Pricing](https://aws.amazon.com/fargate/pricing/)
- [AWS Fargate Spot](https://aws.amazon.com/blogs/aws/aws-fargate-spot-now-generally-available/)
- [AWS NAT Gateway Pricing](https://aws.amazon.com/vpc/pricing/)