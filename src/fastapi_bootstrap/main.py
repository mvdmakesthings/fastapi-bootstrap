import json
import logging
import os

import boto3
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# OpenTelemetry imports
from opentelemetry import propagate, trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.botocore import BotocoreInstrumentor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# Instrumentation libraries
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.propagators.aws.aws_xray_propagator import AwsXRayPropagator

# AWS X-Ray integration
from opentelemetry.sdk.extension.aws.trace import AwsXRayIdGenerator
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

from fastapi_bootstrap.api.v1.router import router as router_v1
from fastapi_bootstrap.utils.middleware import OpenTelemetryMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("fastapi-bootstrap")

# Initialize FastAPI app
app = FastAPI(
    title="FastAPI Bootstrap",
    description="A bootstrapped FastAPI project with versioned APIs",
    version="0.1.0",
)

# Add OpenTelemetry middleware for request context
app.add_middleware(OpenTelemetryMiddleware)


# Configure OpenTelemetry tracing
def setup_opentelemetry():
    """
    Set up OpenTelemetry with AWS X-Ray integration for distributed tracing.
    """
    app_name = os.environ.get("APP_NAME", "fastapi-bootstrap")
    environment = os.environ.get("ENVIRONMENT", "dev")

    # Create resource with service info
    resource = Resource.create(
        {
            "service.name": app_name,
            "service.namespace": "fastapi",
            "deployment.environment": environment,
            "deployment.id": os.environ.get("DEPLOYMENT_ID", "unknown"),
        }
    )

    # Set up tracer provider with the resource
    tracer_provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer_provider)

    # Set the propagator for X-Ray
    propagate.set_global_textmap(AwsXRayPropagator())

    # Configure AWS X-Ray ID generator and OTLP exporter
    tracer_provider.id_generator = AwsXRayIdGenerator()
    otlp_exporter = OTLPSpanExporter()
    tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

    # Add console exporter for local debugging if enabled
    if os.environ.get("OTEL_DEBUG", "false").lower() == "true":
        tracer_provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

    # Instrument FastAPI
    FastAPIInstrumentor.instrument_app(app, tracer_provider=tracer_provider)

    # Instrument other libraries
    RequestsInstrumentor().instrument(tracer_provider=tracer_provider)
    BotocoreInstrumentor().instrument(tracer_provider=tracer_provider)

    logger.info("OpenTelemetry configured with AWS X-Ray integration")
    return tracer_provider


# Initialize OpenTelemetry
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
        "api_v1_url": "/api/v1",
    }


# Function to get parameters from SSM Parameter Store
def get_ssm_parameter(name: str, decrypt: bool = True):
    """
    Get a parameter from SSM Parameter Store
    """
    try:
        environment = os.environ.get("ENVIRONMENT", "dev")
        app_name = os.environ.get("APP_NAME", "fastapi-bootstrap")

        ssm = boto3.client("ssm")
        response = ssm.get_parameter(
            Name=f"/{app_name}/{environment}/{name}", WithDecryption=decrypt
        )
        return response["Parameter"]["Value"]
    except Exception as e:
        logger.error(f"Error getting SSM parameter {name}: {str(e)}")
        return None


# Structured logging helper
def log_event(event_type: str, **kwargs):
    """
    Log an event with structured data
    """
    logger.info(
        json.dumps(
            {
                "event_type": event_type,
                "environment": os.environ.get("ENVIRONMENT", "dev"),
                "deployment_id": os.environ.get("DEPLOYMENT_ID", "unknown"),
                **kwargs,
            }
        )
    )
