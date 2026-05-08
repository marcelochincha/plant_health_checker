"""HTTP tests for GET /classifier/predictions."""
from __future__ import annotations

import io

from fastapi.testclient import TestClient

from services.classifier.tests.conftest import make_token


def _png_bytes() -> bytes:
    return (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
        b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4"
        b"\x89\x00\x00\x00\rIDATx\x9cc\xfa\xcf\x00\x00\x00\x02\x00\x01"
        b"\xe2!\xbc3\x00\x00\x00\x00IEND\xaeB`\x82"
    )


def test_history_without_token_returns_401(client: TestClient) -> None:
    """Listing predictions without a Bearer token is rejected."""
    response = client.get("/classifier/predictions")
    assert response.status_code == 401


def test_history_empty_for_new_user(client: TestClient) -> None:
    """A user who never predicted gets an empty list, not 404."""
    token = make_token(user_id=999)
    response = client.get(
        "/classifier/predictions",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json() == []


def test_history_returns_only_own_predictions(client: TestClient) -> None:
    """User A and user B cannot see each other's predictions."""
    token_a = make_token(user_id=1)
    token_b = make_token(user_id=2)

    a_post = client.post(
        "/classifier/predict",
        headers={"Authorization": f"Bearer {token_a}"},
        files={"file": ("a.png", io.BytesIO(_png_bytes()), "image/png")},
    )
    b_post = client.post(
        "/classifier/predict",
        headers={"Authorization": f"Bearer {token_b}"},
        files={"file": ("b.png", io.BytesIO(_png_bytes()), "image/png")},
    )
    assert a_post.status_code == 200
    assert b_post.status_code == 200

    a_history = client.get(
        "/classifier/predictions",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    b_history = client.get(
        "/classifier/predictions",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert a_history.status_code == 200
    assert b_history.status_code == 200

    a_rows = a_history.json()
    b_rows = b_history.json()
    assert len(a_rows) == 1
    assert len(b_rows) == 1
    assert a_rows[0]["user_id"] == 1
    assert a_rows[0]["image_filename"] == "a.png"
    assert b_rows[0]["user_id"] == 2
    assert b_rows[0]["image_filename"] == "b.png"


def test_history_orders_newest_first(client: TestClient) -> None:
    """Two consecutive predictions come back in newest-first order."""
    token = make_token(user_id=42)
    headers = {"Authorization": f"Bearer {token}"}

    first = client.post(
        "/classifier/predict",
        headers=headers,
        files={"file": ("first.png", io.BytesIO(_png_bytes()), "image/png")},
    )
    second = client.post(
        "/classifier/predict",
        headers=headers,
        files={"file": ("second.png", io.BytesIO(_png_bytes()), "image/png")},
    )
    assert first.status_code == 200
    assert second.status_code == 200

    history = client.get("/classifier/predictions", headers=headers).json()
    assert len(history) == 2
    assert history[0]["id"] > history[1]["id"]
    assert history[0]["image_filename"] == "second.png"
