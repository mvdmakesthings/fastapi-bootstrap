# Blue/Green Deployment Configuration

This document outlines the blue/green deployment strategy implemented in this project for AWS ECS services.

## Overview

Blue/green deployment is a technique that reduces downtime and risk by running two identical production environments called Blue and Green. At any time, only one of the environments is live, serving all production traffic. The other environment remains idle.

## Implementation Details

### AppSpec Files

The AppSpec files (`.aws/appspec-v1-*.yaml`) define how CodeDeploy should handle the deployment:

- **version**: Must be set to "0.0" for ECS deployments
- **Resources**: Defines the ECS service properties
- **Hooks**: Lambda functions that run at various stages of deployment

### Key Components

1. **NetworkConfiguration**: Required for tasks using awsvpc network mode
2. **LoadBalancerInfo**: Specifies the container and port for routing traffic
3. **Hooks**: Validation functions at different deployment stages

### Deployment Hooks

Our deployment process includes the following hooks:

- **BeforeInstall**: Validates prerequisites before deployment
- **AfterInstall**: Validates the deployment was successful
- **AfterAllowTestTraffic**: Validates the application with test traffic
- **BeforeAllowTraffic**: Runs database migrations before production traffic
- **AfterAllowTraffic**: Final validation after production traffic is routed

## Health Checks

The application provides two health check endpoints:

- `/health`: Basic health check that returns the application status
- `/ready`: Readiness check used during deployment to verify the application is ready to receive traffic

## Best Practices

1. **Deployment Configuration**: Using `CodeDeployDefault.ECSAllAtOnce` for development environments
2. **Auto Rollback**: Configured to automatically roll back on deployment failures
3. **Termination Settings**: Blue instances are terminated 5 minutes after successful deployment
4. **Health Check Configuration**: Using the `/ready` endpoint with appropriate intervals

## Considerations for ECS Blue/Green Deployments

1. **Network Configuration**: Must be specified in the AppSpec file for tasks using awsvpc network mode
2. **Task Definition Immutability**: Task definitions are immutable; each deployment creates a new revision
3. **Container Health Checks**: Configured with appropriate intervals and timeouts
4. **Deployment Tracking**: Using environment variables to track deployment IDs
5. **Rollback Strategy**: Automatic rollback on deployment failures

## References

- [AWS CloudFormation User Guide - Blue/Green Considerations](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/blue-green-considerations.html)
- [AWS CodeDeploy User Guide - AppSpec File Reference](https://docs.aws.amazon.com/codedeploy/latest/userguide/reference-appspec-file.html)