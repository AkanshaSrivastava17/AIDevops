"""Requests Session implementation."""
class Session:
    def __init__(self):
        self.headers = {}
        self.auth = None

    def request(self, method: str, url: str, **kwargs):
        return {"status_code": 200, "url": url, "method": method}
