from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from backend.app.db.models.monitoring import UserFeedback
from backend.app.main import app

client = TestClient(app)


def test_post_feedback_invalid_rating() -> None:
    response = client.post(
        "/api/v1/feedback",
        json={
            "request_id": "test-uuid-bad",
            "rating": "superb",
        },
    )
    assert response.status_code == 422


@patch("backend.app.api.v1.endpoints.feedback.MonitoringService")
def test_post_feedback_returns_201(mock_service_class) -> None:
    mock_service = mock_service_class.return_value
    from datetime import UTC, datetime

    mock_service.record_feedback = AsyncMock(
        return_value=UserFeedback(
            id=1,
            request_id="test-uuid-feedback",
            rating="positive",
            feedback_text="nice",
            created_at=datetime.now(UTC),
        )
    )

    response = client.post(
        "/api/v1/feedback",
        json={
            "request_id": "test-uuid-feedback",
            "rating": "positive",
            "feedback_text": "nice",
        },
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["request_id"] == "test-uuid-feedback"
    assert payload["rating"] == "positive"
