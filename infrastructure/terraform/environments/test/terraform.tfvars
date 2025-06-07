environment = "test"
aws_region  = "us-east-1"

# ECS configuration
task_cpu    = 256
task_memory = 512
min_capacity = 1
max_capacity = 1

# KMS key for encryption
kms_key_id = "arn:aws:kms:us-east-1:0987654321:key/1234abcd-12ab-34cd-56"

# SSL certificate for HTTPS
certificate_arn = "arn:aws:acm:us-east-1:0987654321:certificate/abcd1234-ab12-cd34-ef56-abcdef123456"

# Cost optimization features
use_fargate_spot = true
enable_scheduled_scaling = true
business_hours_start = "13:00"  # 9:00 AM EST/EDT
business_hours_end = "01:00"    # 9:00 PM EST/EDT