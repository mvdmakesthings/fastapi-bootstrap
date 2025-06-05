environment = "prod"
aws_region  = "us-east-1"

# ECS configuration
task_cpu    = 1024
task_memory = 2048
min_capacity = 1
max_capacity = 2

# CHANGE THIS KEY
kms_key_id = "arn:aws:kms:us-east-1:0987654321:key/1234abcd-12ab-34cd-56"