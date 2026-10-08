"""FastAPI APIRouter implementation."""
class APIRouter:
    def __init__(self, prefix: str = ""):
        self.prefix = prefix
        self.routes = []

    def get(self, path: str):
        def decorator(func):
            self.routes.append(("GET", self.prefix + path, func))
            return func
        return decorator
