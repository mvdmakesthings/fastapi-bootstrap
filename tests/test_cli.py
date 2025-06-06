"""
Unit tests for CLI commands.
"""

import os
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from fastapi_bootstrap.cli.commands.deploy import deploy_application
from fastapi_bootstrap.cli.commands.infra import (
    bootstrap_aws_environment,
    deploy_infrastructure,
)
from fastapi_bootstrap.cli.commands.init import init_project


class TestInitCommands:
    """Tests for the initialization commands."""

    @patch("fastapi_bootstrap.cli.commands.init.get_aws_session")
    @patch("fastapi_bootstrap.cli.commands.init.get_account_id")
    @patch("fastapi_bootstrap.cli.commands.init.create_s3_bucket")
    @patch("fastapi_bootstrap.cli.commands.init.create_dynamodb_table")
    @patch("fastapi_bootstrap.cli.commands.init.Config")
    def test_init_project(
        self,
        mock_config,
        mock_create_dynamo,
        mock_create_s3,
        mock_get_account_id,
        mock_get_aws_session,
    ):
        """Test the init project command."""
        # Set up mocks
        mock_session = MagicMock()
        mock_get_aws_session.return_value = mock_session
        mock_get_account_id.return_value = "123456789012"
        mock_create_s3.return_value = True
        mock_create_dynamo.return_value = True

        mock_config_instance = MagicMock()
        mock_config_instance.config = {}
        mock_config_instance.save_config.return_value = True
        mock_config.return_value = mock_config_instance

        # Run the command
        runner = CliRunner()
        result = runner.invoke(
            init_project,
            [
                "--org-name",
                "test-org",
                "--aws-profile",
                "test-profile",
                "--aws-region",
                "us-west-2",
                "--environment",
                "dev",
            ],
        )

        # Check the result
        assert result.exit_code == 0
        assert "Initializing FastAPI Bootstrap project for test-org" in result.output
        assert "AWS Profile: test-profile" in result.output
        assert "AWS Region: us-west-2" in result.output
        assert "Environment: dev" in result.output
        assert "Project initialization completed!" in result.output

        # Verify the function calls
        mock_get_aws_session.assert_called_once_with(
            profile_name="test-profile", region_name="us-west-2"
        )
        mock_get_account_id.assert_called_once_with(mock_session)

        # Check S3 bucket creations
        assert mock_create_s3.call_count == 2
        mock_create_s3.assert_any_call(
            "test-org-dev-terraform-state-123456789012", "us-west-2", mock_session
        )
        mock_create_s3.assert_any_call(
            "cdk-bootstrap-test-org-dev-123456789012", "us-west-2", mock_session
        )

        # Check DynamoDB table creation
        mock_create_dynamo.assert_called_once_with(
            "test-org-dev-terraform-locks", "us-west-2", mock_session
        )

        # Check config saving
        mock_config_instance.save_config.assert_called_once()
        assert "environments" in mock_config_instance.config
        assert "dev" in mock_config_instance.config["environments"]
        assert (
            mock_config_instance.config["environments"]["dev"]["org_name"] == "test-org"
        )
        assert (
            mock_config_instance.config["environments"]["dev"]["aws_profile"]
            == "test-profile"
        )
        assert (
            mock_config_instance.config["environments"]["dev"]["aws_region"]
            == "us-west-2"
        )


class TestInfraCommands:
    """Tests for the infrastructure commands."""

    @patch("fastapi_bootstrap.cli.commands.infra.subprocess.run")
    def test_bootstrap_aws_environment(self, mock_run):
        """Test the bootstrap AWS environment command."""
        # Set up mocks
        mock_run.return_value = MagicMock(stdout="Bootstrap successful", stderr="")

        # Run the command
        runner = CliRunner()
        result = runner.invoke(
            bootstrap_aws_environment,
            ["--aws-profile", "test-profile", "--aws-region", "us-west-2"],
        )

        # Check the result
        assert result.exit_code == 0
        assert (
            "Bootstrapping AWS environment in us-west-2 using profile test-profile"
            in result.output
        )
        assert "AWS environment bootstrapped successfully!" in result.output

        # Verify the function calls
        mock_run.assert_called_once()

        # Check environment variables were set
        assert os.environ.get("AWS_PROFILE") == "test-profile"
        assert os.environ.get("AWS_REGION") == "us-west-2"

    @patch("fastapi_bootstrap.cli.commands.infra.Config")
    @patch("fastapi_bootstrap.cli.commands.infra.subprocess.run")
    def test_deploy_infrastructure(self, mock_run, mock_config):
        """Test the deploy infrastructure command."""
        # Set up mocks
        mock_run.return_value = MagicMock(stdout="Deployment successful", stderr="")

        mock_config_instance = MagicMock()
        mock_config_instance.config = {
            "environments": {
                "dev": {
                    "org_name": "test-org",
                    "aws_profile": "stored-profile",
                    "aws_region": "us-east-1",
                }
            }
        }
        mock_config.return_value = mock_config_instance

        # Run the command
        runner = CliRunner()
        result = runner.invoke(
            deploy_infrastructure,
            [
                "--env",
                "dev",
                "--aws-profile",
                "test-profile",
                "--aws-region",
                "us-west-2",
            ],
        )

        # Check the result
        assert result.exit_code == 0
        assert (
            "Deploying infrastructure to dev environment in us-west-2" in result.output
        )
        assert (
            "Infrastructure deployed to dev environment successfully!" in result.output
        )

        # Verify the function calls
        mock_run.assert_called_once()

        # Check environment variables were set
        assert os.environ.get("AWS_PROFILE") == "test-profile"
        assert os.environ.get("AWS_REGION") == "us-west-2"
        assert os.environ.get("FASTAPI_ENV") == "dev"
        assert os.environ.get("FASTAPI_ORG_NAME") == "test-org"


class TestDeployCommands:
    """Tests for the deployment commands."""

    @patch("fastapi_bootstrap.cli.commands.deploy.Config")
    @patch("fastapi_bootstrap.cli.commands.deploy.get_aws_session")
    @patch("fastapi_bootstrap.cli.commands.deploy.get_ecr_repository_uri")
    @patch("fastapi_bootstrap.cli.commands.deploy.subprocess.run")
    @patch("fastapi_bootstrap.cli.commands.deploy.subprocess.check_output")
    def test_deploy_application(
        self,
        mock_check_output,
        mock_run,
        mock_get_ecr,
        mock_get_aws_session,
        mock_config,
    ):
        """Test the deploy application command."""
        # Set up mocks
        mock_session = MagicMock()
        mock_get_aws_session.return_value = mock_session
        mock_get_ecr.return_value = (
            "123456789012.dkr.ecr.us-west-2.amazonaws.com/test-org-dev-api"
        )
        mock_check_output.return_value = "ecr-password"
        mock_run.return_value = MagicMock()

        # Mock ECS client and responses
        mock_ecs_client = MagicMock()
        mock_session.client.return_value = mock_ecs_client

        mock_ecs_client.describe_services.return_value = {
            "services": [
                {
                    "serviceName": "test-org-dev-api-service",
                    "taskDefinition": "arn:aws:ecs:us-west-2:123456789012:task-definition/test-org-dev-api:1",
                    "status": "ACTIVE",
                    "desiredCount": 2,
                    "runningCount": 2,
                    "pendingCount": 0,
                    "deployments": [],
                    "events": [],
                }
            ]
        }

        mock_ecs_client.describe_task_definition.return_value = {
            "taskDefinition": {
                "family": "test-org-dev-api",
                "taskRoleArn": "arn:aws:iam::123456789012:role/task-role",
                "executionRoleArn": "arn:aws:iam::123456789012:role/execution-role",
                "networkMode": "awsvpc",
                "containerDefinitions": [
                    {
                        "name": "test-org-dev-api-container",
                        "image": "123456789012.dkr.ecr.us-west-2.amazonaws.com/test-org-dev-api:old-tag",
                    }
                ],
                "volumes": [],
                "placementConstraints": [],
                "requiresCompatibilities": ["FARGATE"],
                "cpu": "256",
                "memory": "512",
            }
        }

        mock_ecs_client.register_task_definition.return_value = {
            "taskDefinition": {
                "taskDefinitionArn": "arn:aws:ecs:us-west-2:123456789012:task-definition/test-org-dev-api:2"
            }
        }

        mock_config_instance = MagicMock()
        mock_config_instance.config = {
            "environments": {
                "dev": {
                    "org_name": "test-org",
                    "aws_profile": "stored-profile",
                    "aws_region": "us-east-1",
                }
            }
        }
        mock_config.return_value = mock_config_instance

        # Run the command
        runner = CliRunner()
        result = runner.invoke(
            deploy_application,
            [
                "--env",
                "dev",
                "--aws-profile",
                "test-profile",
                "--aws-region",
                "us-west-2",
                "--image-tag",
                "test-tag",
            ],
        )

        # Check the result
        assert result.exit_code == 0
        assert "Deploying application to dev environment" in result.output
        assert "AWS Profile: test-profile" in result.output
        assert "AWS Region: us-west-2" in result.output
        assert "Image Tag: test-tag" in result.output
        assert "Application deployed to dev environment successfully!" in result.output

        # Verify function calls
        mock_get_aws_session.assert_called_once_with(
            profile_name="test-profile", region_name="us-west-2"
        )
        mock_get_ecr.assert_called_once_with("test-org-dev-api", mock_session)

        # Check docker commands were called
        mock_run.assert_any_call(
            [
                "docker",
                "build",
                "-t",
                "123456789012.dkr.ecr.us-west-2.amazonaws.com/test-org-dev-api:test-tag",
                "-f",
                "infrastructure/docker/Dockerfile.dev",
                ".",
            ],
            check=True,
        )

        # Check ECS task definition update
        assert mock_ecs_client.register_task_definition.call_count == 1
        container_defs = mock_ecs_client.register_task_definition.call_args[1][
            "containerDefinitions"
        ]
        assert (
            container_defs[0]["image"]
            == "123456789012.dkr.ecr.us-west-2.amazonaws.com/test-org-dev-api:test-tag"
        )

        # Check ECS service update
        mock_ecs_client.update_service.assert_called_once_with(
            cluster="test-org-dev-cluster",
            service="test-org-dev-api-service",
            taskDefinition="arn:aws:ecs:us-west-2:123456789012:task-definition/test-org-dev-api:2",
            forceNewDeployment=True,
        )
