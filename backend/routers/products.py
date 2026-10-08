"""backend/routers/products.py

API router for product creation, URL metadata extraction, and OCR screenshot analysis.
"""

import os
import uuid
import shutil
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.schemas import (
    ProductCreate,
    ProductResponse,
    ProductUrlRequest,
    ProductExtractedResponse,
)
from backend.crud import create_product, get_product
from backend.services.product_service import extract_from_url, extract_from_image

router = APIRouter(prefix="/products", tags=["Products"])

UPLOAD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../uploads"))
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/manual", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product_manual(product: ProductCreate, db: Session = Depends(get_db)):
    return create_product(db, product)


@router.post("/analyze-url", response_model=ProductExtractedResponse)
def analyze_product_url(payload: ProductUrlRequest):
    if not payload.url.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="URL cannot be empty"
        )
    extracted = extract_from_url(payload.url.strip())
    return ProductExtractedResponse(**extracted)


@router.post("/analyze-image", response_model=ProductExtractedResponse)
async def analyze_product_image(file: UploadFile = File(...)):
    # Validate content type
    allowed_types = ["image/jpeg", "image/png", "image/webp", "image/bmp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{file.content_type}'. Please upload JPEG, PNG, or WebP.",
        )

    # Save to uploads directory
    file_ext = os.path.splitext(file.filename or "")[1] or ".png"
    unique_filename = f"{uuid.uuid4().hex}{file_ext}"
    saved_path = os.path.join(UPLOAD_DIR, unique_filename)

    with open(saved_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    extracted = extract_from_image(saved_path)
    # Store relative path so frontend can access /uploads/...
    extracted["image_path"] = f"/uploads/{unique_filename}"
    return ProductExtractedResponse(**extracted)


@router.get("/{product_id}", response_model=ProductResponse)
def fetch_product(product_id: int, db: Session = Depends(get_db)):
    product = get_product(db, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )
    return product
