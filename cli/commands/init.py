"""
Project initialization commands.
"""

import click

from cli.utils.aws import (
    create_dynamodb_table,
    create_s3_bucket,
    get_account_id,
    get_aws_session,
)
from cli.utils.config import Config
from cli.utils.credentials import CredentialManager


@click.group(name="init")
def init_cmd():
    """Initialize the FastAPI Bootstrap project."""
    pass


@init_cmd.command(name="project")
@click.option(
    "--org-name", required=True, help="Organization name (used for resource naming)"
)
@click.option(
    "--aws-profile", default="default", help="AWS profile to use for initialization"
)
@click.option(
    "--aws-region", default="us-east-1", help="AWS region to deploy resources to"
)
@click.option(
    "--environment",
    default="dev",
    type=click.Choice(["dev", "test", "prod"]),
    help="Environment to initialize",
)
@click.option(
    "--use-credentials", is_flag=True, help="Use AWS credentials instead of profile"
)
def init_project(org_name, aws_profile, aws_region, environment, use_credentials):
    """Initialize the FastAPI Bootstrap project with required AWS resources."""
    click.echo(f"Initializing FastAPI Bootstrap project for {org_name}...")
    click.echo(f"AWS Profile: {aws_profile}")
    click.echo(f"AWS Region: {aws_region}")
    click.echo(f"Environment: {environment}")

    # Set up AWS session
    session = None

    if use_credentials:
        # Get AWS credentials from user
        aws_access_key_id = click.prompt("AWS Access Key ID", hide_input=False)
        aws_secret_access_key = click.prompt("AWS Secret Access Key", hide_input=True)
        aws_session_token = click.prompt(
            "AWS Session Token (optional)", default="", show_default=False
        )

        # Store credentials securely
        cred_manager = CredentialManager(env_name=environment)
        if aws_session_token:
            cred_manager.store_aws_credentials(
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                aws_session_token=aws_session_token,
            )
            session = get_aws_session(
                region_name=aws_region,
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                aws_session_token=aws_session_token,
            )
        else:
            cred_manager.store_aws_credentials(
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
            )
            session = get_aws_session(
                region_name=aws_region,
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
            )

        click.echo("AWS credentials stored securely.")
    else:
        session = get_aws_session(profile_name=aws_profile, region_name=aws_region)

    account_id = get_account_id(session)
    click.echo(f"AWS Account ID: {account_id}")

    # Create resource names
    state_bucket_name = f"{org_name}-{environment}-terraform-state-{account_id}"
    dynamo_table_name = f"{org_name}-{environment}-terraform-locks"
    cdk_bootstrap_bucket = f"cdk-bootstrap-{org_name}-{environment}-{account_id}"

    # Create S3 bucket for state storage
    click.echo(f"Creating S3 bucket for state storage: {state_bucket_name}")
    if create_s3_bucket(state_bucket_name, aws_region, session):
        click.echo(f"✅ S3 bucket created or already exists: {state_bucket_name}")
    else:
        click.echo(f"❌ Failed to create S3 bucket: {state_bucket_name}")
        return

    # Create DynamoDB table for state locking
    click.echo(f"Creating DynamoDB table for state locking: {dynamo_table_name}")
    if create_dynamodb_table(dynamo_table_name, aws_region, session):
        click.echo(f"✅ DynamoDB table created or already exists: {dynamo_table_name}")
    else:
        click.echo(f"❌ Failed to create DynamoDB table: {dynamo_table_name}")
        return

    # Create S3 bucket for CDK bootstrap assets
    click.echo(f"Creating S3 bucket for CDK bootstrap assets: {cdk_bootstrap_bucket}")
    if create_s3_bucket(cdk_bootstrap_bucket, aws_region, session):
        click.echo(f"✅ S3 bucket created or already exists: {cdk_bootstrap_bucket}")
    else:
        click.echo(f"❌ Failed to create S3 bucket: {cdk_bootstrap_bucket}")
        return

    # Save configuration
    config = Config()
    if "environments" not in config.config:
        config.config["environments"] = {}

    if environment not in config.config["environments"]:
        config.config["environments"][environment] = {}

    config.config["environments"][environment].update(
        {
            "org_name": org_name,
            "aws_profile": aws_profile if not use_credentials else None,
            "aws_region": aws_region,
            "account_id": account_id,
            "state_bucket": state_bucket_name,
            "lock_table": dynamo_table_name,
            "cdk_bootstrap_bucket": cdk_bootstrap_bucket,
            "use_credentials": use_credentials,
        }
    )

    if config.save_config():
        click.echo("✅ Configuration saved successfully")
    else:
        click.echo("❌ Failed to save configuration")
        return

    click.echo("\n🚀 Project initialization completed!")
    click.echo("\nNext steps:")
    click.echo("1. Bootstrap the AWS CDK environment:")
    if use_credentials:
        click.echo(f"   fastapi-bootstrap infra bootstrap --aws-region {aws_region}")
    else:
        click.echo(
            f"   fastapi-bootstrap infra bootstrap --aws-profile {aws_profile} --aws-region {aws_region}"
        )
    click.echo("2. Deploy the infrastructure:")
    click.echo(f"   fastapi-bootstrap infra deploy --env {environment}")


@init_cmd.command(name="database")
@click.option(
    "--env",
    required=True,
    type=click.Choice(["dev", "test", "prod"]),
    help="Environment to initialize database for",
)
@click.option("--username", required=True, help="Database username")
@click.option(
    "--password", required=True, help="Database password", prompt=True, hide_input=True
)
@click.option("--host", required=True, help="Database host")
@click.option("--port", required=True, type=int, help="Database port")
@click.option("--database", required=True, help="Database name")
def init_database(env, username, password, host, port, database):
    """Initialize database credentials for an environment."""
    click.echo(f"Initializing database credentials for {env} environment...")

    # Store database credentials
    cred_manager = CredentialManager(env_name=env)
    if cred_manager.store_database_credentials(
        username=username,
        password=password,
        host=host,
        port=port,
        database_name=database,
    ):
        click.echo("✅ Database credentials stored successfully")
    else:
        click.echo("❌ Failed to store database credentials")
        return

    # Ask to store in AWS Secrets Manager
    if click.confirm("Do you want to store these credentials in AWS Secrets Manager?"):
        # Load configuration
        config = Config()
        env_config = config.config.get("environments", {}).get(env, {})

        # Get AWS session
        session = None
        if env_config.get("use_credentials"):
            aws_creds = cred_manager.get_aws_credentials()
            if aws_creds:
                session = get_aws_session(
                    region_name=env_config.get("aws_region"),
                    aws_access_key_id=aws_creds.get("aws_access_key_id"),
                    aws_secret_access_key=aws_creds.get("aws_secret_access_key"),
                    aws_session_token=aws_creds.get("aws_session_token"),
                )
            else:
                click.echo("❌ Failed to load AWS credentials")
                return
        else:
            session = get_aws_session(
                profile_name=env_config.get("aws_profile"),
                region_name=env_config.get("aws_region"),
            )

        # Store in AWS Secrets Manager
        secret_name = (
            f"{env_config.get('org_name', 'fastapi')}-{env}-database-credentials"
        )
        if cred_manager.store_credentials_in_aws_secrets_manager(secret_name, session):
            click.echo(
                f"✅ Database credentials stored in AWS Secrets Manager as '{secret_name}'"
            )
        else:
            click.echo("❌ Failed to store credentials in AWS Secrets Manager")

    click.echo("\n🚀 Database initialization completed!")
