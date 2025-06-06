"""
Database Stack for the FastAPI application.
"""

from aws_cdk import (
    CfnOutput,
    Duration,
    Stack,
)
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_rds as rds
from aws_cdk import aws_ssm as ssm
from constructs import Construct

from fastapi_bootstrap.infrastructure.constants import (
    SSM_PATHS,
    Environment,
    get_removal_policy,
)


class DatabaseStack(Stack):
    """Stack for the FastAPI application database."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        vpc: ec2.Vpc,
        env_name: str,
        org_name: str,
        **kwargs,
    ) -> None:
        """
        Initialize the Database stack.

        Args:
            scope: Parent construct
            construct_id: Construct ID
            vpc: VPC to deploy the database in
            env_name: Environment name (dev, test, prod)
            org_name: Organization name
            **kwargs: Additional arguments to pass to the Stack constructor
        """
        super().__init__(scope, construct_id, **kwargs)

        # Store parameters
        self.vpc = vpc
        self.env_name = env_name
        self.org_name = org_name
        self.env = Environment(
            env_name
        )  # Use self.env instead of self.environment for consistency

        # Get environment-specific configuration
        self.removal_policy = get_removal_policy(self.env)

        # Create resources
        self._create_db_security_group()
        self._create_database()
        self._create_database_parameters()

        # Store resources for monitoring
        self.monitoring_resources = {
            "database": self.database,
        }

        # Create outputs
        self._create_outputs()

    def _create_db_security_group(self) -> None:
        """Create security group for the database."""
        self.db_security_group = ec2.SecurityGroup(
            self,
            "DatabaseSecurityGroup",
            vpc=self.vpc,
            description="Security group for the database",
            allow_all_outbound=True,
        )

        # Allow PostgreSQL traffic from within the VPC
        self.db_security_group.add_ingress_rule(
            ec2.Peer.ipv4(self.vpc.vpc_cidr_block),
            ec2.Port.tcp(5432),
            "Allow PostgreSQL traffic from within the VPC",
        )

    def _create_database(self) -> None:
        """Create RDS database."""
        # Create parameter group
        parameter_group = rds.ParameterGroup(
            self,
            "ParameterGroup",
            engine=rds.DatabaseClusterEngine.aurora_postgres(
                version=rds.AuroraPostgresEngineVersion.VER_14_6
            ),
            parameters={
                "shared_preload_libraries": "pg_stat_statements",
                "pg_stat_statements.track": "ALL",
                "log_statement": "ddl",
                "log_connections": "1",
                "log_disconnections": "1",
            },
        )

        # Create subnet group
        subnet_group = rds.SubnetGroup(
            self,
            "SubnetGroup",
            description=f"Subnet group for {self.org_name}-{self.env_name} database",
            vpc=self.vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
        )

        # Create credentials
        credentials = rds.Credentials.from_generated_secret(
            username="postgres",
            secret_name=f"{self.org_name}-{self.env_name}-db-credentials",
        )

        # Determine instance type based on environment
        if self.env == Environment.PROD:
            instance_type = ec2.InstanceType.of(
                ec2.InstanceClass.BURSTABLE3,
                ec2.InstanceSize.MEDIUM,
            )
        else:
            instance_type = ec2.InstanceType.of(
                ec2.InstanceClass.BURSTABLE3,
                ec2.InstanceSize.SMALL,
            )

        # Create database
        self.database = rds.DatabaseInstance(
            self,
            "Database",
            engine=rds.DatabaseInstanceEngine.postgres(
                version=rds.PostgresEngineVersion.VER_14_6
            ),
            instance_type=instance_type,
            vpc=self.vpc,
            security_groups=[self.db_security_group],
            credentials=credentials,
            allocated_storage=20,
            storage_encrypted=True,
            multi_az=self.env == Environment.PROD,
            auto_minor_version_upgrade=True,
            parameter_group=parameter_group,
            subnet_group=subnet_group,
            backup_retention=Duration.days(7 if self.env == Environment.PROD else 1),
            deletion_protection=self.env == Environment.PROD,
            removal_policy=self.removal_policy,
            instance_identifier=f"{self.org_name}-{self.env_name}",
            database_name="app",
        )

    def _create_database_parameters(self) -> None:
        """Create SSM parameters for database connection."""
        # Create a secure parameter for the database URL
        self.db_url_parameter = ssm.StringParameter(
            self,
            "DatabaseUrlParameter",
            parameter_name=SSM_PATHS["database_url"].format(env=self.env_name),
            string_value=(
                f"postgresql://{{username}}:{{password}}@{self.database.db_instance_endpoint_address}:"
                f"{self.database.db_instance_endpoint_port}/app"
            ),
            type=ssm.ParameterType.SECURE_STRING,
            description=f"Database URL for {self.org_name}-{self.env_name}",
        )

        # Add dependency on the database
        self.db_url_parameter.node.add_dependency(self.database)

    def _create_outputs(self) -> None:
        """Create CloudFormation outputs."""
        # Create CloudFormation outputs
        CfnOutput(
            self,
            "DatabaseEndpoint",
            value=self.database.db_instance_endpoint_address,
            description="Database Endpoint",
            export_name=f"{self.org_name}-{self.env_name}-database-endpoint",
        )

        CfnOutput(
            self,
            "DatabasePort",
            value=str(self.database.db_instance_endpoint_port),
            description="Database Port",
            export_name=f"{self.org_name}-{self.env_name}-database-port",
        )

        # Handle the secret ARN output safely
        if hasattr(self.database, "secret") and self.database.secret:
            secret_arn = (
                self.database.secret.secret_full_arn or self.database.secret.secret_arn
            )
            CfnOutput(
                self,
                "DatabaseSecretArn",
                value=secret_arn,
                description="Database Secret ARN",
                export_name=f"{self.org_name}-{self.env_name}-database-secret-arn",
            )
