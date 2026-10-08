"""Test APIRouter."""
from fastapi.routing.router import APIRouter

def test_router_get():
    router = APIRouter(prefix="/api")
    @router.get("/items")
    def get_items(): return []
    assert len(router.routes) == 1
