"""
Constants and configuration values for infrastructure.
"""

from enum import Enum


class Environment(str, Enum):
    """Environment types."""

    DEV = "dev"
    TEST = "test"
    PROD = "prod"


# Default VPC configuration
DEFAULT_VPC_CONFIG = {
    "cidr": "10.0.0.0/16",
    "max_azs": 2,
    "nat_gateways": 1,
}

# ECS configuration by environment
ECS_CONFIG = {
    Environment.DEV: {
        "desired_count": 1,
        "cpu": 256,
        "memory_limit_mib": 512,
        "auto_scaling_min_capacity": 1,
        "auto_scaling_max_capacity": 2,
    },
    Environment.TEST: {
        "desired_count": 2,
        "cpu": 512,
        "memory_limit_mib": 1024,
        "auto_scaling_min_capacity": 2,
        "auto_scaling_max_capacity": 4,
    },
    Environment.PROD: {
        "desired_count": 2,
        "cpu": 1024,
        "memory_limit_mib": 2048,
        "auto_scaling_min_capacity": 2,
        "auto_scaling_max_capacity": 10,
    },
}

# SSM parameter paths
SSM_PATHS = {
    "database_url": "/fastapi-bootstrap/{env}/database/url",
    "api_secret_key": "/fastapi-bootstrap/{env}/api/secret_key",
}

# Default tags
DEFAULT_TAGS = {
    "Project": "FastAPI-Bootstrap",
    "ManagedBy": "CDK",
}


# Removal policies by environment
def get_removal_policy(env: Environment):
    """Get the removal policy for the specified environment."""
    from aws_cdk import RemovalPolicy

    if env == Environment.PROD:
        return RemovalPolicy.RETAIN
    else:
        return RemovalPolicy.DESTROY
