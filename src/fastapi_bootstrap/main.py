import os

from fastapi import FastAPI

from fastapi_bootstrap.api.v1.router import router as router_v1

app = FastAPI(
    title="FastAPI Bootstrap",
    description="A bootstrapped FastAPI project with versioning and AWS Fargate deployment",
    version="1.0.0",
)


# Add health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy"}


# Include versioned routers
app.include_router(router_v1, prefix="/api/v1")


# Add environment information
@app.get("/", tags=["Root"])
async def root():
    return {
        "app": "FastAPI Bootstrap",
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "development"),
    }
