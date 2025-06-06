from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_bootstrap.api.v1.router import router as router_v1
import os
import boto3
import json
import logging

# OpenTelemetry imports
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
# AWS X-Ray integration
# Importable instrumentation libraries
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.botocore import BotocoreInstrumentor
# Optional instrumentation libraries that can be uncommented as needed
# from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
# from opentelemetry.instrumentation.redis import RedisInstrumentor
# from opentelemetry.instrumentation.pymysql import PyMySQLInstrumentor
# Jaeger exporter - will be imported dynamically if needed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("fastapi-bootstrap")

# Initialize FastAPI app
app = FastAPI(
    title="FastAPI Bootstrap",
    description="A bootstrapped FastAPI project with versioned APIs",
    version="0.1.0",
)

# Configure OpenTelemetry tracing
def setup_opentelemetry():
    """
    Set up OpenTelemetry with configurable exporter to support different
    observability providers. Supports:

    - AWS X-Ray (default): Set OTEL_EXPORTER=xray
    - OTLP (OpenTelemetry Protocol): Set OTEL_EXPORTER=otlp and OTEL_EXPORTER_OTLP_ENDPOINT
    - Jaeger: Set OTEL_EXPORTER=jaeger and OTEL_EXPORTER_JAEGER_ENDPOINT
    - Console (for debugging): Set OTEL_EXPORTER=console
    - Custom: Set OTEL_EXPORTER=custom and implement in the else clause

    Additional configuration can be provided through standard OpenTelemetry
    environment variables: https://opentelemetry.io/docs/concepts/sdk-configuration/
    """
    app_name = os.environ.get("APP_NAME", "fastapi-bootstrap")
    environment = os.environ.get("ENVIRONMENT", "dev")

    # Get additional attributes from environment
    attributes = {
        "service.name": app_name,
        "service.namespace": "fastapi",
        "deployment.environment": environment,
        "deployment.id": os.environ.get("DEPLOYMENT_ID", "unknown"),
    }

    # Add custom attributes if defined
    custom_attributes = os.environ.get("OTEL_RESOURCE_ATTRIBUTES", "")
    if custom_attributes:
        for attr in custom_attributes.split(','):
            if '=' in attr:
                key, value = attr.split('=', 1)
                attributes[key.strip()] = value.strip()

    # Create a resource with service info
    resource = Resource.create(attributes)

    # Set the tracer provider with the resource
    tracer_provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer_provider)

    # Configure the exporter based on environment variables
    exporter_type = os.environ.get("OTEL_EXPORTER", "xray")

    if exporter_type == "xray":
        # AWS X-Ray integration via propagator
        from opentelemetry.propagator.aws_xray import AwsXRayPropagator
        from opentelemetry import propagate

        # Set the propagator for X-Ray
        propagate.set_global_textmap(AwsXRayPropagator())

        # Use OTLP exporter with X-Ray propagator
        otlp_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
        otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
        tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

        logger.info("OpenTelemetry configured with AWS X-Ray integration")
    elif exporter_type == "otlp":
        # OTLP exporter (for most observability platforms like Honeycomb, Lightstep, etc.)
        otlp_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
        otlp_headers = os.environ.get("OTEL_EXPORTER_OTLP_HEADERS", "")

        headers = {}
        if otlp_headers:
            for header in otlp_headers.split(','):
                if '=' in header:
                    key, value = header.split('=', 1)
                    headers[key.strip()] = value.strip()

        otlp_exporter = OTLPSpanExporter(
            endpoint=otlp_endpoint,
            headers=headers if headers else None
        )
        tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        logger.info(f"OpenTelemetry configured with OTLP exporter at {otlp_endpoint}")
    elif exporter_type == "jaeger":
        # If Jaeger exporter is needed
        try:
            from opentelemetry.exporter.jaeger.thrift import JaegerExporter
            jaeger_endpoint = os.environ.get("OTEL_EXPORTER_JAEGER_ENDPOINT", "http://localhost:14268/api/traces")
            jaeger_exporter = JaegerExporter(
                collector_endpoint=jaeger_endpoint,
            )
            tracer_provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))
            logger.info(f"OpenTelemetry configured with Jaeger exporter at {jaeger_endpoint}")
        except ImportError:
            logger.warning("Jaeger exporter requested but opentelemetry-exporter-jaeger package not installed")
            logger.info("Install with: pip install opentelemetry-exporter-jaeger")
    elif exporter_type == "console":
        # Console exporter for debugging
        tracer_provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
        logger.info("OpenTelemetry configured with Console exporter for debugging")
    else:
        logger.warning(f"Unknown exporter type: {exporter_type}, tracing disabled")

    # Instrument FastAPI
    FastAPIInstrumentor.instrument_app(app, tracer_provider=tracer_provider)

    # Instrument other libraries
    RequestsInstrumentor().instrument(tracer_provider=tracer_provider)
    BotocoreInstrumentor().instrument(tracer_provider=tracer_provider)

    # Add more instrumentations as needed:
    # SQLAlchemyInstrumentor().instrument(tracer_provider=tracer_provider)
    # RedisInstrumentor().instrument(tracer_provider=tracer_provider)
    # PyMySQLInstrumentor().instrument(tracer_provider=tracer_provider)

    return tracer_provider

# Initialize OpenTelemetry if not running locally or if explicitly enabled
if os.environ.get("ENVIRONMENT") != "local" or os.environ.get("ENABLE_TRACING") == "true":
    setup_opentelemetry()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router_v1, prefix="/api/v1")

# Health check endpoint for ALB
@app.get("/health")
async def health():
    """
    Health check endpoint for the load balancer
    """
    return {"status": "healthy"}

# Readiness check endpoint for deployment
@app.get("/ready")
async def ready():
    """
    Readiness check endpoint for deployment
    """
    return {"status": "ready"}

# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint
    """
    return {
        "message": "Welcome to FastAPI Bootstrap",
        "docs_url": "/docs",
        "api_v1_url": "/api/v1"
    }

# Function to get parameters from SSM Parameter Store
def get_ssm_parameter(name: str, decrypt: bool = True):
    """
    Get a parameter from SSM Parameter Store
    """
    try:
        environment = os.environ.get("ENVIRONMENT", "dev")
        app_name = os.environ.get("APP_NAME", "fastapi-bootstrap")

        ssm = boto3.client('ssm')
        response = ssm.get_parameter(
            Name=f"/{app_name}/{environment}/{name}",
            WithDecryption=decrypt
        )
        return response['Parameter']['Value']
    except Exception as e:
        logger.error(f"Error getting SSM parameter {name}: {str(e)}")
        return None

# Structured logging helper
def log_event(event_type: str, **kwargs):
    """
    Log an event with structured data
    """
    logger.info(json.dumps({
        "event_type": event_type,
        "environment": os.environ.get("ENVIRONMENT", "dev"),
        "deployment_id": os.environ.get("DEPLOYMENT_ID", "unknown"),
        **kwargs
    }))