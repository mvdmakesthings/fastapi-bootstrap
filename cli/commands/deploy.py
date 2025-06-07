"""
Deployment commands for the FastAPI application.
"""

import os
import subprocess
import sys

import click

from cli.utils.aws import get_aws_session, get_ecr_repository_uri
from cli.utils.config import Config


@click.group(name="deploy")
def deploy_cmd():
    """Deploy the FastAPI application to AWS."""
    pass


@deploy_cmd.command(name="app")
@click.option(
    "--env",
    required=True,
    type=click.Choice(["dev", "test", "prod"]),
    help="Environment to deploy to",
)
@click.option("--aws-profile", default=None, help="AWS profile to use")
@click.option("--aws-region", default=None, help="AWS region to deploy to")
@click.option("--image-tag", default=None, help="Docker image tag to deploy")
@click.option("--skip-build", is_flag=True, help="Skip building the Docker image")
def deploy_application(env, aws_profile, aws_region, image_tag, skip_build):
    """Deploy the FastAPI application to AWS ECS."""
    # Load configuration
    config = Config()
    if not config.config.get("environments", {}).get(env):
        click.echo(
            f"❌ Environment {env} not initialized. Run 'fastapi-bootstrap init project' first."
        )
        sys.exit(1)

    env_config = config.config["environments"][env]

    # Use parameters if provided, otherwise use config values
    aws_profile = aws_profile or env_config.get("aws_profile", "default")
    aws_region = aws_region or env_config.get("aws_region", "us-east-1")
    org_name = env_config.get("org_name")

    if not org_name:
        click.echo("❌ Organization name not found in config.")
        sys.exit(1)

    # Generate image tag if not provided
    if not image_tag:
        # Use timestamp as image tag if not provided
        from datetime import datetime

        image_tag = datetime.now().strftime("%Y%m%d%H%M%S")

    click.echo(f"Deploying application to {env} environment...")
    click.echo(f"AWS Profile: {aws_profile}")
    click.echo(f"AWS Region: {aws_region}")
    click.echo(f"Image Tag: {image_tag}")

    # Set environment variables for AWS SDK
    os.environ["AWS_PROFILE"] = aws_profile
    os.environ["AWS_REGION"] = aws_region

    # Get AWS session
    session = get_aws_session(profile_name=aws_profile, region_name=aws_region)

    # Get ECR repository URI
    repository_name = f"{org_name}-{env}-api"
    repository_uri = get_ecr_repository_uri(repository_name, session)

    if not repository_uri:
        click.echo(
            f"❌ ECR repository {repository_name} not found. Make sure infrastructure is deployed."
        )
        sys.exit(1)

    # Build and push Docker image if not skipped
    if not skip_build:
        click.echo("Building Docker image...")

        # Build the Docker image
        try:
            dockerfile_path = "infrastructure/docker/Dockerfile"
            if env == "dev":
                dockerfile_path = "infrastructure/docker/Dockerfile.dev"
            elif env == "test":
                dockerfile_path = "infrastructure/docker/Dockerfile.test"

            subprocess.run(
                [
                    "docker",
                    "build",
                    "-t",
                    f"{repository_uri}:{image_tag}",
                    "-f",
                    dockerfile_path,
                    ".",
                ],
                check=True,
            )
            click.echo("✅ Docker image built successfully.")
        except subprocess.CalledProcessError as e:
            click.echo(f"❌ Failed to build Docker image: {e}")
            sys.exit(1)

        # Log in to ECR
        click.echo("Logging in to ECR...")
        try:
            ecr_login_command = subprocess.check_output(
                [
                    "aws",
                    "ecr",
                    "get-login-password",
                    "--region",
                    aws_region,
                    "--profile",
                    aws_profile,
                ],
                text=True,
            )
            subprocess.run(
                [
                    "docker",
                    "login",
                    "--username",
                    "AWS",
                    "--password-stdin",
                    f"{repository_uri.split('/')[0]}",
                ],
                input=ecr_login_command,
                text=True,
                check=True,
            )
            click.echo("✅ Logged in to ECR successfully.")
        except subprocess.CalledProcessError as e:
            click.echo(f"❌ Failed to log in to ECR: {e}")
            sys.exit(1)

        # Push the Docker image
        click.echo(f"Pushing Docker image to {repository_uri}:{image_tag}...")
        try:
            subprocess.run(
                ["docker", "push", f"{repository_uri}:{image_tag}"], check=True
            )
            click.echo("✅ Docker image pushed successfully.")
        except subprocess.CalledProcessError as e:
            click.echo(f"❌ Failed to push Docker image: {e}")
            sys.exit(1)

    # Update ECS service to use the new image
    click.echo("Updating ECS service...")
    try:
        # Get the ECS cluster and service names
        cluster_name = f"{org_name}-{env}-cluster"
        service_name = f"{org_name}-{env}-api-service"

        # Update the ECS service to use the new image
        ecs_client = session.client("ecs")

        # Get the current task definition
        response = ecs_client.describe_services(
            cluster=cluster_name, services=[service_name]
        )

        if not response["services"]:
            click.echo(
                f"❌ ECS service {service_name} not found in cluster {cluster_name}."
            )
            sys.exit(1)

        task_definition_arn = response["services"][0]["taskDefinition"]

        # Get the task definition details
        task_def_response = ecs_client.describe_task_definition(
            taskDefinition=task_definition_arn
        )

        # Create a new revision with the new image
        container_definitions = task_def_response["taskDefinition"][
            "containerDefinitions"
        ]
        for container in container_definitions:
            if container["name"] == f"{org_name}-{env}-api-container":
                container["image"] = f"{repository_uri}:{image_tag}"

        new_task_def_response = ecs_client.register_task_definition(
            family=task_def_response["taskDefinition"]["family"],
            taskRoleArn=task_def_response["taskDefinition"]["taskRoleArn"],
            executionRoleArn=task_def_response["taskDefinition"]["executionRoleArn"],
            networkMode=task_def_response["taskDefinition"]["networkMode"],
            containerDefinitions=container_definitions,
            volumes=task_def_response["taskDefinition"].get("volumes", []),
            placementConstraints=task_def_response["taskDefinition"].get(
                "placementConstraints", []
            ),
            requiresCompatibilities=task_def_response["taskDefinition"].get(
                "requiresCompatibilities", []
            ),
            cpu=task_def_response["taskDefinition"].get("cpu"),
            memory=task_def_response["taskDefinition"].get("memory"),
        )

        new_task_definition_arn = new_task_def_response["taskDefinition"][
            "taskDefinitionArn"
        ]

        # Update the service to use the new task definition
        ecs_client.update_service(
            cluster=cluster_name,
            service=service_name,
            taskDefinition=new_task_definition_arn,
            forceNewDeployment=True,
        )

        click.echo(
            f"✅ ECS service updated successfully with new image: {repository_uri}:{image_tag}"
        )
    except Exception as e:
        click.echo(f"❌ Failed to update ECS service: {e}")
        sys.exit(1)

    click.echo(f"\n🚀 Application deployed to {env} environment successfully!")
    click.echo("\nTo monitor the deployment, use:")
    click.echo(f"  fastapi-bootstrap deploy status --env {env}")


@deploy_cmd.command(name="status")
@click.option(
    "--env",
    required=True,
    type=click.Choice(["dev", "test", "prod"]),
    help="Environment to check",
)
@click.option("--aws-profile", default=None, help="AWS profile to use")
@click.option("--aws-region", default=None, help="AWS region")
def check_deployment_status(env, aws_profile, aws_region):
    """Check the status of the application deployment."""
    # Load configuration
    config = Config()
    if not config.config.get("environments", {}).get(env):
        click.echo(f"❌ Environment {env} not initialized.")
        sys.exit(1)

    env_config = config.config["environments"][env]

    # Use parameters if provided, otherwise use config values
    aws_profile = aws_profile or env_config.get("aws_profile", "default")
    aws_region = aws_region or env_config.get("aws_region", "us-east-1")
    org_name = env_config.get("org_name")

    if not org_name:
        click.echo("❌ Organization name not found in config.")
        sys.exit(1)

    click.echo(f"Checking deployment status in {env} environment...")

    # Set environment variables for AWS SDK
    os.environ["AWS_PROFILE"] = aws_profile
    os.environ["AWS_REGION"] = aws_region

    # Get AWS session
    session = get_aws_session(profile_name=aws_profile, region_name=aws_region)

    try:
        # Get the ECS cluster and service names
        cluster_name = f"{org_name}-{env}-cluster"
        service_name = f"{org_name}-{env}-api-service"

        # Get the service status
        ecs_client = session.client("ecs")
        response = ecs_client.describe_services(
            cluster=cluster_name, services=[service_name]
        )

        if not response["services"]:
            click.echo(
                f"❌ ECS service {service_name} not found in cluster {cluster_name}."
            )
            sys.exit(1)

        service = response["services"][0]

        # Display service status
        click.echo(f"\nService: {service['serviceName']}")
        click.echo(f"Status: {service['status']}")
        click.echo(f"Task Definition: {service['taskDefinition']}")
        click.echo(f"Desired Count: {service['desiredCount']}")
        click.echo(f"Running Count: {service['runningCount']}")
        click.echo(f"Pending Count: {service['pendingCount']}")

        # Display deployments
        click.echo("\nDeployments:")
        for deployment in service["deployments"]:
            click.echo(f"  ID: {deployment['id']}")
            click.echo(f"  Status: {deployment['status']}")
            click.echo(f"  Task Definition: {deployment['taskDefinition']}")
            click.echo(f"  Desired Count: {deployment['desiredCount']}")
            click.echo(f"  Running Count: {deployment['runningCount']}")
            click.echo(f"  Pending Count: {deployment['pendingCount']}")
            click.echo(f"  Created At: {deployment['createdAt']}")
            click.echo(f"  Updated At: {deployment['updatedAt']}")
            click.echo("")

        # Display events
        click.echo("Recent Events:")
        for event in service["events"][:5]:
            click.echo(f"  {event['createdAt']}: {event['message']}")

    except Exception as e:
        click.echo(f"❌ Failed to check deployment status: {e}")
        sys.exit(1)
