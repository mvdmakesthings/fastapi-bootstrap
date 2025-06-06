"""
Main AWS CDK application entry point.
"""

import os

from aws_cdk import App, Environment, Tags

from fastapi_bootstrap.infrastructure.constants import DEFAULT_TAGS
from fastapi_bootstrap.infrastructure.stacks.api_stack import ApiStack
from fastapi_bootstrap.infrastructure.stacks.database_stack import DatabaseStack
from fastapi_bootstrap.infrastructure.stacks.monitoring_stack import MonitoringStack


def main():
    """Main CDK application."""
    # Get AWS account and region from environment variables
    account = os.environ.get("CDK_DEFAULT_ACCOUNT")
    region = os.environ.get("CDK_DEFAULT_REGION", "us-east-1")

    # Get environment name from environment variable
    env_name = os.environ.get("FASTAPI_ENV", "dev")

    # Organization name for resource naming
    org_name = os.environ.get("FASTAPI_ORG_NAME", "fastapi-bootstrap")

    # Create CDK app
    app = App()

    # Create AWS environment
    aws_env = Environment(account=account, region=region)

    # Create stacks
    # VPC and networking resources are created within the API stack
    api_stack = ApiStack(
        app,
        f"{org_name}-{env_name}-api",
        env=aws_env,
        env_name=env_name,
        org_name=org_name,
    )

    # Database stack depends on the VPC created in the API stack
    database_stack = DatabaseStack(
        app,
        f"{org_name}-{env_name}-database",
        vpc=api_stack.vpc,
        env=aws_env,
        env_name=env_name,
        org_name=org_name,
    )

    # Monitoring stack depends on resources from both API and database stacks
    MonitoringStack(
        app,
        f"{org_name}-{env_name}-monitoring",
        api_resources=api_stack.monitoring_resources,
        db_resources=database_stack.monitoring_resources,
        env=aws_env,
        env_name=env_name,
        org_name=org_name,
    )

    # Add default tags to all resources
    for key, value in DEFAULT_TAGS.items():
        Tags.of(app).add(key, value)

    # Add environment tag
    Tags.of(app).add("Environment", env_name)

    # Add organization tag
    Tags.of(app).add("Organization", org_name)

    # Synthesize CloudFormation template
    app.synth()


if __name__ == "__main__":
    main()
