# Observability Documentation

This document outlines the observability features implemented in the FastAPI Bootstrap project.

## Overview

Observability in the FastAPI Bootstrap project is implemented through multiple components:

1. **Metrics**: CloudWatch metrics for system and application performance
2. **Logging**: Centralized logging with CloudWatch Logs
3. **Tracing**: Distributed tracing with AWS X-Ray
4. **Dashboards**: Pre-configured CloudWatch dashboards
5. **Alerting**: CloudWatch Alarms for critical metrics

## Metrics

The following metrics are collected and monitored:

### Infrastructure Metrics

- **ECS Metrics**:
  - CPU Utilization
  - Memory Utilization
  - Running Task Count

- **ALB Metrics**:
  - Request Count
  - Target Response Time
  - HTTP Status Codes (2XX, 4XX, 5XX)
  - Connection Count

- **WAF Metrics**:
  - Allowed Requests
  - Blocked Requests
  - Rate-limited Requests

### Application Metrics

The application can be extended to publish custom metrics to CloudWatch:

```python
import boto3

cloudwatch = boto3.client('cloudwatch')

def publish_metric(name, value, unit='Count'):
    cloudwatch.put_metric_data(
        Namespace='FastAPIBootstrap',
        MetricData=[
            {
                'MetricName': name,
                'Value': value,
                'Unit': unit
            }
        ]
    )
```

## Logging

All logs are centralized in CloudWatch Logs:

- **Log Groups**:
  - `/ecs/fastapi-bootstrap-{environment}`: Application logs
  - `/aws/lambda/fastapi-bootstrap-{environment}-*`: Lambda function logs

- **Log Retention**: 30 days (configurable)

- **Log Encryption**: All logs are encrypted with KMS

### Structured Logging

The application uses structured logging to make logs more searchable:

```python
import logging
import json

logger = logging.getLogger("app")

def log_event(event_type, **kwargs):
    logger.info(json.dumps({
        "event_type": event_type,
        **kwargs
    }))
```

## Distributed Tracing

The application uses OpenTelemetry for distributed tracing with AWS X-Ray:

- **AWS X-Ray**: Enterprise-grade distributed tracing from AWS
- **Console**: Optional local debugging exporter (enabled with OTEL_DEBUG=true)

### Configuring OpenTelemetry

OpenTelemetry is configured using environment variables:

```bash
# Enable debug console output (optional)
OTEL_DEBUG=true

# Standard OpenTelemetry environment variables
OTEL_SERVICE_NAME=fastapi-bootstrap
OTEL_RESOURCE_ATTRIBUTES=deployment.region=us-west-2,team=backend
```

### OpenTelemetry Implementation

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# Create resource with service info
resource = Resource.create({
    "service.name": "fastapi-bootstrap",
    "service.namespace": "fastapi",
    "deployment.environment": "production"
})

# Set up tracer provider
tracer_provider = TracerProvider(resource=resource)

# Configure the exporter (X-Ray, OTLP, Jaeger, etc.)
# Example for X-Ray:
from opentelemetry.exporter.aws_xray import AwsXRaySpanExporter
from opentelemetry.propagator.aws_xray import AwsXRayPropagator
from opentelemetry import propagate

# Set the propagator for X-Ray
propagate.set_global_textmap(AwsXRayPropagator())

# Configure the X-Ray exporter
exporter = AwsXRaySpanExporter()
tracer_provider.add_span_processor(BatchSpanProcessor(exporter))

# Register the tracer provider
trace.set_tracer_provider(tracer_provider)

# Instrument FastAPI
app = FastAPI()
FastAPIInstrumentor.instrument_app(app)
```

### Available Instrumentation

The following libraries are automatically instrumented:

- FastAPI/Starlette
- Requests HTTP client
- boto3 (AWS SDK)

Optional instrumentation (install with extras):

```bash
# Install all instrumentation
pip install ".[all-instrumentation]"

# Or individual components
pip install ".[sqlalchemy]"
pip install ".[redis]"
pip install ".[mysql]"
```

## Installation

To use OpenTelemetry tracing, you need to install the required packages:

### Basic Installation

```bash
# Install the basic OpenTelemetry packages
pip install "opentelemetry-api>=1.22.0" "opentelemetry-sdk>=1.22.0"
pip install "opentelemetry-instrumentation-fastapi>=0.44b0"
pip install "opentelemetry-instrumentation-requests>=0.44b0"
pip install "opentelemetry-instrumentation-boto3>=0.44b0"
```

### AWS X-Ray Integration

```bash
# Install AWS X-Ray integration
pip install "opentelemetry-exporter-aws-xray>=1.0.0"
pip install "opentelemetry-propagator-aws-xray>=1.0.0"
```

### Additional Instrumentation

```bash
# Install additional instrumentation as needed
pip install "opentelemetry-instrumentation-sqlalchemy>=0.44b0"
pip install "opentelemetry-instrumentation-redis>=0.44b0"
pip install "opentelemetry-instrumentation-pymysql>=0.44b0"
```

## CloudWatch Dashboards

Pre-configured CloudWatch dashboards provide visibility into:

- **Application Performance**: Response times, request rates
- **Infrastructure Health**: CPU, memory, network
- **Error Rates**: HTTP status codes, application errors
- **Security**: WAF blocked requests

The dashboard URL is provided as an output from Terraform:
```
dashboard_url = https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=fastapi-bootstrap-dev
```

## Alerting

CloudWatch Alarms are configured for critical metrics:

- **High CPU Utilization**: Alerts when CPU exceeds 80%
- **High Memory Utilization**: Alerts when memory exceeds 80%
- **High Error Rate**: Alerts when 5XX errors exceed threshold
- **Deployment Failures**: Alerts on CodeDeploy failures

Alerts can be sent to:
- Email (via SNS)
- Slack (via Lambda and SNS)
- PagerDuty (via webhook)

## Health Checks

The application provides health check endpoints:

- `/health`: Basic health check for load balancer
- `/ready`: Readiness check for deployment
- `/metrics`: Prometheus-compatible metrics endpoint (optional)

## Best Practices for Developers

When extending the application, follow these observability best practices:

1. **Use structured logging**
   - Include context in logs (request ID, user ID, etc.)
   - Use appropriate log levels

2. **Add custom metrics for business logic**
   - Track important business events
   - Monitor application-specific performance

3. **Implement proper error handling**
   - Log errors with stack traces
   - Use appropriate HTTP status codes

4. **Add custom dimensions to metrics**
   - Enable filtering and grouping of metrics
   - Provide context for troubleshooting

## Future Enhancements

Potential observability enhancements for future versions:

1. **Prometheus Metrics Integration**: Add support for Prometheus metrics collection
2. **Log Insights Queries**: Pre-configured queries for common scenarios
3. **Anomaly Detection**: Automatic detection of abnormal patterns
4. **Custom Metric Dashboards**: Business-specific dashboards
5. **Synthetic Monitoring**: Proactive testing of critical paths
6. **Additional Instrumentation Libraries**: Support for more frameworks and libraries
7. **OpenTelemetry Metrics API**: Standardized metrics collection alongside tracing

## Usage Examples

Here are some examples of how to use the OpenTelemetry tracing utilities:

### Basic Tracing

```python
from fastapi_bootstrap.utils.telemetry import traced, add_span_attributes

# Use the traced decorator to create a span for a function
@traced(name="my_function", attributes={"function.type": "example"})
def my_function(param1, param2):
    # Add custom attributes to the current span
    add_span_attributes({
        "param1.value": param1,
        "param2.value": param2
    })

    # Function code here
    result = process_data(param1, param2)

    return result
```

### Measuring Execution Time

```python
from fastapi_bootstrap.utils.telemetry import timed_span

# Use the timed_span decorator to measure function execution time
@timed_span(name="database_operation")
async def query_database(query):
    # This function's execution time will be recorded in the span
    # as the attribute "execution_time_ms"
    results = await db.execute(query)
    return results
```

### Manual Span Creation

```python
from fastapi_bootstrap.utils.telemetry import get_tracer

# Get a tracer for the current module
tracer = get_tracer()

# Create a span
with tracer.start_as_current_span("process_payment") as span:
    # Add attributes to the span
    span.set_attribute("payment.amount", amount)
    span.set_attribute("payment.method", method)

    # Perform payment processing
    result = process_payment(amount, method)

    # Add result information
    span.set_attribute("payment.successful", result.success)
```

### Error Handling

```python
from fastapi_bootstrap.utils.telemetry import record_exception

try:
    # Some operation that might fail
    result = risky_operation()
except Exception as e:
    # Record the exception in the current span
    record_exception(e, {"operation": "risky_operation"})

    # Handle the error
    handle_error(e)
```

### Context Propagation

```python
from fastapi_bootstrap.utils.telemetry import propagate_context
import requests

def call_external_service(url, data):
    # Get the current headers
    headers = {"Content-Type": "application/json"}
    
    # Propagate the trace context to the outgoing request
    headers = propagate_context(headers)
    
    # Make the request with the updated headers
    response = requests.post(url, json=data, headers=headers)
    return response
```

### Using Baggage for Cross-Service Context

```python
from fastapi_bootstrap.utils.telemetry import create_baggage, get_baggage

# Set baggage items that will be propagated with the trace
create_baggage({
    "user.id": user_id,
    "tenant.id": tenant_id,
    "deployment.region": "us-west-2"
})

# Later, in another service or component, retrieve the baggage
user_id = get_baggage("user.id")
```

### Metrics Collection

```python
from fastapi_bootstrap.utils.telemetry import create_metrics_counter, create_metrics_histogram

# Create a counter for tracking business events
order_counter = create_metrics_counter(
    name="orders.created",
    description="Number of orders created",
    unit="1"
)

# Create a histogram for tracking latency
payment_latency = create_metrics_histogram(
    name="payment.processing_time",
    description="Time taken to process payments",
    unit="ms"
)

# Use the metrics
def create_order(order_data):
    # Record the order creation
    order_counter.add(1, {"order_type": order_data.type})
    
    # Process the order
    result = process_order(order_data)
    
    return result

def process_payment(payment_data):
    start_time = time.perf_counter()
    
    # Process the payment
    result = payment_processor.process(payment_data)
    
    # Record the processing time
    duration_ms = (time.perf_counter() - start_time) * 1000
    payment_latency.record(duration_ms, {
        "payment_method": payment_data.method,
        "successful": result.success
    })
    
    return result
```