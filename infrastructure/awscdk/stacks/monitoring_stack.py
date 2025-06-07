"""
Monitoring Stack for the FastAPI application.
"""

from typing import Any, Dict, Optional, cast

from aws_cdk import (
    CfnOutput,
    Duration,
    Stack,
    Tags,
)
from aws_cdk import aws_cloudwatch as cloudwatch
from aws_cdk import aws_sns as sns
from constructs import Construct

from infrastructure.awscdk.constants import Environment


class MonitoringStack(Stack):
    """Stack for monitoring the FastAPI application."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        api_resources: Dict[str, Any],
        db_resources: Dict[str, Any],
        env_name: str,
        org_name: str,
        alarm_email: Optional[str] = None,
        **kwargs,
    ) -> None:
        """
        Initialize the Monitoring stack.

        Args:
            scope: Parent construct
            construct_id: Construct ID
            api_resources: Resources from the API stack
            db_resources: Resources from the Database stack
            env_name: Environment name (dev, test, prod)
            org_name: Organization name
            alarm_email: Email address for alarm notifications (optional)
            **kwargs: Additional arguments to pass to the Stack constructor
        """
        super().__init__(scope, construct_id, **kwargs)

        # Store parameters
        self.api_resources = api_resources
        self.db_resources = db_resources
        self.env_name = env_name
        self.org_name = org_name
        self.env = Environment(env_name)  # Use self.env instead of self.environment
        self.alarm_email = alarm_email

        # Create resources
        self._create_alarm_topic()
        self._create_dashboard()
        self._create_alarms()

        # Create outputs
        self._create_outputs()

    def _create_alarm_topic(self) -> None:
        """Create SNS topic for alarms."""
        # Create the topic
        topic_name = f"{self.org_name}-{self.env_name}-alarms"

        # Create a topic
        self.alarm_topic = sns.Topic(
            self,
            "AlarmTopic",
            display_name=topic_name,
            topic_name=topic_name,
        )

        # Add email subscription if email is provided
        if self.alarm_email:
            # Use the CfnSubscription directly to add an email subscription
            sns.CfnSubscription(
                self,
                "EmailSubscription",
                topic_arn=self.alarm_topic.topic_arn,
                protocol="email",
                endpoint=self.alarm_email,
            )

        # Add tags to the topic
        Tags.of(self.alarm_topic).add("Environment", self.env_name)
        Tags.of(self.alarm_topic).add("Organization", self.org_name)
        Tags.of(self.alarm_topic).add("Service", "Monitoring")

    def _create_dashboard(self) -> None:
        """Create CloudWatch dashboard."""
        self.dashboard = cloudwatch.Dashboard(
            self,
            "Dashboard",
            dashboard_name=f"{self.org_name}-{self.env_name}",
        )

        # Add widgets to the dashboard
        self.dashboard.add_widgets(
            # Service metrics
            cloudwatch.GraphWidget(
                title="ECS Service CPU Utilization",
                left=[
                    self.api_resources["service"].metric_cpu_utilization(
                        period=Duration.minutes(1),
                    ),
                ],
            ),
            cloudwatch.GraphWidget(
                title="ECS Service Memory Utilization",
                left=[
                    self.api_resources["service"].metric_memory_utilization(
                        period=Duration.minutes(1),
                    ),
                ],
            ),
            # Load balancer metrics
            cloudwatch.GraphWidget(
                title="Load Balancer Request Count",
                left=[
                    self.api_resources["load_balancer"].metric_request_count(
                        period=Duration.minutes(1),
                    ),
                ],
            ),
            cloudwatch.GraphWidget(
                title="Target Group Response Time",
                left=[
                    self.api_resources["target_group"].metric_target_response_time(
                        period=Duration.minutes(1),
                        statistic="p90",
                    ),
                ],
            ),
            # HTTP Status code metrics
            cloudwatch.GraphWidget(
                title="HTTP Status Codes",
                left=[
                    self.api_resources["load_balancer"].metric_http_code_elb_4_xx_count(
                        period=Duration.minutes(1),
                    ),
                    self.api_resources["load_balancer"].metric_http_code_elb_5_xx_count(
                        period=Duration.minutes(1),
                    ),
                ],
            ),
            # Target Group health metrics
            cloudwatch.GraphWidget(
                title="Target Group Health",
                left=[
                    self.api_resources["target_group"].metric_healthy_host_count(
                        period=Duration.minutes(1),
                    ),
                    self.api_resources["target_group"].metric_unhealthy_host_count(
                        period=Duration.minutes(1),
                    ),
                ],
            ),
            # Database metrics
            cloudwatch.GraphWidget(
                title="Database CPU Utilization",
                left=[
                    self.db_resources["database"].metric_cpu_utilization(
                        period=Duration.minutes(1),
                    ),
                ],
            ),
            cloudwatch.GraphWidget(
                title="Database Connections",
                left=[
                    self.db_resources["database"].metric_database_connections(
                        period=Duration.minutes(1),
                    ),
                ],
            ),
            # Database storage metrics
            cloudwatch.GraphWidget(
                title="Database Storage",
                left=[
                    self.db_resources["database"].metric_free_storage_space(
                        period=Duration.minutes(5),
                    ),
                ],
            ),
            # Database read/write metrics
            cloudwatch.GraphWidget(
                title="Database Read/Write IOPS",
                left=[
                    self.db_resources["database"].metric_read_iops(
                        period=Duration.minutes(1),
                    ),
                ],
                right=[
                    self.db_resources["database"].metric_write_iops(
                        period=Duration.minutes(1),
                    ),
                ],
            ),
        )

        # Add tags to the dashboard
        Tags.of(self.dashboard).add("Environment", self.env_name)
        Tags.of(self.dashboard).add("Organization", self.org_name)
        Tags.of(self.dashboard).add("Service", "Monitoring")

    def _create_alarms(self) -> None:
        """Create CloudWatch alarms."""
        # Service CPU utilization alarm
        self.service_cpu_alarm = cloudwatch.Alarm(
            self,
            "ServiceCpuAlarm",
            alarm_name=f"{self.org_name}-{self.env_name}-service-cpu",
            alarm_description="Alarm when service CPU utilization exceeds 80%",
            metric=self.api_resources["service"].metric_cpu_utilization(
                period=Duration.minutes(1),
            ),
            threshold=80,
            evaluation_periods=3,
            datapoints_to_alarm=2,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
        )

        # Service memory utilization alarm
        self.service_memory_alarm = cloudwatch.Alarm(
            self,
            "ServiceMemoryAlarm",
            alarm_name=f"{self.org_name}-{self.env_name}-service-memory",
            alarm_description="Alarm when service memory utilization exceeds 80%",
            metric=self.api_resources["service"].metric_memory_utilization(
                period=Duration.minutes(1),
            ),
            threshold=80,
            evaluation_periods=3,
            datapoints_to_alarm=2,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
        )

        # Target group health alarm
        self.target_group_health_alarm = cloudwatch.Alarm(
            self,
            "TargetGroupHealthAlarm",
            alarm_name=f"{self.org_name}-{self.env_name}-target-group-health",
            alarm_description="Alarm when healthy host count drops below 1",
            metric=self.api_resources["target_group"].metric_healthy_host_count(
                period=Duration.minutes(1),
            ),
            threshold=1,
            evaluation_periods=3,
            datapoints_to_alarm=2,
            comparison_operator=cloudwatch.ComparisonOperator.LESS_THAN_THRESHOLD,
            treat_missing_data=cloudwatch.TreatMissingData.BREACHING,
        )

        # Database CPU utilization alarm
        self.db_cpu_alarm = cloudwatch.Alarm(
            self,
            "DbCpuAlarm",
            alarm_name=f"{self.org_name}-{self.env_name}-db-cpu",
            alarm_description="Alarm when database CPU utilization exceeds 80%",
            metric=self.db_resources["database"].metric_cpu_utilization(
                period=Duration.minutes(1),
            ),
            threshold=80,
            evaluation_periods=3,
            datapoints_to_alarm=2,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
        )

        # Add ALB 5XX errors alarm (additional best practice)
        self.alb_5xx_alarm = cloudwatch.Alarm(
            self,
            "Alb5xxAlarm",
            alarm_name=f"{self.org_name}-{self.env_name}-alb-5xx",
            alarm_description="Alarm when ALB 5XX errors exceed threshold",
            metric=self.api_resources["load_balancer"].metric_http_code_elb_5_xx_count(
                period=Duration.minutes(1),
            ),
            threshold=5,
            evaluation_periods=3,
            datapoints_to_alarm=2,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
        )

        # Add ALB 4XX errors alarm
        self.alb_4xx_alarm = cloudwatch.Alarm(
            self,
            "Alb4xxAlarm",
            alarm_name=f"{self.org_name}-{self.env_name}-alb-4xx",
            alarm_description="Alarm when ALB 4XX errors exceed threshold",
            metric=self.api_resources["load_balancer"].metric_http_code_elb_4_xx_count(
                period=Duration.minutes(1),
            ),
            threshold=50,  # Higher threshold for 4XX as they can be more common
            evaluation_periods=3,
            datapoints_to_alarm=2,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
        )

        # Add database storage alarm
        self.db_storage_alarm = cloudwatch.Alarm(
            self,
            "DbStorageAlarm",
            alarm_name=f"{self.org_name}-{self.env_name}-db-storage",
            alarm_description="Alarm when database free storage space is low",
            metric=self.db_resources["database"].metric_free_storage_space(
                period=Duration.minutes(5),
            ),
            threshold=10_000_000_000,  # 10GB in bytes
            evaluation_periods=3,
            datapoints_to_alarm=2,
            comparison_operator=cloudwatch.ComparisonOperator.LESS_THAN_THRESHOLD,
            treat_missing_data=cloudwatch.TreatMissingData.BREACHING,
        )

        # Add database connections alarm
        self.db_connections_alarm = cloudwatch.Alarm(
            self,
            "DbConnectionsAlarm",
            alarm_name=f"{self.org_name}-{self.env_name}-db-connections",
            alarm_description="Alarm when database connections are high",
            metric=self.db_resources["database"].metric_database_connections(
                period=Duration.minutes(1),
            ),
            threshold=self.env_name == "prod"
            and 80
            or 20,  # Different thresholds based on environment
            evaluation_periods=3,
            datapoints_to_alarm=2,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
        )

        # Add alarm actions - using the CloudFormation level properties
        alarms = [
            self.service_cpu_alarm,
            self.service_memory_alarm,
            self.target_group_health_alarm,
            self.db_cpu_alarm,
            self.alb_5xx_alarm,
            self.alb_4xx_alarm,
            self.db_storage_alarm,
            self.db_connections_alarm,
        ]

        # Get the topic ARN for alarm actions
        topic_arn = self.alarm_topic.topic_arn

        for alarm in alarms:
            # Get the underlying CloudFormation resource and cast it
            cfn_alarm = cast(cloudwatch.CfnAlarm, alarm.node.default_child)

            # Set alarm actions directly using the properties
            if cfn_alarm:
                cfn_alarm.alarm_actions = [topic_arn]
                cfn_alarm.ok_actions = [topic_arn]

            # Add tags to alarms
            Tags.of(alarm).add("Environment", self.env_name)
            Tags.of(alarm).add("Organization", self.org_name)
            Tags.of(alarm).add("Service", "Monitoring")

    def _create_outputs(self) -> None:
        """Create CloudFormation outputs."""
        CfnOutput(
            self,
            "DashboardUrl",
            value=f"https://{self.region}.console.aws.amazon.com/cloudwatch/home?region={self.region}#dashboards:name={self.org_name}-{self.env_name}",
            description="CloudWatch Dashboard URL",
            export_name=f"{self.org_name}-{self.env_name}-dashboard-url",
        )

        CfnOutput(
            self,
            "AlarmTopicArn",
            value=self.alarm_topic.topic_arn,
            description="Alarm SNS Topic ARN",
            export_name=f"{self.org_name}-{self.env_name}-alarm-topic-arn",
        )
