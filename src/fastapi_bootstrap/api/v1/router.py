import time

from fastapi import APIRouter, HTTPException
from opentelemetry import trace

from fastapi_bootstrap.utils.telemetry import (
    add_span_attributes,
    get_tracer,
    timed_span,
    traced,
)

router = APIRouter(tags=["v1"])


@router.get("/")
async def root_v1():
    """
    Root endpoint for API v1
    """
    return {"version": "v1", "message": "Welcome to API v1"}


@router.get("/traced-example")
@traced(name="traced_example_endpoint", attributes={"endpoint.type": "example"})
async def traced_example():
    """
    Example endpoint showing custom OpenTelemetry tracing
    """
    # Add custom attributes to the current span
    add_span_attributes(
        {"custom.attribute": "example-value", "request.type": "internal"}
    )

    # Get a tracer for a specific component
    tracer = get_tracer("api.example")

    # Create a custom sub-span
    with tracer.start_as_current_span("process_data") as span:
        # Simulate some work
        time.sleep(0.1)

        # Add attributes to the span
        span.set_attribute("data.records.processed", 100)

        # Simulate a database call in another span
        with tracer.start_as_current_span("database_query") as db_span:
            db_span.set_attribute("db.system", "postgresql")
            db_span.set_attribute("db.operation", "select")
            time.sleep(0.2)

    return {
        "message": "Traced example request processed successfully",
        "trace_id": trace.get_current_span().get_span_context().trace_id,
    }


@router.get("/error-example")
@traced(name="error_example_endpoint")
async def error_example():
    """
    Example endpoint showing error tracing
    """
    # Simulate a failure
    try:
        # Start a new span for the failing operation
        tracer = get_tracer()
        with tracer.start_as_current_span("failing_operation") as span:
            span.set_attribute("operation.critical", True)
            # Simulate some work before failure
            time.sleep(0.1)
            # Raise an exception
            raise ValueError("Example error for demonstration")
    except Exception as e:
        # The traced decorator will record the exception and set the status
        # But we can also add custom handling here
        raise HTTPException(status_code=500, detail=f"Operation failed: {str(e)}")


@router.get("/timed-example")
@timed_span(name="timed_example_endpoint", attributes={"endpoint.type": "timed"})
async def timed_example():
    """
    Example endpoint showing timing measurement with spans
    """
    # Simulate some work
    time.sleep(0.3)

    # Get a tracer for a specific component
    tracer = get_tracer("api.timed_example")

    # Create a timed sub-operation
    with tracer.start_as_current_span("sub_operation") as span:
        # Set attributes
        span.set_attribute("operation.name", "database_query")

        # Record start time
        start = time.perf_counter()

        # Simulate work
        time.sleep(0.2)

        # Record execution time manually
        execution_time = (time.perf_counter() - start) * 1000  # Convert to ms
        span.set_attribute("execution_time_ms", execution_time)

    return {
        "message": "Timed operation completed",
        "time_attributes": "Check the 'execution_time_ms' attribute in the spans",
    }
