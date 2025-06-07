variable "app_name" {
  description = "The name of the application"
  type        = string
}

variable "environment" {
  description = "The deployment environment (dev, test, prod)"
  type        = string
}

resource "aws_ecr_repository" "main" {
  name                 = "${var.app_name}"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name        = "${var.app_name}"
    Environment = var.environment
  }
}

resource "aws_ecr_lifecycle_policy" "main" {
  repository = aws_ecr_repository.main.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 10 images"
        selection = {
          tagStatus     = "any"
          countType     = "imageCountMoreThan"
          countNumber   = 10
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

output "repository_url" {
  value = aws_ecr_repository.main.repository_url
}

output "repository_name" {
  value = aws_ecr_repository.main.name
}
