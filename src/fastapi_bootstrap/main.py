import os
import socket

from fastapi import FastAPI, Response

from fastapi_bootstrap.api.v1.router import router as router_v1

app = FastAPI(
    title="FastAPI Bootstrap",
    description="A bootstrapped FastAPI project with versioning and AWS Fargate deployment",
    version="1.0.0",
)


# Add health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "hostname": socket.gethostname()}


# Add readiness check endpoint for blue/green deployment
@app.get("/ready", tags=["Health"])
async def ready_check(response: Response):
    # This endpoint can be used to validate if the application is ready to receive traffic
    # during blue/green deployment
    try:
        # Add any additional readiness checks here (database connections, etc.)
        return {"status": "ready", "hostname": socket.gethostname()}
    except Exception as e:
        response.status_code = 503
        return {"status": "not ready", "reason": str(e)}


# Include versioned routers
app.include_router(router_v1, prefix="/api/v1")


# Add environment information
@app.get("/", tags=["Root"])
async def root():
    return {
        "app": "FastAPI Bootstrap",
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "hostname": socket.gethostname(),
    }
