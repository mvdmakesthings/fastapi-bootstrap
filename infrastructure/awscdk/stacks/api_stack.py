"""
API Stack for the FastAPI application.
"""

from typing import Optional

from aws_cdk import (
    CfnOutput,
    Duration,
    Stack,
    Tags,
)
from aws_cdk import aws_certificatemanager as acm
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecr as ecr
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_elasticloadbalancingv2 as elbv2
from aws_cdk import aws_iam as iam
from aws_cdk import aws_logs as logs
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_ssm as ssm
from constructs import Construct

from infrastructure.awscdk.constants import (
    DEFAULT_VPC_CONFIG,
    ECS_CONFIG,
    Environment,
    get_removal_policy,
)


class ApiStack(Stack):
    """Stack for the FastAPI application API."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        env_name: str,
        org_name: str,
        domain_name: Optional[str] = None,
        **kwargs,
    ) -> None:
        """
        Initialize the API stack.

        Args:
            scope: Parent construct
            construct_id: Construct ID
            env_name: Environment name (dev, test, prod)
            org_name: Organization name
            domain_name: Domain name for the API (optional)
            **kwargs: Additional arguments to pass to the Stack constructor
        """
        super().__init__(scope, construct_id, **kwargs)

        # Store parameters
        self.env_name = env_name
        self.org_name = org_name
        self.env = Environment(env_name)  # Changed from self.environment to self.env
        self.domain_name = domain_name

        # Get environment-specific configuration
        self.ecs_config = ECS_CONFIG[self.env]  # Updated reference
        self.removal_policy = get_removal_policy(self.env)  # Updated reference

        # Create resources
        self._create_vpc()
        self._create_ecr_repository()
        self._create_ecs_cluster()
        self._create_load_balancer()
        self._create_ecs_task_definition()
        self._create_ecs_service()

        # Store resources for monitoring
        self.monitoring_resources = {
            "cluster": self.cluster,
            "service": self.service,
            "load_balancer": self.load_balancer,
            "target_group": self.target_group,
        }

        # Create outputs
        self._create_outputs()

    def _create_vpc(self) -> None:
        """Create VPC and networking resources with security best practices."""
        self.vpc = ec2.Vpc(
            self,
            "VPC",
            max_azs=DEFAULT_VPC_CONFIG["max_azs"],
            cidr=DEFAULT_VPC_CONFIG["cidr"],
            nat_gateways=DEFAULT_VPC_CONFIG["nat_gateways"],
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    name="Private",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    name="Isolated",
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                    cidr_mask=24,
                ),
            ],
            enable_dns_hostnames=True,
            enable_dns_support=True,
            flow_logs={
                "FlowLogs": {
                    "destination": ec2.FlowLogDestination.to_cloud_watch_logs(),
                    "traffic_type": ec2.FlowLogTrafficType.ALL,
                }
            },
        )

        # Add VPC endpoints for ECR, Logs, and SSM to reduce NAT gateway costs and improve security
        self.vpc.add_gateway_endpoint(
            "S3Endpoint",
            service=ec2.GatewayVpcEndpointAwsService.S3,
        )

        self.vpc.add_interface_endpoint(
            "EcrDockerEndpoint",
            service=ec2.InterfaceVpcEndpointAwsService.ECR_DOCKER,
        )

        self.vpc.add_interface_endpoint(
            "EcrEndpoint",
            service=ec2.InterfaceVpcEndpointAwsService.ECR,
        )

        self.vpc.add_interface_endpoint(
            "CloudWatchLogsEndpoint",
            service=ec2.InterfaceVpcEndpointAwsService.CLOUDWATCH_LOGS,
        )

        self.vpc.add_interface_endpoint(
            "SsmEndpoint",
            service=ec2.InterfaceVpcEndpointAwsService.SSM,
        )

        # Security group for the load balancer with restricted outbound access
        self.alb_security_group = ec2.SecurityGroup(
            self,
            "ALBSecurityGroup",
            vpc=self.vpc,
            description="Security group for the application load balancer",
            allow_all_outbound=False,  # Restrict outbound traffic
        )

        # Allow outbound traffic only to the ECS security group
        self.alb_security_group.add_egress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.tcp(8000),
            "Allow outbound traffic to ECS service",
        )

        # Allow HTTP and HTTPS traffic from anywhere
        self.alb_security_group.add_ingress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.tcp(80),
            "Allow HTTP traffic from anywhere",
        )

        self.alb_security_group.add_ingress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.tcp(443),
            "Allow HTTPS traffic from anywhere",
        )

        # Security group for the ECS service with minimal permissions
        self.ecs_security_group = ec2.SecurityGroup(
            self,
            "ECSSecurityGroup",
            vpc=self.vpc,
            description="Security group for the ECS service",
            allow_all_outbound=False,  # Restrict outbound traffic
        )

        # Allow only necessary outbound traffic
        self.ecs_security_group.add_egress_rule(
            ec2.Peer.any_ipv4(), ec2.Port.tcp(443), "Allow HTTPS outbound traffic"
        )

        self.ecs_security_group.add_egress_rule(
            ec2.Peer.any_ipv4(), ec2.Port.tcp(80), "Allow HTTP outbound traffic"
        )

        # Allow traffic from the ALB security group only
        self.ecs_security_group.add_ingress_rule(
            ec2.Peer.security_group_id(self.alb_security_group.security_group_id),
            ec2.Port.tcp(8000),
            "Allow traffic from the ALB",
        )

    def _create_ecr_repository(self) -> None:
        """Create ECR repository for Docker images with enhanced security."""
        self.repository = ecr.Repository(
            self,
            "Repository",
            repository_name=f"{self.org_name}-{self.env_name}",
            removal_policy=self.removal_policy,
            image_scan_on_push=True,
            image_tag_mutability=ecr.TagMutability.IMMUTABLE,
            encryption=ecr.RepositoryEncryption.KMS,  # Use KMS encryption
            lifecycle_rules=[
                ecr.LifecycleRule(
                    description="Keep only the latest 5 images",
                    max_image_count=5,
                    rule_priority=1,
                    tag_status=ecr.TagStatus.ANY,
                ),
                ecr.LifecycleRule(
                    description="Remove untagged images older than 14 days",
                    max_image_age=Duration.days(14),
                    rule_priority=2,
                    tag_status=ecr.TagStatus.UNTAGGED,
                ),
            ],
        )

        # Add tags to repository
        Tags.of(self.repository).add("Application", "FastAPI")
        Tags.of(self.repository).add("Environment", self.env_name)
        Tags.of(self.repository).add("Service", "API")

    def _create_ecs_cluster(self) -> None:
        """Create ECS cluster."""
        self.cluster = ecs.Cluster(
            self,
            "Cluster",
            vpc=self.vpc,
            cluster_name=f"{self.org_name}-{self.env_name}",
            container_insights=True,
        )

    def _create_load_balancer(self) -> None:
        """Create Application Load Balancer."""
        # Create S3 bucket for ALB access logs
        s3.Bucket(
            self,
            "AccessLogsBucket",
            bucket_name=f"{self.org_name}-{self.env_name}-alb-logs",
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=self.removal_policy,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
            lifecycle_rules=[
                s3.LifecycleRule(
                    expiration=Duration.days(90),
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.INTELLIGENT_TIERING,
                            transition_after=Duration.days(30),
                        )
                    ],
                )
            ],
        )

        # Create Application Load Balancer with best practices
        self.load_balancer = elbv2.ApplicationLoadBalancer(
            self,
            "ALB",
            vpc=self.vpc,
            internet_facing=True,
            security_group=self.alb_security_group,
            load_balancer_name=f"{self.org_name}-{self.env_name}",
            deletion_protection=self.env.value
            == "prod",  # Enable deletion protection in production
            http2_enabled=True,  # Enable HTTP/2 for better performance
            idle_timeout=Duration.seconds(60),  # Optimize idle timeout
        )

        # Note: Access logs should be enabled through AWS Console or using L1 constructs
        # as L2 construct doesn't currently support this feature directly

        # Create a target group for the service with optimized health checks
        self.target_group = elbv2.ApplicationTargetGroup(
            self,
            "TargetGroup",
            vpc=self.vpc,
            port=8000,
            protocol=elbv2.ApplicationProtocol.HTTP,
            target_type=elbv2.TargetType.IP,
            deregistration_delay=Duration.seconds(30),  # Optimized deregistration delay
            health_check=elbv2.HealthCheck(
                path="/api/v1/health",
                interval=Duration.seconds(15),  # More frequent health checks
                timeout=Duration.seconds(5),
                healthy_threshold_count=2,
                unhealthy_threshold_count=3,
                healthy_http_codes="200-299",  # Accept any 2XX response as healthy
            ),
            target_group_name=f"{self.org_name}-{self.env_name}",
            slow_start=Duration.seconds(60),  # Give containers time to warm up
        )

        # Create an HTTPS listener if a domain name is provided
        if self.domain_name:
            # Create a certificate
            certificate = acm.Certificate(
                self,
                "Certificate",
                domain_name=self.domain_name,
                validation=acm.CertificateValidation.from_dns(),
            )

            # Create an HTTPS listener with security headers
            self.load_balancer.add_listener(
                "HTTPSListener",
                port=443,
                certificates=[certificate],
                ssl_policy=elbv2.SslPolicy.TLS12,  # Ensure minimum TLS 1.2
                default_action=elbv2.ListenerAction.forward([self.target_group]),
            )

            # Redirect HTTP to HTTPS with 301 (permanent) redirect
            self.load_balancer.add_listener(
                "HTTPListener",
                port=80,
                default_action=elbv2.ListenerAction.redirect(
                    protocol="HTTPS",
                    port="443",
                    permanent=True,
                    host="#{host}",
                    path="/#{path}",
                    query="#{query}",
                ),
            )
        else:
            # Create an HTTP listener
            self.load_balancer.add_listener(
                "HTTPListener",
                port=80,
                default_action=elbv2.ListenerAction.forward([self.target_group]),
            )

            # Add a comment to remind developers that HTTP-only is not recommended for production
            # In a real environment, we should always use HTTPS with a valid certificate

    def _create_ecs_task_definition(self) -> None:
        """Create ECS task definition."""
        # Roles are now created automatically by the FargateTaskDefinition
        # We'll add policies to them through the task definition object

        # Create log group for the container
        log_group = logs.LogGroup(
            self,
            "LogGroup",
            log_group_name=f"/ecs/{self.org_name}-{self.env_name}",
            removal_policy=self.removal_policy,
            retention=logs.RetentionDays.ONE_MONTH,
            encryption_key=None,  # Enables AWS managed encryption by default
        )

        # Create task definition with enhanced security
        self.task_definition = ecs.FargateTaskDefinition(
            self,
            "TaskDefinition",
            family=f"{self.org_name}-{self.env_name}",
            cpu=self.ecs_config["cpu"],
            memory_limit_mib=self.ecs_config["memory_limit_mib"],
            ephemeral_storage_gib=30,  # Increase from default 20 GiB for better performance
            runtime_platform=ecs.RuntimePlatform(
                operating_system_family=ecs.OperatingSystemFamily.LINUX,
                cpu_architecture=ecs.CpuArchitecture.X86_64,
            ),
        )

        # Add tags to the task definition
        Tags.of(self.task_definition).add("Application", "FastAPI")
        Tags.of(self.task_definition).add("Environment", self.env_name)
        Tags.of(self.task_definition).add("Service", "API")

        # Assign IAM roles directly to task definition properties with least privilege
        self.task_definition.add_to_execution_role_policy(
            iam.PolicyStatement(
                sid="ECSExecutionPolicy",
                actions=[
                    "ecr:GetAuthorizationToken",
                    "ecr:BatchCheckLayerAvailability",
                    "ecr:GetDownloadUrlForLayer",
                    "ecr:BatchGetImage",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                ],
                resources=["*"],
            )
        )

        # Add repository-specific ECR permissions
        self.task_definition.add_to_execution_role_policy(
            iam.PolicyStatement(
                sid="ECRPullPolicy",
                actions=["ecr:BatchGetImage", "ecr:GetDownloadUrlForLayer"],
                resources=[self.repository.repository_arn],
            )
        )

        # Add the task role policy with least privilege
        self.task_definition.add_to_task_role_policy(
            iam.PolicyStatement(
                sid="SSMParameterAccess",
                actions=["ssm:GetParameters", "ssm:GetParameter"],
                resources=[
                    f"arn:aws:ssm:{self.region}:{self.account}:parameter/fastapi-bootstrap/{self.env_name}/*"
                ],
            )
        )

        # Add CloudWatch metric permissions for better observability
        self.task_definition.add_to_task_role_policy(
            iam.PolicyStatement(
                sid="CloudWatchMetricsAccess",
                actions=["cloudwatch:PutMetricData"],
                resources=["*"],
                conditions={
                    "StringEquals": {
                        "cloudwatch:namespace": f"CustomMetrics/{self.org_name}/{self.env_name}"
                    }
                },
            )
        )

        # Add container to the task definition with enhanced security and observability
        self.container = self.task_definition.add_container(
            "Container",
            image=ecs.ContainerImage.from_ecr_repository(self.repository, "latest"),
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix=f"{self.org_name}-{self.env_name}",
                log_group=log_group,
            ),
            environment={
                "ENVIRONMENT": self.env_name,
                "LOG_LEVEL": "INFO" if self.env.value == "prod" else "DEBUG",
                "ENABLE_METRICS": "true",
                "SERVICE_NAME": f"{self.org_name}-api",
            },
            port_mappings=[
                ecs.PortMapping(
                    container_port=8000,
                    host_port=8000,
                    protocol=ecs.Protocol.TCP,
                ),
            ],
            health_check=ecs.HealthCheck(
                command=[
                    "CMD-SHELL",
                    "curl -f http://localhost:8000/api/v1/health || exit 1",
                ],
                interval=Duration.seconds(30),
                timeout=Duration.seconds(5),
                retries=3,
                start_period=Duration.seconds(60),
            ),
            essential=True,
            readonly_root_filesystem=True,  # Security best practice
            privileged=False,  # Security best practice
            container_name="api",
        )

    def _create_ecs_service(self) -> None:
        """Create ECS service."""
        # Create service with deployment configuration for blue/green deployments
        self.service = ecs.FargateService(
            self,
            "Service",
            cluster=self.cluster,
            task_definition=self.task_definition,
            desired_count=self.ecs_config["desired_count"],
            security_groups=[self.ecs_security_group],
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
            assign_public_ip=False,
            service_name=f"{self.org_name}-{self.env_name}",
            circuit_breaker=ecs.DeploymentCircuitBreaker(
                rollback=True
            ),  # Auto-rollback on failure
            deployment_controller=ecs.DeploymentController(
                type=ecs.DeploymentControllerType.ECS
            ),
            enable_ecs_managed_tags=True,
            propagate_tags=ecs.PropagatedTagSource.SERVICE,
            health_check_grace_period=Duration.seconds(
                120
            ),  # Give more time for health checks during deployment
        )

        # Add tags to service
        Tags.of(self.service).add("Application", "FastAPI")
        Tags.of(self.service).add("Environment", self.env_name)
        Tags.of(self.service).add("Service", "API")

        # Add auto scaling with more sophisticated configuration
        scaling = self.service.auto_scale_task_count(
            min_capacity=self.ecs_config["auto_scaling_min_capacity"],
            max_capacity=self.ecs_config["auto_scaling_max_capacity"],
        )

        # Add scaling based on CPU utilization
        scaling.scale_on_cpu_utilization(
            "CPUScaling",
            target_utilization_percent=70,
            scale_in_cooldown=Duration.seconds(300),  # More conservative scale-in
            scale_out_cooldown=Duration.seconds(60),  # Quick scale-out
        )

        # Add scaling based on memory utilization
        scaling.scale_on_memory_utilization(
            "MemoryScaling",
            target_utilization_percent=75,
            scale_in_cooldown=Duration.seconds(300),
            scale_out_cooldown=Duration.seconds(60),
        )

        # Add scaling based on request count per target if in production
        if self.env.value == "prod":
            scaling.scale_on_request_count(
                "RequestScaling",
                requests_per_target=1000,
                target_group=self.target_group,
                scale_in_cooldown=Duration.seconds(300),
                scale_out_cooldown=Duration.seconds(60),
            )

        # Register with target group
        self.service.attach_to_application_target_group(self.target_group)

    def _create_outputs(self) -> None:
        """Create CloudFormation outputs with enhanced metadata."""
        CfnOutput(
            self,
            "RepositoryUri",
            value=self.repository.repository_uri,
            description="ECR Repository URI",
            export_name=f"{self.org_name}-{self.env_name}-repository-uri",
        )

        CfnOutput(
            self,
            "LoadBalancerDns",
            value=self.load_balancer.load_balancer_dns_name,
            description="Load Balancer DNS Name",
            export_name=f"{self.org_name}-{self.env_name}-load-balancer-dns",
        )

        CfnOutput(
            self,
            "LoadBalancerArn",
            value=self.load_balancer.load_balancer_arn,
            description="Load Balancer ARN",
            export_name=f"{self.org_name}-{self.env_name}-load-balancer-arn",
        )

        CfnOutput(
            self,
            "ServiceName",
            value=self.service.service_name,
            description="ECS Service Name",
            export_name=f"{self.org_name}-{self.env_name}-service-name",
        )

        CfnOutput(
            self,
            "ServiceArn",
            value=self.service.service_arn,
            description="ECS Service ARN",
            export_name=f"{self.org_name}-{self.env_name}-service-arn",
        )

        CfnOutput(
            self,
            "ClusterName",
            value=self.cluster.cluster_name,
            description="ECS Cluster Name",
            export_name=f"{self.org_name}-{self.env_name}-cluster-name",
        )

        CfnOutput(
            self,
            "ClusterArn",
            value=self.cluster.cluster_arn,
            description="ECS Cluster ARN",
            export_name=f"{self.org_name}-{self.env_name}-cluster-arn",
        )

        CfnOutput(
            self,
            "VpcId",
            value=self.vpc.vpc_id,
            description="VPC ID",
            export_name=f"{self.org_name}-{self.env_name}-vpc-id",
        )

        CfnOutput(
            self,
            "TaskDefinitionArn",
            value=self.task_definition.task_definition_arn,
            description="Task Definition ARN",
            export_name=f"{self.org_name}-{self.env_name}-task-definition-arn",
        )

        # Store essential resource information in SSM Parameter Store for cross-stack reference
        ssm.StringParameter(
            self,
            "VpcIdParameter",
            parameter_name=f"/fastapi-bootstrap/{self.env_name}/infrastructure/vpc-id",
            string_value=self.vpc.vpc_id,
            description="VPC ID for FastAPI application",
            tier=ssm.ParameterTier.STANDARD,
        )

        ssm.StringParameter(
            self,
            "ClusterArnParameter",
            parameter_name=f"/fastapi-bootstrap/{self.env_name}/infrastructure/cluster-arn",
            string_value=self.cluster.cluster_arn,
            description="ECS Cluster ARN for FastAPI application",
            tier=ssm.ParameterTier.STANDARD,
        )

        ssm.StringParameter(
            self,
            "LoadBalancerDnsParameter",
            parameter_name=f"/fastapi-bootstrap/{self.env_name}/infrastructure/load-balancer-dns",
            string_value=self.load_balancer.load_balancer_dns_name,
            description="Load Balancer DNS for FastAPI application",
            tier=ssm.ParameterTier.STANDARD,
        )
