"""
OpenTelemetry utilities for distributed tracing.
"""

import functools
import inspect
import time
from typing import Any, Callable, Dict, Optional, TypeVar, Union, cast

from opentelemetry import trace
from opentelemetry.trace import Span, Status, StatusCode

# Type variables for function decorators
F = TypeVar("F", bound=Callable[..., Any])
R = TypeVar("R")


def get_tracer(module_name: Optional[str] = None) -> trace.Tracer:
    """
    Get a tracer instance for the given module.

    Args:
        module_name: The name of the module. If not provided,
                     it will be inferred from the caller.

    Returns:
        An OpenTelemetry tracer instance.
    """
    if module_name is None:
        frame = inspect.currentframe()
        if frame is not None and frame.f_back is not None:
            module_name = frame.f_back.f_globals["__name__"]
        else:
            module_name = "fastapi_bootstrap.unknown"

    return trace.get_tracer(module_name or "fastapi_bootstrap.unknown")


def traced(
    name: Optional[str] = None,
    attributes: Optional[Dict[str, Union[str, bool, int, float]]] = None,
) -> Callable[[F], F]:
    """
    Decorator to create a span for a function.

    Args:
        name: The name of the span. If not provided, the function name will be used.
        attributes: Attributes to add to the span.

    Returns:
        The decorated function.
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get the span name
            span_name = name if name is not None else func.__name__

            # Get the tracer
            tracer = get_tracer(func.__module__)

            # Start a new span
            with tracer.start_as_current_span(span_name) as span:
                # Add attributes if provided
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)

                # Call the function
                try:
                    result = func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    # Add error information to the span
                    span.set_status(Status(StatusCode.ERROR))
                    span.record_exception(e)
                    raise

        return cast(F, wrapper)

    return decorator


def add_span_attributes(attributes: Dict[str, Union[str, bool, int, float]]) -> None:
    """
    Add attributes to the current active span.

    Args:
        attributes: A dictionary of attributes to add to the span.
    """
    current_span = trace.get_current_span()
    if current_span:
        for key, value in attributes.items():
            current_span.set_attribute(key, value)


def record_exception(
    exception: Exception, attributes: Optional[Dict[str, str]] = None
) -> None:
    """
    Record an exception in the current span.

    Args:
        exception: The exception to record.
        attributes: Additional attributes to add to the exception event.
    """
    current_span = trace.get_current_span()
    if current_span:
        current_span.record_exception(exception, attributes)
        current_span.set_status(Status(StatusCode.ERROR))


def create_span(
    name: str, attributes: Optional[Dict[str, Union[str, bool, int, float]]] = None
) -> Span:
    """
    Create a new span as a child of the current span.

    Args:
        name: The name of the span.
        attributes: Attributes to add to the span.

    Returns:
        The created span.
    """
    tracer = get_tracer()
    span = tracer.start_span(name)

    if attributes:
        for key, value in attributes.items():
            span.set_attribute(key, value)

    return span


def timed_span(
    name: Optional[str] = None,
    attributes: Optional[Dict[str, Union[str, bool, int, float]]] = None,
) -> Callable[[F], F]:
    """
    Decorator to measure and record the execution time of a function in a span.

    Args:
        name: The name of the span. If not provided, the function name will be used.
        attributes: Additional attributes to add to the span.

    Returns:
        The decorated function.
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get the span name
            span_name = name if name is not None else f"{func.__name__}_timed"

            # Get the tracer
            tracer = get_tracer(func.__module__)

            # Start a new span
            with tracer.start_as_current_span(span_name) as span:
                # Add attributes if provided
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)

                # Record start time
                start_time = time.perf_counter()

                # Call the function
                try:
                    result = func(*args, **kwargs)

                    # Record execution time
                    execution_time = (
                        time.perf_counter() - start_time
                    ) * 1000  # Convert to ms
                    span.set_attribute("execution_time_ms", execution_time)

                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    # Record execution time even on error
                    execution_time = (
                        time.perf_counter() - start_time
                    ) * 1000  # Convert to ms
                    span.set_attribute("execution_time_ms", execution_time)

                    # Add error information to the span
                    span.set_status(Status(StatusCode.ERROR))
                    span.record_exception(e)
                    raise

        return cast(F, wrapper)

    return decorator


def propagate_context(headers: Dict[str, str]) -> Dict[str, str]:
    """
    Extract context from incoming headers and update outgoing headers for context propagation.
    This is particularly useful for propagating trace context across service boundaries.

    Args:
        headers: The headers to update with context information.

    Returns:
        The updated headers with context information.
    """
    from opentelemetry.propagate import extract, inject
    from opentelemetry.trace import set_span_in_context

    # Extract context from headers
    context = extract(headers)

    # Create a new dictionary to avoid modifying the original
    new_headers = headers.copy()

    # Get current span and create a context with it
    current_span = trace.get_current_span()
    if current_span:
        context = set_span_in_context(current_span, context)

    # Inject the current context into the headers
    inject(new_headers, context=context)

    return new_headers


def create_baggage(key_values: Dict[str, str]) -> None:
    """
    Create and set baggage items for the current context.
    Baggage allows you to propagate key-value pairs alongside the trace context.

    Args:
        key_values: A dictionary of key-value pairs to add to the baggage.
    """
    from opentelemetry.baggage import set_baggage

    for key, value in key_values.items():
        set_baggage(key, value)


def get_baggage(key: str) -> Optional[str]:
    """
    Get a baggage value by key from the current context.

    Args:
        key: The baggage key to retrieve.

    Returns:
        The baggage value if found, None otherwise.
    """
    from opentelemetry.baggage import get_baggage

    value = get_baggage(key)
    return str(value) if value is not None else None


def create_metrics_counter(name: str, description: str, unit: str = "1") -> Any:
    """
    Create a counter metric for counting events.

    Args:
        name: The name of the metric.
        description: A description of what the metric represents.
        unit: The unit of the metric.

    Returns:
        A counter metric object.
    """
    try:
        from opentelemetry.metrics import get_meter

        meter = get_meter("fastapi_bootstrap")
        return meter.create_counter(name=name, description=description, unit=unit)
    except ImportError:
        # If metrics API is not available, return a dummy counter
        class DummyCounter:
            def add(
                self, value: float, attributes: Optional[Dict[str, Any]] = None
            ) -> None:
                pass

        return DummyCounter()


def create_metrics_histogram(name: str, description: str, unit: str = "ms") -> Any:
    """
    Create a histogram metric for measuring distributions.

    Args:
        name: The name of the metric.
        description: A description of what the metric represents.
        unit: The unit of the metric.

    Returns:
        A histogram metric object.
    """
    try:
        from opentelemetry.metrics import get_meter

        meter = get_meter("fastapi_bootstrap")
        return meter.create_histogram(name=name, description=description, unit=unit)
    except ImportError:
        # If metrics API is not available, return a dummy histogram
        class DummyHistogram:
            def record(
                self, value: float, attributes: Optional[Dict[str, Any]] = None
            ) -> None:
                pass

        return DummyHistogram()
