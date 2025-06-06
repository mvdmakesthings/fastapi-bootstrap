"""
Infrastructure management commands using AWS CDK.
"""

import os
import subprocess
import sys

import click

from fastapi_bootstrap.cli.utils.config import Config


@click.group(name="infra")
def infra_cmd():
    """Manage AWS infrastructure using CDK."""
    pass


@infra_cmd.command(name="bootstrap")
@click.option("--aws-profile", default="default", help="AWS profile to use")
@click.option("--aws-region", default="us-east-1", help="AWS region to bootstrap")
def bootstrap_aws_environment(aws_profile, aws_region):
    """Bootstrap AWS environment for CDK deployments."""
    click.echo(
        f"Bootstrapping AWS environment in {aws_region} using profile {aws_profile}..."
    )

    # Set environment variables for AWS SDK and CDK
    os.environ["AWS_PROFILE"] = aws_profile
    os.environ["AWS_REGION"] = aws_region

    # Execute CDK bootstrap command
    try:
        result = subprocess.run(
            [
                "npx",
                "cdk",
                "bootstrap",
                f"aws://{os.environ.get('AWS_ACCOUNT_ID')}/{aws_region}",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        click.echo(result.stdout)
        click.echo("✅ AWS environment bootstrapped successfully!")
    except subprocess.CalledProcessError as e:
        click.echo(f"❌ Failed to bootstrap AWS environment: {e}")
        click.echo(e.stderr)
        sys.exit(1)


@infra_cmd.command(name="deploy")
@click.option(
    "--env",
    required=True,
    type=click.Choice(["dev", "test", "prod"]),
    help="Environment to deploy to",
)
@click.option("--aws-profile", default=None, help="AWS profile to use")
@click.option("--aws-region", default=None, help="AWS region to deploy to")
@click.option("--org-name", default=None, help="Organization name")
def deploy_infrastructure(env, aws_profile, aws_region, org_name):
    """Deploy infrastructure to AWS using CDK."""
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
    org_name = org_name or env_config.get("org_name")

    if not org_name:
        click.echo(
            "❌ Organization name not found in config and not provided as parameter."
        )
        sys.exit(1)

    click.echo(f"Deploying infrastructure to {env} environment in {aws_region}...")

    # Set environment variables for AWS SDK and CDK
    os.environ["AWS_PROFILE"] = aws_profile
    os.environ["AWS_REGION"] = aws_region
    os.environ["FASTAPI_ENV"] = env
    os.environ["FASTAPI_ORG_NAME"] = org_name

    # Execute CDK deploy command
    try:
        result = subprocess.run(
            ["npx", "cdk", "deploy", "--all", "--require-approval", "never"],
            capture_output=True,
            text=True,
            check=True,
        )
        click.echo(result.stdout)
        click.echo(f"✅ Infrastructure deployed to {env} environment successfully!")
    except subprocess.CalledProcessError as e:
        click.echo(f"❌ Failed to deploy infrastructure: {e}")
        click.echo(e.stderr)
        sys.exit(1)


@infra_cmd.command(name="destroy")
@click.option(
    "--env",
    required=True,
    type=click.Choice(["dev", "test", "prod"]),
    help="Environment to destroy",
)
@click.option("--aws-profile", default=None, help="AWS profile to use")
@click.option("--aws-region", default=None, help="AWS region")
@click.option("--org-name", default=None, help="Organization name")
@click.option("--force", is_flag=True, help="Force destruction without confirmation")
def destroy_infrastructure(env, aws_profile, aws_region, org_name, force):
    """Destroy infrastructure in AWS using CDK."""
    if not force:
        if not click.confirm(
            f"Are you sure you want to destroy the {env} environment? This action cannot be undone."
        ):
            click.echo("Destruction cancelled.")
            return

    # Load configuration
    config = Config()
    if not config.config.get("environments", {}).get(env):
        click.echo(f"❌ Environment {env} not initialized. Nothing to destroy.")
        sys.exit(1)

    env_config = config.config["environments"][env]

    # Use parameters if provided, otherwise use config values
    aws_profile = aws_profile or env_config.get("aws_profile", "default")
    aws_region = aws_region or env_config.get("aws_region", "us-east-1")
    org_name = org_name or env_config.get("org_name")

    if not org_name:
        click.echo(
            "❌ Organization name not found in config and not provided as parameter."
        )
        sys.exit(1)

    click.echo(f"Destroying infrastructure in {env} environment...")

    # Set environment variables for AWS SDK and CDK
    os.environ["AWS_PROFILE"] = aws_profile
    os.environ["AWS_REGION"] = aws_region
    os.environ["FASTAPI_ENV"] = env
    os.environ["FASTAPI_ORG_NAME"] = org_name

    # Execute CDK destroy command
    try:
        result = subprocess.run(
            ["npx", "cdk", "destroy", "--all", "--force"],
            capture_output=True,
            text=True,
            check=True,
        )
        click.echo(result.stdout)
        click.echo(f"✅ Infrastructure in {env} environment destroyed successfully!")
    except subprocess.CalledProcessError as e:
        click.echo(f"❌ Failed to destroy infrastructure: {e}")
        click.echo(e.stderr)
        sys.exit(1)


@infra_cmd.command(name="status")
@click.option(
    "--env",
    required=True,
    type=click.Choice(["dev", "test", "prod"]),
    help="Environment to check",
)
@click.option("--aws-profile", default=None, help="AWS profile to use")
@click.option("--aws-region", default=None, help="AWS region")
def check_infrastructure_status(env, aws_profile, aws_region):
    """Check infrastructure status in AWS."""
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

    click.echo(f"Checking infrastructure status in {env} environment...")

    # Set environment variables for AWS SDK and CDK
    os.environ["AWS_PROFILE"] = aws_profile
    os.environ["AWS_REGION"] = aws_region
    os.environ["FASTAPI_ENV"] = env
    os.environ["FASTAPI_ORG_NAME"] = org_name

    # Execute CDK diff command to show changes
    try:
        result = subprocess.run(
            ["npx", "cdk", "diff"], capture_output=True, text=True, check=True
        )
        click.echo(result.stdout)
    except subprocess.CalledProcessError as e:
        click.echo(f"❌ Failed to check infrastructure status: {e}")
        click.echo(e.stderr)
        sys.exit(1)
