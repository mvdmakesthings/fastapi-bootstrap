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

variable "security_group_id" {
  description = "The security group ID for the database"
  type        = string
}

variable "kms_key_id" {
  description = "The KMS key ID for encryption"
  type        = string
}

variable "db_instance_class" {
  description = "The instance class for the RDS instance"
  type        = string
  default     = "db.t3.micro"
}

variable "db_allocated_storage" {
  description = "The allocated storage for the RDS instance in GB"
  type        = number
  default     = 20
}

variable "db_engine" {
  description = "The database engine to use"
  type        = string
  default     = "postgres"
}

variable "db_engine_version" {
  description = "The database engine version"
  type        = string
  default     = "13.7"
}

variable "db_name" {
  description = "The name of the database"
  type        = string
  default     = "app"
}

variable "db_username" {
  description = "The username for the database"
  type        = string
  default     = "postgres"
}

variable "db_password" {
  description = "The password for the database"
  type        = string
  sensitive   = true
}

variable "db_port" {
  description = "The port for the database"
  type        = number
  default     = 5432
}

variable "db_backup_retention_period" {
  description = "The backup retention period in days"
  type        = number
  default     = 7
}

variable "db_deletion_protection" {
  description = "Whether to enable deletion protection"
  type        = bool
  default     = false
}

variable "db_multi_az" {
  description = "Whether to enable multi-AZ deployment"
  type        = bool
  default     = false
}

# Database security group
resource "aws_security_group" "db" {
  name        = "${var.app_name}-${var.environment}-db-sg"
  description = "Security group for the database"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = var.db_port
    to_port         = var.db_port
    protocol        = "tcp"
    security_groups = [var.security_group_id]
    description     = "Allow traffic from ECS"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }

  tags = {
    Name        = "${var.app_name}-${var.environment}-db-sg"
    Environment = var.environment
  }
}

# Database subnet group
resource "aws_db_subnet_group" "main" {
  name       = "${var.app_name}-${var.environment}"
  subnet_ids = var.private_subnets

  tags = {
    Name        = "${var.app_name}-${var.environment}"
    Environment = var.environment
  }
}

# Database parameter group
resource "aws_db_parameter_group" "main" {
  name   = "${var.app_name}-${var.environment}"
  family = "${var.db_engine}${split(".", var.db_engine_version)[0]}"

  parameter {
    name  = "log_statement"
    value = "all"
  }

  parameter {
    name  = "log_min_duration_statement"
    value = "1000"
  }

  tags = {
    Name        = "${var.app_name}-${var.environment}"
    Environment = var.environment
  }
}

# Database instance
resource "aws_db_instance" "main" {
  identifier                  = "${var.app_name}-${var.environment}"
  engine                      = var.db_engine
  engine_version              = var.db_engine_version
  instance_class              = var.db_instance_class
  allocated_storage           = var.db_allocated_storage
  storage_type                = "gp2"
  storage_encrypted           = true
  kms_key_id                  = var.kms_key_id
  name                        = var.db_name
  username                    = var.db_username
  password                    = var.db_password
  port                        = var.db_port
  vpc_security_group_ids      = [aws_security_group.db.id]
  db_subnet_group_name        = aws_db_subnet_group.main.name
  parameter_group_name        = aws_db_parameter_group.main.name
  backup_retention_period     = var.db_backup_retention_period
  deletion_protection         = var.db_deletion_protection
  multi_az                    = var.db_multi_az
  skip_final_snapshot         = var.environment != "prod"
  final_snapshot_identifier   = var.environment == "prod" ? "${var.app_name}-${var.environment}-final" : null
  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]
  
  tags = {
    Name        = "${var.app_name}-${var.environment}"
    Environment = var.environment
  }
}

# Store database connection information in SSM Parameter Store
resource "aws_ssm_parameter" "db_host" {
  name        = "/${var.app_name}/${var.environment}/database/host"
  description = "Database host"
  type        = "String"
  value       = aws_db_instance.main.address
  
  tags = {
    Name        = "${var.app_name}-${var.environment}-db-host"
    Environment = var.environment
  }
}

resource "aws_ssm_parameter" "db_port" {
  name        = "/${var.app_name}/${var.environment}/database/port"
  description = "Database port"
  type        = "String"
  value       = tostring(var.db_port)
  
  tags = {
    Name        = "${var.app_name}-${var.environment}-db-port"
    Environment = var.environment
  }
}

resource "aws_ssm_parameter" "db_name" {
  name        = "/${var.app_name}/${var.environment}/database/name"
  description = "Database name"
  type        = "String"
  value       = var.db_name
  
  tags = {
    Name        = "${var.app_name}-${var.environment}-db-name"
    Environment = var.environment
  }
}

resource "aws_ssm_parameter" "db_username" {
  name        = "/${var.app_name}/${var.environment}/database/username"
  description = "Database username"
  type        = "String"
  value       = var.db_username
  
  tags = {
    Name        = "${var.app_name}-${var.environment}-db-username"
    Environment = var.environment
  }
}

resource "aws_ssm_parameter" "db_password" {
  name        = "/${var.app_name}/${var.environment}/database/password"
  description = "Database password"
  type        = "SecureString"
  value       = var.db_password
  key_id      = var.kms_key_id
  
  tags = {
    Name        = "${var.app_name}-${var.environment}-db-password"
    Environment = var.environment
  }
}

resource "aws_ssm_parameter" "db_url" {
  name        = "/${var.app_name}/${var.environment}/database/url"
  description = "Database connection URL"
  type        = "SecureString"
  value       = "postgresql://${var.db_username}:${var.db_password}@${aws_db_instance.main.address}:${var.db_port}/${var.db_name}"
  key_id      = var.kms_key_id
  
  tags = {
    Name        = "${var.app_name}-${var.environment}-db-url"
    Environment = var.environment
  }
}

# Outputs
output "db_instance_id" {
  description = "The ID of the RDS instance"
  value       = aws_db_instance.main.id
}

output "db_instance_address" {
  description = "The address of the RDS instance"
  value       = aws_db_instance.main.address
}

output "db_instance_endpoint" {
  description = "The endpoint of the RDS instance"
  value       = aws_db_instance.main.endpoint
}

output "db_instance_arn" {
  description = "The ARN of the RDS instance"
  value       = aws_db_instance.main.arn
}

output "db_security_group_id" {
  description = "The ID of the database security group"
  value       = aws_security_group.db.id
}

output "db_parameter_group_id" {
  description = "The ID of the database parameter group"
  value       = aws_db_parameter_group.main.id
}

output "db_subnet_group_id" {
  description = "The ID of the database subnet group"
  value       = aws_db_subnet_group.main.id
}

output "db_connection_url_parameter" {
  description = "The SSM parameter name for the database connection URL"
  value       = aws_ssm_parameter.db_url.name
}