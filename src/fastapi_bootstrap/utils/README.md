# OpenTelemetry Integration for FastAPI Bootstrap

This directory contains utilities for integrating OpenTelemetry tracing into the FastAPI Bootstrap project.

## Overview

OpenTelemetry is a vendor-neutral observability framework that provides APIs, libraries, and integrations to capture distributed traces and metrics from your application. This implementation provides a flexible foundation that supports multiple backends including:

- AWS X-Ray
- OTLP-compatible systems (Honeycomb, Lightstep, New Relic, Datadog)
- Jaeger
- Console output (for debugging)

## Components

### Telemetry Utilities (`telemetry.py`)

A collection of helper functions and decorators for working with OpenTelemetry traces:

- **`get_tracer()`**: Get a tracer instance for the current module
- **`traced()`**: Decorator to create a span for a function
- **`timed_span()`**: Decorator to measure execution time of a function
- **`add_span_attributes()`**: Add attributes to the current span
- **`record_exception()`**: Record an exception in the current span
- **`create_span()`**: Create a new span as a child of the current span
- **`propagate_context()`**: Extract and inject trace context for distributed tracing
- **`create_baggage()`**: Create baggage items for cross-service context propagation
- **`get_baggage()`**: Retrieve baggage items from the current context
- **`create_metrics_counter()`**: Create a counter metric
- **`create_metrics_histogram()`**: Create a histogram metric for measuring distributions

### OpenTelemetry Middleware (`middleware.py`)

A FastAPI middleware that adds request context to spans:

- HTTP method
- URL
- Host
- User agent
- Client IP
- Status code
- Response size
- Request duration
- Service version
- Environment information

## Installation

To use these utilities, ensure you have the required dependencies installed:

```bash
# Basic OpenTelemetry dependencies
pip install "opentelemetry-api>=1.22.0" "opentelemetry-sdk>=1.22.0"
pip install "opentelemetry-instrumentation-fastapi>=0.44b0"

# For AWS X-Ray integration
pip install "opentelemetry-exporter-aws-xray>=1.0.0"
pip install "opentelemetry-propagator-aws-xray>=1.0.0"

# For additional instrumentations (optional)
pip install "opentelemetry-instrumentation-requests>=0.44b0"
pip install "opentelemetry-instrumentation-boto3>=0.44b0"
```

## Usage

### Basic Tracing

```python
from fastapi_bootstrap.utils.telemetry import traced

@traced(name="my_function", attributes={"function.type": "example"})
def my_function(param1, param2):
    # Function code here
    return result
```

### Measuring Execution Time

```python
from fastapi_bootstrap.utils.telemetry import timed_span

@timed_span(name="database_operation")
async def query_database(query):
    results = await db.execute(query)
    return results
```

### Manual Span Creation

```python
from fastapi_bootstrap.utils.telemetry import get_tracer

tracer = get_tracer()
with tracer.start_as_current_span("process_payment") as span:
    span.set_attribute("payment.amount", amount)
    # Process payment
    result = process_payment(amount)
    span.set_attribute("payment.success", result.success)
```

### Error Handling

```python
from fastapi_bootstrap.utils.telemetry import record_exception

try:
    result = risky_operation()
except Exception as e:
    record_exception(e, {"operation": "risky_operation"})
    # Handle the exception
```

### Context Propagation for Microservices

```python
from fastapi_bootstrap.utils.telemetry import propagate_context
import requests

def call_external_service(url, data):
    headers = {"Content-Type": "application/json"}
    headers = propagate_context(headers)  # Add trace context to headers
    response = requests.post(url, json=data, headers=headers)
    return response
```

### Metrics Collection

```python
from fastapi_bootstrap.utils.telemetry import create_metrics_counter, create_metrics_histogram
import time

# Create metrics
order_counter = create_metrics_counter("orders.created", "Number of orders created")
payment_latency = create_metrics_histogram("payment.processing_time", "Payment processing time in ms")

# Use the metrics
def process_order(order_data):
    # Increment counter with dimensions
    order_counter.add(1, {"order_type": order_data.type})

    # Track processing time
    start_time = time.perf_counter()
    result = payment_processor.process(order_data.payment)
    duration_ms = (time.perf_counter() - start_time) * 1000
    payment_latency.record(duration_ms, {"payment_method": order_data.payment.method})

    return result
```

### Adding the Middleware

```python
from fastapi import FastAPI
from fastapi_bootstrap.utils.middleware import OpenTelemetryMiddleware

app = FastAPI()
app.add_middleware(OpenTelemetryMiddleware)
```

## Configuration

OpenTelemetry is configured using environment variables:

```bash
# Choose an exporter
OTEL_EXPORTER=xray|otlp|jaeger|console

# Enable debug mode (optional)
OTEL_DEBUG=true

# For OTLP exporter (Honeycomb, Lightstep, etc.)
OTEL_EXPORTER_OTLP_ENDPOINT=https://api.honeycomb.io:443
OTEL_EXPORTER_OTLP_HEADERS="x-honeycomb-team=YOUR_API_KEY"

# For Jaeger exporter
OTEL_EXPORTER_JAEGER_ENDPOINT=http://localhost:14268/api/traces

# Standard OpenTelemetry environment variables
OTEL_SERVICE_NAME=fastapi-bootstrap
OTEL_RESOURCE_ATTRIBUTES=deployment.region=us-west-2,team=backend,version=1.0.0
```

## Best Practices

1. **Name spans meaningfully**: Use descriptive names that indicate what operation is being performed
2. **Add context with attributes**: Include relevant business data as span attributes
3. **Record exceptions properly**: Always record exceptions in spans for better debugging
4. **Use baggage for cross-service context**: Pass important context between services
5. **Keep metrics and traces aligned**: Use the same dimension names for metrics and trace attributes

## Performance Considerations

- The overhead of OpenTelemetry tracing is minimal but not zero
- For extremely high-throughput services, consider sampling traces
- Configure appropriate batch sizes for exporters to balance latency and throughput

## Additional Resources

- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [FastAPI Instrumentation](https://opentelemetry-python-contrib.readthedocs.io/en/latest/instrumentation/fastapi/fastapi.html)
- [AWS X-Ray Exporter](https://aws-otel.github.io/docs/getting-started/python-sdk/trace-manual-instrumentation)
- [OpenTelemetry Best Practices](https://opentelemetry.io/docs/instrumentation/python/cookbook/)
