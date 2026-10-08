"""Test Session."""
from requests.sessions.session import Session

def test_session_request():
    s = Session()
    resp = s.request("GET", "https://httpbin.org/get")
    assert resp["status_code"] == 200
