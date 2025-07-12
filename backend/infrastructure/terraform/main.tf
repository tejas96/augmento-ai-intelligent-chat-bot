# Terraform configuration for LangGraph Multimodal Chatbot

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Configure AWS Provider
provider "aws" {
  region = var.aws_region
}

# Variables
variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "langgraph-chatbot"
}

variable "s3_bucket_name" {
  description = "S3 bucket name for image storage"
  type        = string
  default     = "langgraph-chatbot-images"
}

# Data sources
data "aws_caller_identity" "current" {}

# S3 Bucket for image storage
resource "aws_s3_bucket" "images" {
  bucket = "${var.s3_bucket_name}-${var.environment}"
  
  tags = {
    Name        = "${var.project_name}-images"
    Environment = var.environment
    Project     = var.project_name
  }
}

# S3 Bucket versioning
resource "aws_s3_bucket_versioning" "images" {
  bucket = aws_s3_bucket.images.id
  versioning_configuration {
    status = "Enabled"
  }
}

# S3 Bucket CORS configuration
resource "aws_s3_bucket_cors_configuration" "images" {
  bucket = aws_s3_bucket.images.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "PUT", "POST", "DELETE"]
    allowed_origins = ["*"]
    expose_headers  = ["ETag"]
    max_age_seconds = 3000
  }
}

# S3 Bucket public access block
resource "aws_s3_bucket_public_access_block" "images" {
  bucket = aws_s3_bucket.images.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# IAM Role for the application
resource "aws_iam_role" "app_role" {
  name = "${var.project_name}-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = [
            "lambda.amazonaws.com",
            "ecs-tasks.amazonaws.com",
            "ec2.amazonaws.com"
          ]
        }
      }
    ]
  })

  tags = {
    Name        = "${var.project_name}-role"
    Environment = var.environment
    Project     = var.project_name
  }
}

# IAM Policy for Bedrock access
resource "aws_iam_policy" "bedrock_policy" {
  name        = "${var.project_name}-bedrock-policy-${var.environment}"
  description = "Policy for Bedrock access"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream",
          "bedrock:GetModel",
          "bedrock:ListModels"
        ]
        Resource = [
          "arn:aws:bedrock:*:*:model/anthropic.claude-*",
          "arn:aws:bedrock:*:*:model/amazon.titan-*",
          "arn:aws:bedrock:*:*:model/stability.stable-diffusion-*"
        ]
      }
    ]
  })
}

# IAM Policy for S3 access
resource "aws_iam_policy" "s3_policy" {
  name        = "${var.project_name}-s3-policy-${var.environment}"
  description = "Policy for S3 access"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket",
          "s3:GetBucketLocation"
        ]
        Resource = [
          aws_s3_bucket.images.arn,
          "${aws_s3_bucket.images.arn}/*"
        ]
      }
    ]
  })
}

# IAM Policy for CloudWatch Logs
resource "aws_iam_policy" "logs_policy" {
  name        = "${var.project_name}-logs-policy-${var.environment}"
  description = "Policy for CloudWatch Logs access"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

# Attach policies to the role
resource "aws_iam_role_policy_attachment" "bedrock_policy_attachment" {
  role       = aws_iam_role.app_role.name
  policy_arn = aws_iam_policy.bedrock_policy.arn
}

resource "aws_iam_role_policy_attachment" "s3_policy_attachment" {
  role       = aws_iam_role.app_role.name
  policy_arn = aws_iam_policy.s3_policy.arn
}

resource "aws_iam_role_policy_attachment" "logs_policy_attachment" {
  role       = aws_iam_role.app_role.name
  policy_arn = aws_iam_policy.logs_policy.arn
}

# VPC for ECS deployment (optional)
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name        = "${var.project_name}-vpc"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name        = "${var.project_name}-igw"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Public subnets
resource "aws_subnet" "public" {
  count = 2

  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.${count.index + 1}.0/24"
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name        = "${var.project_name}-public-subnet-${count.index + 1}"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Route table for public subnets
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name        = "${var.project_name}-public-rt"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Route table association
resource "aws_route_table_association" "public" {
  count = length(aws_subnet.public)

  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# Security group for the application
resource "aws_security_group" "app" {
  name        = "${var.project_name}-sg"
  description = "Security group for the application"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.project_name}-sg"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Data source for availability zones
data "aws_availability_zones" "available" {
  state = "available"
}

# Outputs
output "s3_bucket_name" {
  description = "Name of the S3 bucket"
  value       = aws_s3_bucket.images.bucket
}

output "s3_bucket_arn" {
  description = "ARN of the S3 bucket"
  value       = aws_s3_bucket.images.arn
}

output "iam_role_arn" {
  description = "ARN of the IAM role"
  value       = aws_iam_role.app_role.arn
}

output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}

output "subnet_ids" {
  description = "IDs of the public subnets"
  value       = aws_subnet.public[*].id
}

output "security_group_id" {
  description = "ID of the security group"
  value       = aws_security_group.app.id
} 