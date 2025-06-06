# Security Documentation

This comprehensive security documentation outlines the multi-layered security approach implemented in the FastAPI Bootstrap project. It is designed for Solutions Architects, DevOps Engineers, and Software Engineers who need to understand, implement, and maintain the security posture of the application.

## Security Architecture Overview

The FastAPI Bootstrap project implements a defense-in-depth security strategy with multiple layers of protection:

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│                        AWS WAF (Shield)                         │
│                                                                 │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│                   Application Load Balancer                     │
│                   (TLS Termination, HTTPS)                      │
│                                                                 │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                         VPC Boundary                            │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                 Public Subnet (DMZ)                      │   │
│  └────────────────────────────┬────────────────────────────┘   │
│                               │                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                 Private Subnet                          │   │
│  │   ┌──────────────────────────────────────────────┐     │   │
│  │   │          ECS Fargate Containers              │     │   │
│  │   │     (FastAPI App + Security Middleware)      │     │   │
│  │   └──────────────────┬───────────────────────────┘     │   │
│  │                      │                                  │   │
│  └──────────────────────┼──────────────────────────────────┘   │
│                         │                                      │
└─────────────────────────┼──────────────────────────────────────┘
                          │
                          ▼
┌───────────────────────────────────────────────────────────────┐
│                    Data Protection Layer                       │
│  ┌───────────────┐  ┌────────────────┐  ┌────────────────┐    │
│  │      KMS      │  │  Parameter     │  │    Database    │    │
│  │   Encryption  │  │     Store      │  │   Encryption   │    │
│  └───────────────┘  └────────────────┘  └────────────────┘    │
└───────────────────────────────────────────────────────────────┘
```

## Network Security

The application is deployed within a carefully designed Virtual Private Cloud (VPC) with the following security features:

- **Public Subnets**: Only contain the Application Load Balancer, creating a demilitarized zone (DMZ)
- **Private Subnets**: Contain the ECS tasks and other resources, completely isolated from direct internet access
- **Network ACLs**: Provide stateless filtering of traffic at the subnet level
- **Security Groups**: Implement stateful, fine-grained traffic control between components:
  - **ALB Security Group**: Only allows HTTP/HTTPS traffic from the internet
  - **ECS Security Group**: Only allows traffic from the ALB on the application port
  - **Database Security Group**: Only allows traffic from the ECS tasks on the database port
- **NAT Gateway**: Allows outbound internet access from private subnets while preventing inbound connections
- **VPC Endpoints**: Provides private connectivity to AWS services without traversing the internet

## Web Application Firewall (WAF)

AWS WAF is configured as the first line of defense to protect the application from common web exploits and attacks:

### AWS Managed Rules

Pre-configured rule sets that protect against common threats:

- **Core Rule Set (CRS)**: Provides protection against OWASP Top 10 vulnerabilities including:
  - SQL Injection
  - Cross-Site Scripting (XSS)
  - Local/Remote File Inclusion
  - HTTP Protocol Violations
  - Bad Input Validation

- **Known Bad Inputs**: Protection against known malicious inputs and attack patterns

- **Admin Protection**: Special protection for administrative interfaces and paths

### Custom WAF Rules

Custom WAF rules are implemented to provide application-specific protection:

- **Rate-Based Rules**: Limit the number of requests from any single IP address (e.g., 1000 requests per 5-minute period)
- **Geo-Match Rules**: Optional rules to restrict access from specific geographic locations
- **Size Constraint Rules**: Prevent oversized requests that could lead to DoS conditions
- **Custom Pattern Rules**: Additional protection based on application-specific patterns

### WAF Logging and Monitoring

- **CloudWatch Logs**: All WAF events are logged to CloudWatch
- **CloudWatch Metrics**: Custom metrics track blocked requests and rule triggers
- **CloudWatch Alarms**: Alerts are configured for unusual patterns

## IAM Least Privilege

Identity and Access Management (IAM) roles and policies are designed following the principle of least privilege:

### Service-Specific IAM Roles

- **ECS Task Execution Role**: Limited permissions to:
  - Pull container images from ECR
  - Write logs to CloudWatch
  - Read secrets from SSM Parameter Store

- **ECS Task Role**: Runtime permissions for the application limited to:
  - Reading specific SSM parameters
  - Writing application logs
  - Accessing specific AWS services required by the application

- **CodeDeploy Role**: Limited to:
  - Deploying to specific ECS services
  - Reading from specific S3 buckets
  - Invoking specific Lambda functions

- **Lambda Execution Roles**: Specific permissions for deployment hooks:
  - Updating CodeDeploy lifecycle events
  - Accessing ECS services
  - Running database migrations

### Resource-Based Policies

Access is restricted to specific resources using naming conventions and path-based policies:

- **SSM Parameters**: Access limited to parameters under `/${app_name}/${environment}/`
- **CloudWatch Logs**: Access limited to log groups under `/ecs/${app_name}-${environment}`
- **S3 Buckets**: Access limited to specific bucket paths
- **KMS Keys**: Access limited to specific keys by alias

### IAM Policy Examples

Example of a least-privilege ECS task role policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ssm:GetParameters",
        "ssm:GetParameter"
      ],
      "Resource": "arn:aws:ssm:*:*:parameter/fastapi-bootstrap/${environment}/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "kms:Decrypt"
      ],
      "Resource": "${kms_key_arn}"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:log-group:/ecs/fastapi-bootstrap-${environment}/*"
    }
  ]
}
```

## Secure Configuration Management

Sensitive configuration is managed securely using AWS Systems Manager Parameter Store, providing centralized and encrypted storage for configuration data:

### Parameter Store Structure

Parameters are organized hierarchically by application and environment:

```
/fastapi-bootstrap/
├── dev/
│   ├── database/
│   │   ├── url
│   │   ├── username
│   │   └── password
│   └── api/
│       ├── secret_key
│       └── api_tokens
├── test/
│   └── ...
└── prod/
    └── ...
```
- **Access Control**: IAM policies restrict access to specific parameters
- **No Hardcoded Secrets**: Application retrieves secrets at runtime

Example parameter hierarchy:
```
/fastapi-bootstrap/dev/database/url
/fastapi-bootstrap/dev/api/secret_key
```

## Encryption

Data encryption is implemented at multiple levels:

- **Data at Rest**:
  - CloudWatch Logs: Encrypted with KMS
  - SSM Parameters: Encrypted with KMS
  - S3 (Terraform state): Server-side encryption

- **Data in Transit**:
  - HTTPS for all external traffic
  - VPC for internal traffic

## HTTPS Configuration

All traffic to the application is served over HTTPS:

- **SSL/TLS Certificates**: Managed through AWS Certificate Manager
- **HTTP to HTTPS Redirection**: Automatic redirection of HTTP requests
- **Modern TLS Policy**: Using ELBSecurityPolicy-2016-08 for strong encryption

## Monitoring and Alerting

Security monitoring is implemented through:

- **CloudWatch Alarms**: Alerts for suspicious activity
- **WAF Metrics**: Tracking of blocked requests
- **CloudWatch Dashboard**: Visualization of security metrics

## Best Practices for Developers

When extending the application, follow these security best practices:

1. **Never store secrets in code or environment variables**
   - Use SSM Parameter Store for all secrets

2. **Validate all user input**
   - Implement input validation at the API level

3. **Follow the principle of least privilege**
   - Request only the permissions your code needs

4. **Keep dependencies updated**
   - Regularly update dependencies to patch security vulnerabilities

5. **Enable security scanning in CI/CD**
   - Add security scanning tools to your CI/CD pipeline

## Security Compliance

The infrastructure is designed to help meet common compliance requirements:

- **Encryption**: Helps meet requirements for data protection
- **Access Control**: Helps meet requirements for access management
- **Logging**: Helps meet requirements for audit trails
- **Network Isolation**: Helps meet requirements for network security

## Future Security Enhancements

Potential security enhancements for future versions:

1. **AWS Security Hub Integration**: Centralized security management
2. **GuardDuty Integration**: Threat detection
3. **AWS Config**: Configuration compliance monitoring
4. **VPC Flow Logs**: Network traffic monitoring
5. **Enhanced WAF Rules**: Additional custom rules for specific threats