from fastapi.testclient import TestClient

from app.main import app


def test_http_exception_uses_common_api_response() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/applications/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404
    payload = response.json()
    assert payload["success"] is False
    assert payload["data"] is None
    assert payload["error"]
    assert "timestamp" in payload
