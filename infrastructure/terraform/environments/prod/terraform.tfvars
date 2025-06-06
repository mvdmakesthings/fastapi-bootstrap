environment = "prod"
aws_region  = "us-east-1"

# ECS configuration
task_cpu    = 1024
task_memory = 2048
min_capacity = 1
max_capacity = 2

# KMS key for encryption
kms_key_id = "arn:aws:kms:us-east-1:0987654321:key/1234abcd-12ab-34cd-56"

# SSL certificate for HTTPS
certificate_arn = "arn:aws:acm:us-east-1:0987654321:certificate/abcd1234-ab12-cd34-ef56-abcdef123456"

# Cost optimization features - disabled for production
use_fargate_spot = false
enable_scheduled_scaling = false