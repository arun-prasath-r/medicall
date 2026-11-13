from sqlalchemy import text


def test_app_startup(client):
    """Verifies that the application root responds and exposes documentation."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "Medicall API" in data["message"]
    assert data["docs"] == "/docs"


def test_health_endpoint(client):
    """Verifies the /api/v1/health endpoint returns healthy status."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "medicall-backend"


def test_database_connection(db_session):
    """Verifies active SQLAlchemy database connectivity."""
    result = db_session.execute(text("SELECT 1")).scalar()
    assert result == 1

