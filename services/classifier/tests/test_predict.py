"""HTTP tests for POST /classifier/predict."""
from __future__ import annotations

import io

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from services.classifier.app.models import Prediction
from services.classifier.tests.conftest import make_token


def _png_bytes() -> bytes:
    """Smallest valid PNG payload — content does not matter, the model is stubbed."""
    return (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
        b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4"
        b"\x89\x00\x00\x00\rIDATx\x9cc\xfa\xcf\x00\x00\x00\x02\x00\x01"
        b"\xe2!\xbc3\x00\x00\x00\x00IEND\xaeB`\x82"
    )


def test_predict_without_token_returns_401(client: TestClient) -> None:
    """A predict request without a Bearer token is rejected with 401."""
    response = client.post(
        "/classifier/predict",
        files={"file": ("leaf.png", io.BytesIO(_png_bytes()), "image/png")},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "not authenticated"


def test_predict_with_token_persists_prediction(
    client: TestClient, db_session: Session
) -> None:
    """A valid prediction persists a row owned by the authenticated user."""
    token = make_token(user_id=7)
    response = client.post(
        "/classifier/predict",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("leaf.png", io.BytesIO(_png_bytes()), "image/png")},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["label"] == "healthy"
    assert body["confidence"] == 0.9
    assert body["user_id"] == 7
    assert body["image_filename"] == "leaf.png"

    rows = db_session.scalars(select(Prediction)).all()
    assert len(rows) == 1
    assert rows[0].user_id == 7
    assert rows[0].label == "healthy"


def test_predict_rejects_unsupported_content_type(client: TestClient) -> None:
    """Files that are not JPEG/PNG are rejected before reaching the model."""
    token = make_token(user_id=1)
    response = client.post(
        "/classifier/predict",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("a.txt", io.BytesIO(b"hello"), "text/plain")},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "unsupported content_type"


def test_predict_invalid_image_returns_400(
    client: TestClient, stub_classifier_predict
) -> None:
    """A ValueError from the classifier surfaces as 400 'invalid image'."""
    stub_classifier_predict.predict.side_effect = ValueError("bad bytes")
    token = make_token(user_id=2)
    response = client.post(
        "/classifier/predict",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("leaf.png", io.BytesIO(_png_bytes()), "image/png")},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "invalid image"
