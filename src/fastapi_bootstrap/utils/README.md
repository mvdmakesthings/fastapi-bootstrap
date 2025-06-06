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

# For OTLP exporter (Honeycomb, Lightstep, etc.)
OTEL_EXPORTER_OTLP_ENDPOINT=https://api.honeycomb.io:443
OTEL_EXPORTER_OTLP_HEADERS="x-honeycomb-team=YOUR_API_KEY"

# For Jaeger exporter
OTEL_EXPORTER_JAEGER_ENDPOINT=http://localhost:14268/api/traces

# Other standard OpenTelemetry environment variables
OTEL_SERVICE_NAME=fastapi-bootstrap
OTEL_RESOURCE_ATTRIBUTES=deployment.region=us-west-2,team=backend
```

## Additional Resources

- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [FastAPI Instrumentation](https://opentelemetry-python-contrib.readthedocs.io/en/latest/instrumentation/fastapi/fastapi.html)
- [AWS X-Ray Exporter](https://aws-otel.github.io/docs/getting-started/python-sdk/trace-manual-instrumentation)
