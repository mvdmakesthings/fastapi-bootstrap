from fastapi_bootstrap.api.v1.router import router as router_v1


def test_v1_router_exists():
    assert router_v1
    assert router_v1.routes
