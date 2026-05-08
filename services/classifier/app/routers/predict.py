"""HTTP routes for the classifier service: prediction (history lands in B4)."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi import File
from fastapi import HTTPException
from fastapi import UploadFile
from sqlalchemy.orm import Session

from ..db import get_db
from ..inference_singleton import get_classifier
from ..models import Prediction
from ..schemas import PredictionOut
from ..security import get_current_user_id


router = APIRouter()


_ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/jpg", "image/png"}


@router.post("/predict", response_model=PredictionOut)
def predict(
    user_id: Annotated[int, Depends(get_current_user_id)],
    db: Annotated[Session, Depends(get_db)],
    file: UploadFile = File(...),
) -> Prediction:
    """Run inference on the uploaded image and persist the result."""
    if file.content_type not in _ALLOWED_CONTENT_TYPES:
        raise HTTPException(400, "unsupported content_type")

    image_bytes = file.file.read()

    classifier = get_classifier()
    try:
        result = classifier.predict(image_bytes)
    except ValueError:
        raise HTTPException(400, "invalid image")

    pred = Prediction(
        user_id=user_id,
        label=result["label"],
        confidence=float(result["confidence"]),
        image_filename=file.filename,
    )
    db.add(pred)
    db.commit()
    db.refresh(pred)
    return pred
